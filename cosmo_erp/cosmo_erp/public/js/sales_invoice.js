// Améliorations UI pour Sales Invoice dans le contexte Cosmo
frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Imprimer Cosmo'), function() {
                frappe.set_route('print', 'Sales Invoice', frm.doc.name, 'Cosmo Invoice');
            }, __('Cosmo'));
        }
    }
});
