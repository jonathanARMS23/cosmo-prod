# COSMO ERP

> ERP boutique cosmetique Madagascar — ERPNext v15 + Hermes Agent IA via Telegram

## Architecture

```
Telegram (Jonathan + Caissiere)
        |
  Hermes Agent (claude-opus-4-8)
        | MCP Protocol
  cosmo-mcp (Node.js 20 / TypeScript)
        | REST API (API Key)
  ERPNext v15 (Frappe)  <-- cosmo_erp custom app
        |
  MariaDB 10.6 + Redis 7
```

## Composants

| Composant | Description |
|-----------|-------------|
| `cosmo_erp` | App Frappe/ERPNext custom : DocTypes, events, fixtures, scheduler, POS simplifie |
| `cosmo-mcp` | Serveur MCP Node.js 20/TypeScript exposant l'API ERPNext a Hermes |
| `hermes` | Agent IA Telegram (claude-opus-4-8) pour la gestion boutique en langage naturel |
| `db` | MariaDB 10.6 — base de donnees principale ERPNext |
| `redis-cache` | Redis 7 — cache Frappe |
| `redis-queue` | Redis 7 — file de taches asynchrones Frappe |
| `frontend` | Nginx ERPNext — sert l'interface web et proxifie le backend |
| `scheduler` | Processus Frappe — alertes stock/expiry quotidiennes, rapport hebdomadaire |
| `worker-short` | Worker Frappe — taches courtes et taches par defaut |
| `worker-long` | Worker Frappe — taches longues (exports, backups) |

## Quick Start

```bash
git clone https://github.com/ARMS-projects/cosmo_erp.git
cd cosmo_erp

cp .env.prod.example .env.prod          # Remplir toutes les variables
make setup-telegram TOKEN=<bot_token>   # Recuperer les IDs Telegram
make install SITE=cosmo.mg              # Installer cosmo_erp dans ERPNext
make setup-apikey SITE=cosmo.mg         # Creer l'utilisateur Hermes + API Key
make prod-up                            # Demarrer le stack
```

## Structure du projet

```
cosmo_erp/
├── cosmo_erp/               # App Frappe principale
│   ├── api/                 # Endpoints REST custom (dashboard, stock, scan)
│   ├── controllers/         # Validation item, logique metier
│   ├── doctype/             # DocTypes custom (Cosmo Product Scan, etc.)
│   ├── events/              # Hooks Python (Sales Invoice, Item)
│   ├── fixtures/            # Custom Fields, Print Formats, Roles (JSON)
│   ├── public/              # JS/CSS globaux et par DocType
│   ├── tasks/               # Taches planifiees (daily, weekly, monthly)
│   ├── templates/           # Pages web Frappe (POS, Hermes)
│   └── hooks.py             # Point d'entree Frappe (assets, events, scheduler)
├── hermes/                  # Agent IA Telegram
│   ├── SOUL.md              # Personnalite et regles metier de Hermes
│   └── setup/               # Scripts d'initialisation (get_telegram_ids.py)
├── docker-compose.prod.yml  # Stack production (Hetzner / Coolify)
├── docker-compose.dev.yml   # Stack developpement local
├── Makefile                 # Toutes les commandes operationnelles
└── .env.prod.example        # Template de configuration
```

## Commandes make

| Commande | Description |
|----------|-------------|
| `make help` | Affiche la liste des commandes disponibles |
| `make dev-up` | Demarre l'environnement de developpement |
| `make dev-down` | Arrete l'environnement de developpement |
| `make dev-logs` | Affiche les logs du dev |
| `make build-mcp` | Build le MCP Server TypeScript |
| `make build-all` | Build tous les composants |
| `make install SITE=<site>` | Installe cosmo_erp dans ERPNext |
| `make migrate SITE=<site>` | Lance bench migrate (fixtures, custom fields) |
| `make fixtures-export SITE=<site>` | Exporte les fixtures vers JSON |
| `make clear-cache SITE=<site>` | Vide le cache Frappe |
| `make prod-up` | Demarre le stack production (necessite .env.prod) |
| `make prod-down` | Arrete le stack production |
| `make prod-logs` | Logs de tous les services production |
| `make prod-logs-hermes` | Logs Hermes Agent uniquement |
| `make prod-restart-hermes` | Redemmarre Hermes sans toucher ERPNext |
| `make setup-apikey SITE=<site>` | Cree l'utilisateur Hermes et genere l'API Key |
| `make setup-telegram TOKEN=<token>` | Recupere les IDs Telegram interactivement |
| `make test-mcp` | Teste la connexion cosmo-mcp vers ERPNext |
| `make status` | Affiche le statut de tous les services |
| `make backup` | Sauvegarde la DB ERPNext |

## Variables d'environnement

| Variable | Description | Exemple |
|----------|-------------|---------|
| `FRAPPE_SITE_NAME` | Nom du site ERPNext | `cosmo.ma-boutique.mg` |
| `DB_ROOT_PASSWORD` | Mot de passe root MariaDB | `strong_password` |
| `DB_NAME` | Nom de la base de donnees | `_cosmo_prod` |
| `COSMO_MCP_API_KEY` | Cle API ERPNext role "Cosmo Hermes" | `abc123...` |
| `COSMO_MCP_API_SECRET` | Secret API ERPNext | `xyz789...` |
| `ANTHROPIC_API_KEY` | Cle API Anthropic pour claude-opus-4-8 | `sk-ant-...` |
| `TELEGRAM_BOT_TOKEN` | Token du bot Telegram (BotFather) | `123456:ABC...` |
| `TELEGRAM_MANAGER_ID` | ID Telegram du manager (Jonathan) | `987654321` |
| `TELEGRAM_CASHIER_ID` | ID Telegram de la caissiere | `123456789` |
| `LOG_LEVEL` | Niveau de log Hermes | `info` |
| `TZ` | Fuseau horaire serveur | `Indian/Antananarivo` |

## Stack technique

- **ERPNext v15** / Frappe Framework — ERP open-source
- **MariaDB 10.6** — base de donnees relationnelle
- **Redis 7** — cache et file de taches
- **Node.js 20** / TypeScript 5.3 — runtime cosmo-mcp
- **MCP SDK 1.0** (`@modelcontextprotocol/sdk`) — protocole agent-outil
- **claude-opus-4-8** (Anthropic) — modele IA Hermes Agent
- **Python 3.11+** — app Frappe et scripts setup
- **Docker / Docker Compose** — containerisation
- **Nginx** — reverse proxy ERPNext
- **Hetzner + Coolify** — hebergement production

## Licence

MIT — Copyright 2024 ARMS (jonathan@overlord.fund)
