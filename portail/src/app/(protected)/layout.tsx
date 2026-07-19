import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { Nav } from "@/components/Nav";

export default async function ProtectedLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const session = await getSession();
  if (!session.isLoggedIn) {
    redirect("/login");
  }

  const roleLabel = session.isManager
    ? "Manager"
    : session.isCashier
      ? "Caissière"
      : "Employé";

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <Nav
        fullName={session.fullName ?? session.user ?? "Employé"}
        roleLabel={roleLabel}
        isManager={Boolean(session.isManager)}
      />
      <main className="flex-1 pb-20 md:pb-0">{children}</main>
    </div>
  );
}
