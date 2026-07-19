import { StockClient } from "@/components/stock/StockClient";

export default function StockPage() {
  return (
    <div className="p-4">
      <h1 className="mb-4 text-xl font-bold text-slate-900">Stock</h1>
      <StockClient />
    </div>
  );
}
