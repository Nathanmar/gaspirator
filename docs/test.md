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
├── src/
│   ├── components/loader.tsx
│   └── features/auth/
│       ├── login-form.tsx
│       └── login-schema.ts
└── test/
    ├── setup.ts                          # exécuté avant chaque fichier de test
    ├── components/loader.test.tsx
    └── features/auth/
        ├── login-form.test.tsx
        └── login-schema.test.ts
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
| `setupFiles` | `test/setup.ts` | Charge jest-dom et démonte les composants après chaque test (`cleanup`) |

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

Formulaire de connexion (TanStack Form) validé par `loginSchema`. Il reçoit une prop `onSubmit` et ne fait encore aucun appel à l'API.

| Cas | Résultat attendu |
| --- | ---------------- |
| Affichage | Champs « E-mail » (`type="email"`) et « Mot de passe » (`type="password"`), bouton « Se connecter » |
| Envoi du formulaire vide | Les deux messages d'erreur s'affichent, le champ e-mail passe en `aria-invalid`, `onSubmit` n'est pas appelé |
| E-mail sans `@` | « L'adresse e-mail est invalide. » s'affiche |
| Formulaire valide | `onSubmit` reçoit l'e-mail sans les espaces autour et le mot de passe |

### `Loader` — `src/components/loader.tsx`

| Cas | Résultat attendu |
| --- | ---------------- |
| Affichage | Élément `role="status"` nommé « Loading… », annoncé par les lecteurs d'écran |
