"""
cosmo_erp REST API — Contrat entre ERPNext et le MCP Server cosmo-mcp.

Toutes les fonctions sont @frappe.whitelist() et retournent des dicts JSON sérialisables.
Chaque réponse inclut un champ "message" lisible humainement (pour Hermes Agent).
Les erreurs retournent frappe.throw() avec un message en français.

Appelé via : POST /api/method/cosmo_erp.cosmo_erp.api.main.<function_name>
Auth : header Authorization: token {API_KEY}:{API_SECRET}
"""
import frappe
from frappe import _
from frappe.utils import flt, cint, nowdate, now_datetime, add_days, get_first_day

# TTL de la clé d'idempotence create_sale — assez long pour couvrir un retry
# après coupure réseau (fréquent à Madagascar), assez court pour ne pas
# accumuler indéfiniment dans le cache Redis.
SALE_IDEMPOTENCY_TTL_SECONDS = 24 * 60 * 60


# ══════════════════════════════════════════════════════════════════════════════
# AUTH / SESSION — pour le portail employés (BFF Next.js)
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_current_user_context():
    """Retourne l'utilisateur connecté et ses rôles Cosmo, pour piloter l'UI du portail.

    Appelé juste après le login (POST /api/method/login) pour savoir si
    l'employé est Caissière, Manager, ou les deux — le portail affiche/masque
    ses écrans en conséquence (pas de logique de permission dupliquée côté
    front : Frappe reste la seule source de vérité des rôles).

    Returns:
        dict: {user, full_name, roles, is_manager, is_cashier, message}
    """
    user = frappe.session.user
    if user == "Guest":
        frappe.throw(_("Non authentifié."), frappe.AuthenticationError)

    roles = frappe.get_roles(user)
    full_name = frappe.db.get_value("User", user, "full_name") or user

    return {
        "user": user,
        "full_name": full_name,
        "roles": roles,
        "is_manager": "Cosmo Manager" in roles,
        "is_cashier": "Cosmo Caissière" in roles,
        "message": f"Connecté en tant que {full_name}.",
    }


