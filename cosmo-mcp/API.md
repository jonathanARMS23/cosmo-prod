# cosmo-mcp — Référence des Tools MCP

## Vue d'ensemble

| Tool | Module | Endpoint ERPNext | Description |
|------|--------|-----------------|-------------|
| `get_item_stock` | Stock | `get_item_stock` | Stock actuel d'un produit |
| `get_low_stock_items` | Stock | `get_low_stock_items` | Produits sous seuil de réappro |
| `get_expiring_items` | Stock | `get_expiring_items` | Produits expirant dans N jours |
| `search_items` | Stock | `search_items` | Recherche catalogue par nom/code/marque |
| `receive_stock` | Stock | `receive_stock` | Réception marchandise fournisseur |
| `adjust_stock` | Stock | `adjust_stock` | Correction inventaire (Stock Reconciliation) |
| `create_item` | Stock | `create_item` | Créer un nouveau produit |
| `update_item_price` | Stock | `update_item_price` | Mettre à jour le prix de vente |
| `create_sale` | Ventes | `create_sale` | Créer une facture vente (POS) |
| `get_daily_sales` | Ventes | `get_daily_sales` | Résumé ventes d'une journée |
| `get_sales_period` | Ventes | `get_sales_period` | Analyse ventes sur période |
| `get_invoice` | Ventes | `get_invoice` | Détail d'une facture par numéro |
| `cancel_invoice` | Ventes | `cancel_invoice` | Annuler une facture soumise |
| `find_or_create_customer` | CRM | `get_customer` + `create_customer` | Trouver ou créer un client |
| `get_customer_profile` | CRM | `get_customer` + `get_customer_history` | Profil complet + historique |
| `get_inactive_customers` | CRM | `get_inactive_customers` | Clients sans achat depuis N jours |
| `get_top_customers` | CRM | `get_top_customers` | Meilleures clientes par CA |
| `create_supplier_order` | Fournisseurs | `create_supplier_order` | Créer une commande fournisseur |
| `get_pending_orders` | Fournisseurs | `get_pending_orders` | Commandes en attente de livraison |
| `get_suppliers` | Fournisseurs | `get_suppliers` | Liste fournisseurs actifs |
| `identify_product_from_image` | Vision | `search_items` | Identifier un produit via données image |
| `process_supplier_invoice_image` | Vision | `create_supplier_order` | Enregistrer facture fournisseur OCR |
| `create_item_from_image` | Vision | `create_item` | Créer fiche produit depuis photo |
| `get_dashboard` | Rapports | `get_dashboard_summary` | Briefing boutique : CA, alertes, top produit |
| `get_revenue_trend` | Rapports | `get_revenue_trend` | Évolution CA sur N jours |
| `get_category_performance` | Rapports | `get_category_breakdown` | Performances par catégorie cosmétique |

---

## Authentification

L'API ERPNext utilise des API Keys statiques. Le MCP Server les lit depuis les variables d'environnement :

```
ERPNEXT_API_KEY=<api_key>
ERPNEXT_API_SECRET=<api_secret>
ERPNEXT_URL=https://<votre-instance>.erpnext.com
```

Chaque requête inclut le header :

```
Authorization: token <ERPNEXT_API_KEY>:<ERPNEXT_API_SECRET>
```

Les clés se génèrent dans ERPNext > Paramètres Utilisateur > API Access.

---

## Convention de réponse

Tous les endpoints retournent un champ `message` en français lisible par Hermes, plus les données structurées.

**Succès :**
```json
{ "message": "Produit 'Crème Hydratante' : 12 Pcs en stock.", "item_code": "COSMO-001", "qty": 12 }
```

**Erreur (isError) :**
```json
{ "message": "❌ Produit COSMO-999 introuvable.", "isError": true }
```

Les erreurs ERPNext lèvent `frappe.throw()` en français — le MCP les capture et retourne `isError: true`.

---

## Module Stock (8 tools)

### `get_item_stock`
Retourne le stock actuel d'un produit, le seuil de réapprovisionnement, et les détails par entrepôt.

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| `item_code` | string | Non* | Code ERPNext du produit (prioritaire) |
| `item_name` | string | Non* | Nom du produit (recherche fuzzy) |

*Au moins un des deux est requis.

```json
{ "item_code": "COSMO-001", "item_name": "Crème Hydratante", "qty": 12, "uom": "Pcs",
  "cosmo_reorder_level": 5, "is_low_stock": false, "message": "Crème Hydratante : 12 Pcs en stock." }
```

