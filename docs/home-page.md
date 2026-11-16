# Page d'accueil — ce qui doit apparaître

Page publique du site web (visiteur non connecté). Conçue **mobile first** : une seule colonne sur mobile, puis grille à partir de `md`.

Le web sert aux **fournisseurs** et au back-office admin ; les **associations** utilisent l'app mobile. La home doit donc convertir un fournisseur et orienter une association vers le mobile.

## Sections, dans l'ordre

| # | Section | Contenu | Lien avec le contrat |
| - | ------- | ------- | -------------------- |
| 1 | Barre de navigation | Logo Gaspirator, liens vers les sections (cachés sur mobile), bouton **Se connecter** | `POST /auth/login` (US-01) |
| 2 | Hero | Badge de crédibilité, titre (« Vos invendus alimentaires donnés, pas jetés »), sous-titre, CTA **Demander une inscription** + **Se connecter**, illustration (à droite sur desktop, en dessous sur mobile) | `POST /registration-requests` (US-01) |
| 3 | Partenaires | Logos des structures partenaires | — |
| 4 | Fonctionnalités | 4 cartes : publier un lot, trouver des fournisseurs proches, réserver un lot, confirmer le retrait par code | US-02, US-03, US-04, US-05 |
| 5 | Pourquoi Gaspirator | 4 arguments courts (moins de gaspillage, gratuit, rapide, local…) | — |
| 6 | Avis | Témoignages de fournisseurs et d'associations, défilement horizontal | — |
| 7 | FAQ | 4 questions minimum (qui peut s'inscrire, combien ça coûte, comment est validée l'inscription, comment récupérer un lot) | — |
| 8 | Appel à l'action final | Titre + CTA **Demander une inscription** + visuel | US-01 |
| 9 | Pied de page | Logo, champ e-mail de contact, colonnes de liens (navigation, réseaux sociaux, mentions légales) | — |

## Indispensable même en version minimale

Barre de navigation, Hero avec les deux CTA, Fonctionnalités, Appel à l'action final, Pied de page avec mentions légales. Partenaires, Avis et FAQ peuvent attendre d'avoir du vrai contenu.

## Règles

- Les deux CTA (inscription, connexion) sont visibles **sans scroller** sur mobile.
- Tout le texte est en français.
- Accessible : un seul `h1`, titres de section en `h2`, boutons de taille tactile (≥ 44 px), contraste suffisant, FAQ utilisable au clavier.
- Pas de données chargées depuis l'API : le contrat ne prévoit aucun endpoint public pour la home.

## Hors périmètre pour l'instant

- Partenaires et avis réels : à fournir, ne pas inventer de faux logos ni de faux témoignages.
- Chiffres d'impact (badge « X kg sauvés ») : aucun endpoint ne les fournit, texte fixe en attendant.
- Champ e-mail du pied de page : aucun endpoint newsletter/contact dans le contrat.
- Liens de téléchargement de l'app mobile : l'app n'existe pas encore.
- Palette de couleurs : stockée dans `apps/web/src/index.css`, pas encore appliquée.
