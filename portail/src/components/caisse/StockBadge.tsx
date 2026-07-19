/**
 * Badge d'état de stock — accessible (icône + texte + couleur, jamais la
 * couleur seule).
 *
 * Note : search_items ne renvoie que la quantité, pas is_low_stock. On applique
 * un seuil d'affichage local (LOW_STOCK_THRESHOLD). La vérification de stock
 * qui fait autorité a lieu au moment de l'encaissement via get_stock_for_items.
 */
const LOW_STOCK_THRESHOLD = 5;

export function StockBadge({ qty }: { qty: number }) {
  if (qty <= 0) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700">
        <span aria-hidden>✕</span> Rupture
      </span>
    );
  }
  if (qty <= LOW_STOCK_THRESHOLD) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">
        <span aria-hidden>⚠</span> Stock {qty} bas
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">
      <span aria-hidden>✓</span> Stock {qty}
    </span>
  );
}
