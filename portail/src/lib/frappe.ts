import "server-only";

/**
 * Client HTTP côté serveur pour Frappe/ERPNext (BFF).
 *
 * Toutes les requêtes vers Frappe passent par ici — jamais depuis le
 * navigateur. On relaie le cookie de session `sid` stocké (chiffré) dans la
 * session du portail, et pour les POST en écriture le header
 * X-Frappe-CSRF-Token.
 *
 * Conventions Frappe :
 *  - Les méthodes @frappe.whitelist() en LECTURE sont appelables en GET (pas
 *    de jeton CSRF requis) : on les utilise en GET.
 *  - Les POST en écriture (create_sale) exigent le header X-Frappe-CSRF-Token.
 *  - La valeur de retour est enveloppée dans `{ "message": <retour> }`.
 */

const DEFAULT_ERPNEXT_URL = "http://localhost:8081";

/**
 * URL interne de Frappe.
 *  - Dev  : http://localhost:8081 (port nginx du docker-compose existant)
 *  - Prod : http://frontend:8080 (réseau Docker interne) — via ERPNEXT_URL
 */
export function getErpnextUrl(): string {
  return process.env.ERPNEXT_URL ?? DEFAULT_ERPNEXT_URL;
}

/** Erreur Frappe avec code HTTP, message déjà en français lisible si possible. */
export class FrappeError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "FrappeError";
    this.status = status;
  }
}

interface FrappeEnvelope<T> {
  message: T;
}

/** Extrait le `sid` d'un tableau d'en-têtes Set-Cookie. */
export function extractSid(setCookies: string[]): string | null {
  for (const cookie of setCookies) {
    const match = /(?:^|;\s*)sid=([^;]+)/.exec(cookie);
    if (match && match[1] && match[1] !== "Guest") {
      return match[1];
    }
  }
  return null;
}

function stripHtml(input: string): string {
  return input.replace(/<[^>]*>/g, "").trim();
}

/**
 * Extrait un message d'erreur lisible d'une réponse Frappe.
 * Frappe.throw() renvoie le message humain dans `_server_messages`
 * (un JSON de JSON), déjà en français côté cosmo_erp.
 */
export function parseFrappeError(bodyText: string): string | null {
  try {
    const json = JSON.parse(bodyText) as {
      _server_messages?: string;
      exception?: string;
      message?: string;
    };
    if (typeof json._server_messages === "string") {
      const parsed = JSON.parse(json._server_messages) as string[];
      const messages = parsed.map((entry) => {
        try {
          const obj = JSON.parse(entry) as { message?: string };
          return obj.message ? stripHtml(obj.message) : stripHtml(entry);
        } catch {
          return stripHtml(entry);
        }
      });
      const joined = messages.filter(Boolean).join(" ");
      if (joined) return joined;
    }
    if (typeof json.message === "string" && json.message) {
      return stripHtml(json.message);
    }
    if (typeof json.exception === "string" && json.exception) {
      return stripHtml(json.exception);
    }
  } catch {
    /* corps non-JSON */
  }
  return null;
}

/** GET d'une méthode whitelistée Frappe (lecture, sans CSRF). */
export async function frappeGet<T>(
  method: string,
  sid: string,
  params?: Record<string, string>,
): Promise<T> {
  const url = new URL(`${getErpnextUrl()}/api/method/${method}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      url.searchParams.set(key, value);
    }
  }

  const res = await fetch(url, {
    method: "GET",
    headers: {
      Cookie: `sid=${sid}`,
      Accept: "application/json",
    },
    cache: "no-store",
  });

  const text = await res.text();
  if (!res.ok) {
    throw new FrappeError(
      parseFrappeError(text) ?? `Erreur serveur (${res.status}).`,
      res.status,
    );
  }
  return (JSON.parse(text) as FrappeEnvelope<T>).message;
}

/** POST d'une méthode whitelistée Frappe (écriture, avec CSRF). */
export async function frappePost<T>(
  method: string,
  sid: string,
  csrfToken: string,
  body: Record<string, unknown>,
): Promise<T> {
  const res = await fetch(`${getErpnextUrl()}/api/method/${method}`, {
    method: "POST",
    headers: {
      Cookie: `sid=${sid}`,
      "Content-Type": "application/json",
      Accept: "application/json",
      "X-Frappe-CSRF-Token": csrfToken,
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const text = await res.text();
  if (!res.ok) {
    throw new FrappeError(
      parseFrappeError(text) ?? `Erreur serveur (${res.status}).`,
      res.status,
    );
  }
  return (JSON.parse(text) as FrappeEnvelope<T>).message;
}
