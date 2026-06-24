"""API endpoints whitelisted pour cosmo_erp (appelés depuis le JS client)."""
import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist()
def get_item_stock(item_code):
    """Retourne le stock actuel et le niveau de réapprovisionnement d'un item."""
    if not frappe.has_permission("Item", "read"):
        frappe.throw(_("Permission refusée."))

    actual_qty = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(actual_qty), 0)
        FROM `tabBin`
        WHERE item_code = %(item_code)s
    """, {"item_code": item_code})[0][0])

    item = frappe.db.get_value(
        "Item",
        item_code,
        ["item_name", "cosmo_reorder_level", "cosmo_expiry_date", "cosmo_preferred_supplier"],
        as_dict=True
    )

    return {
        "item_code": item_code,
        "item_name": item.item_name if item else "",
        "actual_qty": actual_qty,
        "reorder_level": flt(item.cosmo_reorder_level) if item else 0,
        "expiry_date": str(item.cosmo_expiry_date) if item and item.cosmo_expiry_date else None,
        "preferred_supplier": item.cosmo_preferred_supplier if item else None,
    }


@frappe.whitelist()
def retry_product_scan(scan_name):
    """Relance le Background Job de reconnaissance pour un scan existant."""
    scan = frappe.get_doc("Cosmo Product Scan", scan_name)
    if scan.scan_status not in ("Erreur", "Non identifié"):
        frappe.throw(_("Ce scan ne peut pas être relancé (statut: {0}).").format(scan.scan_status))

    scan.db_set("scan_status", "En cours")
    frappe.enqueue(
        "cosmo_erp.vision.product_recognition.process_scan",
        scan_name=scan_name,
        queue="long",
        timeout=120,
    )
    return {"status": "enqueued"}


@frappe.whitelist()
def update_item_from_scan(scan_name, item_code):
    """Met à jour les champs IA d'un Item depuis les données d'un scan confirmé."""
    if not frappe.has_permission("Item", "write"):
        frappe.throw(_("Permission refusée."))

    scan = frappe.get_doc("Cosmo Product Scan", scan_name)

    extracted = {}
    if scan.extracted_data:
        import json
        try:
            extracted = json.loads(scan.extracted_data) if isinstance(scan.extracted_data, str) else scan.extracted_data
        except (json.JSONDecodeError, TypeError):
            pass

    item = frappe.get_doc("Item", item_code)

    if extracted.get("brand"):
        item.cosmo_brand = extracted["brand"]
    if extracted.get("product_type"):
        item.cosmo_category = extracted["product_type"]
    if scan.ai_raw_response:
        item.cosmo_ai_description = scan.ai_raw_response[:500]

    from frappe.utils import now_datetime
    item.cosmo_ai_last_scan = now_datetime()
    item.save(ignore_permissions=True)

    scan.db_set("action_taken", "Item mis à jour")
    scan.db_set("matched_item", item_code)

    return {"updated": item_code}
