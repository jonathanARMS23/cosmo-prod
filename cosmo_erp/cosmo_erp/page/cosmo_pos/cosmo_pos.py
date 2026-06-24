"""Backend API pour le POS Cosmo — endpoints appelés via frappe.call() depuis le JS."""
import frappe
from frappe import _
from frappe.utils import flt, nowdate, now_datetime, get_url


@frappe.whitelist()
def get_items_with_stock(category=None, search=None):
    """Retourne les articles en stock avec leurs infos cosmétiques et le niveau de stock actuel.

    Args:
        category: filtre cosmo_category (optionnel)
        search: filtre textuel sur item_name ou cosmo_brand (optionnel)

    Returns:
        list[dict]: articles avec item_code, item_name, price, stock_qty,
                    cosmo_category, cosmo_brand, image
    """
    items = frappe.db.sql("""
        SELECT
            i.item_code,
            i.item_name,
            i.cosmo_category,
            i.cosmo_brand,
            i.image,
            COALESCE(ip.price_list_rate, 0) AS price,
            COALESCE(SUM(bin.actual_qty), 0) AS stock_qty,
            i.cosmo_reorder_level,
            i.cosmo_expiry_date
        FROM `tabItem` i
        LEFT JOIN `tabItem Price` ip
            ON ip.item_code = i.item_code
            AND ip.selling = 1
            AND ip.price_list = (
                SELECT default_price_list FROM `tabSelling Settings` LIMIT 1
            )
        LEFT JOIN `tabBin` bin ON bin.item_code = i.item_code
        WHERE i.disabled = 0 AND i.is_sales_item = 1
          AND (%(category)s IS NULL OR i.cosmo_category = %(category)s)
          AND (%(search)s IS NULL OR i.item_name LIKE %(search_like)s OR i.cosmo_brand LIKE %(search_like)s)
        GROUP BY i.item_code
        ORDER BY i.item_name
        LIMIT 200
    """, {"category": category or None, "search": search or None, "search_like": f"%{search}%" if search else None}, as_dict=True)

    return items


@frappe.whitelist(allow_guest=False)
def get_item_categories():
    """Retourne la liste des catégories cosmétiques distinctes présentes dans le catalogue."""
    categories = frappe.db.sql("""
        SELECT DISTINCT cosmo_category
        FROM `tabItem`
        WHERE cosmo_category IS NOT NULL AND cosmo_category != ''
          AND disabled = 0 AND is_sales_item = 1
        ORDER BY cosmo_category
    """, as_list=True)
    return [c[0] for c in categories if c[0]]


@frappe.whitelist(allow_guest=False)
def create_sale(items, payment_mode, customer=None, discount_amount=0, discount_percent=0):
    """Crée une Sales Invoice depuis le POS Cosmo.

    Args:
        items: JSON list de {item_code, qty, rate}
        payment_mode: "Espèces" | "Carte" | "Mobile Money"
        customer: nom du client (optionnel, défaut: "Walk-in Customer")
        discount_amount: remise en montant (optionnel)
        discount_percent: remise en % (optionnel)

    Returns:
        dict: {invoice_name, grand_total, print_url}
    """
    import json

    if isinstance(items, str):
        items = json.loads(items)

    # Client par défaut pour les ventes anonymes
    customer = customer or _get_default_customer()

    # Vérification du stock avant création
    for item in items:
        stock = flt(frappe.db.sql(
            "SELECT COALESCE(SUM(actual_qty),0) FROM `tabBin` WHERE item_code=%s",
            item["item_code"]
        )[0][0])
        if stock < flt(item["qty"]):
            frappe.throw(_(
                "Stock insuffisant pour {0} : {1} disponible(s), {2} demandé(s)."
            ).format(item["item_code"], stock, item["qty"]))

    # Récupère la caisse POS par défaut
    pos_profile = _get_default_pos_profile()

    invoice = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": customer,
        "posting_date": nowdate(),
        "posting_time": now_datetime().strftime("%H:%M:%S"),
        "due_date": nowdate(),
        "is_pos": 1,
        "pos_profile": pos_profile,
        "cosmo_payment_mode": payment_mode,
        "discount_amount": flt(discount_amount),
        "additional_discount_percentage": flt(discount_percent),
        "items": [
            {
                "item_code": item["item_code"],
                "qty": flt(item["qty"]),
                "rate": flt(item.get("rate", 0)) or frappe.db.get_value(
                    "Item Price",
                    {"item_code": item["item_code"], "selling": 1},
                    "price_list_rate"
                ) or 0,
            }
            for item in items
        ],
        "payments": [
            {
                "mode_of_payment": _map_payment_mode(payment_mode),
                "amount": 0,  # calculé automatiquement par Frappe
            }
        ],
    })
    invoice.set_missing_values()
    invoice.calculate_taxes_and_totals()

    # Règle le paiement sur le total réel
    if invoice.payments:
        invoice.payments[0].amount = invoice.grand_total

    invoice.insert(ignore_permissions=True)
    invoice.submit()

    return {
        "invoice_name": invoice.name,
        "grand_total": invoice.grand_total,
        "print_url": get_url(f"/printview?doctype=Sales+Invoice&name={invoice.name}&format=Cosmo+Invoice"),
    }


@frappe.whitelist(allow_guest=False)
def get_daily_summary():
    """Retourne le résumé de la journée en cours pour l'en-tête du POS."""
    today = nowdate()
    result = frappe.db.sql("""
        SELECT
            COALESCE(SUM(grand_total), 0) AS revenue,
            COUNT(*) AS transaction_count,
            COALESCE(AVG(grand_total), 0) AS avg_basket
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND posting_date = %(today)s
    """, {"today": today}, as_dict=True)

    return result[0] if result else {"revenue": 0, "transaction_count": 0, "avg_basket": 0}


@frappe.whitelist(allow_guest=False)
def close_register():
    """Déclenche la clôture de caisse : retourne le résumé du jour."""
    summary = get_daily_summary()
    # Log la clôture
    frappe.logger().info(
        f"Cosmo POS: Clôture caisse {nowdate()} — "
        f"{summary['transaction_count']} transactions, "
        f"{summary['revenue']} MGA"
    )
    return summary


def _get_default_customer():
    """Retourne le client par défaut pour les ventes anonymes."""
    default = frappe.db.get_single_value("Selling Settings", "customer") or "Walk-in Customer"
    if not frappe.db.exists("Customer", default):
        # Crée le client par défaut s'il n'existe pas
        c = frappe.get_doc({"doctype": "Customer", "customer_name": "Walk-in Customer", "customer_type": "Individual"})
        c.insert(ignore_permissions=True)
        frappe.db.commit()
    return default


def _get_default_pos_profile():
    """Retourne le profil POS par défaut pour l'utilisateur courant."""
    pos_profile = frappe.db.get_value(
        "POS Profile User",
        {"user": frappe.session.user, "default": 1},
        "parent"
    )
    return pos_profile or ""


def _map_payment_mode(mode):
    """Mappe les modes de paiement Cosmo vers les modes ERPNext."""
    mapping = {
        "Espèces": "Cash",
        "Carte": "Credit Card",
        "Mobile Money": "Mobile Money",
    }
    return mapping.get(mode, "Cash")
