/**
 * Tools MCP — Dashboard et rapports.
 */
import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { getClient } from '../client.js';
import { ToolResult } from '../types.js';

export const reportTools: Tool[] = [
  {
    name: 'get_dashboard',
    description:
      "Obtenir le résumé complet de la boutique : ventes du jour, stock critique, " +
      "produits expirant bientôt, top produit du jour. " +
      "Utiliser pour le briefing matinal, les questions générales sur l'état de la boutique, " +
      "'comment ça se passe aujourd'hui ?', 'point boutique', 'résumé du jour'.",
    inputSchema: {
      type: 'object',
      properties: {
        include_alerts: {
          type: 'boolean',
          description: 'Inclure les alertes stock et expiration (défaut: true)',
          default: true,
        },
      },
    },
  },
  {
    name: 'get_revenue_trend',
    description:
      "Voir l'évolution du chiffre d'affaires sur les derniers N jours. " +
      "Utiliser pour analyser les tendances, identifier les bons/mauvais jours, " +
      "comparer les semaines, ou quand l'utilisateur demande 'comment ça évolue'.",
    inputSchema: {
      type: 'object',
      properties: {
        days: { type: 'number', description: 'Nombre de jours à analyser (défaut: 30)', default: 30 },
      },
    },
  },
  {
    name: 'get_category_performance',
    description:
      "Analyser les ventes et performances par catégorie de produits cosmétiques. " +
      "Utiliser pour savoir quelle catégorie se vend le mieux, " +
      "ajuster les commandes fournisseurs selon les tendances, " +
      "ou optimiser l'espace en rayon.",
    inputSchema: {
      type: 'object',
      properties: {
        period: {
          type: 'string',
          enum: ['week', 'month', 'quarter'],
          description: "Période d'analyse (défaut: month)",
          default: 'month',
        },
      },
    },
  },
];

export async function handleReportTool(name: string, args: Record<string, unknown>): Promise<ToolResult> {
  const client = getClient();
  try {
    const apiMethod = name === 'get_dashboard' ? 'get_dashboard_summary'
      : name === 'get_category_performance' ? 'get_category_breakdown'
      : name;

    const result = await client.call(apiMethod, args);
    const text = typeof result === 'object' && result !== null && 'message' in result
      ? (result as { message: string }).message + '\n\n```json\n' + JSON.stringify(result, null, 2) + '\n```'
      : JSON.stringify(result, null, 2);
    return { content: [{ type: 'text', text }] };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { content: [{ type: 'text', text: `Erreur rapports — ${msg}` }], isError: true };
  }
}
