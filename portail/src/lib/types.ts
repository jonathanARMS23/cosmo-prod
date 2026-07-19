// Types partagés du portail Cosmo.

/** Produit retourné par cosmo_erp.api.main.search_items. `qty` = stock disponible. */
export interface Item {
  item_code: string;
  item_name: string;
  cosmo_category: string | null;
  cosmo_brand: string | null;
  cosmo_expiry_date: string | null;
  standard_rate: number;
  qty: number;
}

/** Ligne de panier côté portail. */
export interface CartLine {
  item_code: string;
  item_name: string;
  rate: number;
  qty: number;
  /** Stock disponible connu au moment de l'ajout / dernier rafraîchissement. */
  available: number;
}

/** Modes de paiement acceptés par l'API (chaînes françaises exactes, accent inclus). */
export type PaymentMode = "Espèces" | "Carte" | "Mobile Money";

/** Contexte utilisateur retourné par get_current_user_context. */
export interface UserContext {
  user: string;
  full_name: string;
  roles: string[];
  is_manager: boolean;
  is_cashier: boolean;
  message: string;
}

/** Info de stock retournée par get_stock_for_items. */
export interface StockInfo {
  qty: number;
  is_low_stock: boolean;
}

/** Résultat de create_sale. */
export interface SaleResult {
  invoice_name: string;
  customer: string;
  total: number;
  discount: number;
  grand_total: number;
  payment_mode: string;
  status: string;
  items_detail: string[];
  message: string;
}

/** Enveloppe de résultat des Server Actions : succès typé ou erreur lisible. */
export type ActionResult<T> = { ok: true; data: T } | { ok: false; error: string };
