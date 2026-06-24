/**
 * Tools MCP — Fournisseurs et commandes.
 */
import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { getClient } from '../client.js';
import { ToolResult } from '../types.js';

export const supplierTools: Tool[] = [
  {
    name: 'create_supplier_order',
    description:
      "Créer une commande fournisseur dans ERPNext. " +
      "Utiliser quand l'utilisateur veut commander des produits auprès d'un fournisseur. " +
      "Toujours vérifier le stock actuel des produits concernés avant de créer la commande. " +
      "Présenter un récapitulatif complet et demander confirmation avant de créer.",
    inputSchema: {
      type: 'object',
      properties: {
        supplier_name: { type: 'string', description: 'Nom exact du fournisseur dans ERPNext' },
        items: {
          type: 'array',
          description: 'Articles à commander',
          items: {
            type: 'object',
            properties: {
              item_code_or_name: { type: 'string' },
              qty: { type: 'number' },
              rate: { type: 'number', description: "Prix d'achat (optionnel)" },
            },
            required: ['item_code_or_name', 'qty'],
          },
        },
        notes: { type: 'string', description: 'Notes pour le fournisseur (optionnel)' },
      },
      required: ['supplier_name', 'items'],
    },
  },
  {
    name: 'get_pending_orders',
    description:
      "Voir les commandes fournisseurs en cours (envoyées mais pas encore reçues). " +
      "Utiliser pour le suivi des livraisons, ou quand l'utilisateur demande " +
      "'les commandes en attente', 'qu'est-ce qu'on attend comme livraison'.",
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'get_suppliers',
    description:
      "Lister les fournisseurs actifs avec leurs produits habituels. " +
      "Utiliser pour savoir auprès de qui commander un produit, " +
      "ou avant de créer une commande fournisseur.",
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
];

export async function handleSupplierTool(name: string, args: Record<string, unknown>): Promise<ToolResult> {
  const client = getClient();
  try {
    const result = await client.call(name, args);
    const text = typeof result === 'object' && result !== null && 'message' in result
      ? (result as { message: string }).message + '\n\n```json\n' + JSON.stringify(result, null, 2) + '\n```'
      : JSON.stringify(result, null, 2);
    return { content: [{ type: 'text', text }] };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { content: [{ type: 'text', text: `Erreur fournisseurs — ${msg}` }], isError: true };
  }
}
