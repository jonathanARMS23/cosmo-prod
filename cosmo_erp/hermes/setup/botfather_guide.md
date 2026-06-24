# Créer le bot Telegram COSMO

## Étape 1 — Créer le bot via @BotFather

1. Ouvrir Telegram et chercher **@BotFather**
2. Envoyer `/newbot`
3. Choisir un nom affiché : `COSMO Boutique`
4. Choisir un username unique : `cosmo_boutique_bot` (doit finir par `bot`)
5. Copier le **token** affiché (format : `1234567890:ABCdefGHI...`)

## Étape 2 — Configurer le bot (optionnel mais recommandé)

Dans @BotFather :
```
/setdescription → "Assistant IA de la boutique cosmétique"
/setabouttext → "Gestion de stock, ventes et rapports via Telegram"
/setcommands →
start - Démarrer
aide - Afficher l'aide
stock - Vérifier le stock
ventes - Résumé des ventes du jour
```

## Étape 3 — Récupérer les IDs utilisateurs

```bash
python3 cosmo_erp/hermes/setup/get_telegram_ids.py --token VOTRE_TOKEN
```

→ Jonathan envoie un message au bot
→ La caissière envoie un message au bot
→ Le script affiche les IDs à copier dans `.env.prod`

## Étape 4 — Mettre à jour .env.prod

```env
TELEGRAM_BOT_TOKEN=votre_token_ici
TELEGRAM_MANAGER_ID=id_jonathan_ici
TELEGRAM_CASHIER_ID=id_caissiere_ici
```

## Étape 5 — Redémarrer Hermes

```bash
make prod-restart-hermes
```

## Vérification

Envoyer "Bonjour" au bot → Hermes doit répondre.
