// Types partagés entre tous les modules cosmo-mcp

export interface ErpNextResponse<T = unknown> {
  message: T;
}

export interface ItemStock {
  item_code: string;
  item_name: string;
  cosmo_category?: string;
  cosmo_brand?: string;
  qty: number;
  uom: string;
  cosmo_reorder_level: number;
  cosmo_expiry_date?: string;
  is_low_stock: boolean;
  message: string;
}

export interface SaleItem {
  item_code_or_name: string;
  qty: number;
  rate?: number;
}

export interface SaleResult {
  invoice_name: string;
  customer: string;
  total: number;
  grand_total: number;
  payment_mode: string;
  status: string;
  items_detail: string[];
  message: string;
}

export interface DashboardSummary {
  today_revenue: number;
  today_transactions: number;
  low_stock_count: number;
  expiring_soon_count: number;
  top_product_today?: string;
  alerts: string[];
  message: string;
}

export interface ToolResult {
  content: Array<{ type: 'text'; text: string }>;
  isError?: boolean;
  [key: string]: unknown; // Required: SDK v1.10+ ServerResultSchema expects Record<string, unknown>
}

export type PaymentMode = 'Cash' | 'Card' | 'Mobile Money' | 'Espèces' | 'Carte';
