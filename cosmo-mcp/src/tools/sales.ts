/**
 * Tools MCP — Ventes et facturation.
 */
import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { getClient } from '../client.js';
import { ToolResult } from '../types.js';

export const salesTools: Tool[] = [
  {
    name: 'create_sale',
    description:
      "Créer une vente / facture client dans ERPNext. " +
      "Utiliser quand l'utilisateur dit 'vendre X à Y', 'créer une facture pour', 'encaisser', " +
      "'vends [produit] à [client]', 'facture : [liste produits]'. " +
      "IMPORTANT : toujours présenter un récapitulatif clair et demander confirmation AVANT de créer. " +
      "Format de confirmation : 'Je vais créer cette vente : [détail]. Total : [montant]. Confirmer ?'",
    inputSchema: {
      type: 'object',
      properties: {
        items: {
          type: 'array',
          description: 'Liste des articles à vendre',
          items: {
            type: 'object',
            properties: {
              item_code_or_name: { type: 'string', description: 'Code ou nom du produit' },
              qty: { type: 'number', description: 'Quantité' },
              rate: { type: 'number', description: 'Prix unitaire (optionnel, utilise le prix catalogue si omis)' },
            },
            required: ['item_code_or_name', 'qty'],
          },
        },
        customer: { type: 'string', description: 'Nom du client (optionnel, défaut: Walk-in Customer)' },
        payment_mode: {
          type: 'string',
          enum: ['Cash', 'Card', 'Mobile Money', 'Espèces', 'Carte'],
          description: 'Mode de paiement (défaut: Cash)',
          default: 'Cash',
        },
        discount: { type: 'number', description: 'Remise en pourcentage 0-100 (défaut: 0)', default: 0 },
      },
      required: ['items'],
    },
  },
  {
    name: 'get_daily_sales',
    description:
      "Obtenir le résumé des ventes du jour ou d'une date spécifique. " +
      "Utiliser pour 'combien on a fait aujourd'hui', 'chiffre du jour', " +
      "'résumé des ventes', 'bilan journalier', 'CA du jour'.",
    inputSchema: {
      type: 'object',
      properties: {
        date: { type: 'string', description: "Date ISO YYYY-MM-DD (défaut: aujourd'hui)" },
      },
    },
  },
  {
    name: 'get_sales_period',
    description:
      "Analyser les ventes sur une période personnalisée. " +
      "Utiliser pour les bilans semaine/mois, comparaisons de périodes, analyses de tendances. " +
      "Retourne CA total, top produits et répartition par catégorie.",
    inputSchema: {
      type: 'object',
      properties: {
        date_from: { type: 'string', description: 'Date de début ISO YYYY-MM-DD' },
        date_to: { type: 'string', description: 'Date de fin ISO YYYY-MM-DD' },
      },
      required: ['date_from', 'date_to'],
    },
  },
  {
    name: 'get_invoice',
    description:
      "Récupérer le détail complet d'une facture par son numéro. " +
      "Utiliser quand l'utilisateur mentionne un numéro de facture spécifique " +
      "ou veut vérifier une vente passée.",
    inputSchema: {
      type: 'object',
      properties: {
        invoice_name: { type: 'string', description: "Numéro de facture ERPNext (ex: ACC-SINV-2024-00001)" },
      },
      required: ['invoice_name'],
    },
  },
  {
    name: 'cancel_invoice',
    description:
      "Annuler une facture existante. Action IRREVERSIBLE. " +
      "Toujours demander confirmation avec le numéro de facture et le motif. " +
      "Ne jamais annuler sans confirmation explicite de l'utilisateur. " +
      "Utiliser uniquement en cas d'erreur avérée.",
    inputSchema: {
      type: 'object',
      properties: {
        invoice_name: { type: 'string', description: 'Numéro de facture à annuler' },
        reason: { type: 'string', description: "Motif d'annulation (obligatoire, min. 5 caractères)" },
      },
      required: ['invoice_name', 'reason'],
    },
  },
];

export async function handleSalesTool(name: string, args: Record<string, unknown>): Promise<ToolResult> {
  const client = getClient();
  try {
    const result = await client.call(name, args);
    const text = typeof result === 'object' && result !== null && 'message' in result
      ? (result as { message: string }).message
      : JSON.stringify(result, null, 2);
    return { content: [{ type: 'text', text: text + '\n\n```json\n' + JSON.stringify(result, null, 2) + '\n```' }] };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { content: [{ type: 'text', text: `Erreur ventes — ${msg}` }], isError: true };
  }
}