---

### `get_low_stock_items`
Aucun paramètre. Retourne les produits dont le stock < `cosmo_reorder_level`.

```json
{ "count": 3, "items": [{ "item_name": "Sérum Vitamine C", "qty": 1, "reorder_level": 5, "deficit": 4 }],
  "message": "3 produit(s) en stock critique : Sérum Vitamine C, ..." }
```

---

### `get_expiring_items`

| Paramètre | Type | Requis | Défaut |
|-----------|------|--------|--------|
| `days` | number | Non | 30 |

```json
{ "count": 2, "items": [{ "item_name": "Fond de Teint", "cosmo_expiry_date": "2026-07-10", "days_remaining": 16, "qty": 5 }],
  "message": "2 produit(s) expirent dans moins de 30 jours." }
```

---

### `search_items`

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| `query` | string | Oui | Terme (min. 2 caractères) |
| `category` | string | Non | `Soin Visage` \| `Soin Corps` \| `Maquillage` \| `Parfum` \| `Hygiène` \| `Autre` |

```json
{ "count": 2, "items": [{ "item_code": "COSMO-012", "item_name": "Crème Hydratante SPF50", "standard_rate": 45000, "qty": 8 }] }
```

---

### `receive_stock`

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| `item_code` | string | Oui | Code produit |
| `qty` | number | Oui | Quantité reçue |
| `rate` | number | Oui | Prix d'achat unitaire (Ariary) |
| `supplier` | string | Non | Nom fournisseur |
| `expiry_date` | string | Non | Date expiration YYYY-MM-DD |

Crée une **Stock Entry de type Material Receipt**.

```json
{ "stock_entry_name": "STE-00042", "item_name": "Crème Hydratante", "qty": 20, "rate": 18000,
  "message": "Réception enregistrée : 20 x Crème Hydratante à 18000 Ar/u." }
```

---

### `adjust_stock`

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| `item_code` | string | Oui | Code produit |
| `new_qty` | number | Oui | Quantité réelle constatée (pas la différence) |
| `reason` | string | Oui | Motif obligatoire |

Crée une **Stock Reconciliation**. Action irréversible — demander confirmation avant.

```json
{ "stock_entry_name": "SRECON-00005", "old_qty": 10, "new_qty": 7, "difference": -3,
  "message": "Stock ajusté pour Crème Hydratante : 10 -> 7 (-3). Motif : Casse." }
```

---

### `create_item`

| Paramètre | Type | Requis | Défaut |
|-----------|------|--------|--------|
| `item_name` | string | Oui | — |
| `cosmo_category` | string | Oui | — |
| `standard_rate` | number | Oui | — |
| `cosmo_brand` | string | Non | — |
| `cosmo_reorder_level` | number | Non | 5 |
| `cosmo_preferred_supplier` | string | Non | — |

```json
{ "item_code": "COSMO-089", "item_name": "Gel Douche Coco", "message": "Produit 'Gel Douche Coco' créé avec le code COSMO-089." }
```

---

### `update_item_price`

| Paramètre | Type | Requis |
|-----------|------|--------|
| `item_code` | string | Oui |
| `new_price` | number | Oui |

```json
{ "success": true, "old_price": 25000, "new_price": 28000, "message": "Prix de 'Crème Hydratante' mis à jour : 25000 -> 28000 Ar." }
```

---

## Module Ventes (5 tools)

### `create_sale`

| Paramètre | Type | Requis | Défaut |
|-----------|------|--------|--------|
| `items` | array | Oui | — |
| `items[].item_code_or_name` | string | Oui | — |
| `items[].qty` | number | Oui | — |
| `items[].rate` | number | Non | Prix catalogue |
| `customer` | string | Non | Walk-in Customer |
| `payment_mode` | string | Non | Cash |
| `discount` | number | Non | 0 |

`payment_mode` accepte : `Cash`, `Card`, `Mobile Money`, `Espèces`, `Carte`.
Décrémente le stock automatiquement. Toujours demander confirmation avant appel.

```json
{ "invoice_name": "ACC-SINV-2026-00123", "grand_total": 56000, "payment_mode": "Cash",
  "status": "Submitted", "message": "Vente créée : ACC-SINV-2026-00123 — 56000 Ar (Cash)." }
```

---

### `get_daily_sales`

| Paramètre | Type | Requis | Défaut |
|-----------|------|--------|--------|
| `date` | string | Non | Aujourd'hui |

