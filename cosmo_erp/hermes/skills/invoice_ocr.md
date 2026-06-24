# Skill : Traitement de facture fournisseur par photo

## Quand utiliser ce skill

Quand un utilisateur envoie une photo de document et que c'est une **facture fournisseur**
(pas un ticket client, pas une facture de vente).

Indices visuels : en-tête fournisseur, tableau d'articles, sous-total/total, date, numéro de facture.

## Workflow

### Étape 1 — Extraction OCR (vision native)

Extraire structurellement :
- **Fournisseur** : nom de l'entreprise émettrice
- **Numéro facture** : référence du document (ex: "FAC-2024-0042")
- **Date** : date d'émission (format YYYY-MM-DD)
- **Lignes articles** : pour chaque ligne →
  - Description (nom du produit)
  - Quantité
  - Prix unitaire
  - Montant ligne (= vérification : qty × prix)
- **Total** : montant total TTC
- **Devise** : MGA/Ariary de préférence

Si un champ est illisible → noter "non lisible" plutôt que deviner.

### Étape 2 — Validation et présentation

Avant de créer quoi que ce soit, présenter le récapitulatif extrait :
```
📄 Facture détectée :

🏢 Fournisseur : [nom]
📋 Réf : [numéro]
📅 Date : [date]

Articles :
• [Produit 1] × [qty] à [prix] Ar = [montant] Ar
• [Produit 2] × [qty] à [prix] Ar = [montant] Ar

💰 Total : [total] Ar

✅ Enregistrer cette facture dans ERPNext ?
```

### Étape 3 — Enregistrement

Si confirmation → appeler `process_supplier_invoice_image` avec les données structurées.

## Gestion des erreurs courantes

- **Total ne correspond pas** : avertir → "Le total calculé ([X] Ar) diffère du total facture ([Y] Ar). Vérifier avant de confirmer."
- **Fournisseur non trouvé dans ERPNext** : afficher la liste des fournisseurs via `get_suppliers` et demander lequel correspond
- **Produit non reconnu** : proposer une correspondance manuelle ou créer le produit