@frappe.whitelist()
def get_csrf_token():
    """Retourne le jeton CSRF de la session courante.

    Nécessaire pour tout POST du portail (create_sale, receive_stock,
    adjust_stock, ...) une fois authentifié par cookie de session `sid`
    (le portail utilise l'auth par session, pas par API Key — voir header
    du module). Frappe exige ce jeton sur les requêtes en écriture faites
    par un utilisateur en session cookie, pour se protéger du CSRF.

    Returns:
        dict: {csrf_token, message}
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Non authentifié."), frappe.AuthenticationError)
    return {
        "csrf_token": frappe.sessions.get_csrf_token(),
        "message": "Jeton CSRF généré.",
    }


# ══════════════════════════════════════════════════════════════════════════════
# STOCK & PRODUITS
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_item_stock(item_code=None, item_name=None):
    """Retourne le stock actuel d'un produit spécifique.

    Args:
        item_code: code ERPNext (prioritaire)
        item_name: nom du produit (si item_code non fourni — recherche fuzzy)

    Returns:
        dict: item_code, item_name, qty, uom, warehouse_details,
              cosmo_reorder_level, cosmo_expiry_date, is_low_stock, message
    """
    if not item_code and not item_name:
        frappe.throw(_("Fournir item_code ou item_name."))

    # Résoudre item_name → item_code si nécessaire
    if not item_code and item_name:
        results = frappe.db.sql("""
            SELECT item_code FROM `tabItem`
            WHERE (item_name LIKE %(q)s OR item_code LIKE %(q)s) AND disabled = 0
            LIMIT 1
        """, {"q": f"%{item_name}%"}, as_dict=True)
        if not results:
            frappe.throw(_("Produit '{0}' introuvable.").format(item_name))
        item_code = results[0].item_code

    item = frappe.db.get_value("Item", item_code,
        ["item_code", "item_name", "stock_uom", "cosmo_category", "cosmo_brand",
         "cosmo_reorder_level", "cosmo_expiry_date", "cosmo_preferred_supplier", "disabled"],
        as_dict=True)

    if not item or item.disabled:
        frappe.throw(_("Produit {0} introuvable ou désactivé.").format(item_code))

    warehouses = frappe.db.sql("""
        SELECT warehouse, actual_qty, valuation_rate
        FROM `tabBin`
        WHERE item_code = %(code)s AND actual_qty != 0
        ORDER BY actual_qty DESC
    """, {"code": item_code}, as_dict=True)

    total_qty = sum(flt(w.actual_qty) for w in warehouses)
    reorder = flt(item.cosmo_reorder_level)
    is_low = total_qty < reorder if reorder > 0 else False

    return {
        "item_code": item_code,
        "item_name": item.item_name,
        "cosmo_category": item.cosmo_category,
        "cosmo_brand": item.cosmo_brand,
        "qty": total_qty,
        "uom": item.stock_uom,
        "warehouse_details": warehouses,
        "cosmo_reorder_level": reorder,
        "cosmo_expiry_date": str(item.cosmo_expiry_date) if item.cosmo_expiry_date else None,
        "cosmo_preferred_supplier": item.cosmo_preferred_supplier,
        "is_low_stock": is_low,
        "message": (
            f"{item.item_name} : {total_qty} {item.stock_uom} en stock."
            + (" Stock bas (sous le seuil de reapprovisionnement)." if is_low else "")
        ),
    }


@frappe.whitelist()
def get_stock_for_items(item_codes):
    """Retourne le stock actuel pour une LISTE de produits en un seul appel.

    Pensé pour le panier du portail POS : rafraîchir le stock de toutes les
    lignes du panier juste avant l'encaissement sans faire N appels à
    get_item_stock (un par article).

    Args:
        item_codes: JSON list de item_code, ex. ["ITEM-001", "ITEM-002"]

    Returns:
        dict: {items: {item_code: {qty, is_low_stock}}, message}
    """
    import json
    if isinstance(item_codes, str):
        item_codes = json.loads(item_codes)

    if not item_codes:
        frappe.throw(_("La liste item_codes ne peut pas être vide."))
    if len(item_codes) > 200:
        frappe.throw(_("Maximum 200 articles par appel."))

    rows = frappe.db.sql("""
        SELECT
            i.item_code,
            i.cosmo_reorder_level,
            COALESCE(SUM(bin.actual_qty), 0) AS qty
        FROM `tabItem` i
        LEFT JOIN `tabBin` bin ON bin.item_code = i.item_code
        WHERE i.item_code IN %(codes)s
        GROUP BY i.item_code
    """, {"codes": tuple(item_codes)}, as_dict=True)

    by_code = {}
    for r in rows:
        reorder = flt(r.cosmo_reorder_level)
        qty = flt(r.qty)
        by_code[r.item_code] = {
            "qty": qty,
            "is_low_stock": qty < reorder if reorder > 0 else False,
        }

    # Les codes demandés mais introuvables (désactivé, supprimé, faute de frappe)
    # sont explicitement signalés à qty=None plutôt que silencieusement omis —
    # le panier du portail doit pouvoir distinguer "stock 0" de "produit invalide".
    for code in item_codes:
        if code not in by_code:
            by_code[code] = {"qty": None, "is_low_stock": False}

    return {
        "items": by_code,
        "message": f"Stock rafraîchi pour {len(item_codes)} article(s).",
    }


@frappe.whitelist()
def get_all_stock(warehouse=None):
    """Retourne le stock complet de tous les produits.

    Args:
        warehouse: filtrer par entrepôt (optionnel)

    Returns:
        list: [{item_code, item_name, qty, cosmo_category, cosmo_expiry_date, is_low_stock}]
    """
    values = {}
    values["warehouse"] = warehouse or None

    items = frappe.db.sql("""
        SELECT
            i.item_code,
            i.item_name,
            i.cosmo_category,
            i.cosmo_brand,
            i.cosmo_reorder_level,
            i.cosmo_expiry_date,
            i.stock_uom AS uom,
            COALESCE(SUM(bin.actual_qty), 0) AS qty
        FROM `tabItem` i
        LEFT JOIN `tabBin` bin ON bin.item_code = i.item_code
        WHERE i.disabled = 0 AND i.is_stock_item = 1
          AND (%(warehouse)s IS NULL OR bin.warehouse = %(warehouse)s)
        GROUP BY i.item_code
        HAVING COALESCE(SUM(bin.actual_qty), 0) >= 0
        ORDER BY i.item_name
        LIMIT 500
    """, values, as_dict=True)

    for item in items:
        item["is_low_stock"] = (
            flt(item.qty) < flt(item.cosmo_reorder_level)
            if flt(item.cosmo_reorder_level) > 0 else False
        )
        item["cosmo_expiry_date"] = str(item.cosmo_expiry_date) if item.cosmo_expiry_date else None

    return {"items": items, "count": len(items), "message": f"{len(items)} produits en stock."}


@frappe.whitelist()
def get_low_stock_items():
    """Retourne les produits dont le stock est sous le seuil de réapprovisionnement.

    Returns:
        dict: {count, items: [{item_code, item_name, qty, reorder_level, deficit, preferred_supplier}]}
    """
    items = frappe.db.sql("""
        SELECT
            i.item_code,
            i.item_name,
            i.cosmo_category,
            i.cosmo_brand,
            i.cosmo_reorder_level AS reorder_level,
            i.cosmo_preferred_supplier AS preferred_supplier,
            COALESCE(SUM(bin.actual_qty), 0) AS qty
        FROM `tabItem` i
        LEFT JOIN `tabBin` bin ON bin.item_code = i.item_code
        WHERE i.disabled = 0
          AND i.is_stock_item = 1
          AND i.cosmo_reorder_level > 0
        GROUP BY i.item_code
        HAVING qty < i.cosmo_reorder_level
        ORDER BY (qty / i.cosmo_reorder_level)
        LIMIT 100
    """, as_dict=True)

    for item in items:
        item["deficit"] = flt(item.reorder_level) - flt(item.qty)
        item["qty"] = flt(item.qty)

    count = len(items)
    if count == 0:
        msg = "Aucun produit en stock critique."
    else:
        msg = f"{count} produit(s) en stock critique : " + ", ".join(i.item_name for i in items[:5])
        if count > 5:
            msg += f" (et {count-5} autres)"

    return {"count": count, "items": items, "message": msg}


@frappe.whitelist()
def get_expiring_items(days=30):
    """Retourne les produits expirant dans les prochains N jours.

    Args:
        days: horizon en jours (défaut 30)

    Returns:
        dict: {count, items: [{item_code, item_name, cosmo_expiry_date, days_remaining, qty}]}
    """
    days = cint(days)
    cutoff = add_days(nowdate(), days)

    items = frappe.db.sql("""
        SELECT
            i.item_code,
            i.item_name,
            i.cosmo_brand,
            i.cosmo_expiry_date,
            DATEDIFF(i.cosmo_expiry_date, CURDATE()) AS days_remaining,
            COALESCE(SUM(bin.actual_qty), 0) AS qty
        FROM `tabItem` i
        LEFT JOIN `tabBin` bin ON bin.item_code = i.item_code
        WHERE i.disabled = 0
          AND i.cosmo_expiry_date IS NOT NULL
          AND i.cosmo_expiry_date <= %(cutoff)s
          AND i.cosmo_expiry_date >= CURDATE()
        GROUP BY i.item_code
        ORDER BY i.cosmo_expiry_date
        LIMIT 50
    """, {"cutoff": cutoff}, as_dict=True)

    for item in items:
        item["cosmo_expiry_date"] = str(item.cosmo_expiry_date)
        item["qty"] = flt(item.qty)

    count = len(items)
    if count == 0:
        msg = f"Aucun produit n'expire dans les {days} prochains jours."
    else:
        msg = f"{count} produit(s) expirent dans moins de {days} jours."

    return {"count": count, "items": items, "message": msg}


@frappe.whitelist()
def search_items(query, category=None):
    """Recherche fulltext dans le catalogue produits.

    Args:
        query: terme de recherche (nom, code, marque)
        category: filtrer par cosmo_category (optionnel)

    Returns:
        dict: {count, items: [{item_code, item_name, cosmo_brand, standard_rate, qty}]}
    """
    if not query or len(query.strip()) < 2:
        frappe.throw(_("La recherche doit contenir au moins 2 caractères."))

    items = frappe.db.sql("""
        SELECT
            i.item_code,
            i.item_name,
            i.cosmo_category,
            i.cosmo_brand,
            i.cosmo_expiry_date,
            COALESCE(ip.price_list_rate, 0) AS standard_rate,
            COALESCE(SUM(bin.actual_qty), 0) AS qty
        FROM `tabItem` i
        LEFT JOIN `tabItem Price` ip
            ON ip.item_code = i.item_code AND ip.selling = 1
            AND ip.price_list = (SELECT value FROM `tabSingles`
                WHERE doctype='Selling Settings' AND field='selling_price_list' LIMIT 1)
        LEFT JOIN `tabBin` bin ON bin.item_code = i.item_code
        WHERE i.disabled = 0
          AND (i.item_name LIKE %(q)s OR i.item_code LIKE %(q)s OR i.cosmo_brand LIKE %(q)s)
          AND (%(category)s IS NULL OR i.cosmo_category = %(category)s)
        GROUP BY i.item_code
        ORDER BY i.item_name
        LIMIT 20
    """, {"q": f"%{query.strip()}%", "category": category or None}, as_dict=True)

    for item in items:
        item["cosmo_expiry_date"] = str(item.cosmo_expiry_date) if item.cosmo_expiry_date else None

    count = len(items)
    return {
        "count": count,
        "items": items,
        "message": f"{count} produit(s) trouve(s) pour '{query}'." if count else f"Aucun produit trouve pour '{query}'.",
    }


@frappe.whitelist()
def create_item(item_name, cosmo_category, standard_rate, cosmo_brand=None,
                cosmo_expiry_date=None, cosmo_reorder_level=0, cosmo_preferred_supplier=None):
    """Crée un nouveau produit dans le catalogue ERPNext.

    Returns:
        dict: {item_code, item_name, message}
    """
    if not item_name or not cosmo_category:
        frappe.throw(_("item_name et cosmo_category sont obligatoires."))

    valid_categories = ["Soin Visage", "Soin Corps", "Maquillage", "Parfum", "Hygiene", "Autre"]
    if cosmo_category not in valid_categories:
        frappe.throw(_("Categorie invalide. Options : {0}").format(", ".join(valid_categories)))

    item = frappe.get_doc({
        "doctype": "Item",
        "item_name": item_name,
        "item_group": "Products",
        "is_stock_item": 1,
        "is_sales_item": 1,
        "is_purchase_item": 1,
        "cosmo_category": cosmo_category,
        "cosmo_brand": cosmo_brand or "",
        "cosmo_reorder_level": flt(cosmo_reorder_level),
        "cosmo_preferred_supplier": cosmo_preferred_supplier,
        "cosmo_expiry_date": cosmo_expiry_date or None,
    })
    item.insert(ignore_permissions=True)

    # Créer le prix de vente
    if flt(standard_rate) > 0:
        selling_pl = frappe.db.get_single_value("Selling Settings", "selling_price_list") or "Standard Selling"
        price = frappe.get_doc({
            "doctype": "Item Price",
            "item_code": item.item_code,
            "price_list": selling_pl,
            "price_list_rate": flt(standard_rate),
            "selling": 1,
        })
        price.insert(ignore_permissions=True)

    frappe.db.commit()

    return {
        "item_code": item.item_code,
        "item_name": item.item_name,
        "message": f"Produit '{item.item_name}' cree avec le code {item.item_code}.",
    }


@frappe.whitelist()
def update_item_price(item_code, new_price):
    """Met à jour le prix de vente d'un produit.

    Returns:
        dict: {success, old_price, new_price, message}
    """
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Produit {0} introuvable.").format(item_code))

    selling_pl = frappe.db.get_single_value("Selling Settings", "selling_price_list") or "Standard Selling"

    old_price = frappe.db.get_value("Item Price",
        {"item_code": item_code, "price_list": selling_pl, "selling": 1},
        "price_list_rate") or 0

    existing = frappe.db.get_value("Item Price",
        {"item_code": item_code, "price_list": selling_pl, "selling": 1}, "name")

    if existing:
        frappe.db.set_value("Item Price", existing, "price_list_rate", flt(new_price))
    else:
        price = frappe.get_doc({
            "doctype": "Item Price",
            "item_code": item_code,
            "price_list": selling_pl,
            "price_list_rate": flt(new_price),
            "selling": 1,
        })
        price.insert(ignore_permissions=True)

    frappe.db.commit()
    item_name = frappe.db.get_value("Item", item_code, "item_name")

    return {
        "success": True,
        "old_price": flt(old_price),
        "new_price": flt(new_price),
        "message": f"Prix de '{item_name}' mis a jour : {old_price} -> {new_price} Ar.",
    }


# ══════════════════════════════════════════════════════════════════════════════
# VENTES
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def create_sale(items, customer=None, payment_mode="Cash", discount=0, idempotency_key=None):
    """Crée une vente (Sales Invoice) et décrémente le stock.

    Args:
        items: JSON list [{item_code_or_name, qty, rate?}]
        customer: nom client (défaut "Walk-in Customer")
        payment_mode: "Cash" | "Card" | "Mobile Money"
        discount: remise en % (0-100)
        idempotency_key: identifiant unique généré côté portail (ex. UUID) au
            moment où la caissière tape "Encaisser". Si le même appel est
            rejoué (retry après coupure réseau, double-tap), la facture n'est
            PAS créée deux fois : la réponse déjà obtenue est simplement
            renvoyée. Fortement recommandé depuis le portail, optionnel pour
            les autres appelants (Hermes/MCP) qui gèrent déjà leurs propres
            retries en amont.

    Returns:
        dict: {invoice_name, total, grand_total, status, items_detail, message}
    """
    import json
    if isinstance(items, str):
        items = json.loads(items)

    if not items:
        frappe.throw(_("La liste d'articles ne peut pas être vide."))

    cache_key = None
    if idempotency_key:
        cache_key = f"cosmo_sale_idem:{idempotency_key}"
        # expires=True : cette clé porte une expiration (voir set_value plus
        # bas). Sans ce flag, RedisWrapper.get_value() met le résultat (y
        # compris None si rien n'est encore présent) en cache LOCAL au
        # process (frappe.local.cache) et ne revérifiera plus jamais Redis
        # pour cette clé tant que le process vit — un retry légitime dans le
        # même worker gunicorn recevrait alors un faux None et créerait un
        # doublon (confirmé par repro : bench console reproduit exactement
        # ce piège car il garde `frappe.local.cache` sur toute la session).
        cached = frappe.cache().get_value(cache_key, expires=True)
        if cached:
            return cached

    discount = min(max(flt(discount), 0), 100)

    # Résoudre les noms → codes et vérifier le stock
    resolved_items = []
    for item in items:
        code = item.get("item_code_or_name") or item.get("item_code")
        qty = flt(item.get("qty", 1))

        # Résolution si nom donné
        if not frappe.db.exists("Item", code):
            found = frappe.db.sql(
                "SELECT item_code FROM `tabItem` WHERE item_name LIKE %(q)s AND disabled=0 LIMIT 1",
                {"q": f"%{code}%"}, as_dict=True
            )
            if not found:
                frappe.throw(_("Produit '{0}' introuvable.").format(code))
            code = found[0].item_code

        # Vérifier stock
        stock = flt(frappe.db.sql(
            "SELECT COALESCE(SUM(actual_qty),0) FROM `tabBin` WHERE item_code=%s", code
        )[0][0])
        if stock < qty:
            item_name = frappe.db.get_value("Item", code, "item_name")
            frappe.throw(_(
                "Stock insuffisant pour {0} : {1} disponible(s), {2} demande(s)."
            ).format(item_name, stock, qty))

        # Récupérer le prix si non fourni
        rate = flt(item.get("rate", 0))
        if not rate:
            selling_pl = frappe.db.get_single_value("Selling Settings", "selling_price_list") or "Standard Selling"
            rate = flt(frappe.db.get_value(
                "Item Price",
                {"item_code": code, "price_list": selling_pl, "selling": 1},
                "price_list_rate"
            ) or 0)

        resolved_items.append({"item_code": code, "qty": qty, "rate": rate})

    customer = customer or "Walk-in Customer"
    if not frappe.db.exists("Customer", customer):
        _ensure_walkin_customer()
        customer = "Walk-in Customer"

    payment_map = {
        "Cash": "Cash",
        "Card": "Credit Card",
        "Mobile Money": "Mobile Money",
        "Especes": "Cash",
        "Carte": "Credit Card",
    }
    erp_payment_mode = payment_map.get(payment_mode, "Cash")

    # frappe.get_doc(dict).insert() ne passe PAS par le mécanisme de valeurs
    # par défaut habituellement appliqué par le JS du formulaire Desk (qui
    # préremplit "company" depuis les Global Defaults à l'ouverture du
    # formulaire) — sans ce champ explicite, set_missing_values() plante avec
    # "Please select a Company" (confirmé par repro locale : create_sale
    # n'avait jamais été exécuté de bout en bout jusqu'ici).
    company = _get_default_company()

    invoice = frappe.get_doc({
        "doctype": "Sales Invoice",
        "company": company,
        "customer": customer,
        "posting_date": nowdate(),
        "is_pos": 1,
        "cosmo_payment_mode": payment_mode,
        "additional_discount_percentage": discount,
        "items": [
            {"item_code": i["item_code"], "qty": i["qty"], "rate": i["rate"]}
            for i in resolved_items
        ],
        "payments": [{"mode_of_payment": erp_payment_mode, "amount": 0}],
    })
    invoice.set_missing_values()
    invoice.calculate_taxes_and_totals()
    if invoice.payments:
        invoice.payments[0].amount = invoice.grand_total

    from erpnext.stock.stock_ledger import NegativeStockError

    invoice.insert(ignore_permissions=True)
    try:
        invoice.submit()
    except NegativeStockError:
        # Une autre vente a pris le stock restant entre la vérification
        # ci-dessus et ce submit (deux caisses sur le même dernier article) —
        # ERPNext refuse le mouvement de stock négatif au niveau du grand
        # livre, c'est la vraie protection anti-survente. On nettoie la
        # facture non soumise et on renvoie un message clair plutôt qu'une
        # trace technique brute.
        invoice.delete(ignore_permissions=True)
        frappe.db.commit()
        frappe.throw(_(
            "Stock insuffisant : un ou plusieurs articles viennent d'être vendus "
            "par une autre caisse. Vérifiez le panier et réessayez."
        ))
    frappe.db.commit()

    items_detail = [
        f"  * {frappe.db.get_value('Item', i['item_code'], 'item_name')} x {i['qty']} = {i['qty']*i['rate']:.0f} Ar"
        for i in resolved_items
    ]

    result = {
        "invoice_name": invoice.name,
        "customer": customer,
        "total": flt(invoice.net_total),
        "discount": discount,
        "grand_total": flt(invoice.grand_total),
        "payment_mode": payment_mode,
        "status": "Submitted",
        "items_detail": items_detail,
        "message": f"Vente creee : {invoice.name} — {invoice.grand_total:.0f} Ar ({payment_mode}).",
    }

    if cache_key:
        frappe.cache().set_value(cache_key, result, expires_in_sec=SALE_IDEMPOTENCY_TTL_SECONDS)

    return result


@frappe.whitelist()
def get_daily_sales(date=None):
    """Résumé des ventes d'une journée.

    Returns:
        dict: {date, total_revenue, transaction_count, avg_basket, items_sold, message}
    """
    date = date or nowdate()
    result = frappe.db.sql("""
        SELECT
            COALESCE(SUM(si.grand_total), 0) AS total_revenue,
            COUNT(*) AS transaction_count,
            COALESCE(AVG(si.grand_total), 0) AS avg_basket
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1 AND si.posting_date = %(date)s
    """, {"date": date}, as_dict=True)[0]

    top_items = frappe.db.sql("""
        SELECT sii.item_name, SUM(sii.qty) AS qty, SUM(sii.amount) AS amount
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.docstatus = 1 AND si.posting_date = %(date)s
        GROUP BY sii.item_code ORDER BY amount DESC LIMIT 5
    """, {"date": date}, as_dict=True)

    return {
        "date": str(date),
        "total_revenue": flt(result.total_revenue),
        "transaction_count": cint(result.transaction_count),
        "avg_basket": flt(result.avg_basket),
        "top_items": top_items,
        "message": (
            f"{date} : {result.transaction_count} vente(s) — "
            f"{result.total_revenue:.0f} Ar (panier moyen {result.avg_basket:.0f} Ar)."
        ),
    }


@frappe.whitelist()
def get_sales_period(date_from, date_to):
    """Analyse des ventes sur une période.

    Returns:
        dict: {total_revenue, transactions, avg_basket, top_items, by_category, message}
    """
    result = frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total),0) AS total, COUNT(*) AS txn,
               COALESCE(AVG(grand_total),0) AS avg
        FROM `tabSales Invoice`
        WHERE docstatus=1 AND posting_date BETWEEN %(df)s AND %(dt)s
    """, {"df": date_from, "dt": date_to}, as_dict=True)[0]

    top_items = frappe.db.sql("""
        SELECT sii.item_name, SUM(sii.qty) AS qty, SUM(sii.amount) AS revenue
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name=sii.parent
        WHERE si.docstatus=1 AND si.posting_date BETWEEN %(df)s AND %(dt)s
        GROUP BY sii.item_code ORDER BY revenue DESC LIMIT 10
    """, {"df": date_from, "dt": date_to}, as_dict=True)

    by_category = frappe.db.sql("""
        SELECT COALESCE(i.cosmo_category,'Non categorise') AS category,
               SUM(sii.amount) AS revenue
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name=sii.parent
        JOIN `tabItem` i ON i.item_code=sii.item_code
        WHERE si.docstatus=1 AND si.posting_date BETWEEN %(df)s AND %(dt)s
        GROUP BY i.cosmo_category ORDER BY revenue DESC
    """, {"df": date_from, "dt": date_to}, as_dict=True)

    return {
        "date_from": date_from, "date_to": date_to,
        "total_revenue": flt(result.total), "transactions": cint(result.txn),
        "avg_basket": flt(result.avg), "top_items": top_items, "by_category": by_category,
        "message": f"{date_from} -> {date_to} : {result.txn} ventes, {result.total:.0f} Ar.",
    }


