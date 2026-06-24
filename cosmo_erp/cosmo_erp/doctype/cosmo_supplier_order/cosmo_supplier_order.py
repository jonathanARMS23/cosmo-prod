import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, add_days, flt, nowdate


class CosmoSupplierOrder(Document):

    def validate(self):
        """Valide la commande fournisseur avant sauvegarde."""
        self._validate_supplier()
        self._calculate_amounts()
        self._check_expiry_concerns()
        self._validate_dates()

    def on_submit(self):
        """À la soumission : crée automatiquement un Purchase Order ERPNext."""
        try:
            po = self._create_purchase_order()
            self.db_set("linked_purchase_order", po.name)
            frappe.msgprint(
                _("Purchase Order {0} créé automatiquement.").format(
                    frappe.utils.get_link_to_form("Purchase Order", po.name)
                ),
                indicator="green"
            )
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Cosmo: Erreur création PO pour {self.name}")
            frappe.throw(_("Erreur lors de la création du Purchase Order. Voir les logs."))

    def before_cancel(self):
        """Annule le Purchase Order lié s'il existe et est en brouillon."""
        if self.linked_purchase_order:
            po_status = frappe.db.get_value("Purchase Order", self.linked_purchase_order, "docstatus")
            if po_status == 0:
                # Brouillon : on peut supprimer
                frappe.delete_doc("Purchase Order", self.linked_purchase_order, ignore_permissions=True)
                frappe.msgprint(_("Purchase Order {0} supprimé.").format(self.linked_purchase_order))
            elif po_status == 1:
                # Soumis : annuler
                po = frappe.get_doc("Purchase Order", self.linked_purchase_order)
                po.cancel()
                frappe.msgprint(_("Purchase Order {0} annulé.").format(self.linked_purchase_order))

    def _validate_supplier(self):
        if not self.supplier:
            frappe.throw(_("Le fournisseur est obligatoire."))

    def _calculate_amounts(self):
        total_qty = 0.0
        total_amount = 0.0
        for item in self.items:
            item.amount = flt(item.qty) * flt(item.rate)
            total_qty += flt(item.qty)
            total_amount += flt(item.amount)
        self.total_qty = total_qty
        self.total_amount = total_amount

    def _check_expiry_concerns(self):
        """Marque les lignes dont le stock existant est proche de l'expiration."""
        for item in self.items:
            expiry = frappe.db.get_value("Item", item.item_code, "cosmo_expiry_date")
            if expiry and str(expiry) < add_days(nowdate(), 30):
                item.cosmo_expiry_concern = 1
            else:
                item.cosmo_expiry_concern = 0

    def _validate_dates(self):
        if self.expected_delivery and self.expected_delivery < self.order_date:
            frappe.throw(_("La date de livraison prévue ne peut pas être antérieure à la date de commande."))

    def _create_purchase_order(self):
        """Crée un Purchase Order ERPNext à partir de cette commande Cosmo."""
        supplier_currency = frappe.db.get_value("Supplier", self.supplier, "default_currency") or "MGA"

        po = frappe.get_doc({
            "doctype": "Purchase Order",
            "supplier": self.supplier,
            "transaction_date": self.order_date or today(),
            "schedule_date": self.expected_delivery or add_days(today(), 7),
            "currency": supplier_currency,
            "cosmo_source_order": self.name,
            "items": [
                {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "uom": item.uom or frappe.db.get_value("Item", item.item_code, "stock_uom"),
                    "rate": item.rate,
                    "schedule_date": self.expected_delivery or add_days(today(), 7),
                    "warehouse": frappe.db.get_single_value("Stock Settings", "default_warehouse"),
                }
                for item in self.items
            ],
        })
        po.insert(ignore_permissions=True)
        return po
