/**
 * Tools MCP — Vision et OCR.
 * NOTE ARCHITECTURE : Hermes fait l'analyse visuelle en amont avec son tool natif vision_analyze.
 * Ces tools reçoivent les données extraites par Hermes et les mappent vers ERPNext.
 */
import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { getClient } from '../client.js';
import { ToolResult } from '../types.js';

export const visionTools: Tool[] = [
  {
    name: 'identify_product_from_image',
    description:
      "Identifier un produit cosmétique dans ERPNext à partir des données extraites d'une image. " +
      "WORKFLOW : 1) Hermes analyse d'abord l'image avec vision_analyze pour extraire marque/nom/type, " +
      "2) Hermes appelle CE tool avec les données extraites, " +
      "3) Ce tool cherche dans ERPNext et retourne le résultat. " +
      "Utiliser quand l'utilisateur envoie une photo de produit et demande " +
      "'c'est quoi ce produit', 'combien coûte ça', 'on l'a en stock ?'.",
    inputSchema: {
      type: 'object',
      properties: {
        image_description: { type: 'string', description: "Description que Hermes a extraite de l'image" },
        brand: { type: 'string', description: 'Marque identifiée (optionnel)' },
        product_name: { type: 'string', description: 'Nom du produit lu sur le packaging (optionnel)' },
        barcode: { type: 'string', description: 'Code-barres si visible (optionnel)' },
      },
      required: ['image_description'],
    },
  },
  {
    name: 'process_supplier_invoice_image',
    description:
      "Enregistrer une facture fournisseur dont les données ont été extraites d'une image par Hermes. " +
      "WORKFLOW : 1) Hermes analyse la photo avec vision_analyze, " +
      "2) Hermes appelle CE tool avec les données structurées extraites, " +
      "3) Ce tool crée un Cosmo OCR Invoice dans ERPNext et propose une Purchase Invoice. " +
      "Utiliser quand l'utilisateur envoie une photo de facture fournisseur.",
    inputSchema: {
      type: 'object',
      properties: {
        supplier_name: { type: 'string', description: 'Nom du fournisseur extrait de la facture' },
        invoice_number: { type: 'string', description: 'Numéro de référence facture fournisseur' },
        invoice_date: { type: 'string', description: 'Date de la facture ISO YYYY-MM-DD' },
        items: {
          type: 'array',
          description: 'Lignes de produits extraites',
          items: {
            type: 'object',
            properties: {
              description: { type: 'string' },
              qty: { type: 'number' },
              unit_price: { type: 'number' },
            },
            required: ['description', 'qty', 'unit_price'],
          },
        },
        total_amount: { type: 'number', description: 'Montant total de la facture' },
        raw_text: { type: 'string', description: 'Texte brut extrait par Hermes (pour audit)' },
      },
      required: ['supplier_name', 'items', 'total_amount'],
    },
  },
  {
    name: 'create_item_from_image',
    description:
      "Créer une fiche produit à partir des données extraites d'une photo de produit non référencé. " +
      "Utiliser après identify_product_from_image quand le produit n'est pas trouvé dans ERPNext " +
      "et que l'utilisateur confirme vouloir l'ajouter au catalogue.",
    inputSchema: {
      type: 'object',
      properties: {
        item_name: { type: 'string', description: 'Nom du produit' },
        cosmo_brand: { type: 'string', description: 'Marque' },
        cosmo_category: {
          type: 'string',
          enum: ['Soin Visage', 'Soin Corps', 'Maquillage', 'Parfum', 'Hygiène', 'Autre'],
        },
        standard_rate: { type: 'number', description: 'Prix de vente en Ariary' },
        cosmo_ingredients: { type: 'string', description: 'Ingrédients INCI visibles (optionnel)' },
      },
      required: ['item_name', 'cosmo_category', 'standard_rate'],
    },
  },
];

export async function handleVisionTool(name: string, args: Record<string, unknown>): Promise<ToolResult> {
  const client = getClient();

  try {
    if (name === 'identify_product_from_image') {
      const { brand, product_name, image_description } = args as {
        brand?: string; product_name?: string; barcode?: string; image_description: string;
      };

      // Stratégie : chercher par barcode d'abord, puis par nom/marque
      const query = product_name || brand || image_description.split(' ').slice(0, 3).join(' ');
      const result = await client.call<{ count: number; items: Array<{ item_code: string; item_name: string; qty: number; standard_rate: number }> }>(
        'search_items', { query, category: undefined }
      );

      if (result.count === 0) {
        return {
          content: [{
            type: 'text',
            text: `Produit non trouvé dans le catalogue pour : "${query}". ` +
                  `Voulez-vous l'ajouter ? (utiliser create_item_from_image)`,
          }],
        };
      }

      const items = result.items.slice(0, 3);
      const text = `${result.count} produit(s) correspondent :\n` +
        items.map((i, idx) => `${idx + 1}. ${i.item_name} — ${i.standard_rate} Ar — Stock: ${i.qty}`).join('\n');

      return { content: [{ type: 'text', text: text + '\n\n```json\n' + JSON.stringify({ found: true, items }, null, 2) + '\n```' }] };
    }

    if (name === 'process_supplier_invoice_image') {
      // Crée un Cosmo OCR Invoice via l'API cosmo_erp
      // Pour l'instant, utilise create_supplier_order comme proxy
      const { supplier_name, items, total_amount, invoice_number, invoice_date } = args as {
        supplier_name: string;
        items: Array<{ description: string; qty: number; unit_price: number }>;
        total_amount: number;
        invoice_number?: string;
        invoice_date?: string;
      };

      const mappedItems = items.map((i) => ({
        item_code_or_name: i.description,
        qty: i.qty,
        rate: i.unit_price,
      }));

      const notes = `Facture OCR${invoice_number ? ` N°${invoice_number}` : ''}${invoice_date ? ` du ${invoice_date}` : ''} — Total : ${total_amount} Ar`;

      const result = await client.call('create_supplier_order', {
        supplier_name,
        items: mappedItems,
        notes,
      });

      const msg = typeof result === 'object' && result !== null && 'message' in result
        ? (result as { message: string }).message : JSON.stringify(result);

      return {
        content: [{
          type: 'text',
          text: `Facture traitée. ${msg}\n\n` +
                `Validation requise : vérifiez les produits mappés et confirmez la création de la Purchase Invoice.`,
        }],
      };
    }

    if (name === 'create_item_from_image') {
      const result = await client.call('create_item', args);
      const text = typeof result === 'object' && result !== null && 'message' in result
        ? (result as { message: string }).message : JSON.stringify(result);
      return { content: [{ type: 'text', text }] };
    }

    return { content: [{ type: 'text', text: `Tool vision inconnu : ${name}` }], isError: true };

  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { content: [{ type: 'text', text: `Erreur vision — ${msg}` }], isError: true };
  }
}