@frappe.whitelist()
def get_invoice(invoice_name):
    """Retourne une Sales Invoice complète.

    Returns:
        dict: invoice complet avec items, paiements, statut
    """
    if not frappe.db.exists("Sales Invoice", invoice_name):
        frappe.throw(_("Facture {0} introuvable.").format(invoice_name))

    inv = frappe.get_doc("Sales Invoice", invoice_name)
    return {
        "name": inv.name,
        "customer": inv.customer,
        "posting_date": str(inv.posting_date),
        "grand_total": flt(inv.grand_total),
        "status": inv.status,
        "cosmo_payment_mode": inv.get("cosmo_payment_mode", ""),
        "items": [
            {"item_code": i.item_code, "item_name": i.item_name,
             "qty": i.qty, "rate": i.rate, "amount": i.amount}
            for i in inv.items
        ],
        "message": f"Facture {invoice_name} — {inv.grand_total:.0f} Ar ({inv.status}).",
    }


@frappe.whitelist()
def cancel_invoice(invoice_name, reason):
    """Annule une Sales Invoice (action irréversible).

    Returns:
        dict: {success, message}
    """
    if not reason or len(reason.strip()) < 5:
        frappe.throw(_("Le motif d'annulation est obligatoire (min. 5 caractères)."))

    if not frappe.db.exists("Sales Invoice", invoice_name):
        frappe.throw(_("Facture {0} introuvable.").format(invoice_name))

    inv = frappe.get_doc("Sales Invoice", invoice_name)
    if inv.docstatus != 1:
        frappe.throw(_("Seules les factures soumises peuvent etre annulees (statut actuel : {0}).").format(inv.docstatus))

    try:
        inv.cancel()
        frappe.db.set_value("Sales Invoice", invoice_name, "cosmo_cancel_reason", reason)
        frappe.db.commit()
        return {"success": True, "message": f"Facture {invoice_name} annulee. Motif : {reason}"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Cosmo cancel_invoice {invoice_name}")
        frappe.throw(_("Erreur lors de l'annulation : {0}").format(str(e)))


# ══════════════════════════════════════════════════════════════════════════════
# STOCK ENTRIES
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def receive_stock(item_code, qty, rate, supplier=None, batch_no=None, expiry_date=None):
    """Enregistre une réception de marchandise (Stock Entry de type Receipt).

    Returns:
        dict: {stock_entry_name, item_name, qty, message}
    """
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Produit {0} introuvable.").format(item_code))

    qty = flt(qty)
    rate = flt(rate)
    if qty <= 0:
        frappe.throw(_("La quantité doit être supérieure à 0."))

    default_warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse") or "Stores - C"
    stock_uom = frappe.db.get_value("Item", item_code, "stock_uom")

    se = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Receipt",
        "supplier": supplier,
        "cosmo_origin": "MCP Server",
        "items": [{
            "item_code": item_code,
            "qty": qty,
            "basic_rate": rate,
            "t_warehouse": default_warehouse,
            "batch_no": batch_no or "",
            "expiry_date": expiry_date or None,
            # uom + conversion_factor explicites : sans ça, set_missing_values()
            # ne les déduit pas toujours tout seul côté serveur (uniquement
            # rempli normalement par le JS du formulaire Desk) et l'insert
            # échoue avec "UOM Conversion Factor is mandatory" (confirmé par
            # repro locale — receive_stock n'avait jamais été testé de bout
            # en bout jusqu'ici).
            "uom": stock_uom,
            "conversion_factor": 1,
        }],
    })
    se.set_missing_values()
    se.insert(ignore_permissions=True)
    se.submit()

    # Mise à jour de la date d'expiration sur l'Item si fournie
    if expiry_date:
        frappe.db.set_value("Item", item_code, "cosmo_expiry_date", expiry_date)

    frappe.db.commit()

    item_name = frappe.db.get_value("Item", item_code, "item_name")
    return {
        "stock_entry_name": se.name,
        "item_code": item_code,
        "item_name": item_name,
        "qty": qty,
        "rate": rate,
        "message": f"Reception enregistree : {qty} x {item_name} a {rate:.0f} Ar/u. ({se.name})",
    }


