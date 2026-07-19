"""Patch d'hydratation : injecte le catalogue initial Ravaka + stock d'ouverture.

Source : cosmo_erp/fixtures/ravaka_initial_stock.json (279 entrées {item_code, qty},
déjà nettoyées, dédupliquées et agrégées en amont — NE PAS resommer ici).

Ce patch est idempotent :
  - Frappe trace l'exécution unique via le Patch Log (bench migrate ne le rejoue pas) ;
  - en plus, chaque création est gardée par un frappe.db.exists(...) / un contrôle de
    stock existant, pour supporter une ré-exécution manuelle
    (`bench execute ...` ou `bench migrate --skip-failing`) sans doublons ni erreurs.

Décisions techniques documentées :
  - Company        : "Ravaka" (abbr "RAV"), devise MGA, pays Madagascar.
  - Warehouse      : "Stores - RAV" (créé si absent — ERPNext le crée en général
                     automatiquement à la création de la Company).
  - Item           : item_name = item_code (placeholder assumé), item_group "Products",
                     is_stock_item = 1, stock_uom "Nos" (défaut ERPNext, aucune autre
                     convention d'UOM n'existe dans le repo). Aucune marque / catégorie /
                     description n'est inventée.
  - Expiry hook    : le hook `item_controller.validate_cosmo_fields` rend
                     cosmo_expiry_date obligatoire pour les articles en stock. Le stock
                     legacy importé n'a AUCUNE date d'expiration connue et la consigne
                     interdit d'inventer des données. On insère donc les Item avec
                     flags.ignore_validate = True pour contourner UNIQUEMENT cette
                     validation applicative durant l'import de masse (le hook n'est pas
                     modifié). Les dates d'expiration seront renseignées manuellement
                     plus tard, comme les item_name.
  - valuation_rate : aucune donnée de prix/coût n'existe dans la source. La Stock
                     Reconciliation "Opening Stock" est passée avec valuation_rate = 0 et
                     allow_zero_valuation_rate = 1 sur chaque ligne — c'est la voie
                     supportée par ERPNext pour un stock d'ouverture à valeur nulle sans
                     fabriquer de prix fictif.
  - qty == 0       : l'Item est créé, mais AUCUN mouvement de stock n'est généré.
"""

import json
import os

import frappe

COMPANY_NAME = "Ravaka"
COMPANY_ABBR = "RAV"
COMPANY_CURRENCY = "MGA"
COMPANY_COUNTRY = "Madagascar"
WAREHOUSE_NAME = "Stores - RAV"
ITEM_GROUP = "Products"
STOCK_UOM = "Nos"
FIXTURE_RELPATH = ("fixtures", "ravaka_initial_stock.json")


def execute():
    """Point d'entrée du patch (appelé par `bench migrate`)."""
    entries = _load_fixture()

    _ensure_currency()
    _ensure_company()
    _ensure_warehouse()

    stats = {"items_created": 0, "items_existing": 0, "sr_created": 0, "sr_skipped": 0}
    failures = []

    for idx, entry in enumerate(entries):
        item_code = (entry.get("item_code") or "").strip()
        qty = entry.get("qty", 0)
        if not item_code:
            failures.append(f"ligne {idx}: item_code vide -> ignorée")
            continue
        try:
            created = _ensure_item(item_code)
            if created:
                stats["items_created"] += 1
            else:
                stats["items_existing"] += 1

            if qty and qty > 0:
                if _create_opening_stock(item_code, qty):
                    stats["sr_created"] += 1
                else:
                    stats["sr_skipped"] += 1
        except Exception:
            # Un item en échec ne doit pas faire planter tout le patch.
            frappe.db.rollback()
            failures.append(f"{item_code}: {frappe.get_traceback(with_context=False)}")
            frappe.log_error(
                title=f"Ravaka hydrate — échec item {item_code}",
                message=frappe.get_traceback(),
            )

    frappe.db.commit()

    summary = (
        f"Ravaka hydrate terminé — "
        f"{stats['items_created']} items créés, "
        f"{stats['items_existing']} déjà présents, "
        f"{stats['sr_created']} stock reconciliations créées, "
        f"{stats['sr_skipped']} ignorées (stock déjà présent), "
        f"{len(failures)} échec(s)."
    )
    print(summary)
    frappe.logger().info(summary)
    if failures:
        frappe.log_error(
            title="Ravaka hydrate — résumé des échecs",
            message=summary + "\n\n" + "\n---\n".join(failures),
        )


