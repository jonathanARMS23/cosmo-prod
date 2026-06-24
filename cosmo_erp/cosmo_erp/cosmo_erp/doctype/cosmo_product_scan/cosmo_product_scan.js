frappe.ui.form.on('Cosmo Product Scan', {
    refresh: function(frm) {
        _update_status_indicator(frm);

        // Bouton "Relancer le scan" si erreur
        if (frm.doc.scan_status === 'Erreur' || frm.doc.scan_status === 'Non identifié') {
            frm.add_custom_button(__('Relancer le scan'), function() {
                frappe.call({
                    method: 'cosmo_erp.api.retry_product_scan',
                    args: { scan_name: frm.docname },
                    callback: function() {
                        frm.reload_doc();
                        frappe.show_alert({ message: __('Scan relancé'), indicator: 'blue' });
                    }
                });
            });
        }

        // Bouton "Créer l'article" si non identifié
        if (frm.doc.scan_status === 'Non identifié') {
            frm.add_custom_button(__('Créer un article'), function() {
                frm.events.create_item_from_scan(frm);
            }, __('Actions'));
        }

        // Écouter les événements realtime de match
        frappe.realtime.on('cosmo_scan_match', function(data) {
            if (data.scan === frm.docname) {
                frappe.confirm(
                    __('Produit identifié : {0} (confiance {1}%). Mettre à jour la fiche produit ?',
                       [data.item, data.confidence]),
                    function() {
                        frappe.call({
                            method: 'cosmo_erp.api.update_item_from_scan',
                            args: { scan_name: frm.docname, item_code: data.item },
                            callback: function() {
                                frm.reload_doc();
                            }
                        });
                    }
                );
            }
        });
    },

    create_item_from_scan: function(frm) {
        if (!frm.doc.extracted_data) {
            frappe.msgprint(__('Aucune donnée extraite disponible.'));
            return;
        }

        let data = {};
        try {
            data = JSON.parse(frm.doc.extracted_data);
        } catch(e) {
            frappe.msgprint(__('Erreur de lecture des données extraites.'));
            return;
        }

        frappe.new_doc('Item', {
            item_name: data.product_name || '',
            cosmo_brand: data.brand || '',
            cosmo_category: data.product_type || '',
            cosmo_ai_description: frm.doc.ai_raw_response || '',
        });
    }
});

function _update_status_indicator(frm) {
    const colors = {
        'En cours': 'blue',
        'Identifié': 'green',
        'Non identifié': 'orange',
        'Erreur': 'red',
        'Archivé': 'grey'
    };
    const color = colors[frm.doc.scan_status] || 'grey';
    frm.set_indicator_formatter('scan_status', function() { return color; });
}