@frappe.whitelist()
def adjust_stock(item_code, new_qty, reason):
    """Ajuste le stock après inventaire ou perte (Stock Reconciliation).

    Returns:
        dict: {stock_entry_name, old_qty, new_qty, difference, message}
    """
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Produit {0} introuvable.").format(item_code))
    if not reason:
        frappe.throw(_("Le motif d'ajustement est obligatoire."))

    new_qty = flt(new_qty)
    default_warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse") or "Stores - C"

    old_qty = flt(frappe.db.sql(
        "SELECT COALESCE(SUM(actual_qty),0) FROM `tabBin` WHERE item_code=%s AND warehouse=%s",
        (item_code, default_warehouse)
    )[0][0])

    current_rate = flt(frappe.db.sql(
        "SELECT COALESCE(valuation_rate, 0) FROM `tabBin` WHERE item_code=%s LIMIT 1", item_code
    )[0][0]) or 100

    recon = frappe.get_doc({
        "doctype": "Stock Reconciliation",
        "purpose": "Stock Reconciliation",
        "posting_date": nowdate(),
        "items": [{
            "item_code": item_code,
            "warehouse": default_warehouse,
            "qty": new_qty,
            "valuation_rate": current_rate,
        }],
        "cosmo_reason": reason,
    })
    recon.insert(ignore_permissions=True)
    recon.submit()
    frappe.db.commit()

    item_name = frappe.db.get_value("Item", item_code, "item_name")
    diff = new_qty - old_qty
    sign = "+" if diff >= 0 else ""

    return {
        "stock_entry_name": recon.name,
        "item_name": item_name,
        "old_qty": old_qty,
        "new_qty": new_qty,
        "difference": diff,
        "message": f"Stock ajuste pour {item_name} : {old_qty} -> {new_qty} ({sign}{diff:.0f}). Motif : {reason}",
    }


