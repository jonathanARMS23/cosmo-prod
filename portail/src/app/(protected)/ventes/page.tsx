import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";

export default async function VentesPage() {
  const session = await getSession();
  // Réservé aux managers.
  if (!session.isManager) {
    redirect("/caisse");
  }

  return (
    <div className="p-4">
      <h1 className="mb-4 text-xl font-bold text-slate-900">Ventes</h1>
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
        <p className="text-4xl" aria-hidden>
          📊
        </p>
        <p className="mt-3 font-medium text-slate-700">Bientôt disponible</p>
        <p className="mt-1 text-sm text-slate-500">
          Le récapitulatif des ventes arrivera dans un prochain lot.
        </p>
      </div>
    </div>
  );
}
