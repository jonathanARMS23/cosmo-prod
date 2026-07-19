# Portail Cosmo (Next.js)

Portail web employés pour la boutique Cosmo — interface simple et tactile en
remplacement de l'ERPNext Desk pour les caissières et managers. Backend :
ERPNext v15 (Frappe), consommé via l'API `cosmo_erp.api.main`.

Lot actuel (MVP) : **Caisse** (vente) et **Stock** (consultation lecture seule).

## Architecture (BFF)

Le navigateur ne parle **jamais** directement à Frappe. Tout passe par le
serveur Next.js (Server Actions + Server Components) :

1. **Login** → Server Action `loginAction` : `POST {ERPNEXT_URL}/api/method/login`
   avec `{usr, pwd}`, récupère le cookie `sid` (header `Set-Cookie`).
2. Récupère le contexte utilisateur (`get_current_user_context`) et le jeton
   CSRF (`get_csrf_token`) **en GET** (les méthodes de lecture whitelistées ne
   requièrent pas de CSRF).
3. Stocke `{sid, csrfToken, user, fullName, isManager, isCashier}` dans un
   **cookie de session chiffré** (`iron-session`, `httpOnly` + `secure` en prod
   + `sameSite: lax`). Aucun secret n'atteint le navigateur.
4. Les lectures (`search_items`, `get_stock_for_items`) sont relayées en GET
   avec le cookie `sid`. Les écritures (`create_sale`) sont relayées en POST
   avec le header `X-Frappe-CSRF-Token`.

### Gestion du jeton CSRF

Le jeton CSRF est récupéré **une fois juste après le login** et conservé dans
la session chiffrée à côté du `sid`. Il est réutilisé sur chaque `create_sale`.
S'il manque (session créée avant cette logique), il est re-récupéré à la demande
dans `createSaleAction` puis re-sauvegardé.

### Idempotence des ventes

`idempotencyKey` (`crypto.randomUUID()`) est généré **à l'ouverture de l'écran
paiement** et envoyé à chaque tentative de `create_sale`, y compris les retries
après échec réseau — pas de doublon de facture.

## Variables d'environnement

Voir `.env.local.example`. Copier en `.env.local` :

- `ERPNEXT_URL` — URL interne Frappe. Dev : `http://localhost:8081`.
  Prod : `http://frontend:8080` (réseau Docker interne). **Jamais** `NEXT_PUBLIC_`.
- `SESSION_SECRET` — clé de chiffrement du cookie (≥ 32 caractères).
  Générer en prod : `openssl rand -base64 32`. **Jamais** `NEXT_PUBLIC_`.

## Développement

```bash
npm install
npm run dev     # http://localhost:3000
npm run build   # build de production
```

## Structure

```
src/
  app/
    layout.tsx                  # layout racine (lang=fr, viewport)
    page.tsx                    # redirige vers /caisse ou /login
    login/page.tsx              # page de connexion
    (protected)/
      layout.tsx                # garde d'auth + navigation
      caisse/page.tsx           # écran caisse
      stock/page.tsx            # consultation stock (lecture seule)
      ventes/page.tsx           # stub manager "à venir"
  actions/
    auth.ts                     # loginAction, logoutAction
    sales.ts                    # searchItemsAction, refreshStockAction, createSaleAction
  lib/
    session.ts                  # config iron-session + getSession
    frappe.ts                   # client HTTP serveur → Frappe (GET/POST, parse erreurs)
    format.ts                   # formatAriary : "12 500 Ar"
    types.ts                    # types partagés
  components/
    LoginForm.tsx               # formulaire login (client)
    Nav.tsx                     # nav latérale (≥md) + onglets bas (mobile)
    caisse/
      CaisseClient.tsx          # écran caisse complet (recherche/panier/paiement)
      PaymentDrawer.tsx         # drawer d'encaissement
      StockBadge.tsx            # badge stock accessible
    stock/StockClient.tsx       # recherche stock lecture seule
```