# ══════════════════════════════════════════════════════════════════════════════
# CLIENTS / CRM
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def create_customer(customer_name, mobile_no=None, email_id=None):
    """Crée un nouveau client.

    Returns:
        dict: {customer_name, message}
    """
    if not customer_name:
        frappe.throw(_("Le nom du client est obligatoire."))

    if frappe.db.exists("Customer", customer_name):
        return {"customer_name": customer_name, "message": f"Client '{customer_name}' existe deja."}

    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": customer_name,
        "customer_type": "Individual",
        "customer_group": "Individual",
        "territory": "All Territories",
        "mobile_no": mobile_no or "",
        "email_id": email_id or "",
    })
    customer.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "customer_name": customer.name,
        "message": f"Client '{customer_name}' cree avec succes.",
    }


@frappe.whitelist()
def get_customer(customer_name=None, mobile_no=None):
    """Récupère le profil d'un client par nom ou téléphone.

    Returns:
        dict: {customer_name, mobile_no, email_id, total_purchases, last_purchase, message}
    """
    if not customer_name and not mobile_no:
        frappe.throw(_("Fournir customer_name ou mobile_no."))

    # Chercher par numéro de téléphone si fourni
    if mobile_no and not customer_name:
        found = frappe.db.get_value("Customer", {"mobile_no": mobile_no}, "name")
        if not found:
            return {"found": False, "message": f"Aucun client avec le numero {mobile_no}."}
        customer_name = found

    if not frappe.db.exists("Customer", customer_name):
        return {"found": False, "message": f"Client '{customer_name}' introuvable."}

    c = frappe.get_doc("Customer", customer_name)

    stats = frappe.db.sql("""
        SELECT COUNT(*) AS visits, COALESCE(SUM(grand_total),0) AS total,
               MAX(posting_date) AS last_purchase
        FROM `tabSales Invoice`
        WHERE customer=%(name)s AND docstatus=1
    """, {"name": customer_name}, as_dict=True)[0]

    return {
        "found": True,
        "customer_name": c.customer_name,
        "mobile_no": c.mobile_no or "",
        "email_id": c.email_id or "",
        "total_purchases": flt(stats.total),
        "visits": cint(stats.visits),
        "last_purchase": str(stats.last_purchase) if stats.last_purchase else None,
        "message": (
            f"{c.customer_name} — {stats.visits} visites, "
            f"{stats.total:.0f} Ar au total, derniere visite : {stats.last_purchase or 'jamais'}."
        ),
    }


