frappe.ui.form.on('Cosmo Supplier Order', {
    refresh: function(frm) {
        // Bouton "Envoyer par Email" sur documents soumis
        if (frm.doc.docstatus === 1 && frm.doc.status !== 'Annulé') {
            frm.add_custom_button(__('Envoyer par Email'), function() {
                frm.events.send_order_email(frm);
            }, __('Actions'));
        }

        // Badge visuel selon statut
        if (frm.doc.status === 'Reçu') {
            frm.dashboard.set_headline_alert(
                `<div class="alert alert-success">Commande reçue</div>`
            );
        }
    },

    send_order_email: function(frm) {
        frappe.call({
            method: 'frappe.core.doctype.communication.email.make',
            args: {
                doctype: frm.doctype,
                name: frm.docname,
                subject: __('Commande {0} — {1}', [frm.doc.name, frm.doc.supplier]),
                recipients: '',
                send_email: 0,
            },
            callback: function(r) {
                if (r.message) {
                    new frappe.views.CommunicationComposer({
                        doc: frm.doc,
                        subject: __('Commande {0}', [frm.doc.name]),
                        recipients: r.message.recipients || '',
                    });
                }
            }
        });
    }
});

// Ligne d'item : fetch stock actuel + alerte visuelle
frappe.ui.form.on('Cosmo Supplier Order Item', {
    item_code: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.item_code) return;

        // Fetch le stock actuel via frappe.call
        frappe.call({
            method: 'cosmo_erp.api.get_item_stock',
            args: { item_code: row.item_code },
            callback: function(r) {
                if (r.message !== undefined) {
                    frappe.model.set_value(cdt, cdn, 'current_stock', r.message.actual_qty);

                    // Alerte si qty suggérée < reorder_level
                    const reorder = r.message.reorder_level;
                    if (reorder && r.message.actual_qty < reorder) {
                        frappe.model.set_value(cdt, cdn, 'qty', Math.max(reorder - r.message.actual_qty, 1));
                        frappe.show_alert({
                            message: __('Stock bas pour {0} ({1} restants)', [row.item_code, r.message.actual_qty]),
                            indicator: 'orange'
                        }, 4);
                    }
                }
            }
        });
    },

    qty: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'amount', (row.qty || 0) * (row.rate || 0));
        frm.refresh_field('items');
        // Recalcul des totaux
        frm.trigger('recalculate_totals');
    },

    rate: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'amount', (row.qty || 0) * (row.rate || 0));
        frm.refresh_field('items');
        frm.trigger('recalculate_totals');
    }
});
