// Custom scripts pour le DocType Item — champs cosmétiques
frappe.ui.form.on('Item', {
    refresh: function(frm) {
        if (frm.doc.is_stock_item && !frm.doc.cosmo_expiry_date) {
            frm.set_df_property('cosmo_expiry_date', 'reqd', 1);
        }
    },

    is_stock_item: function(frm) {
        frm.set_df_property('cosmo_expiry_date', 'reqd', frm.doc.is_stock_item ? 1 : 0);
    },

    cosmo_category: function(frm) {
        // Pré-sélectionne le type de peau selon la catégorie
        if (frm.doc.cosmo_category === 'Maquillage') {
            frm.set_value('cosmo_skin_type', 'Tous types');
        }
    }
});
