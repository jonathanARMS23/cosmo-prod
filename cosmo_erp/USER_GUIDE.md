# Guide d'utilisation — COSMO Bot

> Pour Jonathan (manager) et sa femme (caissière)  
> Mis à jour : juin 2026

---

## Premiers pas

Ouvrez la conversation avec **Cosmo Boutique Bot** sur Telegram et envoyez :

> "Bonjour !"

COSMO vous répond et affiche un menu de bienvenue avec les commandes disponibles selon votre profil.  
Si c'est la première fois, COSMO vous demandera votre nom pour personnaliser les réponses.

---

## Ce que COSMO peut faire

### Pour la caissière

---

**1. Vendre un produit**

Dites simplement ce que vous voulez facturer :

- "Vends 2 crèmes Nivea"
- "Je veux facturer : 1 fond de teint L'Oréal + 2 rouges à lèvres Mac"
- "Vente : 3 masques Garnier, 1 huile Camellia"
- Envoyez une **photo du produit** + "Vends ça"

COSMO vous répond avec un récapitulatif :

```
Vente proposée :
• 2 crèmes Nivea Soft — 2 × 7 500 Ar = 15 000 Ar
• 1 fond de teint L'Oréal — 12 000 Ar

Total : 27 000 Ar

Confirmer ? (oui / non)
```

Répondez **"oui"** pour enregistrer, **"non"** pour annuler.

---

**2. Chercher un produit**

- "C'est quoi le stock de la crème Nivea ?"
- "Tu as du fond de teint ?"
- "Prix du shampoing Pantene ?"
- Envoyez une **photo** du produit → COSMO identifie le produit et donne le stock + prix

COSMO affiche :
```
Crème Nivea Soft 200ml
Stock : 18 unités
Prix de vente : 7 500 Ar
```

---

**3. Trouver une cliente**

- "La cliente Mme Rakoto est là, fais sa facture"
- "Cherche Voahangy dans les clientes"
- "Mme Ratsimbazafy a commandé quoi la dernière fois ?"

COSMO retrouve la fiche cliente et peut préparer une facture personnalisée.

---

**4. Consulter les ventes du jour**

- "On a fait combien aujourd'hui ?"
- "Ventes aujourd'hui ?"
- "Combien de transactions ce matin ?"

COSMO répond :
```
Ventes du 23 juin 2026 :
• 14 transactions
• Total : 187 500 Ar
```

---

### Pour le manager (fonctions supplémentaires)

---

**5. Briefing matinal automatique** (8h00 tous les jours)

Chaque matin à 8h00, COSMO envoie automatiquement un résumé :

```
Bonjour Jonathan ! Voici votre briefing du 23/06 :

Hier : 22 ventes — 312 000 Ar
Ce mois : 4 850 000 Ar (objectif 5 000 000 Ar)

Alertes stock :
⚠ Huile Camellia : 3 unités restantes
⚠ Masque Garnier Fructis : 2 unités restantes

Commandes en attente : 1 (Cosmodis)
```

Pas besoin de rien faire, le message arrive tout seul.

---

**6. Gérer le stock**

Réception de marchandises :

- "Reçu 24 bouteilles shampoing Pantene à 8 500 Ar"
- "On a reçu 50 crèmes Nivea Soft, prix achat 4 200 Ar"
- "Livraison Cosmodis : 30 fonds de teint L'Oréal"

Correction d'inventaire :

- "Ajuste le stock du fond de teint L'Oréal à 12 unités (inventaire)"
- "Après inventaire : Pantene = 18, Nivea = 34"

COSMO demande confirmation avant tout ajustement.

---

**7. Commander aux fournisseurs**

- "Commande 50 crèmes Nivea chez Cosmodis"
- "Passe une commande : 100 rouges à lèvres Mac + 40 masques Garnier"
- "Quelles commandes fournisseurs sont en attente ?"
- "La commande Cosmodis, c'est arrivé ?"

COSMO génère le bon de commande et l'enregistre dans le système.

---

**8. Rapports**

- "Rapport hebdomadaire" → envoyé automatiquement chaque lundi matin
- "Qui sont nos meilleures clientes ce mois ?"
- "Montre-moi les ventes de la semaine"
- "Quels produits se vendent le mieux ?"
- "Rapport du mois de mai"

---

**9. Traiter une facture fournisseur (photo)**

Photographiez la facture reçue du fournisseur et envoyez-la à COSMO.

COSMO extrait automatiquement les informations :
```
Facture détectée — Cosmodis, 18 juin 2026
• 24 × Crème Nivea Soft — 4 200 Ar = 100 800 Ar
• 12 × Shampoing Pantene 400ml — 7 800 Ar = 93 600 Ar

Total : 194 400 Ar

Enregistrer cette facture ? (oui / non)
```

---

**10. Alertes automatiques** (10h00 si stock critique)

Si un produit tombe en dessous du seuil minimum, COSMO envoie une alerte à 10h00 :

```
⚠ ALERTE STOCK :
• Huile Camellia Bio : 3 unités (seuil : 10)
• Rouge à lèvres Mac Rouge Couture : 2 unités (seuil : 5)

Commander maintenant ? (oui / non)
```

---

## Règle de confirmation

**COSMO demande toujours "Confirmer ?" avant d'enregistrer une vente, un achat ou une commande.**

C'est une sécurité : si vous avez fait une erreur dans le message, vous pouvez répondre "non" et recommencer.  
Rien n'est enregistré tant que vous n'avez pas dit "oui".

---

## En cas de problème

| Situation | Que faire |
|---|---|
| COSMO dit "Je n'ai pas compris" | Reformulez différemment, soyez plus précis |
| COSMO dit "Erreur" | Réessayez, ou contactez Jonathan |
| Le bot ne répond pas | Vérifiez la connexion internet |
| COSMO donne un mauvais produit | Dites "Annule" et recommencez avec le nom exact |

Pour joindre Jonathan en urgence : appelez directement, ne passez pas par COSMO.

---

## Raccourcis pratiques

| Ce que vous dites | Ce que fait COSMO |
|---|---|
| "Stock ?" | Stock de tous les produits |
| "Ventes aujourd'hui ?" | CA + nombre de transactions |
| "Commandes en attente ?" | Liste des commandes fournisseurs |
| "Alertes ?" | Produits critiques + expirations proches |
| "Menu" | Affiche toutes les commandes disponibles |
| "Aide" | Guide rapide dans Telegram |
