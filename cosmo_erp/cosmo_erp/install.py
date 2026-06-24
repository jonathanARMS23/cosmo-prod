import frappe
from cosmo_erp.cosmo_erp.setup.dashboard_setup import create_dashboard


def after_install():
    """Appelé par bench après installation de cosmo_erp."""
    create_roles()
    create_workspace()
    try:
        create_dashboard()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Cosmo: Erreur création Dashboard (non bloquant)")
    frappe.db.commit()

    # Créer l'utilisateur Hermes Agent (non bloquant)
    try:
        from cosmo_erp.cosmo_erp.setup.create_hermes_user import create_or_update_hermes_user, _print_result
        result = create_or_update_hermes_user()
        _print_result(result)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "after_install: create_hermes_user")
        print("  Création utilisateur Hermes échouée — relancer manuellement avec make setup-apikey")


def create_roles():
    """Crée les rôles Cosmo ERP s'ils n'existent pas."""
    roles = [
        {
            "role_name": "Cosmo Caissière",
            "desk_access": 1,
            "description": "Accès POS uniquement + lecture stock"
        },
        {
            "role_name": "Cosmo Manager",
            "desk_access": 1,
            "description": "Accès complet cosmo_erp + lecture comptabilité"
        },
        {
            "role_name": "Cosmo Hermes",
            "desk_access": 0,
            "description": "Rôle technique pour l'agent IA (accès API total)"
        },
    ]
    for role_data in roles:
        if not frappe.db.exists("Role", role_data["role_name"]):
            role = frappe.get_doc({"doctype": "Role", **role_data})
            role.insert(ignore_permissions=True)
            frappe.logger().info(f"Cosmo: Rôle '{role_data['role_name']}' créé")


def create_workspace():
    """Crée le Workspace 'Cosmo ERP' s'il n'existe pas."""
    if frappe.db.exists("Workspace", "Cosmo ERP"):
        return

    workspace = frappe.get_doc({
        "doctype": "Workspace",
        "name": "Cosmo ERP",
        "title": "Cosmo ERP",
        "module": "Cosmo ERP",
        "icon": "diamond",
        "type": "Private",
        "restrict_to_domain": "",
        "content": "[]",
        "links": [
            {
                "type": "Link",
                "label": "Caisse POS",
                "link_type": "Page",
                "link_to": "cosmo-pos",
                "onboard": 1,
            },
            {
                "type": "Link",
                "label": "Agent Hermes",
                "link_type": "Page",
                "link_to": "cosmo-hermes",
                "onboard": 1,
            },
            {
                "type": "Link",
                "label": "Commandes Fournisseurs",
                "link_type": "DocType",
                "link_to": "Cosmo Supplier Order",
                "onboard": 1,
            },
        ],
    })
    workspace.insert(ignore_permissions=True)
