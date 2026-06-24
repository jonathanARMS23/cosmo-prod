"""Tâches schedulées hebdomadaires — cosmo_erp."""
import frappe
from frappe.utils import nowdate, add_days


def send_weekly_report():
    """Envoie le rapport hebdomadaire aux Cosmo Managers (lundi matin)."""
    try:
        end_date = add_days(nowdate(), -1)   # Hier (dimanche)
        start_date = add_days(end_date, -6)  # Lundi précédent

        report_data = _build_weekly_report(start_date, end_date)
        _email_report(report_data, start_date, end_date)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Cosmo Weekly Report Error")


def _build_weekly_report(start_date, end_date):
    """Construit les données du rapport hebdomadaire."""
    # CA et transactions
    revenue_row = frappe.db.sql("""
        SELECT
            COALESCE(SUM(grand_total), 0) AS total,
            COUNT(*) AS transactions,
            COALESCE(AVG(grand_total), 0) AS avg_basket
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND posting_date BETWEEN %(start)s AND %(end)s
    """, {"start": start_date, "end": end_date}, as_dict=True)

    # Top 10 produits
    top_items = frappe.db.sql("""
        SELECT
            sii.item_name,
            SUM(sii.amount) AS total_revenue,
            SUM(sii.qty) AS total_qty
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.docstatus = 1
          AND si.posting_date BETWEEN %(start)s AND %(end)s
        GROUP BY sii.item_code
        ORDER BY total_revenue DESC
        LIMIT 10
    """, {"start": start_date, "end": end_date}, as_dict=True)

    # Stock critique
    low_stock_count = frappe.db.sql("""
        SELECT COUNT(*) FROM (
            SELECT i.item_code
            FROM `tabItem` i
            LEFT JOIN `tabBin` bin ON bin.item_code = i.item_code
            WHERE i.disabled = 0 AND i.is_stock_item = 1 AND i.cosmo_reorder_level > 0
            GROUP BY i.item_code
            HAVING COALESCE(SUM(bin.actual_qty), 0) < i.cosmo_reorder_level
        ) AS low_stock
    """)[0][0]

    return {
        "revenue": revenue_row[0] if revenue_row else {"total": 0, "transactions": 0, "avg_basket": 0},
        "top_items": top_items,
        "low_stock_count": int(low_stock_count),
    }


def _email_report(data, start_date, end_date):
    """Envoie le rapport par email à tous les Cosmo Managers."""
    managers = frappe.get_all(
        "Has Role",
        filters={"role": "Cosmo Manager"},
        fields=["parent"],
        pluck="parent",
    )
    # Dédupliquer
    managers = list(set(managers))

    for user_email in managers:
        try:
            frappe.sendmail(
                recipients=[user_email],
                subject=f"Rapport Hebdo Cosmo — {start_date} au {end_date}",
                template="cosmo_weekly_report",
                args={
                    "data": data,
                    "start_date": start_date,
                    "end_date": end_date,
                },
                delayed=False,
            )
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Cosmo Weekly Report Email Error — {user_email}"
            )