```json
{ "date": "2026-06-24", "total_revenue": 185000, "transaction_count": 7, "avg_basket": 26428,
  "top_items": [{ "item_name": "Crème Hydratante", "qty": 4, "amount": 100000 }] }
```

---

### `get_sales_period`

| Paramètre | Type | Requis |
|-----------|------|--------|
| `date_from` | string | Oui |
| `date_to` | string | Oui |

```json
{ "total_revenue": 1240000, "transactions": 47, "avg_basket": 26382,
  "top_items": [...], "by_category": [{ "category": "Soin Visage", "revenue": 620000 }] }
```

---

### `get_invoice`

| Paramètre | Type | Requis |
|-----------|------|--------|
| `invoice_name` | string | Oui |

Format : `ACC-SINV-YYYY-NNNNN`

```json
{ "name": "ACC-SINV-2026-00123", "customer": "Mme Rakoto", "grand_total": 56000,
  "status": "Paid", "items": [{ "item_name": "Crème Hydratante", "qty": 2, "rate": 28000 }] }
```

---

### `cancel_invoice`

| Paramètre | Type | Requis |
|-----------|------|--------|
| `invoice_name` | string | Oui |
| `reason` | string | Oui (min. 5 car.) |

Action irréversible. Ne jamais appeler sans confirmation explicite.

```json
{ "success": true, "message": "Facture ACC-SINV-2026-00123 annulée. Motif : Erreur saisie." }
```

---

## Module Clients CRM (4 tools)

### `find_or_create_customer`

| Paramètre | Type | Requis | Défaut |
|-----------|------|--------|--------|
| `name` | string | Oui | — |
| `mobile_no` | string | Non | — |
| `email_id` | string | Non | — |
| `create_if_not_found` | boolean | Non | false |

Cherche d'abord par nom puis par téléphone. Si introuvable et `create_if_not_found: false`, demande confirmation avant création.

---

### `get_customer_profile`

| Paramètre | Type | Requis |
|-----------|------|--------|
| `customer_name` | string | Oui |

Combine `get_customer` + `get_customer_history` (5 dernières factures).

```json
{ "customer_name": "Mme Rakoto", "total_purchases": 320000, "visits": 8,
  "last_purchase": "2026-06-10", "recent_invoices": [...] }
```

---

### `get_inactive_customers`

| Paramètre | Type | Requis | Défaut |
|-----------|------|--------|--------|
| `days` | number | Non | 60 |

```json
{ "count": 12, "customers": [{ "customer_name": "Mme Rasoa", "last_purchase": "2026-03-01", "days_inactive": 115 }],
  "message": "12 client(s) inactif(s) depuis plus de 60 jours." }
```

---

### `get_top_customers`

| Paramètre | Type | Requis | Valeurs | Défaut |
|-----------|------|--------|---------|--------|
| `limit` | number | Non | 1-50 | 10 |
| `period` | string | Non | `today` \| `week` \| `month` \| `quarter` \| `year` | month |

```json
{ "period": "month", "customers": [{ "customer_name": "Mme Rakoto", "total_spent": 320000, "visits": 8 }] }
```

---

## Module Fournisseurs (3 tools)

### `create_supplier_order`

| Paramètre | Type | Requis |
|-----------|------|--------|
| `supplier_name` | string | Oui |
| `items` | array | Oui |
| `items[].item_code_or_name` | string | Oui |
| `items[].qty` | number | Oui |
| `items[].rate` | number | Non |
| `notes` | string | Non |

Crée un doctype **Cosmo Supplier Order** (pas une Purchase Order standard).

```json
{ "order_name": "CSO-2026-00015", "supplier": "Beauty Pro Madagascar", "items_count": 3, "total": 540000,
  "message": "Commande CSO-2026-00015 créée pour Beauty Pro Madagascar (3 article(s))." }
```

---

### `get_pending_orders`
Aucun paramètre. Retourne les `Cosmo Supplier Order` au statut `Envoye` ou `Confirme`.

```json
{ "count": 2, "orders": [{ "name": "CSO-2026-00015", "supplier": "Beauty Pro", "status": "Envoye", "total_amount": 540000 }] }
```

---

### `get_suppliers`
Aucun paramètre. Retourne les fournisseurs actifs + leurs 5 produits habituels.

```json
{ "suppliers": [{ "supplier_name": "Beauty Pro Madagascar", "preferred_items": ["Crème Hydratante", "Sérum"] }],
  "message": "4 fournisseur(s) actif(s)." }
```

