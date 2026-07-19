"use server";

import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { getErpnextUrl, extractSid, frappeGet } from "@/lib/frappe";
import type { UserContext } from "@/lib/types";

export interface LoginState {
  error?: string;
}

/**
 * Authentifie l'employé auprès de Frappe (POST /api/method/login), récupère le
 * `sid`, le contexte utilisateur et le jeton CSRF, puis stocke le tout dans le
 * cookie de session chiffré. Redirige vers /caisse en cas de succès.
 *
 * Message d'erreur volontairement générique : on ne révèle pas si c'est
 * l'identifiant ou le mot de passe qui est faux.
 */
export async function loginAction(
  _prev: LoginState,
  formData: FormData,
): Promise<LoginState> {
  const usr = String(formData.get("usr") ?? "").trim();
  const pwd = String(formData.get("pwd") ?? "");

  if (!usr || !pwd) {
    return { error: "Veuillez saisir votre identifiant et votre mot de passe." };
  }

  let sid: string | null = null;
  try {
    const res = await fetch(`${getErpnextUrl()}/api/method/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ usr, pwd }),
      cache: "no-store",
      redirect: "manual",
    });

    if (res.status >= 500) {
      return { error: "Service momentanément indisponible. Réessayez." };
    }
    sid = extractSid(res.headers.getSetCookie());
    if (!res.ok || !sid) {
      return { error: "Identifiant ou mot de passe incorrect." };
    }
  } catch {
    return { error: "Impossible de joindre le serveur. Vérifiez la connexion." };
  }

  try {
    const context = await frappeGet<UserContext>(
      "cosmo_erp.api.main.get_current_user_context",
      sid,
    );
    const csrf = await frappeGet<{ csrf_token: string }>(
      "cosmo_erp.api.main.get_csrf_token",
      sid,
    );

    const session = await getSession();
    session.sid = sid;
    session.csrfToken = csrf.csrf_token;
    session.user = context.user;
    session.fullName = context.full_name;
    session.isManager = context.is_manager;
    session.isCashier = context.is_cashier;
    session.isLoggedIn = true;
    await session.save();
  } catch {
    return { error: "Connexion établie mais profil illisible. Réessayez." };
  }

  redirect("/caisse");
}

/**
 * Déconnexion : invalide la session Frappe (best-effort) puis détruit le
 * cookie de session du portail. Redirige vers /login.
 */
export async function logoutAction(): Promise<void> {
  const session = await getSession();
  const sid = session.sid;

  if (sid) {
    try {
      await fetch(`${getErpnextUrl()}/api/method/logout`, {
        method: "GET",
        headers: { Cookie: `sid=${sid}`, Accept: "application/json" },
        cache: "no-store",
      });
    } catch {
      /* déconnexion Frappe best-effort : on détruit la session locale de toute façon */
    }
  }

  session.destroy();
  redirect("/login");
}
