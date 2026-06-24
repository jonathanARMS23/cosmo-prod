# Skill : Vente rapide depuis une photo de produit

## Quand utiliser ce skill

Workflow combiné pour les ventes initiées par photo :
1. Utilisateur envoie une photo + demande de vente
2. Identifier le produit → confirmer → créer la vente

Exemple : "Vends ça" + photo | "Facture pour ça" + photo

## Workflow complet

### Phase 1 : Identification
Utiliser le skill `product_recognition` pour identifier le produit.

### Phase 2 : Informations manquantes
Après identification, collecter si nécessaire :
- **Quantité** (si non mentionnée) : "Combien d'unités ?"
- **Client** (optionnel) : "Pour quelle cliente ?" (si non mentionné → Walk-in Customer)
- **Mode de paiement** : demander uniquement si pas de défaut connu → espèces par défaut

### Phase 3 : Confirmation (OBLIGATOIRE)
Format standard de confirmation vente.

### Phase 4 : Exécution
Appeler `create_sale` avec items, customer, payment_mode.

## Cas particulier : plusieurs produits en photo

Si la photo montre un panier / étagère / plusieurs produits :
- Lister tous les produits identifiés
- Demander confirmation de la liste COMPLÈTE avant de créer la vente
- Ne pas créer de vente partielle sans accord

## Timing

Ce skill est optimisé pour la caisse — tout doit être rapide.
Maximum 2 échanges entre la photo et la vente confirmée.