@frappe.whitelist()
def get_customer_history(customer_name, limit=10):
    """Retourne l'historique d'achats d'un client.

    Returns:
        dict: {customer_name, invoices: [{name, date, total, items_count}], message}
    """
    limit = min(cint(limit), 50)
    invoices = frappe.db.sql("""
        SELECT name, posting_date AS date, grand_total AS total,
               (SELECT COUNT(*) FROM `tabSales Invoice Item` WHERE parent=si.name) AS items_count
        FROM `tabSales Invoice` si
        WHERE customer=%(name)s AND docstatus=1
        ORDER BY posting_date DESC
        LIMIT %(limit)s
    """, {"name": customer_name, "limit": limit}, as_dict=True)

    for inv in invoices:
        inv["date"] = str(inv["date"])

    return {
        "customer_name": customer_name,
        "invoices": invoices,
        "message": f"{len(invoices)} derniere(s) facture(s) pour {customer_name}.",
    }


@frappe.whitelist()
def get_top_customers(limit=10, period="month"):
    """Retourne les meilleurs clients par CA.

    Returns:
        dict: {period, customers: [{customer_name, total_spent, visits}], message}
    """
    limit = min(cint(limit), 50)
    valid_periods = {"today", "week", "month", "quarter", "year"}
    if period not in valid_periods:
        period = "month"
    period_days = {"today": 0, "week": 7, "month": 30, "quarter": 90, "year": 365}
    days_back = period_days[period]
    date_from = nowdate() if days_back == 0 else add_days(nowdate(), -days_back)

    if period == "today":
        date_condition = "posting_date = %(date_from)s"
    else:
        date_condition = "posting_date >= %(date_from)s"

    customers = frappe.db.sql(
        "SELECT customer AS customer_name, SUM(grand_total) AS total_spent, COUNT(*) AS visits"
        " FROM `tabSales Invoice`"
        " WHERE docstatus=1 AND " + date_condition +
        " GROUP BY customer ORDER BY total_spent DESC LIMIT %(limit)s",
        {"limit": limit, "date_from": date_from}, as_dict=True)

    top_name = customers[0].customer_name if customers else "aucune donnee"
    top_total = f"{customers[0].total_spent:.0f} Ar" if customers else ""

    return {
        "period": period,
        "customers": customers,
        "message": (
            f"Top {len(customers)} clients ({period}) : "
            + (f"{top_name} ({top_total})" if customers else "aucune donnee") + "."
        ),
    }