# ── Chargement fixture ───────────────────────────────────────────────────────
def _load_fixture():
    """Lit le fichier fixture relatif au module (pas de chemin absolu codé en dur)."""
    path = os.path.join(frappe.get_app_path("cosmo_erp"), *FIXTURE_RELPATH)
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list) or not data:
        frappe.throw(f"Fixture invalide ou vide : {path}")
    return data


# ── Currency / Company / Warehouse ───────────────────────────────────────────
def _ensure_currency():
    if not frappe.db.exists("Currency", COMPANY_CURRENCY):
        frappe.get_doc({
            "doctype": "Currency",
            "currency_name": COMPANY_CURRENCY,
            "enabled": 1,
            "symbol": "Ar",
        }).insert(ignore_permissions=True)


def _ensure_company():
    """Crée la Company Ravaka/RAV si absente. Échoue proprement en cas de conflit."""
    existing_abbr = frappe.db.get_value("Company", COMPANY_NAME, "abbr")
    if existing_abbr:
        # La Company existe déjà : vérifier que l'abréviation correspond.
        if existing_abbr != COMPANY_ABBR:
            frappe.throw(
                f"Conflit de Company : « {COMPANY_NAME} » existe déjà avec "
                f"l'abréviation « {existing_abbr} » (attendu « {COMPANY_ABBR} »). "
                f"Résolvez le conflit manuellement avant de rejouer le patch."
            )
        return

    # Pas de Company nommée Ravaka : vérifier qu'aucune autre n'occupe déjà l'abbr RAV.
    other = frappe.db.get_value("Company", {"abbr": COMPANY_ABBR}, "name")
    if other:
        frappe.throw(
            f"Conflit d'abréviation : l'abréviation « {COMPANY_ABBR} » est déjà "
            f"utilisée par la Company « {other} ». Impossible de créer « {COMPANY_NAME} ». "
            f"Résolvez le conflit manuellement avant de rejouer le patch."
        )

    frappe.get_doc({
        "doctype": "Company",
        "company_name": COMPANY_NAME,
        "abbr": COMPANY_ABBR,
        "default_currency": COMPANY_CURRENCY,
        "country": COMPANY_COUNTRY,
    }).insert(ignore_permissions=True)
    frappe.db.commit()


def _ensure_warehouse():
    """Crée le Warehouse Stores - RAV s'il n'existe pas déjà."""
    if frappe.db.exists("Warehouse", WAREHOUSE_NAME):
        return

    doc = {
        "doctype": "Warehouse",
        "warehouse_name": "Stores",
        "company": COMPANY_NAME,
    }
    parent = f"All Warehouses - {COMPANY_ABBR}"
    if frappe.db.exists("Warehouse", parent):
        doc["parent_warehouse"] = parent
    frappe.get_doc(doc).insert(ignore_permissions=True)
    frappe.db.commit()


# ── Item ─────────────────────────────────────────────────────────────────────
def _ensure_item(item_code):
    """Crée l'Item s'il n'existe pas. Retourne True si créé, False si déjà présent."""
    if frappe.db.exists("Item", item_code):
        return False

    item = frappe.get_doc({
        "doctype": "Item",
        "item_code": item_code,
        "item_name": item_code,      # placeholder assumé — renommage manuel ultérieur
        "item_group": ITEM_GROUP,
        "stock_uom": STOCK_UOM,
        "is_stock_item": 1,
    })
    # Contourne UNIQUEMENT la validation applicative cosmo (expiry obligatoire) pour
    # l'import de masse ; le hook lui-même n'est pas modifié.
    item.flags.ignore_validate = True
    item.insert(ignore_permissions=True)
    return True


# ── Stock d'ouverture ────────────────────────────────────────────────────────
def _create_opening_stock(item_code, qty):
    """Crée + soumet une Stock Reconciliation Opening Stock. Idempotent.

    Retourne True si créée, False si ignorée (stock déjà présent dans l'entrepôt).
    """
    # Idempotence : si l'item a déjà du stock dans l'entrepôt, on ne rejoue pas.
    existing_qty = frappe.db.get_value(
        "Bin", {"item_code": item_code, "warehouse": WAREHOUSE_NAME}, "actual_qty"
    )
    if existing_qty and float(existing_qty) != 0:
        return False

    sr = frappe.get_doc({
        "doctype": "Stock Reconciliation",
        "purpose": "Opening Stock",
        "company": COMPANY_NAME,
        "items": [{
            "item_code": item_code,
            "warehouse": WAREHOUSE_NAME,
            "qty": qty,
            "valuation_rate": 0,
            "allow_zero_valuation_rate": 1,
        }],
    })
    sr.insert(ignore_permissions=True)
    sr.submit()
    return True
