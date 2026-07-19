"use client";

import { useEffect, useState } from "react";
import { searchItemsAction } from "@/actions/sales";
import { formatAriary } from "@/lib/format";
import type { Item } from "@/lib/types";
import { StockBadge } from "@/components/caisse/StockBadge";

/**
 * Consultation du stock (lecture seule) pour ce lot. Basée sur search_items
 * (la seule fonction de listing disponible dans le périmètre de ce lot).
 */
export function StockClient() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Item[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) {
      setResults([]);
      setError(null);
      setSearching(false);
      return;
    }
    let cancelled = false;
    setSearching(true);
    const timer = setTimeout(async () => {
      const res = await searchItemsAction(q);
      if (cancelled) return;
      setSearching(false);
      if (res.ok) {
        setResults(res.data);
        setError(null);
      } else {
        setResults([]);
        setError(res.error);
      }
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query]);

  return (
    <div className="max-w-2xl">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Rechercher un produit (2 caractères min.)…"
        autoComplete="off"
        className="min-h-touch w-full rounded-xl border border-slate-300 px-4 outline-none focus:border-brand focus:ring-2 focus:ring-brand/30"
      />

      <div className="mt-4">
        {searching ? (
          <p className="text-sm text-slate-500">Recherche…</p>
        ) : error ? (
          <p className="text-sm font-medium text-red-600">{error}</p>
        ) : query.trim().length < 2 ? (
          <p className="text-sm text-slate-400">
            Saisissez au moins 2 caractères pour consulter le stock.
          </p>
        ) : results.length === 0 ? (
          <p className="text-sm text-slate-500">Aucun produit trouvé.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {results.map((item) => (
              <li
                key={item.item_code}
                className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium text-slate-900">
                    {item.item_name}
                  </p>
                  {item.cosmo_brand ? (
                    <p className="text-xs text-slate-500">{item.cosmo_brand}</p>
                  ) : null}
                  <p className="mt-1">
                    <StockBadge qty={item.qty} />
                  </p>
                </div>
                <span className="shrink-0 font-semibold text-slate-900">
                  {formatAriary(item.standard_rate)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
