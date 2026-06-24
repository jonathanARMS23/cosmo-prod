# COSMO ERP — Makefile
# Commandes de développement et déploiement

.PHONY: help dev-up dev-down prod-up prod-down build install migrate logs

SITE ?= cosmo.localhost
BENCH = docker compose -f docker-compose.dev.yml exec erpnext-dev bench

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Développement ─────────────────────────────────────────────────────────────

dev-up: ## Démarre l'environnement de développement
	docker compose -f docker-compose.dev.yml up -d
	@echo "ERPNext dev : http://localhost:8000"

dev-down: ## Arrête l'environnement de développement
	docker compose -f docker-compose.dev.yml down

dev-logs: ## Affiche les logs du dev
	docker compose -f docker-compose.dev.yml logs -f

# ── Build ─────────────────────────────────────────────────────────────────────

build-mcp: ## Build le MCP Server TypeScript
	cd ../cosmo-mcp && npm run build
	@echo "cosmo-mcp build OK"

build-all: build-mcp ## Build tous les composants
	docker compose -f docker-compose.prod.yml build

# ── ERPNext — Opérations bench ────────────────────────────────────────────────

install: ## Installe cosmo_erp dans le site de dev
	$(BENCH) --site $(SITE) install-app cosmo_erp
	@echo "cosmo_erp installé sur $(SITE)"

migrate: ## Lance bench migrate (sync fixtures, custom fields, etc.)
	$(BENCH) --site $(SITE) migrate
	@echo "Migration terminée"

fixtures-export: ## Exporte les fixtures depuis ERPNext vers JSON
	$(BENCH) --site $(SITE) export-fixtures --app cosmo_erp
	@echo "Fixtures exportées"

clear-cache: ## Vide le cache Frappe
	$(BENCH) --site $(SITE) clear-cache
	$(BENCH) --site $(SITE) clear-website-cache

# ── Production ────────────────────────────────────────────────────────────────

prod-up: ## Démarre le stack production (nécessite .env.prod)
	@test -f .env.prod || (echo "Fichier .env.prod manquant — copier .env.prod.example" && exit 1)
	docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
	@echo "Stack production démarré"

prod-down: ## Arrête le stack production
	docker compose -f docker-compose.prod.yml down

prod-logs: ## Logs production (tous les services)
	docker compose -f docker-compose.prod.yml logs -f

prod-logs-mcp: ## Logs cosmo-mcp uniquement
	docker compose -f docker-compose.prod.yml logs -f cosmo-mcp

prod-logs-hermes: ## Logs Hermes Agent uniquement
	docker compose -f docker-compose.prod.yml logs -f hermes

prod-restart-hermes: ## Redémarre Hermes Agent sans toucher ERPNext
	docker compose -f docker-compose.prod.yml restart hermes

# ── Utilitaires ───────────────────────────────────────────────────────────────

setup-apikey: ## Crée l'utilisateur Hermes et génère l'API Key ERPNext
	$(BENCH) --site $(SITE) execute cosmo_erp.setup.create_hermes_user.run
	@echo "Copier les valeurs COSMO_MCP_API_KEY et COSMO_MCP_API_SECRET dans .env.prod"

setup-telegram: ## Lance le script interactif de récupération des IDs Telegram
	@test -n "$(TOKEN)" || (echo "Usage: make setup-telegram TOKEN=your_bot_token" && exit 1)
	python3 hermes/setup/get_telegram_ids.py --token $(TOKEN)

api-key: ## Crée une API Key ERPNext pour le rôle Cosmo Hermes (nécessite site opérationnel)
	$(BENCH) --site $(SITE) execute frappe.core.doctype.user.user.generate_keys \
		--args "['Administrator']"
	@echo "Récupérer la clé dans ERPNext > Settings > API Access"

test-mcp: ## Teste la connexion cosmo-mcp → ERPNext
	cd ../cosmo-mcp && node -e " \
		process.env.ERPNEXT_URL='http://localhost:8000'; \
		process.env.ERPNEXT_API_KEY='$$COSMO_MCP_API_KEY'; \
		process.env.ERPNEXT_API_SECRET='$$COSMO_MCP_API_SECRET'; \
		const {getClient} = require('./dist/client.js'); \
		getClient().call('get_dashboard_summary').then(r => console.log('MCP OK:', r.message)).catch(e => console.error('ERREUR:', e.message)); \
	"

status: ## Affiche le statut de tous les services
	docker compose -f docker-compose.prod.yml ps

backup: ## Sauvegarde la DB ERPNext
	$(BENCH) --site $(SITE) backup
	@echo "Backup créé dans sites/$(SITE)/private/backups/"
