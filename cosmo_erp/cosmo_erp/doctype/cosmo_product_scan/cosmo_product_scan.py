import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class CosmoProductScan(Document):

    def before_insert(self):
        """Initialise la date/heure du scan avant insertion."""
        if not self.scan_datetime:
            self.scan_datetime = now_datetime()
        self.scan_status = "En cours"

    def after_insert(self):
        """Déclenche le Background Job de reconnaissance image après création."""
        frappe.enqueue(
            "cosmo_erp.vision.product_recognition.process_scan",
            scan_name=self.name,
            queue="long",
            timeout=120,
            now=frappe.flags.in_test,
        )

    def on_update(self):
        """Si un item est identifié avec haute confiance, propose la mise à jour."""
        if (
            self.matched_item
            and self.confidence_score
            and self.confidence_score >= 85
            and self.action_taken == "Aucune"
        ):
            # Notification realtime pour proposer la mise à jour
            frappe.publish_realtime(
                "cosmo_scan_match",
                {
                    "scan": self.name,
                    "item": self.matched_item,
                    "confidence": self.confidence_score,
                    "extracted": self.extracted_data,
                },
                user=frappe.session.user,
            )