---

## Module Vision (3 tools)

**Architecture Hermes-Vision :** Hermes analyse l'image nativement avec son outil `vision_analyze`, extrait les données textuelles (marque, nom, montant, lignes), puis appelle ces tools MCP avec les données structurées extraites. Ces tools n'ont pas accès direct aux images — ils reçoivent uniquement les données déjà interprétées.

### `identify_product_from_image`

| Paramètre | Type | Requis |
|-----------|------|--------|
| `image_description` | string | Oui |
| `brand` | string | Non |
| `product_name` | string | Non |
| `barcode` | string | Non |

Délègue à `search_items`. Si non trouvé, propose `create_item_from_image`.

---

### `process_supplier_invoice_image`

| Paramètre | Type | Requis |
|-----------|------|--------|
| `supplier_name` | string | Oui |
| `items` | array | Oui |
| `items[].description` | string | Oui |
| `items[].qty` | number | Oui |
| `items[].unit_price` | number | Oui |
| `total_amount` | number | Oui |
| `invoice_number` | string | Non |
| `invoice_date` | string | Non |
| `raw_text` | string | Non |

Crée une `Cosmo Supplier Order` avec les lignes mappées. Requiert validation manuelle pour la Purchase Invoice.

---

### `create_item_from_image`

| Paramètre | Type | Requis |
|-----------|------|--------|
| `item_name` | string | Oui |
| `cosmo_category` | string | Oui |
| `standard_rate` | number | Oui |
| `cosmo_brand` | string | Non |
| `cosmo_ingredients` | string | Non |

Alias de `create_item` avec champ INCI optionnel. À appeler uniquement après confirmation utilisateur.

---

## Module Rapports (3 tools)

### `get_dashboard`

| Paramètre | Type | Requis | Défaut |
|-----------|------|--------|--------|
| `include_alerts` | boolean | Non | true |

Endpoint réel : `get_dashboard_summary`.

```json
{ "today_revenue": 185000, "today_transactions": 7, "low_stock_count": 3,
  "expiring_soon_count": 2, "top_product_today": "Crème Hydratante",
  "alerts": ["3 produit(s) en stock critique"] }
```

---

### `get_revenue_trend`

| Paramètre | Type | Requis | Défaut | Max |
|-----------|------|--------|--------|-----|
| `days` | number | Non | 30 | 90 |

```json
{ "days": 30, "trend": [{ "date": "2026-06-24", "revenue": 185000, "transactions": 7 }] }
```

---

### `get_category_performance`

| Paramètre | Type | Requis | Valeurs | Défaut |
|-----------|------|--------|---------|--------|
| `period` | string | Non | `week` \| `month` \| `quarter` | month |

Endpoint réel : `get_category_breakdown`.

```json
{ "period": "month", "categories": [{ "category": "Soin Visage", "revenue": 620000, "units_sold": 22, "percentage": 50.0 }], "total": 1240000 }
```

---

## Erreurs courantes

| Code HTTP | Cause | Solution |
|-----------|-------|----------|
| 401 | API Key invalide ou absente | Vérifier `ERPNEXT_API_KEY` / `ERPNEXT_API_SECRET` |
| 403 | Permissions insuffisantes | Activer les permissions sur le doctype dans ERPNext |
| 404 | Produit / facture / client introuvable | Vérifier le code exact ou utiliser `search_items` |
| 409 | Conflit (produit déjà existant) | Le client / produit existe déjà — récupérer l'existant |
| 500 | Erreur ERPNext interne | Consulter les logs ERPNext (frappe.log_error) |
| `isError: true` (MCP) | Stock insuffisant, motif manquant, quantité invalide | Lire le champ `message` pour le détail |

---

## Endpoint ERPNext direct

Pattern URL :
```
POST /api/method/cosmo_erp.cosmo_erp.api.main.<function_name>
```

Header obligatoire :
```
Authorization: token <api_key>:<api_secret>
Content-Type: application/json
```

Exemple :
```bash
curl -X POST https://erp.example.com/api/method/cosmo_erp.cosmo_erp.api.main.get_item_stock \
  -H "Authorization: token abc123:xyz789" \
  -H "Content-Type: application/json" \
  -d '{"item_code": "COSMO-001"}'
```

Toutes les fonctions sont décorées `@frappe.whitelist()` dans `cosmo_erp/api/main.py`.
