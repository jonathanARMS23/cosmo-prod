import frappe
from frappe.utils import add_months, nowdate


def archive_old_scans():
    """Archive les Cosmo Product Scan de plus de 6 mois."""
    try:
        cutoff_date = add_months(nowdate(), -6)
        old_scans = frappe.get_all(
            "Cosmo Product Scan",
            filters=[
                ["creation", "<", cutoff_date],
                ["scan_status", "in", ["Identifié", "Non identifié"]]
            ],
            pluck="name"
        )
        for scan in old_scans:
            frappe.db.set_value("Cosmo Product Scan", scan, "scan_status", "Archivé")

        if old_scans:
            frappe.db.commit()

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Cosmo Archive Scans Error")
