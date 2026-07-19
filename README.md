# cosmo-prod

Monorepo de production pour Cosmo ERP (boutique cosmétique) — déployé sur Hetzner via Coolify.

Ce dépôt aplatit deux composants qui vivent aussi comme dépôts séparés
(`cosmo_erp.git`, `cosmo-mcp.git`) car Coolify ne gère pas l'initialisation
automatique des submodules Git. **`cosmo-prod` est la source de vérité pour
le déploiement** ; les correctifs de production (localisation FR/MGA, fix
`Expect: 100-continue`, sessions MCP par connexion, restructuration du module
Frappe) sont appliqués ici en premier.

## Structure

```
cosmo-prod/
├── docker-compose.yml     # stack de production complète (ERPNext + MariaDB + Redis + cosmo-mcp)
├── Dockerfile.frappe      # image ERPNext custom avec cosmo_erp pip-installé (utilisée par la config de build Coolify, hors docker-compose.yml)
├── cosmo_erp/             # custom app Frappe/ERPNext — voir cosmo_erp/README.md
└── cosmo-mcp/             # serveur MCP Node.js/TypeScript — voir cosmo-mcp/README.md
```

Hermes (agent Telegram) tourne sur un serveur externe (Hostinger) et se
connecte à `cosmo-mcp` via HTTP — il n'est pas orchestré par ce
`docker-compose.yml`. Sa config de référence reste dans `cosmo_erp/hermes/`.

## Documentation

| Composant | Doc |
|---|---|
| Cosmo ERP (app Frappe) | [cosmo_erp/README.md](cosmo_erp/README.md) |
| Déploiement production | [cosmo_erp/DEPLOY.md](cosmo_erp/DEPLOY.md) |
| Guide utilisateur (boutique) | [cosmo_erp/USER_GUIDE.md](cosmo_erp/USER_GUIDE.md) |
| Serveur MCP | [cosmo-mcp/README.md](cosmo-mcp/README.md) |
| API MCP (tools exposés) | [cosmo-mcp/API.md](cosmo-mcp/API.md) |

## Démarrage rapide

```bash
cp cosmo_erp/.env.prod.example .env
docker compose up -d
```

Variables requises : voir `cosmo_erp/.env.prod.example`. Ne jamais committer
de fichier `.env` rempli avec de vraies valeurs (voir `.gitignore`).