@frappe.whitelist()
def get_inactive_customers(days=60):
    """Retourne les clients sans achat depuis X jours.

    Returns:
        dict: {count, customers: [{customer_name, last_purchase, days_inactive}], message}
    """
    days = cint(days)
    cutoff = add_days(nowdate(), -days)

    customers = frappe.db.sql("""
        SELECT c.customer_name,
               MAX(si.posting_date) AS last_purchase,
               DATEDIFF(CURDATE(), MAX(si.posting_date)) AS days_inactive
        FROM `tabCustomer` c
        LEFT JOIN `tabSales Invoice` si ON si.customer=c.name AND si.docstatus=1
        WHERE c.disabled=0 AND c.name != 'Walk-in Customer'
        GROUP BY c.name
        HAVING last_purchase < %(cutoff)s OR last_purchase IS NULL
        ORDER BY days_inactive DESC
        LIMIT 50
    """, {"cutoff": cutoff}, as_dict=True)

    for c in customers:
        c["last_purchase"] = str(c["last_purchase"]) if c["last_purchase"] else None

    return {
        "count": len(customers),
        "customers": customers,
        "message": f"{len(customers)} client(s) inactif(s) depuis plus de {days} jours.",
    }


# ══════════════════════════════════════════════════════════════════════════════
# FOURNISSEURS & COMMANDES
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_suppliers():
    """Retourne la liste des fournisseurs actifs.

    Returns:
        dict: {suppliers: [{supplier_name, mobile_no, preferred_items}], message}
    """
    suppliers = frappe.db.sql("""
        SELECT s.name AS supplier_name, s.mobile_no, s.supplier_group
        FROM `tabSupplier` s
        WHERE s.disabled=0
        ORDER BY s.supplier_name
        LIMIT 100
    """, as_dict=True)

    # Ajouter les produits préférés pour chaque fournisseur
    for sup in suppliers:
        preferred = frappe.db.sql("""
            SELECT item_name FROM `tabItem`
            WHERE cosmo_preferred_supplier=%(name)s AND disabled=0
            LIMIT 5
        """, {"name": sup.supplier_name}, as_list=True)
        sup["preferred_items"] = [p[0] for p in preferred]

    return {
        "suppliers": suppliers,
        "message": f"{len(suppliers)} fournisseur(s) actif(s).",
    }


@frappe.whitelist()
def create_supplier_order(supplier_name, items, notes=None):
    """Crée une commande fournisseur (Cosmo Supplier Order).

    Args:
        supplier_name: nom du fournisseur ERPNext
        items: JSON list [{item_code_or_name, qty, rate?}]
        notes: remarques optionnelles

    Returns:
        dict: {order_name, supplier, total, items_count, message}
    """
    import json
    if isinstance(items, str):
        items = json.loads(items)

    if not frappe.db.exists("Supplier", supplier_name):
        frappe.throw(_("Fournisseur '{0}' introuvable.").format(supplier_name))

    resolved_items = []
    for item in items:
        code = item.get("item_code_or_name") or item.get("item_code")
        if not frappe.db.exists("Item", code):
            found = frappe.db.sql(
                "SELECT item_code FROM `tabItem` WHERE item_name LIKE %(q)s LIMIT 1",
                {"q": f"%{code}%"}, as_dict=True
            )
            if not found:
                frappe.throw(_("Produit '{0}' introuvable.").format(code))
            code = found[0].item_code

        resolved_items.append({
            "item_code": code,
            "qty": flt(item.get("qty", 1)),
            "rate": flt(item.get("rate", 0)),
        })

    order = frappe.get_doc({
        "doctype": "Cosmo Supplier Order",
        "supplier": supplier_name,
        "order_date": nowdate(),
        "origin": "Hermes Agent",
        "cosmo_notes": notes or "",
        "items": resolved_items,
    })
    order.insert(ignore_permissions=True)
    frappe.db.commit()

    total = sum(i["qty"] * i["rate"] for i in resolved_items)

    return {
        "order_name": order.name,
        "supplier": supplier_name,
        "items_count": len(resolved_items),
        "total": total,
        "message": f"Commande {order.name} creee pour {supplier_name} ({len(resolved_items)} article(s)).",
    }


