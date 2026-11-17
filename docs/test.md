# Tests du front (web)

Tests unitaires de `apps/web` avec [Vitest](https://vitest.dev). Les tests du serveur (pytest) sont décrits dans [ci.md](ci.md).

## Outils

| Outil | Rôle |
| ----- | ---- |
| Vitest | Lance les tests, fournit `describe` / `it` / `expect` et les mocks (`vi`) |
| jsdom | Simule un navigateur (`document`, `window`) dans Node |
| Testing Library (`@testing-library/react`, `@testing-library/user-event`) | Affiche un composant et interagit avec lui comme un utilisateur |
| jest-dom | Assertions pour le DOM : `toBeInTheDocument()`, `toBeDisabled()`… |

## Organisation

```
apps/web/
├── vitest.config.ts                      # configuration des tests
├── src/                                  # code testé
└── test/
    ├── setup.ts                          # exécuté avant chaque fichier de test
    ├── utils/                            # outils partagés (faux fetch, routeur)
    ├── fixtures/                         # données de test partagées, typées avec le contrat
    ├── components/
    │   ├── loader.test.tsx
    │   └── landing/hud.test.tsx
    └── features/auth/
        ├── auth-api.test.ts
        ├── auth-store.test.ts
        ├── login-form.test.tsx
        ├── login-page.test.tsx
        ├── login-schema.test.ts
        ├── register-page.test.tsx
        └── register-schema.test.ts
```

- `test/` reproduit l'arborescence de `src/` : le test de `src/a/b.ts` est `test/a/b.test.ts`.
- Seuls les fichiers `test/**/*.test.{ts,tsx}` sont lancés. Un test placé ailleurs est ignoré.
- Les tests importent le code avec l'alias `@/` (`@/features/auth/login-schema`), jamais avec des chemins relatifs vers `src/`.

## Configuration

`vitest.config.ts` reprend `vite.config.ts` avec `mergeConfig` (alias `@/`, plugins React et Tailwind) et ajoute :

| Option | Valeur | Pourquoi |
| ------ | ------ | -------- |
| `environment` | `jsdom` | Les composants React ont besoin d'un DOM |
| `include` | `test/**/*.test.{ts,tsx}` | Les tests ne vivent que dans `test/` |
| `setupFiles` | `test/setup.ts` | Charge jest-dom. Après chaque test : démonte les composants (`cleanup`), remet le vrai `fetch` et vide `localStorage` |
| `env` | `VITE_API_URL=http://api.test` | Adresse de l'API pendant les tests. `.test` est un domaine réservé : aucune requête ne peut partir vers un vrai serveur |

La configuration des tests est dans un fichier séparé pour ne pas la mélanger à celle de l'application dans `vite.config.ts`.

## Commandes

Depuis `apps/web` :

| Commande | Effet |
| -------- | ----- |
| `pnpm test` | Lance tous les tests une fois |
| `pnpm exec vitest` | Mode watch : relance les tests à chaque sauvegarde (à utiliser en TDD) |
| `pnpm exec vitest run test/features/auth` | Lance seulement un dossier ou un fichier |
| `pnpm check-types` | Vérifie les types, fichiers de test compris |

Depuis la racine, `pnpm test` lance aussi les tests du web.

La CI ne lance pas encore Vitest (seulement `check-types` et `build`) : lancer `pnpm test` avant de pousser.

## Outils partagés

### Simuler l'API : `test/utils/fetch.ts`

Les tests ne contactent jamais de serveur : ils remplacent `fetch` par un mock (`globalThis.fetch = vi.fn()…`), remis en place par `setup.ts` après chaque test.

| Outil | Rôle |
| ----- | ---- |
| `mockFetch(response)` | Remplace `fetch` par un mock qui renvoie `response` et le retourne pour vérifier les appels |
| `jsonResponse(status, body)` | Construit une vraie `Response` JSON (`new Response(...)`), comme celle d'un navigateur |
| `sentBody(fetchMock)` | Relit le corps JSON de la première requête envoyée |

Pour simuler une coupure réseau : `globalThis.fetch = vi.fn<typeof fetch>().mockRejectedValue(new TypeError("Failed to fetch"))`.

Le corps d'une `Response` ne se lit qu'une fois : appeler le code testé une seule fois, garder l'erreur (`.catch((e: unknown) => e)`), puis faire plusieurs `expect`.

### Afficher une page : `test/utils/render-with-router.tsx`

`renderWithRouter(<Page />, { path: "/login" })` affiche la page dans un routeur en mémoire : `<Link>` et `useNavigate()` fonctionnent. Les autres chemins n'affichent rien ; après une redirection, vérifier `router.state.location.pathname`. Le rendu du routeur est asynchrone : chercher le premier élément avec `findBy…`.

### Données : `test/fixtures/`

`tokens` (réponse de `POST /auth/login`), `supplierRegistration`, `associationRegistration` et `createdRegistration` (requêtes et réponse de `POST /registration-requests`). Elles sont typées avec les types du contrat (`satisfies`) : si le contrat change, `check-types` le signale.

## Écrire un test

```ts
import { describe, expect, it } from "vitest";

import { loginSchema } from "@/features/auth/login-schema";

describe("loginSchema", () => {
  it("rejects an empty email", () => {
    const result = loginSchema.safeParse({ email: "", password: "secret" });

    expect(result.success).toBe(false);
    expect(result.error?.issues[0]?.message).toBe("L'adresse e-mail est obligatoire.");
  });
});
```

Règles :

- Importer `describe`, `it` et `expect` depuis `vitest` (pas de mode `globals`).
- Un `it` = un comportement, décrit par une phrase en anglais.
- Trois temps dans chaque test : préparer les données, appeler le code, vérifier le résultat.
- Chaque test crée ses propres données : aucun état partagé, les tests passent dans n'importe quel ordre.
- `async` uniquement si le test fait un `await` (appel réseau simulé, par exemple).
- `toBe` pour les valeurs simples (chaîne, nombre, booléen), `toEqual` pour les objets et les tableaux.
- `it.todo("…")` marque un test à écrire. Une fonction passée à `it.todo` n'est **jamais exécutée** : remplacer par `it(…)` une fois le test écrit.
- Données de test neutres (`marie.dupont@example.org`).
- Langue : commentaires du code et descriptions de tests en anglais ; textes affichés à l'utilisateur en français.

## Workflow TDD

Chaque fonctionnalité suit le cycle Red → Green → Refactor, avec un commit par étape :

| Étape | Contenu du commit | Message |
| ----- | ----------------- | ------- |
| Red | Uniquement les tests, qui échouent | `test(web): RED <description>` |
| Green | Uniquement le code minimal qui les fait passer, **sans modifier les tests** | `feat(web): GREEN <description>` |
| Refactor | Nettoyage sans changer le comportement, tests toujours verts | `refactor(web): REFACTOR <description>` |

Ne pas ouvrir de PR sur un commit Red : `check-types` échoue tant que le code testé n'existe pas.

Une fonctionnalité découpée en plusieurs étapes utilise des branches empilées : chaque branche part de la précédente (`test/auth-api` → `test/auth-store` → `test/login-page` → `test/register-schema` → `test/register-page`), et la PR de la dernière contient tout.

## Ce qui est testé

### `loginSchema` — `src/features/auth/login-schema.ts`

Validation du formulaire de connexion, alignée sur `LoginRequest` du contrat (`openapi.yaml`).

| Cas | Résultat attendu |
| --- | ---------------- |
| E-mail et mot de passe valides | Accepté |
| E-mail vide | Refusé : « L'adresse e-mail est obligatoire. » |
| E-mail sans `@` | Refusé : « L'adresse e-mail est invalide. » |
| Mot de passe vide | Refusé : « Le mot de passe est obligatoire. » |
| Espaces autour de l'e-mail | Retirés |
| Mot de passe court (`abc`) | Accepté : la longueur minimale de 8 caractères ne s'applique qu'à l'inscription (`AccountCreate`) |

### `LoginForm` — `src/features/auth/login-form.tsx`

Formulaire de connexion (TanStack Form) validé par `loginSchema`. Il reçoit une prop `onSubmit` ; l'appel à l'API est fait par `LoginPage`.

| Cas | Résultat attendu |
| --- | ---------------- |
| Affichage | Champs « E-mail » (`type="email"`) et « Mot de passe » (`type="password"`), bouton « Se connecter » |
| Envoi du formulaire vide | Les deux messages d'erreur s'affichent, le champ e-mail passe en `aria-invalid`, `onSubmit` n'est pas appelé |
| E-mail sans `@` | « L'adresse e-mail est invalide. » s'affiche |
| Formulaire valide | `onSubmit` reçoit l'e-mail sans les espaces autour et le mot de passe |
| Envoi en cours | Le bouton devient « Connexion… » et est désactivé tant que la promesse de `onSubmit` n'est pas terminée |

### `login` — `src/features/auth/auth-api.ts` et `src/lib/api-client.ts`

`POST /auth/login` à travers le client HTTP, avec un faux `fetch`.

| Cas | Résultat attendu |
| --- | ---------------- |
| Requête | `POST http://api.test/auth/login`, en-tête `Content-Type: application/json`, identifiants en JSON |
| 200 | Renvoie les tokens (`AuthTokens`) |
| 401, 403, 422 | Lève une `ApiError` avec `status`, `code`, `message` et `details` du format `Error` du contrat |
| JSON hors contrat (`{"detail": …}`) ou corps non JSON | `ApiError` avec `code: null` et le message de repli « Une erreur inattendue est survenue. Réessayez plus tard. » |
| Serveur injoignable | Lève une `NetworkError` (« Impossible de joindre le serveur. Vérifiez votre connexion. »), l'erreur d'origine dans `cause` |

### `createRegistrationRequest` — `src/features/auth/auth-api.ts`

| Cas | Résultat attendu |
| --- | ---------------- |
| Requête | `POST http://api.test/registration-requests` avec le corps `RegistrationRequestCreate`, renvoie la demande créée |

### `logout` — `src/features/auth/auth-api.ts`

| Cas | Résultat attendu |
| --- | ---------------- |
| Requête | `POST http://api.test/auth/logout`, en-tête `Authorization: Bearer <access_token>`, corps `{ refresh_token }` ; la réponse 204 n'a pas de corps |

### `useAuthStore` — `src/features/auth/auth-store.ts`

| Cas | Résultat attendu |
| --- | ---------------- |
| `setTokens` | Garde les tokens, aussi dans `localStorage` (clé `gaspirator-auth`) : la session survit à un rechargement |
| `clearTokens` | Oublie les tokens |

### `LoginPage` — `src/features/auth/login-page.tsx`

| Cas | Résultat attendu |
| --- | ---------------- |
| `?role=supplier` | Affiche « Espace fournisseur » |
| Lien d'inscription | « Créer un compte » mène à `/register` avec le même `role` |
| Connexion réussie | Tokens enregistrés, redirection vers `/` |
| 401 | « E-mail ou mot de passe incorrect. » (notre texte, pas celui du serveur) |
| 403 | Message du serveur (demande en attente ou refusée) |
| Serveur injoignable | Message de `NetworkError` |

### `registerSchema` — `src/features/auth/register-schema.ts`

Validation de l'inscription, alignée sur `RegistrationRequestCreate`. Sa sortie est le corps envoyé à l'API.

| Cas | Résultat attendu |
| --- | ---------------- |
| Fournisseur valide | `{ supplier, account }` (`SupplierCreate`), sans la confirmation du mot de passe |
| Association valide | `{ association, account }` (`AssociationCreate`), sans type d'établissement |
| Type d'organisation absent | « Choisissez le type de votre organisation. » |
| Fournisseur avec un n° RNA | « Le SIRET doit contenir 14 chiffres. » |
| Association avec un SIRET | « Le n° RNA doit commencer par W, suivi de 9 chiffres. » |
| SIRET tapé avec des espaces | Espaces retirés |
| Fournisseur sans type d'établissement | « Choisissez le type d'établissement. » |
| Code postal de 4 chiffres | « Le code postal doit contenir 5 chiffres. » |
| Téléphone trop court | « Le numéro de téléphone doit contenir au moins 10 caractères. » |
| Prénom vide, e-mail mal formé | Messages d'erreur sur le champ concerné |
| Mot de passe de moins de 8 caractères | « Le mot de passe doit contenir au moins 8 caractères. » |
| Confirmation différente | « Les mots de passe ne correspondent pas. » |
| Espaces autour des textes | Retirés |

### `RegisterPage` — `src/features/auth/register-page.tsx`

Inscription en deux étapes : le compte, puis l'organisation.

| Cas | Résultat attendu |
| --- | ---------------- |
| Arrivée | Étape 1 « Votre compte », l'organisation n'est pas affichée |
| « Continuer » avec un compte invalide | Erreurs affichées, on reste à l'étape 1 |
| « Continuer » avec un compte valide | Étape 2 « Votre organisation » |
| « Retour » | Retour à l'étape 1, valeurs conservées |
| `?role=association` | « Association » cochée, champ « N° RNA », pas de type d'établissement |
| `?role=supplier` | Champs « SIRET » et « Type d'établissement » |
| Lien de connexion | « Se connecter » mène à `/login` avec le même `role` |
| Étape 2 vide | Erreurs affichées, aucune requête |
| Fournisseur valide | `{ supplier, account }` envoyé, écran « Demande envoyée » avec le nom saisi |
| Association valide | `{ association, account }` envoyé, écran « Demande envoyée » avec le nom saisi (pas celui de la réponse : le mock renvoie toujours le même exemple) |
| 409 | Message du serveur (e-mail, ou SIRET / n° RNA déjà utilisé) |
| 422 | « Certaines informations ont été refusées : » suivi des champs refusés, avec leur libellé (« E-mail : adresse e-mail invalide ») |
| Serveur injoignable | Message de `NetworkError` |

### `redirectIfLoggedIn` — `src/features/auth/auth-guard.ts`

`beforeLoad` des routes `/login` et `/register`.

| Cas | Résultat attendu |
| --- | ---------------- |
| Visiteur | La page s'ouvre |
| Utilisateur connecté | Redirection vers `/` |

### `Hud` — `src/components/landing/hud.tsx`

| Cas | Résultat attendu |
| --- | ---------------- |
| Bouton « Rejoindre » | Mène à `/register` |
| Connecté | « Se déconnecter » remplace « Rejoindre » |
| « Se déconnecter » | `POST /auth/logout`, tokens oubliés, « Rejoindre » revient |
| Déconnexion refusée par l'API (token expiré) | La session locale se termine quand même |
| Double toucher sur « Se déconnecter » | Une seule requête |

### `Loader` — `src/components/loader.tsx`

| Cas | Résultat attendu |
| --- | ---------------- |
| Affichage | Élément `role="status"` nommé « Loading… », annoncé par les lecteurs d'écran |
