"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { logoutAction } from "@/actions/auth";

interface NavProps {
  fullName: string;
  roleLabel: string;
  isManager: boolean;
}

interface NavItem {
  href: string;
  label: string;
  icon: string;
}

export function Nav({ fullName, roleLabel, isManager }: NavProps) {
  const pathname = usePathname();

  const items: NavItem[] = [
    { href: "/caisse", label: "Caisse", icon: "🛒" },
    { href: "/stock", label: "Stock", icon: "📦" },
    ...(isManager
      ? [{ href: "/ventes", label: "Ventes", icon: "📊" } as NavItem]
      : []),
  ];

  const isActive = (href: string) =>
    pathname === href || pathname.startsWith(`${href}/`);

  return (
    <>
      {/* En-tête mobile */}
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 md:hidden">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-slate-900">
            {fullName}
          </p>
          <p className="text-xs text-slate-500">{roleLabel}</p>
        </div>
        <form action={logoutAction}>
          <button
            type="submit"
            className="min-h-touch rounded-lg px-3 text-sm font-medium text-red-600"
          >
            Déconnexion
          </button>
        </form>
      </header>

      {/* Barre latérale (tablette/desktop) */}
      <aside className="hidden w-60 flex-col border-r border-slate-200 bg-white md:flex">
        <div className="flex items-center gap-2 px-5 py-5">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand text-lg font-bold text-white">
            C
          </span>
          <span className="text-lg font-bold text-slate-900">Cosmo</span>
        </div>
        <nav className="flex flex-1 flex-col gap-1 px-3">
          {items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex min-h-touch items-center gap-3 rounded-xl px-3 text-base font-medium transition ${
                isActive(item.href)
                  ? "bg-brand text-white"
                  : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              <span aria-hidden>{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="border-t border-slate-200 p-4">
          <p className="truncate text-sm font-semibold text-slate-900">
            {fullName}
          </p>
          <p className="mb-3 text-xs text-slate-500">{roleLabel}</p>
          <form action={logoutAction}>
            <button
              type="submit"
              className="min-h-touch w-full rounded-lg border border-red-200 text-sm font-medium text-red-600 hover:bg-red-50"
            >
              Déconnexion
            </button>
          </form>
        </div>
      </aside>

      {/* Onglets bas (mobile) */}
      <nav className="fixed inset-x-0 bottom-0 z-20 flex border-t border-slate-200 bg-white md:hidden">
        {items.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex flex-1 flex-col items-center justify-center gap-0.5 py-2 text-xs font-medium ${
              isActive(item.href) ? "text-brand" : "text-slate-500"
            }`}
          >
            <span className="text-xl" aria-hidden>
              {item.icon}
            </span>
            {item.label}
          </Link>
        ))}
      </nav>
    </>
  );
}
