/**
 * Cosmo MCP Server — Point d'entrée.
 * Expose les tools ERPNext cosmo_erp à Hermes Agent via le protocole MCP.
 * Transport : stdio (dev local) ou HTTP avec sessions par connexion (Docker prod).
 */
import http from 'http';
import crypto from 'node:crypto';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import dotenv from 'dotenv';

import { stockTools, handleStockTool } from './tools/stock.js';
import { salesTools, handleSalesTool } from './tools/sales.js';
import { customerTools, handleCustomerTool } from './tools/customers.js';
import { supplierTools, handleSupplierTool } from './tools/suppliers.js';
import { visionTools, handleVisionTool } from './tools/vision.js';
import { reportTools, handleReportTool } from './tools/reports.js';

dotenv.config();

// ── Registre des tools ────────────────────────────────────────────────────────
const ALL_TOOLS = [
  ...stockTools,
  ...salesTools,
  ...customerTools,
  ...supplierTools,
  ...visionTools,
  ...reportTools,
];

const STOCK_TOOL_NAMES    = new Set(stockTools.map((t) => t.name));
const SALES_TOOL_NAMES    = new Set(salesTools.map((t) => t.name));
const CUSTOMER_TOOL_NAMES = new Set(customerTools.map((t) => t.name));
const SUPPLIER_TOOL_NAMES = new Set(supplierTools.map((t) => t.name));
const VISION_TOOL_NAMES   = new Set(visionTools.map((t) => t.name));
const REPORT_TOOL_NAMES   = new Set(reportTools.map((t) => t.name));

// ── Factory : crée un Server MCP avec tous les handlers enregistrés ───────────
function createMCPServer(): Server {
  const srv = new Server(
    { name: 'cosmo-mcp', version: '1.0.0' },
    { capabilities: { tools: {} } },
  );

  srv.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: ALL_TOOLS }));

  srv.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args = {} } = request.params;
    try {
      if (STOCK_TOOL_NAMES.has(name))    return await handleStockTool(name,    args as Record<string, unknown>);
      if (SALES_TOOL_NAMES.has(name))    return await handleSalesTool(name,    args as Record<string, unknown>);
      if (CUSTOMER_TOOL_NAMES.has(name)) return await handleCustomerTool(name, args as Record<string, unknown>);
      if (SUPPLIER_TOOL_NAMES.has(name)) return await handleSupplierTool(name, args as Record<string, unknown>);
      if (VISION_TOOL_NAMES.has(name))   return await handleVisionTool(name,   args as Record<string, unknown>);
      if (REPORT_TOOL_NAMES.has(name))   return await handleReportTool(name,   args as Record<string, unknown>);

      return { content: [{ type: 'text' as const, text: `Tool inconnu : ${name}` }], isError: true };
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      return { content: [{ type: 'text' as const, text: `Erreur dans ${name} : ${msg}` }], isError: true };
    }
  });

  return srv;
}

// ── Helper : lire le corps d'une requête POST ─────────────────────────────────
function readBody(req: http.IncomingMessage): Promise<unknown> {
  return new Promise((resolve) => {
    let data = '';
    req.on('data', (chunk: Buffer) => { data += chunk.toString(); });
    req.on('end', () => { try { resolve(JSON.parse(data)); } catch { resolve(undefined); } });
  });
}

// ── Transport ─────────────────────────────────────────────────────────────────
async function main() {
  const transportType = process.env.MCP_TRANSPORT || 'stdio';

  if (transportType === 'http') {
    const port = parseInt(process.env.MCP_HTTP_PORT || '3100', 10);

    // Sessions actives : sessionId → transport (une par connexion cliente)
    const sessions = new Map<string, StreamableHTTPServerTransport>();

    const httpServer = http.createServer(async (req, res) => {
      // Health check
      if (req.url === '/health' && req.method === 'GET') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'ok', tools: ALL_TOOLS.length }));
        return;
      }

      try {
        const sessionId = req.headers['mcp-session-id'] as string | undefined;

        if (sessionId && sessions.has(sessionId)) {
          // Requête sur session existante (GET SSE ou POST tool call)
          const transport = sessions.get(sessionId)!;
          const body = req.method === 'POST' ? await readBody(req) : undefined;
          await transport.handleRequest(req, res, body);

        } else if (!sessionId && req.method === 'POST') {
          // Nouvelle connexion : initialize
          const newSessionId = crypto.randomUUID();
          const transport = new StreamableHTTPServerTransport({
            sessionIdGenerator: () => newSessionId,
          });

          sessions.set(newSessionId, transport);
          transport.onclose = () => {
            sessions.delete(newSessionId);
            console.error(`[cosmo-mcp] Session fermée : ${newSessionId}`);
          };

          const srv = createMCPServer();
          await srv.connect(transport);

          const body = await readBody(req);
          await transport.handleRequest(req, res, body);

        } else {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Mcp-Session-Id manquant ou invalide' }));
        }

      } catch (err) {
        console.error('[cosmo-mcp] Erreur requête :', err);
        if (!res.headersSent) {
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: String(err) }));
        }
      }
    });

    httpServer.listen(port, () => {
      console.error(`[cosmo-mcp] Mode HTTP — port ${port} — ${ALL_TOOLS.length} tools`);
      console.error(`[cosmo-mcp] ERPNext : ${process.env.ERPNEXT_URL || 'URL non configurée'}`);
    });

  } else {
    const transport = new StdioServerTransport();
    const srv = createMCPServer();
    await srv.connect(transport);
    process.stdin.resume();
    process.stdin.on('end', () => process.exit(0));
    console.error(`[cosmo-mcp] Mode stdio — ${ALL_TOOLS.length} tools`);
    console.error(`[cosmo-mcp] ERPNext : ${process.env.ERPNEXT_URL || 'URL non configurée'}`);
  }
}

main().catch((err) => {
  console.error('[cosmo-mcp] Erreur fatale :', err);
  process.exit(1);
});
