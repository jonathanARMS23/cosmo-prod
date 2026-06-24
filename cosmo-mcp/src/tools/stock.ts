/**
 * Tools MCP — Gestion du stock et des produits.
 * Les descriptions sont en français car Hermes les lit pour le routing.
 */
import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { getClient } from '../client.js';
import { ToolResult } from '../types.js';

export const stockTools: Tool[] = [
  {
    name: 'get_item_stock',
    description:
      "Obtenir le niveau de stock actuel d'un produit spécifique. " +
      "Utiliser quand l'utilisateur demande 'combien il reste de X', 'quel est le stock de Y', " +
      "'est-ce qu'on a encore du Z', 'il reste combien de [produit]'. " +
      'Préférer ce tool à get_all_stock quand le produit est identifié.',
    inputSchema: {
      type: 'object',
      properties: {
        item_code: { type: 'string', description: 'Code ERPNext du produit (prioritaire si connu)' },
        item_name: { type: 'string', description: 'Nom du produit (si item_code non disponible)' },
      },
    },
  },
  {
    name: 'get_low_stock_items',
    description:
      "Lister tous les produits dont le stock est sous le seuil minimum de réapprovisionnement. " +
      "Utiliser pour les alertes de réapprovisionnement, les rapports du matin, " +
      "ou quand l'utilisateur demande 'qu'est-ce qu'on doit commander', 'quels produits manquent', " +
      "'qu'est-ce qui est en rupture', 'liste des produits critiques'.",
    inputSchema: { type: 'object', properties: {} },
  },
  {
    name: 'get_expiring_items',
    description:
      "Lister les produits dont la date d'expiration approche dans les prochains N jours. " +
      "Utiliser quand l'utilisateur demande les produits qui vont expirer, pour planifier des promos " +
      "de déstockage, ou pour faire le point avant une commande. " +
      "Par défaut vérifie les 30 prochains jours.",
    inputSchema: {
      type: 'object',
      properties: {
        days: { type: 'number', description: "Horizon en jours (défaut: 30)", default: 30 },
      },
    },
  },
  {
    name: 'search_items',
    description:
      "Rechercher des produits dans le catalogue par nom, code ou marque. " +
      "Utiliser pour trouver un produit avant une vente, avant une commande fournisseur, " +
      "ou pour vérifier si un produit existe dans le système. " +
      "Retourne le prix et le stock de chaque résultat.",
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Terme de recherche (nom, marque, code)' },
        category: {
          type: 'string',
          description: 'Filtrer par catégorie',
          enum: ['Soin Visage', 'Soin Corps', 'Maquillage', 'Parfum', 'Hygiène', 'Autre'],
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'receive_stock',
    description:
      "Enregistrer une réception de marchandise fournisseur dans le stock. " +
      "Utiliser quand l'utilisateur dit 'on vient de recevoir X unités de Y', " +
      "'livraison reçue de [fournisseur]', 'entrée stock', 'on a reçu la commande'. " +
      "Crée une Stock Entry de type Material Receipt dans ERPNext. " +
      "IMPORTANT : ne pas utiliser pour des corrections d'inventaire, utiliser adjust_stock.",
    inputSchema: {
      type: 'object',
      properties: {
        item_code: { type: 'string', description: 'Code du produit reçu' },
        qty: { type: 'number', description: 'Quantité reçue' },
        rate: { type: 'number', description: "Prix d'achat unitaire" },
        supplier: { type: 'string', description: 'Nom du fournisseur (optionnel)' },
        expiry_date: { type: 'string', description: "Date d'expiration ISO YYYY-MM-DD (optionnel)" },
      },
      required: ['item_code', 'qty', 'rate'],
    },
  },
  {
    name: 'adjust_stock',
    description:
      "Corriger le niveau de stock après un inventaire ou une perte (casse, vol). " +
      "Utiliser UNIQUEMENT pour des corrections (inventaire physique, casse, vol), " +
      "PAS pour des réceptions fournisseur (utiliser receive_stock pour ça). " +
      "Demander confirmation à l'utilisateur avant d'exécuter car action irréversible.",
    inputSchema: {
      type: 'object',
      properties: {
        item_code: { type: 'string', description: 'Code du produit à ajuster' },
        new_qty: { type: 'number', description: 'Quantité réelle constatée (pas la différence)' },
        reason: { type: 'string', description: "Motif de l'ajustement (obligatoire)" },
      },
      required: ['item_code', 'new_qty', 'reason'],
    },
  },
  {
    name: 'create_item',
    description:
      "Créer un nouveau produit dans le catalogue ERPNext. " +
      "Utiliser quand un nouveau produit est référencé pour la première fois, " +
      "quand l'utilisateur dit 'ajoute ce produit', 'nouveau produit à créer'. " +
      "Toujours demander confirmation des informations avant de créer.",
    inputSchema: {
      type: 'object',
      properties: {
        item_name: { type: 'string', description: 'Nom commercial du produit' },
        cosmo_category: {
          type: 'string',
          enum: ['Soin Visage', 'Soin Corps', 'Maquillage', 'Parfum', 'Hygiène', 'Autre'],
          description: 'Catégorie cosmétique',
        },
        standard_rate: { type: 'number', description: 'Prix de vente en Ariary' },
        cosmo_brand: { type: 'string', description: 'Marque (optionnel)' },
        cosmo_reorder_level: { type: 'number', description: 'Seuil de réapprovisionnement (défaut: 5)', default: 5 },
        cosmo_preferred_supplier: { type: 'string', description: 'Fournisseur préféré (optionnel)' },
      },
      required: ['item_name', 'cosmo_category', 'standard_rate'],
    },
  },
  {
    name: 'update_item_price',
    description:
      "Mettre à jour le prix de vente d'un produit. " +
      "Utiliser quand l'utilisateur dit 'change le prix de X à Y', 'nouveau prix pour Z'. " +
      "Demander confirmation avant d'appliquer le changement.",
    inputSchema: {
      type: 'object',
      properties: {
        item_code: { type: 'string', description: 'Code du produit' },
        new_price: { type: 'number', description: 'Nouveau prix de vente en Ariary' },
      },
      required: ['item_code', 'new_price'],
    },
  },
];

export async function handleStockTool(name: string, args: Record<string, unknown>): Promise<ToolResult> {
  const client = getClient();
  try {
    const result = await client.call(name, args);
    const text = typeof result === 'object' && result !== null && 'message' in result
      ? (result as { message: string }).message
      : JSON.stringify(result, null, 2);
    return { content: [{ type: 'text', text: text + '\n\n```json\n' + JSON.stringify(result, null, 2) + '\n```' }] };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { content: [{ type: 'text', text: `Erreur stock — ${msg}` }], isError: true };
  }
}
