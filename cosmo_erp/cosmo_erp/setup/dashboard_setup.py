"""Création programmatique du Cosmo Dashboard, Number Cards et Charts dans Frappe v15."""
import frappe
from frappe import _


def create_dashboard():
    """Point d'entrée appelé depuis install.py après_install."""
    _create_number_cards()
    _create_dashboard_charts()
    _create_dashboard()
    frappe.db.commit()
    frappe.logger().info("Cosmo: Dashboard créé avec succès")


# ── Number Cards ──────────────────────────────────────────────────────────────

def _create_number_cards():
    cards = [
        {
            "name": "Cosmo CA Jour",
            "label": "CA du Jour",
            "document_type": "Sales Invoice",
            "function": "Sum",
            "aggregate_function_based_on": "grand_total",
            "filters_json": '[["Sales Invoice","docstatus","=",1],["Sales Invoice","posting_date","=","Today"]]',
            "color": "#e91e8c",
            "is_public": 1,
        },
        {
            "name": "Cosmo Transactions Jour",
            "label": "Transactions Aujourd'hui",
            "document_type": "Sales Invoice",
            "function": "Count",
            "filters_json": '[["Sales Invoice","docstatus","=",1],["Sales Invoice","posting_date","=","Today"]]',
            "color": "#9c27b0",
            "is_public": 1,
        },
        {
            "name": "Cosmo Panier Moyen",
            "label": "Panier Moyen du Jour",
            "document_type": "Sales Invoice",
            "function": "Average",
            "aggregate_function_based_on": "grand_total",
            "filters_json": '[["Sales Invoice","docstatus","=",1],["Sales Invoice","posting_date","=","Today"]]',
            "color": "#ff9800",
            "is_public": 1,
        },
        {
            "name": "Cosmo Stock Critique",
            "label": "Produits Stock Critique",
            "document_type": "Item",
            "function": "Count",
            "filters_json": '[["Item","disabled","=",0],["Item","is_stock_item","=",1]]',
            "color": "#f44336",
            "is_public": 1,
        },
        {
            "name": "Cosmo Produits Expirent",
            "label": "Expirent dans 30 jours",
            "document_type": "Item",
            "function": "Count",
            "filters_json": '[["Item","disabled","=",0],["Item","cosmo_expiry_date","is set",""]]',
            "color": "#ff5722",
            "is_public": 1,
        },
    ]
    for card_data in cards:
        if frappe.db.exists("Number Card", card_data["name"]):
            continue
        card = frappe.get_doc({"doctype": "Number Card", **card_data})
        card.insert(ignore_permissions=True)


# ── Dashboard Charts ──────────────────────────────────────────────────────────

def _create_dashboard_charts():
    charts = [
        {
            "name": "Cosmo Ventes 30 Jours",
            "chart_name": "Cosmo Ventes 30 Jours",
            "chart_type": "Custom",
            "type": "Bar",
            "method": "cosmo_erp.cosmo_erp.dashboard.cosmo_dashboard.get_sales_last_30_days",
            "is_public": 1,
            "timeseries": 0,
            "color": "#e91e8c",
        },
        {
            "name": "Cosmo Top Produits CA",
            "chart_name": "Cosmo Top Produits CA",
            "chart_type": "Custom",
            "type": "Pie",
            "method": "cosmo_erp.cosmo_erp.dashboard.cosmo_dashboard.get_top_products",
            "is_public": 1,
            "timeseries": 0,
        },
        {
            "name": "Cosmo Répartition Catégories",
            "chart_name": "Cosmo Répartition Catégories",
            "chart_type": "Custom",
            "type": "Donut",
            "method": "cosmo_erp.cosmo_erp.dashboard.cosmo_dashboard.get_category_breakdown",
            "is_public": 1,
            "timeseries": 0,
            "color": "#9c27b0",
        },
    ]
    for chart_data in charts:
        if frappe.db.exists("Dashboard Chart", chart_data["name"]):
            continue
        chart = frappe.get_doc({"doctype": "Dashboard Chart", **chart_data})
        chart.insert(ignore_permissions=True)


# ── Dashboard principal ───────────────────────────────────────────────────────

def _create_dashboard():
    if frappe.db.exists("Dashboard", "Cosmo Dashboard"):
        return
    dashboard = frappe.get_doc({
        "doctype": "Dashboard",
        "dashboard_name": "Cosmo Dashboard",
        "is_default": 0,
        "is_standard": 0,
        "cards": [
            {"card": "Cosmo CA Jour"},
            {"card": "Cosmo Transactions Jour"},
            {"card": "Cosmo Panier Moyen"},
            {"card": "Cosmo Stock Critique"},
            {"card": "Cosmo Produits Expirent"},
        ],
        "charts": [
            {"chart": "Cosmo Ventes 30 Jours", "width": "Full"},
            {"chart": "Cosmo Top Produits CA", "width": "Half"},
            {"chart": "Cosmo Répartition Catégories", "width": "Half"},
        ],
    })
    dashboard.insert(ignore_permissions=True)
