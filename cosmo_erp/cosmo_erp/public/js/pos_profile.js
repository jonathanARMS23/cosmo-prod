// Ajoute un bouton vers le POS simplifié Cosmo
frappe.ui.form.on('POS Profile', {
    refresh: function(frm) {
        frm.add_custom_button(__('Ouvrir Cosmo POS'), function() {
            frappe.set_route('cosmo-pos');
        });
    }
});
