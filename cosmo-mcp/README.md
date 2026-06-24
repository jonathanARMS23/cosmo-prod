# cosmo-mcp

MCP Server Node.js 20 + TypeScript exposant ERPNext (cosmo_erp) à Hermes Agent.

## Architecture

```
Telegram
   |
   v
Hermes Agent (NousResearch)
   |  MCP Protocol (stdio)
   v
cosmo-mcp  <-- ce serveur
   |  POST /api/method/cosmo_erp.cosmo_erp.api.main.<function>
   v
ERPNext (cosmo_erp)
```

## Prérequis

- Node.js >= 20.0.0
- Clés API ERPNext (API Key + API Secret)
- ERPNext avec l'app `cosmo_erp` installée

## Installation

```bash
cd cosmo-mcp
npm install
npm run build
```

## Configuration

```bash
cp .env.example .env
# Editer .env avec vos valeurs
```

Variables requises :

| Variable | Description |
|----------|-------------|
| `ERPNEXT_URL` | URL de votre instance ERPNext (ex: `https://erp.ma-boutique.com`) |
| `ERPNEXT_API_KEY` | API Key du compte ERPNext |
| `ERPNEXT_API_SECRET` | API Secret du compte ERPNext |

## Démarrage

```bash
# Production
npm run build && npm start

# Développement
npm run dev
```

## Intégration Hermes (config.yaml)

```yaml
mcp_servers:
  - name: cosmo-erp
    command: node
    args:
      - /chemin/vers/cosmo-mcp/dist/index.js
    env:
      ERPNEXT_URL: "https://erp.ma-boutique.com"
      ERPNEXT_API_KEY: "your_api_key"
      ERPNEXT_API_SECRET: "your_api_secret"
```

## Docker

```bash
docker build -t cosmo-mcp .
docker run --env-file .env cosmo-mcp
```

## Tools disponibles (25)

### Stock (8)

| Tool | Description |
|------|-------------|
| `get_item_stock` | Stock actuel d'un produit spécifique |
| `get_low_stock_items` | Produits sous le seuil de réapprovisionnement |
| `get_expiring_items` | Produits expirant dans les N prochains jours |
| `search_items` | Recherche dans le catalogue par nom/marque/code |
| `receive_stock` | Enregistrer une réception fournisseur |
| `adjust_stock` | Correction d'inventaire (casse, vol) |
| `create_item` | Créer un nouveau produit dans le catalogue |
| `update_item_price` | Mettre à jour le prix de vente |

### Ventes (5)

| Tool | Description |
|------|-------------|
| `create_sale` | Créer une vente / facture client |
| `get_daily_sales` | Résumé des ventes du jour |
| `get_sales_period` | Analyse sur une période personnalisée |
| `get_invoice` | Détail d'une facture par numéro |
| `cancel_invoice` | Annuler une facture (action irréversible) |

### CRM / Clients (4)

| Tool | Description |
|------|-------------|
| `find_or_create_customer` | Trouver ou créer un client |
| `get_customer_profile` | Profil complet avec historique achats |
| `get_inactive_customers` | Clients sans achat depuis X jours |
| `get_top_customers` | Meilleures clientes par CA |

### Fournisseurs (3)

| Tool | Description |
|------|-------------|
| `create_supplier_order` | Créer une commande fournisseur |
| `get_pending_orders` | Commandes en attente de livraison |
| `get_suppliers` | Liste des fournisseurs actifs |

### Vision / OCR (3)

| Tool | Description |
|------|-------------|
| `identify_product_from_image` | Identifier un produit depuis données image extraites par Hermes |
| `process_supplier_invoice_image` | Traiter une facture fournisseur depuis données OCR |
| `create_item_from_image` | Créer une fiche produit depuis données image |

### Rapports / Dashboard (3)

| Tool | Description |
|------|-------------|
| `get_dashboard` | Résumé complet de la boutique (briefing matinal) |
| `get_revenue_trend` | Evolution du CA sur N jours |
| `get_category_performance` | Performances par catégorie cosmétique |

## Test rapide

```bash
# Vérifier que le serveur démarre
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  ERPNEXT_URL=https://test.example.com \
  ERPNEXT_API_KEY=test \
  ERPNEXT_API_SECRET=test \
  node dist/index.js
```

Le serveur doit répondre avec la liste des 25 tools.
