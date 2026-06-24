import frappe


def on_submit(doc, method=None):
    """Déclenché après soumission d'une Sales Invoice.

    Vérifie les expiration des produits vendus et log la transaction Cosmo.
    """
    try:
        _check_expiry_on_sale(doc)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Cosmo on_submit Sales Invoice {doc.name}")


def on_cancel(doc, method=None):
    """Déclenché lors de l'annulation d'une Sales Invoice."""
    try:
        frappe.logger().info(f"Cosmo: Sales Invoice {doc.name} cancelled")
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Cosmo on_cancel Sales Invoice {doc.name}")


def _check_expiry_on_sale(doc):
    """Alerte si un produit vendu est proche de l'expiration."""
    from frappe.utils import add_days, nowdate

    for item in doc.items:
        expiry = frappe.db.get_value("Item", item.item_code, "cosmo_expiry_date")
        if expiry and str(expiry) < add_days(nowdate(), 7):
            frappe.msgprint(
                f"Attention : {item.item_name} expire le {expiry}",
                title="Produit proche de l'expiration",
                indicator="orange"
            )
