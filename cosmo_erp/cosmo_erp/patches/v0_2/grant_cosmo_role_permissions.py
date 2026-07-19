"""Patch : accorde aux rôles Cosmo Caissière/Cosmo Manager les permissions
DocType minimales nécessaires pour utiliser l'API REST cosmo_erp (et donc le
futur portail employés) sans passer par Administrator.

Pourquoi ce patch existe : create_roles() (install.py) crée les rôles Cosmo
mais ne leur accorde AUCUNE permission de DocType. Les fonctions de
cosmo_erp/api/main.py utilisent `ignore_permissions=True` sur les documents
qu'elles créent elles-mêmes (Sales Invoice, Stock Entry, ...), mais certaines
validations internes ERPNext font des vérifications de permission EXPLICITES
indépendantes de ce flag — ex. `get_party_account()` (erpnext/accounts/party.py)
appelle `account_perm_check()` qui vérifie une permission de lecture réelle sur
le DocType "Account". Confirmé par repro locale : create_sale() exécuté en tant
qu'Administrator fonctionne (Administrator bypass toutes les permissions), mais
échoue avec `PermissionError: User don't have permissions to select/read this
account` dès qu'on l'exécute en tant qu'utilisatrice avec seulement le rôle
Cosmo Caissière — ce qui est EXACTEMENT le cas d'usage du futur portail. Aucun
test précédent de ce projet n'avait tourné avec un utilisateur autre
qu'Administrator, d'où ce trou resté invisible jusqu'ici.

Portée volontairement minimale (lecture seule sur Account) : élargir au fil
des permissions manquantes réellement rencontrées, pas par anticipation.
"""

import frappe

# (doctype, role, read, write, create)
GRANTS = [
    ("Account", "Cosmo Caissière", 1, 0, 0),
    ("Account", "Cosmo Manager", 1, 0, 0),
    ("Customer", "Cosmo Caissière", 1, 0, 0),
    ("Customer", "Cosmo Manager", 1, 0, 0),
]


def execute():
    for doctype, role, read, write, create in GRANTS:
        _ensure_docperm(doctype, role, read=read, write=write, create=create)
    frappe.db.commit()


def _ensure_docperm(doctype, role, read=1, write=0, create=0):
    """Ajoute une ligne de permission (Custom DocPerm) pour ce rôle sur ce
    DocType si elle n'existe pas déjà avec au moins ces droits."""
    existing = frappe.db.exists(
        "Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}
    )
    if existing:
        doc = frappe.get_doc("Custom DocPerm", existing)
        changed = False
        if read and not doc.read:
            doc.read = 1
            changed = True
        if write and not doc.write:
            doc.write = 1
            changed = True
        if create and not doc.create:
            doc.create = 1
            changed = True
        if changed:
            doc.save(ignore_permissions=True)
        return

    frappe.get_doc({
        "doctype": "Custom DocPerm",
        "parent": doctype,
        "parenttype": "DocType",
        "parentfield": "permissions",
        "role": role,
        "permlevel": 0,
        "read": read,
        "write": write,
        "create": create,
    }).insert(ignore_permissions=True)
