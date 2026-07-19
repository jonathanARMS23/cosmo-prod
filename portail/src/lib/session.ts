import "server-only";
import { getIronSession, type SessionOptions } from "iron-session";
import { cookies } from "next/headers";

/**
 * Données stockées dans le cookie de session chiffré (iron-session).
 *
 * IMPORTANT : ce cookie est chiffré côté serveur. Le `sid` (cookie de session
 * Frappe) et le jeton CSRF ne quittent JAMAIS le serveur en clair — le
 * navigateur ne reçoit qu'un blob chiffré illisible. Toutes les requêtes vers
 * Frappe sont relayées par les Server Actions / Route Handlers du portail.
 */
export interface SessionData {
  /** Cookie de session Frappe (`sid`). Secret — ne doit jamais atteindre le navigateur. */
  sid?: string;
  /**
   * Jeton CSRF Frappe, récupéré une fois juste après le login via
   * get_csrf_token et conservé ici. Réutilisé sur chaque POST en écriture
   * (create_sale) via le header X-Frappe-CSRF-Token. S'il venait à manquer
   * (ancienne session), il est re-récupéré à la demande côté serveur.
   */
  csrfToken?: string;
  user?: string;
  fullName?: string;
  isManager?: boolean;
  isCashier?: boolean;
  isLoggedIn?: boolean;
}

function getSessionSecret(): string {
  const secret = process.env.SESSION_SECRET;
  if (!secret || secret.length < 32) {
    throw new Error(
      "SESSION_SECRET manquant ou trop court (32 caractères minimum). " +
        "Voir .env.local.example.",
    );
  }
  return secret;
}

export const sessionOptions: SessionOptions = {
  password: getSessionSecret(),
  cookieName: "cosmo_portail_session",
  cookieOptions: {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
  },
};

/** Récupère (ou initialise) la session du portail depuis le cookie chiffré. */
export async function getSession() {
  const cookieStore = await cookies();
  return getIronSession<SessionData>(cookieStore, sessionOptions);
}
