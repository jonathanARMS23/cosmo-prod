# ─────────────────────────────────────────────────────────────────────────────
# Cosmo ERP — hooks.py
# Point d'entrée Frappe pour toutes les extensions et personnalisations.
# Chaque section est commentée pour faciliter la maintenance.
# ─────────────────────────────────────────────────────────────────────────────

# ── Métadonnées de l'application ─────────────────────────────────────────────
app_name = "cosmo_erp"
app_title = "Cosmo ERP"
app_publisher = "ARMS"
app_description = "Custom ERPNext for cosmetics retail boutique"
app_email = "jonathan@overlord.fund"
app_license = "MIT"
app_version = "0.1.0"

# ── Assets globaux (chargés sur toutes les pages Frappe) ─────────────────────
# JS utilitaire global (cosmo namespace, formatage MGA, badges stock, etc.)
app_include_js = ["cosmo_erp/public/js/cosmo_utils.js"]

# Feuille de style globale (variables CSS, classes cosmo-*)
app_include_css = ["cosmo_erp/public/css/cosmo_erp.css"]

# ── Scripts spécifiques par DocType ──────────────────────────────────────────
# Chargés uniquement lorsque le DocType correspondant est ouvert dans le navigateur.
doctype_js = {
    # Enrichit le formulaire Item avec les champs cosmétiques (expiry, catégorie, peau)
    "Item": "cosmo_erp/public/js/item.js",
    # Ajoute le bouton "Imprimer Cosmo" et le format d'impression dédié
    "Sales Invoice": "cosmo_erp/public/js/sales_invoice.js",
    # Ajoute le raccourci vers le POS Cosmo simplifié
    "POS Profile": "cosmo_erp/public/js/pos_profile.js",
}

# ── Événements planifiés (scheduler) ─────────────────────────────────────────
# Frappe Scheduler exécute ces fonctions selon la fréquence définie.
# Chaque fonction doit être idempotente et gérer ses propres exceptions.
scheduler_events = {
    # Exécutés chaque jour à minuit (heure serveur)
    "daily": [
        # Vérifie les articles sous le seuil de réapprovisionnement → notification temps réel
        "cosmo_erp.tasks.daily.check_stock_alerts",
        # Vérifie les articles expirant dans < 30 jours → notification temps réel
        "cosmo_erp.tasks.daily.check_expiry_alerts",
    ],
    # Exécutés chaque lundi matin
    "weekly": [
        # Génère et envoie le rapport hebdomadaire aux Cosmo Managers
        "cosmo_erp.tasks.weekly.send_weekly_report",
    ],
    # Exécutés le 1er de chaque mois
    "monthly": [
        # Archive les Cosmo Product Scan de plus de 6 mois (statut → "Archivé")
        "cosmo_erp.tasks.monthly.archive_old_scans",
    ],
}

# ── Événements DocType (hooks Python côté serveur) ───────────────────────────
# Frappe appelle ces fonctions lors des transitions de statut des documents.
doc_events = {
    "Sales Invoice": {
        # Vérifie l'expiration des produits vendus et log la transaction Cosmo
        "on_submit": "cosmo_erp.events.sales_invoice.on_submit",
        # Log l'annulation pour audit interne
        "on_cancel": "cosmo_erp.events.sales_invoice.on_cancel",
    },
    "Item": {
        # Rend cosmo_expiry_date obligatoire si is_stock_item est coché
        "validate": "cosmo_erp.controllers.item_controller.validate_cosmo_fields",
    },
}

# ── Fixtures (exportées/importées via bench migrate) ─────────────────────────
# Frappe synchronise ces documents depuis le répertoire fixtures/ lors des migrations.
# Les Custom Fields et Property Setters définissent les champs cosmétiques ajoutés
# aux DocTypes standard ERPNext (Item, Customer, etc.).
fixtures = [
    # Champs personnalisés ajoutés aux DocTypes ERPNext standard
    "Custom Field",
    # Surcharges de propriétés de champs existants (reqd, hidden, etc.)
    "Property Setter",
    # Formats d'impression Cosmo (tickets caisse, bons de livraison)
    "Print Format",
    # Workspaces du tableau de bord Cosmo
    "Workspace",
    # Rôles spécifiques Cosmo (filtrés pour éviter d'exporter les rôles ERPNext standard)
    {"dt": "Role",           "filters": [["role_name", "like", "Cosmo%"]]},
    # Dashboard Cosmo : Number Cards, Charts, Dashboard
    {"dt": "Number Card",    "filters": [["name", "like", "Cosmo%"]]},
    {"dt": "Dashboard Chart","filters": [["name", "like", "Cosmo%"]]},
    {"dt": "Dashboard",      "filters": [["name", "like", "Cosmo%"]]},
]

# ── Règles de routage website ─────────────────────────────────────────────────
# Mappe les URLs publiques vers les pages web Frappe (Web Pages ou Vue custom).
website_route_rules = [
    # POS simplifié Cosmo (interface caisse tactile)
    {"from_route": "/cosmo-pos", "to_route": "cosmo-pos"},
    # Interface Hermès (gestion stock avancée)
    {"from_route": "/cosmo-hermes", "to_route": "cosmo-hermes"},
]

# ── Configuration de l'installation ──────────────────────────────────────────
# Appelé une seule fois lors de `bench install-app cosmo_erp`
after_install = "cosmo_erp.install.after_install"

# ── Surcharges de permissions ─────────────────────────────────────────────────
# Permet de définir des règles de permission custom par rôle.
# permission_query_conditions = {
#     "Cosmo Product Scan": "cosmo_erp.permissions.get_permission_query_conditions",
# }

# ── Jinja filters custom ─────────────────────────────────────────────────────
# Disponibles dans les templates Jinja (Print Formats, Email Templates, etc.)
# jinja = {
#     "filters": "cosmo_erp.jinja.filters",
# }
