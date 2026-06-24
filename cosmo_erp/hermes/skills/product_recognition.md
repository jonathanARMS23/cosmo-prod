# Skill : Reconnaissance de produit cosmétique

## Quand utiliser ce skill

Quand un utilisateur envoie une photo de produit cosmétique et demande :
- "C'est quoi ce produit ?"
- "On l'a en stock ?"
- "Combien ça coûte ?"
- "Je veux vendre ça"

## Workflow

### Étape 1 — Analyse visuelle (vision native)

Extraire de l'image :
- **Marque** : logotype ou texte de marque (ex: "L'Oréal", "Nivea", "Maybelline")
- **Nom du produit** : nom commercial complet (ex: "Micellar Water", "BB Cream SPF 15")
- **Type de produit** : catégorie (fond de teint, crème hydratante, mascara, etc.)
- **Référence/SKU** : si visible sur l'emballage
- **Code-barres** : si visible et lisible
- **Contenance** : si visible (ex: "200ml", "50g")

Si l'image est floue ou le produit peu visible → demander une meilleure photo.

### Étape 2 — Recherche dans ERPNext

Appeler `identify_product_from_image` avec les données extraites :
```
{
  "image_description": "[description complète extraite]",
  "brand": "[marque]",
  "product_name": "[nom produit]",
  "barcode": "[code si visible]"
}
```

### Étape 3 — Réponse selon le résultat

**Produit trouvé (1 résultat) :**
```
✅ [Nom produit] — [Marque]
💰 Prix : [prix] Ar
📦 Stock : [qty] [uom]
[Si stock bas : ⚠️ Stock bas (seuil : [niveau])]
```
→ Proposer d'ajouter à une vente si contexte commercial

**Plusieurs résultats :**
Lister les 3 premiers, demander lequel correspond

**Produit non trouvé :**
```
🔍 Je n'ai pas trouvé ce produit dans le catalogue.
Souhaitez-vous :
1. Le rechercher autrement (autre nom ?)
2. L'ajouter au catalogue (nouveau produit)
```

## Points d'attention

- Toujours vérifier le stock AVANT de confirmer une disponibilité
- Un produit avec qty=0 → "Rupture de stock, voici les dernières infos"
- Un produit proche de l'expiration → mentionner la date en plus du stock
