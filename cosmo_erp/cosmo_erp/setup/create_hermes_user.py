"""
Crée l'utilisateur technique Hermes Agent dans ERPNext et génère son API Key.

Usage :
  bench --site cosmo.localhost execute cosmo_erp.setup.create_hermes_user.run

Output :
  Affiche l'API Key et l'API Secret à copier dans .env.prod
"""
import frappe
from frappe import _
from frappe.utils import random_string


HERMES_EMAIL = "hermes@cosmo.local"
HERMES_FULL_NAME = "Hermes Agent"
HERMES_ROLE = "Cosmo Hermes"


def run():
    """Point d'entrée bench execute."""
    try:
        result = create_or_update_hermes_user()
        _print_result(result)
        return result
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_hermes_user")
        print(f"\n Erreur : {e}")
        raise


def create_or_update_hermes_user():
    """Crée ou met à jour l'utilisateur Hermes et retourne ses credentials."""

    # Vérifier que le rôle existe
    if not frappe.db.exists("Role", HERMES_ROLE):
        frappe.throw(_(
            "Le rôle '{0}' n'existe pas. Lancer d'abord : bench --site <site> install-app cosmo_erp"
        ).format(HERMES_ROLE))

    user_exists = frappe.db.exists("User", HERMES_EMAIL)

    if user_exists:
        user = frappe.get_doc("User", HERMES_EMAIL)
        print(f"  Utilisateur {HERMES_EMAIL} existe déjà — régénération des clés.")
    else:
        # Créer l'utilisateur
        user = frappe.get_doc({
            "doctype": "User",
            "email": HERMES_EMAIL,
            "first_name": HERMES_FULL_NAME,
            "user_type": "System User",
            "enabled": 1,
            "send_welcome_email": 0,
            "new_password": random_string(32),  # Mot de passe fort aléatoire (connexion web désactivée)
        })
        user.insert(ignore_permissions=True)
        print(f"  Utilisateur {HERMES_EMAIL} créé.")

    # Ajouter le rôle si absent
    role_names = [r.role for r in user.roles]
    if HERMES_ROLE not in role_names:
        user.append("roles", {"role": HERMES_ROLE})
        user.save(ignore_permissions=True)
        print(f"  Rôle '{HERMES_ROLE}' assigné.")

    # Générer l'API Key + Secret
    api_key, api_secret = _generate_api_keys(user.name)

    frappe.db.commit()

    return {
        "email": HERMES_EMAIL,
        "api_key": api_key,
        "api_secret": api_secret,
        "role": HERMES_ROLE,
    }


def _generate_api_keys(user_name: str):
    """Génère (ou régénère) l'API Key et l'API Secret pour un utilisateur."""
    # API Key : identifiant stable (conservé si existe déjà)
    existing_key = frappe.db.get_value("User", user_name, "api_key")
    if existing_key:
        api_key = existing_key
    else:
        api_key = frappe.generate_hash(length=15)
        frappe.db.set_value("User", user_name, "api_key", api_key)

    # API Secret : hash bcrypt — toujours régénéré pour la sécurité
    api_secret = frappe.generate_hash(length=15)
    frappe.utils.password.update_password(user_name, api_secret, fieldname="api_secret")

    return api_key, api_secret


def _print_result(result: dict):
    """Affiche les credentials de manière claire."""
    separator = "=" * 60
    print(f"""
{separator}
  COSMO ERP — Hermes Agent API Key générée
{separator}

Ajouter ces valeurs dans .env.prod :

  COSMO_MCP_API_KEY={result['api_key']}
  COSMO_MCP_API_SECRET={result['api_secret']}

Utilisateur ERPNext : {result['email']}
Rôle : {result['role']}

  L'API Secret ne peut pas être récupéré après cette session.
    Notez-le immédiatement dans un gestionnaire de mots de passe.
{separator}
""")
