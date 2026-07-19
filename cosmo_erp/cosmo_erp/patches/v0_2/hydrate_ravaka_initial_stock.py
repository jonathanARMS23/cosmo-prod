"""Patch d'hydratation : injecte le catalogue initial Ravaka + stock d'ouverture.

Source : cosmo_erp/data/ravaka_initial_stock.json (279 entrées {item_code, qty},
déjà nettoyées, dédupliquées et agrégées en amont — NE PAS resommer ici).

IMPORTANT : ce fichier NE DOIT PAS vivre dans fixtures/ — Frappe scanne tout
`<app>/fixtures/*.json` et tente d'importer chaque fichier comme une liste de
documents complets (frappe/utils/fixtures.py::import_fixtures), ce qui casse
avec KeyError('doctype') sur un fichier qui n'a pas cette forme (confirmé par
repro locale). D'où le dossier data/ dédié, ignoré par ce mécanisme.

Ce patch est idempotent :
  - Frappe trace l'exécution unique via le Patch Log (bench migrate ne le rejoue pas) ;
  - en plus, chaque création est gardée par un frappe.db.exists(...) / un contrôle de
    stock existant, pour supporter une ré-exécution manuelle
    (`bench execute ...` ou `bench migrate --skip-failing`) sans doublons ni erreurs.

Décisions techniques documentées :
  - Company        : la Company CIBLE n'est PAS codée en dur. Résolue dans l'ordre :
                     1) Global Defaults > Default Company si défini,
                     2) l'unique Company existante si une seule existe (cas réel :
                        "Maison Eliora" / abbr "ME", déjà créée via le Setup Wizard
                        — le stock Ravaka s'hydrate DANS cette Company, on n'en crée
                        pas une nouvelle),
                     3) si aucune Company n'existe (site vierge, ex. tests locaux),
                        on crée "Ravaka" (abbr "RAV", devise MGA, Madagascar) comme
                        avant.
                     4) si plusieurs Companies existent sans default_company défini,
                        le patch échoue proprement (ambiguïté, résolution manuelle
                        requise) plutôt que de deviner.
  - Warehouse      : "Stores - <abbr de la Company résolue>" (créé si absent —
                     ERPNext le crée en général automatiquement à la création
                     d'une Company).
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

# Utilisées UNIQUEMENT dans le cas de repli (aucune Company n'existe encore).
FALLBACK_COMPANY_NAME = "Ravaka"
FALLBACK_COMPANY_ABBR = "RAV"
FALLBACK_COMPANY_CURRENCY = "MGA"
FALLBACK_COMPANY_COUNTRY = "Madagascar"
ITEM_GROUP = "Products"
STOCK_UOM = "Nos"
FIXTURE_RELPATH = ("data", "ravaka_initial_stock.json")


def execute():
    """Point d'entrée du patch (appelé par `bench migrate`).

    IMPORTANT : ce patch ne doit JAMAIS faire échouer `bench migrate` dans son
    ensemble — une erreur ici bloquerait toutes les migrations Frappe/ERPNext
    (donc le démarrage complet du site) pour un problème d'import de données
    legacy non critique. Toute exception est donc journalisée puis avalée.
    """
    try:
        _run()
    except Exception:
        frappe.db.rollback()
        frappe.log_error(
            title="Ravaka hydrate — échec global (patch avalé, migrate continue)",
            message=frappe.get_traceback(),
        )
        print("Ravaka hydrate — ÉCHEC GLOBAL, voir Error Log. Le patch n'a pas bloqué migrate.")


def force_rerun():
    """Supprime le Patch Log de ce patch pour permettre une VRAIE ré-exécution.

    `bench install-app` (contrairement à un `bench migrate` sur un patch déjà
    listé au moment de l'install) appelle en interne
    `frappe.installer.set_all_patches_as_completed()` : TOUTES les entrées de
    patches.txt de l'app installée sont marquées "déjà exécutées" dans Patch
    Log SANS jamais être lancées — aucune option CLI ne permet de désactiver
    ça (confirmé en lisant `bench install-app` et par repro locale : Patch Log
    contenait notre patch juste après l'install, mais aucune trace d'exécution,
    aucune donnée créée). Ce patch est une hydratation de données ponctuelle
    qui doit réellement s'exécuter même juste après l'installation de l'app
    sur un site déjà existant. À appeler explicitement une seule fois juste
    après `bench install-app cosmo_erp` sur un tel site, avant le `bench
    migrate` qui suit (qui, lui, exécutera vraiment le patch une fois son
    entrée Patch Log supprimée).
    """
    frappe.db.delete("Patch Log", {"patch": "cosmo_erp.patches.v0_2.hydrate_ravaka_initial_stock"})
    frappe.db.commit()
    print("Ravaka hydrate — Patch Log réinitialisé, le patch s'exécutera réellement au prochain migrate.")


def _run():
    entries = _load_fixture()

    _ensure_currency()
    _ensure_warehouse_type_transit()
    company = _resolve_company()
    abbr = frappe.db.get_value("Company", company, "abbr")
    warehouse = _ensure_warehouse(company, abbr)
    _ensure_uom_nos()
    _ensure_item_group_products()
    _ensure_fiscal_year()
    expense_account = _resolve_temporary_opening_account(company)

    print(f"Ravaka hydrate — Company cible : {company} (abbr {abbr}), warehouse : {warehouse}")

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
            # Commit immédiatement : si la Stock Reconciliation échoue ensuite,
            # frappe.db.rollback() ne doit PAS aussi défaire la création de
            # l'Item (confirmé par repro locale : sans ce commit, un item
            # recréé "avec succès" à chaque rejeu du patch après un échec SR).
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
            failures.append(f"{item_code}: {frappe.get_traceback(with_context=False)}")
            frappe.log_error(
                title=f"Ravaka hydrate — échec item {item_code}",
                message=frappe.get_traceback(),
            )
            continue

        try:
            if qty and qty > 0:
                if _create_opening_stock(item_code, qty, company, warehouse, expense_account):
                    stats["sr_created"] += 1
                else:
                    stats["sr_skipped"] += 1
            frappe.db.commit()
        except Exception:
            # Un échec de stock reconciliation ne doit pas faire planter tout
            # le patch, ni défaire l'Item déjà committé ci-dessus.
            frappe.db.rollback()
            failures.append(f"{item_code} (stock reconciliation): {frappe.get_traceback(with_context=False)}")
            frappe.log_error(
                title=f"Ravaka hydrate — échec stock reconciliation {item_code}",
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
def _ensure_warehouse_type_transit():
    """Crée le Warehouse Type "Transit" s'il est absent.

    Sur un site créé directement via `bench new-site --install-app` (sans passer
    par le Setup Wizard ERPNext), ce master n'existe pas encore. Or
    `Company.on_update() -> create_default_warehouses()` crée un entrepôt
    "Goods In Transit" lié à `warehouse_type="Transit"` : sans ce master, la
    création de la Company échoue avec un LinkValidationError (confirmé par
    repro locale). ERPNext ne fournit pas de fixture pour ce master hors
    Setup Wizard, donc on le crée nous-mêmes, idempotent.
    """
    if not frappe.db.exists("Warehouse Type", "Transit"):
        frappe.get_doc({
            "doctype": "Warehouse Type",
            "name": "Transit",
        }).insert(ignore_permissions=True)


def _ensure_currency():
    if not frappe.db.exists("Currency", FALLBACK_COMPANY_CURRENCY):
        frappe.get_doc({
            "doctype": "Currency",
            "currency_name": FALLBACK_COMPANY_CURRENCY,
            "enabled": 1,
            "symbol": "Ar",
        }).insert(ignore_permissions=True)


def _resolve_company():
    """Détermine la Company cible pour l'hydratation, sans jamais deviner à l'aveugle.

    Ordre de résolution : Global Defaults > Default Company, puis l'unique
    Company existante, puis création de repli "Ravaka" si le site est vierge.
    Si plusieurs Companies existent sans default_company défini, échoue
    proprement plutôt que de choisir au hasard.
    """
    default_company = frappe.defaults.get_global_default("company")
    if default_company and frappe.db.exists("Company", default_company):
        return default_company

    companies = frappe.get_all("Company", pluck="name")
    if len(companies) == 1:
        return companies[0]

    if not companies:
        return _create_fallback_company()

    frappe.throw(
        f"Impossible de déterminer la Company cible pour l'hydratation Ravaka : "
        f"{len(companies)} Companies existent ({', '.join(companies)}) et aucun "
        f"« Default Company » n'est défini dans Setup > Global Defaults. "
        f"Configure un Default Company puis relance le patch."
    )


def _create_fallback_company():
    """Crée la Company de repli Ravaka/RAV (site vierge, aucune Company existante)."""
    other = frappe.db.get_value("Company", {"abbr": FALLBACK_COMPANY_ABBR}, "name")
    if other:
        frappe.throw(
            f"Conflit d'abréviation : l'abréviation « {FALLBACK_COMPANY_ABBR} » est "
            f"déjà utilisée par la Company « {other} ». Impossible de créer "
            f"« {FALLBACK_COMPANY_NAME} ». Résolvez le conflit manuellement."
        )
    frappe.get_doc({
        "doctype": "Company",
        "company_name": FALLBACK_COMPANY_NAME,
        "abbr": FALLBACK_COMPANY_ABBR,
        "default_currency": FALLBACK_COMPANY_CURRENCY,
        "country": FALLBACK_COMPANY_COUNTRY,
        # Madagascar n'a pas de modèle de plan comptable ERPNext dédié :
        # forcer explicitement le template générique "Standard" évite que
        # Company.after_insert() échoue en cherchant un CoA par pays.
        "create_chart_of_accounts_based_on": "Standard Template",
        "chart_of_accounts": "Standard",
    }).insert(ignore_permissions=True)
    frappe.db.commit()
    return FALLBACK_COMPANY_NAME


def _ensure_warehouse(company, abbr):
    """Retourne le Warehouse "Stores - <abbr>" de la Company, le crée si absent."""
    warehouse = f"Stores - {abbr}"
    if frappe.db.exists("Warehouse", warehouse):
        return warehouse

    doc = {
        "doctype": "Warehouse",
        "warehouse_name": "Stores",
        "company": company,
    }
    parent = f"All Warehouses - {abbr}"
    if frappe.db.exists("Warehouse", parent):
        doc["parent_warehouse"] = parent
    frappe.get_doc(doc).insert(ignore_permissions=True)
    frappe.db.commit()
    return warehouse


def _resolve_temporary_opening_account(company):
    """Trouve le compte "Temporary Opening" de la Company via account_type.

    Le NOM exact varie selon le Chart of Accounts (ex. "Temporary Opening - RAV"
    avec le template "Standard", mais "1910 - Temporary Opening - ME" avec
    "Standard with Numbers" — confirmé en prod). On cherche donc par
    `account_type="Temporary"` (stable quel que soit le CoA) plutôt que de
    construire le nom par concaténation.
    """
    account = frappe.db.get_value(
        "Account", {"company": company, "account_type": "Temporary"}, "name"
    )
    if not account:
        frappe.throw(
            f"Aucun compte account_type=Temporary trouvé pour la Company "
            f"« {company} » — impossible de créer les Stock Reconciliation "
            f"d'ouverture sans compte de différence valide."
        )
    return account


# ── UOM / Item Group ─────────────────────────────────────────────────────────
def _ensure_uom_nos():
    """Crée l'UOM "Nos" si absente.

    Sur un site sans Setup Wizard exécuté, aucun UOM standard n'existe (ils
    sont normalement importés depuis erpnext/setup/setup_wizard/data/uom_data.json
    par le wizard, jamais par `bench new-site --install-app`). Valeurs reprises
    à l'identique de ce fichier officiel pour rester cohérent avec un site qui
    aurait, lui, suivi le Setup Wizard normalement.
    """
    if not frappe.db.exists("UOM", STOCK_UOM):
        frappe.get_doc({
            "doctype": "UOM",
            "uom_name": STOCK_UOM,
            "must_be_whole_number": 1,
        }).insert(ignore_permissions=True)
        frappe.db.commit()


def _ensure_fiscal_year():
    """Crée le Fiscal Year (année civile) couvrant la date du jour, s'il est absent.

    Aucun Fiscal Year n'existe sans Setup Wizard. Sans lui, la validation du
    Stock Ledger Entry lors du submit d'une Stock Reconciliation échoue avec
    `FiscalYearError: Date ... is not in any active Fiscal Year` (confirmé par
    repro locale). Année civile simple (01-01 -> 31-12), cohérent avec le
    calendrier standard utilisé par défaut par ERPNext hors configuration
    spécifique.
    """
    today = frappe.utils.getdate(frappe.utils.today())
    year_name = str(today.year)
    if frappe.db.exists("Fiscal Year", year_name):
        return
    frappe.get_doc({
        "doctype": "Fiscal Year",
        "year": year_name,
        "year_start_date": f"{today.year}-01-01",
        "year_end_date": f"{today.year}-12-31",
    }).insert(ignore_permissions=True)
    frappe.db.commit()


def _ensure_item_group_products():
    """Crée l'arbre Item Group "All Item Groups" > "Products" si absent.

    Même cause que ci-dessus : aucun Item Group n'existe sans Setup Wizard.
    """
    root = "All Item Groups"
    if not frappe.db.exists("Item Group", root):
        frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": root,
            "is_group": 1,
        }).insert(ignore_permissions=True)
        frappe.db.commit()

    if not frappe.db.exists("Item Group", ITEM_GROUP):
        frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": ITEM_GROUP,
            "is_group": 0,
            "parent_item_group": root,
        }).insert(ignore_permissions=True)
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
def _create_opening_stock(item_code, qty, company, warehouse, expense_account):
    """Crée + soumet une Stock Reconciliation Opening Stock. Idempotent.

    Retourne True si créée, False si ignorée (stock déjà présent dans l'entrepôt).
    """
    # Idempotence : si l'item a déjà du stock dans l'entrepôt, on ne rejoue pas.
    existing_qty = frappe.db.get_value(
        "Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty"
    )
    if existing_qty and float(existing_qty) != 0:
        return False

    sr = frappe.get_doc({
        "doctype": "Stock Reconciliation",
        "purpose": "Opening Stock",
        "company": company,
        # Une Opening Entry exige un compte de différence de type Asset/Liability
        # (validate_expense_account côté ERPNext) — résolu dynamiquement par
        # account_type="Temporary" (voir _resolve_temporary_opening_account).
        "expense_account": expense_account,
        "items": [{
            "item_code": item_code,
            "warehouse": warehouse,
            "qty": qty,
            "valuation_rate": 0,
            "allow_zero_valuation_rate": 1,
        }],
    })
    sr.insert(ignore_permissions=True)
    sr.submit()
    return True
