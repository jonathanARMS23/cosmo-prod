import frappe


def check_stock_alerts():
    """Vérifie les items en dessous du seuil de réapprovisionnement et envoie des alertes."""
    try:
        # Récupère les items avec stock < reorder_level
        low_stock_items = frappe.db.sql("""
            SELECT
                i.item_code,
                i.item_name,
                i.cosmo_reorder_level,
                bin.actual_qty,
                i.cosmo_preferred_supplier
            FROM `tabItem` i
            JOIN `tabBin` bin ON bin.item_code = i.item_code
            WHERE i.cosmo_reorder_level > 0
              AND bin.actual_qty < i.cosmo_reorder_level
              AND i.disabled = 0
        """, as_dict=True)

        if low_stock_items:
            _send_stock_alert(low_stock_items)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Cosmo Stock Alert Error")


def check_expiry_alerts():
    """Vérifie les items dont la date d'expiration approche (< 30 jours)."""
    try:
        expiring_items = frappe.db.sql("""
            SELECT item_code, item_name, cosmo_expiry_date
            FROM `tabItem`
            WHERE cosmo_expiry_date IS NOT NULL
              AND cosmo_expiry_date <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
              AND cosmo_expiry_date >= CURDATE()
              AND disabled = 0
        """, as_dict=True)

        if expiring_items:
            _send_expiry_alert(expiring_items)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Cosmo Expiry Alert Error")


def _send_stock_alert(items):
    """Envoie une notification interne pour les stocks bas."""
    managers = frappe.get_all(
        "Has Role",
        filters={"role": "Cosmo Manager"},
        fields=["parent"],
        pluck="parent"
    )
    for user in managers:
        frappe.publish_realtime(
            "cosmo_stock_alert",
            {"items": items, "count": len(items)},
            user=user
        )


def _send_expiry_alert(items):
    """Envoie une notification interne pour les produits proches de l'expiration."""
    managers = frappe.get_all(
        "Has Role",
        filters={"role": "Cosmo Manager"},
        fields=["parent"],
        pluck="parent"
    )
    for user in managers:
        frappe.publish_realtime(
            "cosmo_expiry_alert",
            {"items": items, "count": len(items)},
            user=user
        )
