#!/usr/bin/env python3
"""
Récupère les IDs Telegram de Jonathan (manager) et de la caissière.

Usage :
  python3 get_telegram_ids.py --token YOUR_BOT_TOKEN

Workflow :
  1. Démarre l'écoute des messages
  2. Demande à Jonathan d'envoyer /start au bot
  3. Affiche son ID
  4. Demande à la caissière de faire pareil
  5. Génère le snippet .env.prod à copier

Prérequis : avoir créé le bot via @BotFather et obtenu le token
"""

import sys
import json
import time
import argparse
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError


BASE_URL = "https://api.telegram.org/bot{token}/{method}"


def api_call(token: str, method: str, params: dict = None) -> dict:
    url = BASE_URL.format(token=token, method=method)
    if params:
        url += "?" + urlencode(params)
    try:
        with urlopen(Request(url), timeout=30) as resp:
            return json.loads(resp.read().decode())
    except URLError as e:
        print(f"Erreur API Telegram : {e}")
        sys.exit(1)


def get_updates(token: str, offset: int = 0) -> list:
    result = api_call(token, "getUpdates", {"offset": offset, "timeout": 20, "allowed_updates": ["message"]})
    return result.get("result", [])


def wait_for_message(token: str, offset: int, label: str) -> tuple:
    """Attend qu'un utilisateur envoie un message. Retourne (user_info, new_offset)."""
    print(f"\nEn attente du message de {label}... (envoyer /start ou n'importe quel message au bot)")
    while True:
        updates = get_updates(token, offset)
        for update in updates:
            offset = update["update_id"] + 1
            if "message" in update:
                user = update["message"]["from"]
                return user, offset
        time.sleep(1)


def verify_token(token: str) -> dict:
    result = api_call(token, "getMe")
    if not result.get("ok"):
        print(f"Token invalide : {result.get('description', 'Erreur inconnue')}")
        sys.exit(1)
    return result["result"]


def send_message(token: str, chat_id: int, text: str):
    api_call(token, "sendMessage", {"chat_id": chat_id, "text": text})


def main():
    parser = argparse.ArgumentParser(description="Récupère les IDs Telegram pour COSMO ERP")
    parser.add_argument("--token", required=True, help="Token du bot Telegram (depuis @BotFather)")
    parser.add_argument("--manager-name", default="Jonathan", help="Prénom du manager")
    parser.add_argument("--cashier-name", default="Caissière", help="Prénom de la caissière")
    args = parser.parse_args()

    token = args.token

    print("\n" + "=" * 60)
    print("   COSMO ERP — Configuration Telegram IDs")
    print("=" * 60)

    # Vérifier le token
    bot_info = verify_token(token)
    print(f"\nBot connecté : @{bot_info['username']} ({bot_info['first_name']})")

    # Obtenir le dernier update_id pour partir de maintenant
    updates = get_updates(token, 0)
    offset = updates[-1]["update_id"] + 1 if updates else 0

    print(f"\nOuvrir Telegram et chercher : @{bot_info['username']}")
    print(f"\n{'─' * 60}")
    print(f"ETAPE 1 : {args.manager_name} (Manager)")
    print(f"{'─' * 60}")

    manager, offset = wait_for_message(token, offset, args.manager_name)
    send_message(token, manager["id"], f"Bonjour {manager.get('first_name', args.manager_name)} ! ID récupéré : {manager['id']}")
    print(f"{args.manager_name} -> ID : {manager['id']} (nom Telegram : {manager.get('first_name', '')} {manager.get('last_name', '')})")

    print(f"\n{'─' * 60}")
    print(f"ETAPE 2 : {args.cashier_name}")
    print(f"{'─' * 60}")

    cashier, offset = wait_for_message(token, offset, args.cashier_name)
    send_message(token, cashier["id"], f"Bonjour {cashier.get('first_name', args.cashier_name)} ! ID récupéré : {cashier['id']}")
    print(f"{args.cashier_name} -> ID : {cashier['id']} (nom Telegram : {cashier.get('first_name', '')} {cashier.get('last_name', '')})")

    # Afficher le résultat à copier
    separator = "=" * 60
    print(f"""
{separator}
  COSMO ERP — Variables Telegram à copier dans .env.prod
{separator}

TELEGRAM_BOT_TOKEN={token}
TELEGRAM_MANAGER_ID={manager['id']}
TELEGRAM_CASHIER_ID={cashier['id']}

{separator}

Prochaine étape :
  1. Copier ces 3 lignes dans .env.prod
  2. make prod-up (ou make prod-restart-hermes si déjà démarré)
{separator}
""")


if __name__ == "__main__":
    main()
