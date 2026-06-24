"""Module de reconnaissance d'image produit — Phase 5.
Les appels LLM sont des placeholders (call_vision_llm) pour branchement ultérieur.
"""
import frappe
from frappe.utils import now_datetime
import hashlib


def process_scan(scan_name):
    """Job de reconnaissance image déclenché en background après création d'un Cosmo Product Scan."""
    try:
        scan = frappe.get_doc("Cosmo Product Scan", scan_name)
        scan.db_set("scan_status", "En cours")

        # Étape 1 : analyser l'image
        product_data = analyze_product_image(scan.image_url)

        # Étape 2 : matcher avec les items ERPNext
        match_result = match_to_item(product_data)

        # Étape 3 : mettre à jour le scan avec les résultats
        import json
        scan.db_set("ai_raw_response", str(product_data))
        scan.db_set("extracted_data", json.dumps(product_data))

        if match_result.get("item_code"):
            scan.db_set("scan_status", "Identifié")
            scan.db_set("matched_item", match_result["item_code"])
            scan.db_set("confidence_score", match_result["confidence"])
        else:
            scan.db_set("scan_status", "Non identifié")
            scan.db_set("confidence_score", match_result.get("confidence", 0))

        frappe.db.commit()

    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Cosmo Vision: Erreur scan {scan_name}")
        frappe.db.set_value("Cosmo Product Scan", scan_name, "scan_status", "Erreur")
        frappe.db.commit()


def analyze_product_image(image_path):
    """Analyse une image produit et retourne les données structurées.

    PLACEHOLDER — call_vision_llm() sera branché en Phase 5.
    Retourne des données mockées pour le développement.
    """
    return call_vision_llm(image_path)


def call_vision_llm(image_path):
    """PLACEHOLDER — Appel au modèle de vision (Claude claude-sonnet-4-6 ou équivalent).

    À remplacer en Phase 5 par l'appel réel à l'API Claude.
    Signature attendue du résultat :
    {
        "brand": str,
        "product_name": str,
        "product_type": str,  # Soin Visage | Soin Corps | Maquillage | Parfum | Hygiène | Autre
        "volume_weight": str,
        "key_ingredients": list[str],
        "barcode": str | None,
        "price_visible": float | None,
        "condition": str,     # neuf | ouvert | endommagé
        "color_shade": str | None,
    }
    """
    # Données mockées pour développement/test
    return {
        "brand": "L'Oréal",
        "product_name": "Serum Vitamine C",
        "product_type": "Soin Visage",
        "volume_weight": "30ml",
        "key_ingredients": ["Acide ascorbique", "Niacinamide"],
        "barcode": None,
        "price_visible": None,
        "condition": "neuf",
        "color_shade": None,
        "_mock": True,
    }


def match_to_item(product_data):
    """Recherche l'item ERPNext correspondant aux données extraites.

    Stratégie de matching :
    1. Par barcode si disponible (priorité max)
    2. Par brand + product_name (fuzzy match)
    3. Par image hash
    """
    # 1. Matching par barcode
    if product_data.get("barcode"):
        item = frappe.db.get_value(
            "Item Barcode",
            {"barcode": product_data["barcode"]},
            "parent"
        )
        if item:
            return {"item_code": item, "confidence": 99.0}

    # 2. Matching par brand + nom (recherche exacte puis partielle)
    brand = product_data.get("brand", "")
    name = product_data.get("product_name", "")

    if brand and name:
        # Recherche exacte
        items = frappe.get_all(
            "Item",
            filters={
                "cosmo_brand": brand,
                "item_name": ["like", f"%{name}%"],
                "disabled": 0,
            },
            fields=["name", "item_name", "cosmo_brand"],
            limit=5
        )
        if items:
            return {"item_code": items[0].name, "confidence": 87.0, "candidates": items}

    # 3. Recherche partielle par nom seul
    if name:
        items = frappe.get_all(
            "Item",
            filters={"item_name": ["like", f"%{name}%"], "disabled": 0},
            fields=["name", "item_name", "cosmo_brand"],
            limit=5
        )
        if items:
            return {"item_code": None, "confidence": 45.0, "candidates": items}

    return {"item_code": None, "confidence": 0.0, "candidates": []}


def compute_image_hash(image_path):
    """Calcule le hash SHA256 d'une image pour stockage et comparaison rapide."""
    try:
        site_path = frappe.get_site_path("public", image_path.lstrip("/"))
        with open(site_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except FileNotFoundError:
        frappe.log_error(f"Image introuvable : {image_path}", "Cosmo Vision Hash")
        return None


def create_item_from_scan(product_data):
    """Crée un nouvel Item ERPNext pré-rempli depuis les données d'un scan."""
    item = frappe.get_doc({
        "doctype": "Item",
        "item_name": f"{product_data.get('brand', '')} {product_data.get('product_name', '')}".strip(),
        "item_group": "Products",
        "is_stock_item": 1,
        "cosmo_brand": product_data.get("brand", ""),
        "cosmo_category": product_data.get("product_type", ""),
        "cosmo_ingredients": ", ".join(product_data.get("key_ingredients", [])),
        "cosmo_ai_description": str(product_data),
        "cosmo_ai_last_scan": now_datetime(),
    })
    item.insert(ignore_permissions=True)
    return item.name
