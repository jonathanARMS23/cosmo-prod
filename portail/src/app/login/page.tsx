import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { LoginForm } from "@/components/LoginForm";

export default async function LoginPage() {
  const session = await getSession();
  if (session.isLoggedIn) {
    redirect("/caisse");
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-brand-light p-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-lg">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-brand text-2xl font-bold text-white">
            C
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Portail Cosmo</h1>
          <p className="mt-1 text-sm text-slate-500">Espace employés</p>
        </div>
        <LoginForm />
      </div>
    </main>
  );
}
