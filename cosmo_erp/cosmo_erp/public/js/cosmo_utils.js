// Utilitaires globaux Cosmo ERP — chargés sur toutes les pages Frappe
frappe.provide('cosmo');

cosmo.utils = {
    formatAriary: function(amount) {
        return new Intl.NumberFormat('mg-MG', {
            style: 'currency',
            currency: 'MGA',
            minimumFractionDigits: 0
        }).format(amount);
    },

    showStockBadge: function(qty, reorderLevel) {
        if (qty <= 0) return '<span class="badge badge-danger">Rupture</span>';
        if (reorderLevel && qty <= reorderLevel) return '<span class="badge badge-warning">Faible</span>';
        return '<span class="badge badge-success">Disponible</span>';
    },

    confirmAction: function(message, title, callback) {
        frappe.confirm(message, callback, null, title);
    }
};
