import frappe
from frappe import _


def validate_cosmo_fields(doc, method=None):
    """Hook de validation pour les champs cosmétiques sur Item."""
    if doc.is_stock_item and not doc.get("cosmo_expiry_date"):
        frappe.throw(
            _("La date d'expiration est obligatoire pour les articles en stock cosmétiques."),
            title=_("Champ requis")
        )

    if doc.get("cosmo_reorder_level") and doc.cosmo_reorder_level < 0:
        frappe.throw(_("Le seuil de réapprovisionnement ne peut pas être négatif."))
