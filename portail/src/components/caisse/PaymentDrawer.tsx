"use client";

import { useState } from "react";
import { formatAriary } from "@/lib/format";
import type { PaymentMode } from "@/lib/types";

const QUICK_BILLS = [500, 1000, 2000, 5000, 10000, 20000];

interface PaymentDrawerProps {
  total: number;
  submitting: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (mode: PaymentMode, amountReceived: number | null) => void;
}

export function PaymentDrawer({
  total,
  submitting,
  error,
  onClose,
  onSubmit,
}: PaymentDrawerProps) {
  const [mode, setMode] = useState<PaymentMode | null>(null);
  const [received, setReceived] = useState<number>(0);

  const change = received - total;
  const canValidateCash = received >= total;

  const modeButton = (value: PaymentMode, icon: string) => (
    <button
      type="button"
      onClick={() => {
        setMode(value);
        if (value === "Espèces") setReceived(0);
      }}
      className={`min-h-[64px] flex-1 rounded-2xl border-2 text-base font-semibold transition ${
        mode === value
          ? "border-brand bg-brand text-white"
          : "border-slate-200 bg-white text-slate-800"
      }`}
    >
      <span className="mr-2 text-xl" aria-hidden>
        {icon}
      </span>
      {value}
    </button>
  );

  return (
    <div className="fixed inset-0 z-30 flex items-end justify-center bg-black/40 sm:items-center">
      <div className="w-full max-w-md rounded-t-3xl bg-white p-5 shadow-2xl sm:rounded-3xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900">Encaissement</h2>
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="min-h-touch min-w-touch rounded-full text-slate-500"
            aria-label="Fermer"
          >
            ✕
          </button>
        </div>

        <div className="mb-4 rounded-2xl bg-brand-light p-4 text-center">
          <p className="text-sm text-slate-600">Total à payer</p>
          <p className="text-3xl font-extrabold text-brand-dark">
            {formatAriary(total)}
          </p>
        </div>

        <div className="mb-4 flex gap-2">
          {modeButton("Espèces", "💵")}
          {modeButton("Carte", "💳")}
          {modeButton("Mobile Money", "📱")}
        </div>

        {mode === "Espèces" ? (
          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Montant reçu
            </label>
            <input
              type="number"
              inputMode="numeric"
              min={0}
              value={received === 0 ? "" : received}
              onChange={(e) => setReceived(Number(e.target.value) || 0)}
              placeholder="0"
              className="min-h-touch w-full rounded-xl border border-slate-300 px-4 text-lg font-semibold outline-none focus:border-brand focus:ring-2 focus:ring-brand/30"
            />
            <div className="mt-3 grid grid-cols-3 gap-2">
              {QUICK_BILLS.map((bill) => (
                <button
                  key={bill}
                  type="button"
                  onClick={() => setReceived((prev) => prev + bill)}
                  className="min-h-touch rounded-xl bg-slate-100 text-sm font-semibold text-slate-800 active:scale-95"
                >
                  +{formatAriary(bill)}
                </button>
              ))}
              <button
                type="button"
                onClick={() => setReceived(total)}
                className="min-h-touch rounded-xl bg-slate-200 text-sm font-semibold text-slate-800 active:scale-95"
              >
                Compte juste
              </button>
              <button
                type="button"
                onClick={() => setReceived(0)}
                className="min-h-touch rounded-xl bg-slate-100 text-sm font-medium text-slate-500 active:scale-95"
              >
                Effacer
              </button>
            </div>

            {received > 0 ? (
              <div className="mt-4 rounded-2xl bg-slate-50 p-4 text-center">
                <p className="text-sm text-slate-600">Monnaie à rendre</p>
                <p
                  className={`text-2xl font-extrabold ${
                    change < 0 ? "text-red-600" : "text-emerald-600"
                  }`}
                >
                  {formatAriary(Math.max(change, 0))}
                </p>
                {change < 0 ? (
                  <p className="mt-1 text-xs font-medium text-red-600">
                    Il manque {formatAriary(-change)}
                  </p>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : null}

        {error ? (
          <p
            role="alert"
            className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm font-medium text-red-700"
          >
            {error}
          </p>
        ) : null}

        <button
          type="button"
          disabled={
            submitting ||
            mode === null ||
            (mode === "Espèces" && !canValidateCash)
          }
          onClick={() =>
            mode &&
            onSubmit(mode, mode === "Espèces" ? received : null)
          }
          className="min-h-[56px] w-full rounded-2xl bg-brand text-lg font-bold text-white transition active:scale-[0.99] disabled:opacity-50"
        >
          {submitting ? "Validation…" : "Valider la vente"}
        </button>
      </div>
    </div>
  );
}
