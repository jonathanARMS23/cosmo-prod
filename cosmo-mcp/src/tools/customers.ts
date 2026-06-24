/**
 * Tools MCP — CRM et gestion des clients.
 */
import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { getClient } from '../client.js';
import { ToolResult } from '../types.js';

export const customerTools: Tool[] = [
  {
    name: 'find_or_create_customer',
    description:
      "Trouver un client existant ou en créer un nouveau. " +
      "Utiliser avant create_sale si l'utilisateur mentionne un nom de client. " +
      "Chercher d'abord par nom, puis par téléphone avant de proposer la création. " +
      "Exemple : 'Mme Rakoto', 'cliente avec le numéro 034...', 'nouvelle cliente'.",
    inputSchema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Nom du client à rechercher ou créer' },
        mobile_no: { type: 'string', description: 'Numéro de téléphone (optionnel)' },
        email_id: { type: 'string', description: 'Adresse e-mail (optionnel)' },
        create_if_not_found: {
          type: 'boolean',
          description: 'Créer le client automatiquement si introuvable (défaut: false)',
          default: false,
        },
      },
      required: ['name'],
    },
  },
  {
    name: 'get_customer_profile',
    description:
      "Voir le profil complet d'une cliente : historique achats, produits favoris, " +
      "dernière visite, montant total dépensé. " +
      "Utiliser pour personnaliser le service ou préparer une relance.",
    inputSchema: {
      type: 'object',
      properties: {
        customer_name: { type: 'string', description: 'Nom exact du client dans ERPNext' },
      },
      required: ['customer_name'],
    },
  },
  {
    name: 'get_inactive_customers',
    description:
      "Lister les clients qui n'ont pas acheté depuis X jours. " +
      "Utiliser pour planifier des relances, des campagnes de fidélisation, " +
      "ou quand l'utilisateur demande 'qui n'est pas venue depuis longtemps'.",
    inputSchema: {
      type: 'object',
      properties: {
        days: { type: 'number', description: "Inactivité minimum en jours (défaut: 60)", default: 60 },
      },
    },
  },
  {
    name: 'get_top_customers',
    description:
      "Lister les meilleures clientes par chiffre d'affaires sur une période. " +
      "Utiliser pour identifier les VIP, les fidéliser, ou faire des offres exclusives. " +
      "Exemple : 'qui sont nos meilleures clientes ce mois', 'top 10 clientes'.",
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'number', description: 'Nombre de résultats (défaut: 10)', default: 10 },
        period: {
          type: 'string',
          enum: ['today', 'week', 'month', 'quarter', 'year'],
          description: 'Période (défaut: month)',
          default: 'month',
        },
      },
    },
  },
];

export async function handleCustomerTool(name: string, args: Record<string, unknown>): Promise<ToolResult> {
  const client = getClient();

  try {
    // find_or_create_customer combine get_customer + create_customer
    if (name === 'find_or_create_customer') {
      const { name: customerName, mobile_no, email_id, create_if_not_found } = args as {
        name: string; mobile_no?: string; email_id?: string; create_if_not_found?: boolean;
      };

      const found = await client.call<{ found: boolean; customer_name?: string; message: string }>(
        'get_customer', { customer_name: customerName, mobile_no }
      );

      if (found.found) {
        return { content: [{ type: 'text', text: found.message }] };
      }

      if (create_if_not_found) {
        const created = await client.call('create_customer', {
          customer_name: customerName, mobile_no, email_id,
        });
        const msg = typeof created === 'object' && created !== null && 'message' in created
          ? (created as { message: string }).message : JSON.stringify(created);
        return { content: [{ type: 'text', text: msg }] };
      }

      return {
        content: [{
          type: 'text',
          text: `Client '${customerName}' introuvable. ` +
                `Voulez-vous le créer ? (répondre 'oui' pour créer)`,
        }],
      };
    }

    // get_customer_profile combine get_customer + get_customer_history
    if (name === 'get_customer_profile') {
      const { customer_name } = args as { customer_name: string };
      const [profile, history] = await Promise.all([
        client.call('get_customer', { customer_name }),
        client.call('get_customer_history', { customer_name, limit: 5 }),
      ]);
      if (!profile || !(profile as { found: boolean }).found) {
        const msg = profile && 'message' in (profile as object)
          ? (profile as { message: string }).message
          : `Client '${customer_name}' introuvable.`;
        return { content: [{ type: 'text', text: msg }], isError: true };
      }
      const combined = { ...(profile as object), recent_invoices: (history as { invoices?: unknown[] }).invoices ?? [] };
      return {
        content: [{ type: 'text', text: `${(profile as { message: string }).message}\n\n\`\`\`json\n${JSON.stringify(combined, null, 2)}\n\`\`\`` }],
      };
    }

    const result = await client.call(name, args);
    const text = typeof result === 'object' && result !== null && 'message' in result
      ? (result as { message: string }).message + '\n\n```json\n' + JSON.stringify(result, null, 2) + '\n```'
      : JSON.stringify(result, null, 2);
    return { content: [{ type: 'text', text }] };

  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { content: [{ type: 'text', text: `Erreur CRM — ${msg}` }], isError: true };
  }
}
