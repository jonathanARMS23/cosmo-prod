"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  searchItemsAction,
  refreshStockAction,
  createSaleAction,
} from "@/actions/sales";
import { formatAriary } from "@/lib/format";
import type { CartLine, Item, PaymentMode, SaleResult } from "@/lib/types";
import { StockBadge } from "./StockBadge";
import { PaymentDrawer } from "./PaymentDrawer";

type View = "cart" | "payment" | "confirmation";

interface PendingUndo {
  line: CartLine;
}

const UNDO_DELAY_MS = 5000;

export function CaisseClient() {
  const searchInputRef = useRef<HTMLInputElement>(null);
  const undoTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Item[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [cart, setCart] = useState<CartLine[]>([]);
  const [pendingUndo, setPendingUndo] = useState<PendingUndo | null>(null);

  const [view, setView] = useState<View>("cart");
  const [checkingStock, setCheckingStock] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);

  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [saleError, setSaleError] = useState<string | null>(null);
  const [saleResult, setSaleResult] = useState<SaleResult | null>(null);
  const [lastChange, setLastChange] = useState<number | null>(null);

  const focusSearch = useCallback(() => {
    searchInputRef.current?.focus();
  }, []);

  // Focus auto à l'arrivée sur l'écran caisse.
  useEffect(() => {
    if (view === "cart") focusSearch();
  }, [view, focusSearch]);

  // Recherche avec debounce ~250ms, à partir de 2 caractères.
  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) {
      setResults([]);
      setSearchError(null);
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
        setSearchError(null);
      } else {
        setResults([]);
        setSearchError(res.error);
      }
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query]);

  const totalItems = cart.reduce((sum, line) => sum + line.qty, 0);
  const subtotal = cart.reduce((sum, line) => sum + line.qty * line.rate, 0);

  const addToCart = (item: Item) => {
    if (item.qty <= 0) return;
    setCart((prev) => {
      const existing = prev.find((l) => l.item_code === item.item_code);
      if (existing) {
        return prev.map((l) =>
          l.item_code === item.item_code
            ? {
                ...l,
                qty: Math.min(l.qty + 1, item.qty),
                available: item.qty,
                rate: item.standard_rate,
              }
            : l,
        );
      }
      return [
        ...prev,
        {
          item_code: item.item_code,
          item_name: item.item_name,
          rate: item.standard_rate,
          qty: 1,
          available: item.qty,
        },
      ];
    });
    setGlobalError(null);
    setQuery("");
    setResults([]);
    focusSearch();
  };

  const changeQty = (itemCode: string, delta: number) => {
    setCart((prev) => {
      const line = prev.find((l) => l.item_code === itemCode);
      if (!line) return prev;
      const next = line.qty + delta;
      if (next <= 0) {
        // Passe sous 1 : on retire la ligne (avec possibilité d'annuler).
        queueRemove(line);
        return prev.filter((l) => l.item_code !== itemCode);
      }
      return prev.map((l) =>
        l.item_code === itemCode
          ? { ...l, qty: Math.min(next, l.available) }
          : l,
      );
    });
  };

  const queueRemove = (line: CartLine) => {
    if (undoTimerRef.current) clearTimeout(undoTimerRef.current);
    setPendingUndo({ line });
    undoTimerRef.current = setTimeout(() => {
      setPendingUndo(null);
      undoTimerRef.current = null;
    }, UNDO_DELAY_MS);
  };

  const removeLine = (itemCode: string) => {
    const line = cart.find((l) => l.item_code === itemCode);
    if (!line) return;
    setCart((prev) => prev.filter((l) => l.item_code !== itemCode));
    queueRemove(line);
  };

  const undoRemove = () => {
    if (!pendingUndo) return;
    if (undoTimerRef.current) clearTimeout(undoTimerRef.current);
    const restored = pendingUndo.line;
    setCart((prev) =>
      prev.some((l) => l.item_code === restored.item_code)
        ? prev
        : [...prev, restored],
    );
    setPendingUndo(null);
    undoTimerRef.current = null;
  };

  const openPayment = async () => {
    if (cart.length === 0) return;
    setGlobalError(null);
    setCheckingStock(true);
    const res = await refreshStockAction(cart.map((l) => l.item_code));
    setCheckingStock(false);
    if (!res.ok) {
      setGlobalError(res.error);
      return;
    }
    let insufficient = false;
    setCart((prev) =>
      prev.map((l) => {
        const info = res.data[l.item_code];
        const available = info ? info.qty : l.available;
        if (l.qty > available) insufficient = true;
        return { ...l, available };
      }),
    );
    if (insufficient) {
      setGlobalError(
        "Le stock a changé depuis l'ajout. Vérifiez les quantités signalées.",
      );
      return;
    }
    setIdempotencyKey(crypto.randomUUID());
    setSaleError(null);
    setView("payment");
  };

  const submitSale = async (mode: PaymentMode, amountReceived: number | null) => {
    setSubmitting(true);
    setSaleError(null);
    const res = await createSaleAction({
      items: cart.map((l) => ({ item_code_or_name: l.item_code, qty: l.qty })),
      paymentMode: mode,
      idempotencyKey,
      discount: 0,
    });
    setSubmitting(false);
    if (!res.ok) {
      // On NE PERD PAS le panier ; retry possible avec la même idempotencyKey.
      setSaleError(res.error);
      return;
    }
    setSaleResult(res.data);
    setLastChange(
      amountReceived !== null ? amountReceived - res.data.grand_total : null,
    );
    setView("confirmation");
  };

  const newSale = () => {
    setCart([]);
    setQuery("");
    setResults([]);
    setSaleResult(null);
    setSaleError(null);
    setLastChange(null);
    setIdempotencyKey("");
    setGlobalError(null);
    setView("cart");
    focusSearch();
  };

  // ── Écran de confirmation ────────────────────────────────────────────────
  if (view === "confirmation" && saleResult) {
    return (
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="w-full max-w-md rounded-3xl bg-white p-6 text-center shadow-lg">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-3xl">
            ✓
          </div>
          <h2 className="text-xl font-bold text-slate-900">Vente enregistrée</h2>
          <p className="mt-1 text-sm text-slate-500">
            Facture {saleResult.invoice_name}
          </p>

          <div className="my-5 rounded-2xl bg-brand-light p-4">
            <p className="text-sm text-slate-600">Total encaissé</p>
            <p className="text-3xl font-extrabold text-brand-dark">
              {formatAriary(saleResult.grand_total)}
            </p>
          </div>

          {lastChange !== null ? (
            <div className="mb-5 rounded-2xl bg-slate-50 p-4">
              <p className="text-sm text-slate-600">Monnaie à rendre</p>
              <p className="text-2xl font-extrabold text-emerald-600">
                {formatAriary(Math.max(lastChange, 0))}
              </p>
            </div>
          ) : null}

          <button
            type="button"
            onClick={newSale}
            className="min-h-[56px] w-full rounded-2xl bg-brand text-lg font-bold text-white active:scale-[0.99]"
          >
            Nouvelle vente
          </button>
        </div>
      </div>
    );
  }

  // ── Écran caisse (recherche + panier) ──────────────────────────────────────
  return (
    <div className="flex min-h-full flex-col">
      {/* Recherche */}
      <div className="sticky top-0 z-10 border-b border-slate-200 bg-white p-3">
        <input
          ref={searchInputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Rechercher un produit (2 caractères min.)…"
          autoComplete="off"
          className="min-h-touch w-full rounded-xl border border-slate-300 px-4 outline-none focus:border-brand focus:ring-2 focus:ring-brand/30"
        />

        {(searching || searchError || results.length > 0) && query.trim().length >= 2 ? (
          <div className="mt-2 max-h-72 overflow-y-auto rounded-xl border border-slate-200">
            {searching ? (
              <p className="p-3 text-sm text-slate-500">Recherche…</p>
            ) : searchError ? (
              <p className="p-3 text-sm font-medium text-red-600">{searchError}</p>
            ) : results.length === 0 ? (
              <p className="p-3 text-sm text-slate-500">Aucun produit trouvé.</p>
            ) : (
              <ul className="divide-y divide-slate-100">
                {results.map((item) => {
                  const outOfStock = item.qty <= 0;
                  return (
                    <li key={item.item_code}>
                      <button
                        type="button"
                        disabled={outOfStock}
                        onClick={() => addToCart(item)}
                        className={`flex w-full items-center justify-between gap-3 p-3 text-left transition ${
                          outOfStock
                            ? "cursor-not-allowed bg-slate-50 opacity-60"
                            : "hover:bg-brand-light active:bg-brand-light"
                        }`}
                      >
                        <span className="min-w-0">
                          <span className="block truncate font-medium text-slate-900">
                            {item.item_name}
                          </span>
                          <span className="mt-0.5 block">
                            <StockBadge qty={item.qty} />
                          </span>
                        </span>
                        <span className="shrink-0 font-semibold text-slate-900">
                          {formatAriary(item.standard_rate)}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        ) : null}
      </div>

      {/* Panier */}
      <div className="flex-1 p-3">
        {globalError ? (
          <p
            role="alert"
            className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm font-medium text-red-700"
          >
            {globalError}
          </p>
        ) : null}

        {cart.length === 0 ? (
          <div className="mt-16 text-center text-slate-400">
            <p className="text-4xl" aria-hidden>
              🛒
            </p>
            <p className="mt-2 text-sm">
              Panier vide — recherchez un produit pour commencer.
            </p>
          </div>
        ) : (
          <ul className="flex flex-col gap-2">
            {cart.map((line) => {
              const overStock = line.qty > line.available;
              return (
                <li
                  key={line.item_code}
                  className={`rounded-xl border bg-white p-3 ${
                    overStock ? "border-red-300 bg-red-50" : "border-slate-200"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="truncate font-medium text-slate-900">
                        {line.item_name}
                      </p>
                      <p className="text-sm text-slate-500">
                        {formatAriary(line.rate)} / unité
                      </p>
                      {overStock ? (
                        <p className="text-xs font-semibold text-red-600">
                          Stock insuffisant : {line.available} disponible(s)
                        </p>
                      ) : null}
                    </div>
                    <button
                      type="button"
                      onClick={() => removeLine(line.item_code)}
                      className="min-h-touch min-w-touch rounded-lg text-slate-400 hover:text-red-600"
                      aria-label={`Retirer ${line.item_name}`}
                    >
                      🗑
                    </button>
                  </div>
                  <div className="mt-2 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <button
                        type="button"
                        onClick={() => changeQty(line.item_code, -1)}
                        className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-2xl font-bold text-slate-700 active:scale-95"
                        aria-label="Diminuer la quantité"
                      >
                        −
                      </button>
                      <span className="w-8 text-center text-lg font-bold">
                        {line.qty}
                      </span>
                      <button
                        type="button"
                        onClick={() => changeQty(line.item_code, 1)}
                        disabled={line.qty >= line.available}
                        className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-2xl font-bold text-slate-700 active:scale-95 disabled:opacity-40"
                        aria-label="Augmenter la quantité"
                      >
                        +
                      </button>
                    </div>
                    <span className="font-semibold text-slate-900">
                      {formatAriary(line.qty * line.rate)}
                    </span>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {/* Barre total + Encaisser (sticky) */}
      <div className="sticky bottom-16 z-10 border-t border-slate-200 bg-white p-3 md:bottom-0">
        <div className="mb-2 flex items-center justify-between text-sm text-slate-600">
          <span>{totalItems} article(s)</span>
          <span>Sous-total {formatAriary(subtotal)}</span>
        </div>
        <div className="mb-3 flex items-center justify-between">
          <span className="text-base font-medium text-slate-700">
            Total à payer
          </span>
          <span className="text-2xl font-extrabold text-brand-dark">
            {formatAriary(subtotal)}
          </span>
        </div>
        <button
          type="button"
          onClick={openPayment}
          disabled={cart.length === 0 || checkingStock}
          className="min-h-[56px] w-full rounded-2xl bg-brand text-lg font-bold text-white transition active:scale-[0.99] disabled:opacity-50"
        >
          {checkingStock ? "Vérification du stock…" : "Encaisser"}
        </button>
      </div>

      {/* Toast d'annulation de suppression */}
      {pendingUndo ? (
        <div className="fixed inset-x-0 bottom-24 z-40 flex justify-center px-4 md:bottom-6">
          <div className="flex w-full max-w-md items-center justify-between gap-3 rounded-xl bg-slate-900 px-4 py-3 text-white shadow-lg">
            <span className="truncate text-sm">
              « {pendingUndo.line.item_name} » retiré
            </span>
            <button
              type="button"
              onClick={undoRemove}
              className="shrink-0 rounded-lg px-3 py-1 text-sm font-bold text-brand-light underline"
            >
              Annuler
            </button>
          </div>
        </div>
      ) : null}

      {/* Écran de paiement */}
      {view === "payment" ? (
        <PaymentDrawer
          total={subtotal}
          submitting={submitting}
          error={saleError}
          onClose={() => {
            if (!submitting) setView("cart");
          }}
          onSubmit={submitSale}
        />
      ) : null}
    </div>
  );
}
