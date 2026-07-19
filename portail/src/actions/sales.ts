"use server";

import { getSession } from "@/lib/session";
import { frappeGet, frappePost, FrappeError } from "@/lib/frappe";
import type {
  ActionResult,
  Item,
  PaymentMode,
  SaleResult,
  StockInfo,
} from "@/lib/types";

/** Récupère le sid de la session ou lève une erreur "session expirée". */
async function requireSession() {
  const session = await getSession();
  if (!session.isLoggedIn || !session.sid) {
    throw new FrappeError("Session expirée. Reconnectez-vous.", 401);
  }
  return session;
}

function toMessage(error: unknown): string {
  if (error instanceof FrappeError) return error.message;
  if (error instanceof Error) return error.message;
  return "Une erreur inattendue est survenue.";
}

/**
 * Recherche produit (débounce/min 2 caractères gérés côté client).
 * search_items inclut déjà `qty` (stock) — pas d'appel séparé pour l'affichage.
 */
export async function searchItemsAction(
  query: string,
): Promise<ActionResult<Item[]>> {
  try {
    const session = await requireSession();
    const data = await frappeGet<{ count: number; items: Item[] }>(
      "cosmo_erp.api.main.search_items",
      session.sid!,
      { query },
    );
    return { ok: true, data: data.items };
  } catch (error) {
    return { ok: false, error: toMessage(error) };
  }
}

/**
 * Rafraîchit le stock de TOUT le panier en un seul appel, juste avant paiement.
 */
export async function refreshStockAction(
  itemCodes: string[],
): Promise<ActionResult<Record<string, StockInfo>>> {
  try {
    const session = await requireSession();
    const data = await frappeGet<{ items: Record<string, StockInfo> }>(
      "cosmo_erp.api.main.get_stock_for_items",
      session.sid!,
      { item_codes: JSON.stringify(itemCodes) },
    );
    return { ok: true, data: data.items };
  } catch (error) {
    return { ok: false, error: toMessage(error) };
  }
}

export interface CreateSaleInput {
  items: { item_code_or_name: string; qty: number }[];
  paymentMode: PaymentMode;
  idempotencyKey: string;
  discount?: number;
}

/**
 * Crée la vente (Sales Invoice) via create_sale.
 * - `payment_mode` : chaîne française exacte ("Espèces" | "Carte" | "Mobile Money").
 * - `idempotency_key` : identique à chaque retry pour éviter les doublons.
 * - Le jeton CSRF est lu en session ; s'il manque (ancienne session), il est
 *   re-récupéré à la demande.
 */
export async function createSaleAction(
  input: CreateSaleInput,
): Promise<ActionResult<SaleResult>> {
  try {
    const session = await requireSession();

    let csrfToken = session.csrfToken;
    if (!csrfToken) {
      const csrf = await frappeGet<{ csrf_token: string }>(
        "cosmo_erp.api.main.get_csrf_token",
        session.sid!,
      );
      csrfToken = csrf.csrf_token;
      session.csrfToken = csrfToken;
      await session.save();
    }

    const result = await frappePost<SaleResult>(
      "cosmo_erp.api.main.create_sale",
      session.sid!,
      csrfToken,
      {
        items: input.items,
        payment_mode: input.paymentMode,
        discount: input.discount ?? 0,
        idempotency_key: input.idempotencyKey,
      },
    );
    return { ok: true, data: result };
  } catch (error) {
    return { ok: false, error: toMessage(error) };
  }
}
