# Guide de Déploiement — COSMO ERP

Stack : ERPNext v15 · MariaDB 10.6 · Redis 7 · Hermes Agent · cosmo-mcp
Déployé sur Hetzner via Coolify ou Docker Compose direct.

---

## Prérequis

- Serveur Hetzner CX21 minimum (2 vCPU, 4 GB RAM), Ubuntu 22.04
- Coolify installé **ou** accès SSH direct avec Docker
- Domaine DNS pointé vers l'IP du serveur (ex: `cosmo.ma-boutique.mg`)
- Comptes : Anthropic API (`sk-ant-...`), Telegram BotFather

---

## Étape 1 — Préparer le serveur Hetzner

```bash
# Connexion SSH
ssh root@<IP_SERVEUR>

# Installer Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker $USER

# Installer Coolify (optionnel — recommandé pour les mises à jour)
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash

# Firewall
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw allow 8080  # ERPNext (temporaire, fermer après SSL)
ufw enable
```

---

## Étape 2 — Cloner le projet

```bash
git clone <REPO_URL> /opt/cosmo-erp
cd /opt/cosmo-erp
```

---

## Étape 3 — Créer le bot Telegram

1. Ouvrir Telegram → chercher **@BotFather** → `/newbot`
2. Nom affiché : `COSMO Boutique`
3. Username : `cosmo_boutique_bot` (doit finir par `bot`)
4. Copier le **token** (format : `1234567890:ABCdefGHI...`)
5. Configurer les commandes via `/setcommands` dans @BotFather :
   ```
   start - Démarrer
   aide - Afficher l'aide
   stock - Vérifier le stock
   ventes - Résumé des ventes du jour
   ```

Les IDs utilisateurs seront récupérés à l'étape 7.

---

## Étape 4 — Configurer les variables d'environnement

```bash
cp .env.prod.example .env.prod
nano .env.prod  # Éditer avec les vraies valeurs
```

| Variable | Description | Où l'obtenir |
|---|---|---|
| `FRAPPE_SITE_NAME` | Domaine du site ERPNext | Votre domaine DNS |
| `DB_ROOT_PASSWORD` | Mot de passe root MariaDB | Générer (ex: `openssl rand -hex 24`) |
| `DB_NAME` | Nom de la base de données | Laisser `_cosmo_prod` |
| `COSMO_MCP_API_KEY` | Clé API ERPNext | Étape 6 |
| `COSMO_MCP_API_SECRET` | Secret API ERPNext | Étape 6 |
| `ANTHROPIC_API_KEY` | Clé API Anthropic | console.anthropic.com |
| `TELEGRAM_BOT_TOKEN` | Token du bot Telegram | @BotFather (étape 3) |
| `TELEGRAM_MANAGER_ID` | ID Telegram du manager | Étape 7 |
| `TELEGRAM_CASHIER_ID` | ID Telegram de la caissière | Étape 7 |

> **JAMAIS** committer `.env.prod` dans git.

---

## Étape 5 — Démarrer le stack

```bash
# Build cosmo-mcp (TypeScript) + images Docker
make build-all

# Démarrer tous les services
make prod-up

# Attendre ~2 minutes que ERPNext soit prêt, puis :
make install SITE=cosmo.ma-boutique.mg
make migrate SITE=cosmo.ma-boutique.mg
```

Vérifier que tous les services tournent :
```bash
make status
```

---

## Étape 6 — Obtenir l'API Key ERPNext

```bash
make setup-apikey SITE=cosmo.ma-boutique.mg
# → Affiche COSMO_MCP_API_KEY et COSMO_MCP_API_SECRET
```

Copier ces deux valeurs dans `.env.prod`, puis :
```bash
make prod-restart-hermes
```

---

## Étape 7 — Récupérer les IDs Telegram

```bash
make setup-telegram TOKEN=votre_token_botfather
# → Jonathan envoie un message au bot
# → La caissière envoie un message au bot
# → Le script affiche les deux IDs
```

Copier `TELEGRAM_MANAGER_ID` et `TELEGRAM_CASHIER_ID` dans `.env.prod`, puis :
```bash
make prod-restart-hermes
```

---

## Étape 8 — Vérification

- [ ] `make status` → tous les services en `Up`
- [ ] ERPNext accessible sur `https://cosmo.ma-boutique.mg`
- [ ] Connexion ERPNext avec `Administrator`
- [ ] `make test-mcp` → `MCP OK: {...}`
- [ ] Hermes répond à "Bonjour" sur Telegram (manager)
- [ ] Hermes répond à "Bonjour" sur Telegram (caissière)
- [ ] `make prod-logs-hermes` → pas d'erreur critique
- [ ] `make prod-logs-mcp` → pas de timeout
- [ ] Backup test : `make backup SITE=cosmo.ma-boutique.mg`
- [ ] Firewall : fermer le port 8080 si SSL Coolify actif

---

## Coolify : configuration spécifique

1. Dans Coolify → **New Resource** → **Docker Compose**
2. Pointer vers `docker-compose.prod.yml` dans le repo
3. Dans **Environment Variables**, ajouter toutes les variables de `.env.prod`
4. **Build Command** : `make build-all`
5. **Start Command** : laisser vide (Coolify gère via docker-compose)
6. Activer **Auto-deploy on push** pour les mises à jour automatiques
7. SSL : activer Let's Encrypt sur le domaine `cosmo.ma-boutique.mg` → port `8080`

---

## Mise à jour

```bash
git pull
make build-all
make prod-up         # Rolling update Coolify
make migrate SITE=cosmo.ma-boutique.mg
```

---

## Troubleshooting

**ERPNext ne démarre pas (backend en restart loop)**
```bash
make prod-logs       # Chercher "DB_HOST unreachable" ou "redis"
# Attendre que MariaDB soit healthy (healthcheck toutes les 10s, 5 retries)
docker compose -f docker-compose.prod.yml ps db
```

**cosmo-mcp timeout / `MCP OK` ne s'affiche pas**
```bash
make prod-logs-mcp
# Vérifier COSMO_MCP_API_KEY et COSMO_MCP_API_SECRET dans .env.prod
# Vérifier que ERPNext frontend répond sur port 8080
```

**Hermes ne répond pas sur Telegram**
```bash
make prod-logs-hermes
# Vérifier TELEGRAM_BOT_TOKEN, TELEGRAM_MANAGER_ID, ANTHROPIC_API_KEY
# Redémarrer : make prod-restart-hermes
```

**`make install` échoue avec "Site already exists"**
```bash
# Le site existe déjà — lancer uniquement migrate
make migrate SITE=cosmo.ma-boutique.mg
```

**MariaDB : "Access denied for root"**
```bash
# DB_ROOT_PASSWORD dans .env.prod ne correspond pas au volume existant
# Supprimer le volume et recommencer :
docker compose -f docker-compose.prod.yml down -v
make prod-up && make install SITE=cosmo.ma-boutique.mg
```

**Erreur "sites volume empty" au démarrage frontend**
```bash
# Le site n'a pas encore été créé — install obligatoire avant le frontend
make install SITE=cosmo.ma-boutique.mg
```

---

## Sauvegarde

```bash
make backup SITE=cosmo.ma-boutique.mg
# Fichiers dans : sites/cosmo.ma-boutique.mg/private/backups/
```

Automatiser via cron sur le serveur :
```bash
0 2 * * * cd /opt/cosmo-erp && make backup SITE=cosmo.ma-boutique.mg
```