@frappe.whitelist()
def get_pending_orders():
    """Retourne les commandes fournisseurs en attente (Envoyé ou Confirmé).

    Returns:
        dict: {count, orders: [{name, supplier, order_date, status, total_amount}], message}
    """
    orders = frappe.db.sql("""
        SELECT name, supplier, order_date, status, total_amount, expected_delivery
        FROM `tabCosmo Supplier Order`
        WHERE status IN ('Envoye', 'Confirme') AND docstatus=1
        ORDER BY order_date DESC
        LIMIT 20
    """, as_dict=True)

    for o in orders:
        o["order_date"] = str(o["order_date"])
        o["expected_delivery"] = str(o["expected_delivery"]) if o["expected_delivery"] else None

    return {
        "count": len(orders),
        "orders": orders,
        "message": f"{len(orders)} commande(s) fournisseur en attente." if orders else "Aucune commande en attente.",
    }


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD & RAPPORTS
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_dashboard_summary():
    """Résumé complet de la boutique pour le briefing Hermes.

    Returns:
        dict: {today_revenue, today_transactions, low_stock_count,
               expiring_soon_count, top_product_today, message}
    """
    today = nowdate()

    today_stats = frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total),0) AS revenue, COUNT(*) AS txn
        FROM `tabSales Invoice`
        WHERE docstatus=1 AND posting_date=%(today)s
    """, {"today": today}, as_dict=True)[0]

    low_stock = frappe.db.sql("""
        SELECT COUNT(*) FROM (
            SELECT i.item_code FROM `tabItem` i
            LEFT JOIN `tabBin` bin ON bin.item_code=i.item_code
            WHERE i.disabled=0 AND i.is_stock_item=1 AND i.cosmo_reorder_level>0
            GROUP BY i.item_code HAVING COALESCE(SUM(bin.actual_qty),0) < i.cosmo_reorder_level
        ) AS ls
    """)[0][0]

    expiring = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabItem`
        WHERE disabled=0 AND cosmo_expiry_date IS NOT NULL
          AND cosmo_expiry_date <= %(cutoff)s AND cosmo_expiry_date >= %(today)s
    """, {"cutoff": add_days(today, 30), "today": today})[0][0]

    top_product = frappe.db.sql("""
        SELECT sii.item_name, SUM(sii.amount) AS revenue
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name=sii.parent
        WHERE si.docstatus=1 AND si.posting_date=%(today)s
        GROUP BY sii.item_code ORDER BY revenue DESC LIMIT 1
    """, {"today": today}, as_dict=True)

    alerts = []
    if cint(low_stock) > 0:
        alerts.append(f"{low_stock} produit(s) en stock critique")
    if cint(expiring) > 0:
        alerts.append(f"{expiring} produit(s) expirent dans 30j")

    return {
        "today_revenue": flt(today_stats.revenue),
        "today_transactions": cint(today_stats.txn),
        "low_stock_count": cint(low_stock),
        "expiring_soon_count": cint(expiring),
        "top_product_today": top_product[0].item_name if top_product else None,
        "alerts": alerts,
        "message": (
            f"Aujourd'hui : {today_stats.txn} vente(s) — {today_stats.revenue:.0f} Ar. "
            + (" | ".join(alerts) if alerts else "Aucune alerte.")
        ),
    }


@frappe.whitelist()
def get_category_breakdown(period="month"):
    """Répartition du CA par catégorie cosmétique.

    Returns:
        dict: {period, categories: [{category, revenue, units_sold, percentage}], message}
    """
    valid_periods = {"today", "week", "month"}
    if period not in valid_periods:
        period = "month"
    period_days = {"today": 0, "week": 7, "month": 30}
    days_back = period_days[period]
    date_from = nowdate() if days_back == 0 else add_days(nowdate(), -days_back)

    if period == "today":
        date_condition = "si.posting_date = %(date_from)s"
    else:
        date_condition = "si.posting_date >= %(date_from)s"

    rows = frappe.db.sql(
        "SELECT COALESCE(i.cosmo_category,'Non categorise') AS category,"
        " SUM(sii.amount) AS revenue, SUM(sii.qty) AS units_sold"
        " FROM `tabSales Invoice Item` sii"
        " JOIN `tabSales Invoice` si ON si.name=sii.parent"
        " JOIN `tabItem` i ON i.item_code=sii.item_code"
        " WHERE si.docstatus=1 AND " + date_condition +
        " GROUP BY i.cosmo_category ORDER BY revenue DESC",
        {"date_from": date_from}, as_dict=True)

    total = sum(flt(r.revenue) for r in rows)
    for r in rows:
        r["revenue"] = flt(r.revenue)
        r["units_sold"] = flt(r.units_sold)
        r["percentage"] = round((flt(r.revenue) / total * 100), 1) if total else 0

    return {"period": period, "categories": rows, "total": total, "message": f"Repartition CA ({period})."}


@frappe.whitelist()
def get_revenue_trend(days=30):
    """Évolution du CA sur les derniers N jours.

    Returns:
        dict: {days, trend: [{date, revenue, transactions}], message}
    """
    days = min(cint(days), 90)
    start = add_days(nowdate(), -days + 1)

    rows = frappe.db.sql("""
        SELECT DATE(posting_date) AS date,
               COALESCE(SUM(grand_total),0) AS revenue,
               COUNT(*) AS transactions
        FROM `tabSales Invoice`
        WHERE docstatus=1 AND posting_date >= %(start)s
        GROUP BY DATE(posting_date)
        ORDER BY date
    """, {"start": start}, as_dict=True)

    for r in rows:
        r["date"] = str(r["date"])

    return {
        "days": days,
        "trend": rows,
        "message": f"Tendance CA sur {days} jours ({len(rows)} jours avec ventes).",
    }


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS PRIVES
# ══════════════════════════════════════════════════════════════════════════════

def _get_default_company():
    """Résout la Company par défaut pour les documents créés côté serveur
    (Sales Invoice, etc.) sans passer par le JS du formulaire Desk.

    Ordre : Global Defaults > Default Company, sinon l'unique Company du
    site (site à une seule boutique — cas de cosmo_erp). Échoue proprement
    si aucune Company n'existe ou si plusieurs existent sans default défini,
    plutôt que de deviner (même logique que le patch d'hydratation Ravaka).
    """
    default_company = frappe.defaults.get_global_default("company")
    if default_company and frappe.db.exists("Company", default_company):
        return default_company

    companies = frappe.get_all("Company", pluck="name")
    if len(companies) == 1:
        return companies[0]

    if not companies:
        frappe.throw(_("Aucune Company configurée sur ce site. Configurez-en une avant de créer une vente."))

    frappe.throw(_(
        "Impossible de déterminer la Company pour cette vente : {0} Companies existent "
        "et aucune n'est définie par défaut (Setup > Global Defaults > Default Company)."
    ).format(len(companies)))


def _ensure_walkin_customer():
    """Crée le client Walk-in Customer s'il n'existe pas."""
    if not frappe.db.exists("Customer", "Walk-in Customer"):
        c = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Walk-in Customer",
            "customer_type": "Individual",
            "customer_group": "Individual",
            "territory": "All Territories",
        })
        c.insert(ignore_permissions=True)
        frappe.db.commit()
