# Gaspirator

Plateforme de mise en relation entre des **fournisseurs** de denrées alimentaires (cantines, hôpitaux, supermarchés…) et des **associations**, pour donner les surplus au lieu de les jeter.

- **Front web** : fournisseurs et back-office admin
- **App mobile** : associations
- **Back** + **base de données**

Liens : [GitHub Project](https://github.com/users/Nathanmar/projects/3) · [Notion](https://app.notion.com/p/Projet-409243b4cee0809bb06ee2814d7a2789)

## Applications and resources

- **aspnet-mvc** (dotnet, backend): `apps/server`; part `backend:dotnet:aspnet-mvc`
- **postgres** (universal, database): `packages/db`; part `database:universal:postgres`
- **native-bare** (react-native, mobile): `apps/native`; part `mobile:react-native:native-bare`
- **eslint** (universal, codeQuality): `.`; part `codequality:universal:eslint`
- **prettier** (universal, codeQuality): `.`; part `codequality:universal:prettier`
- **husky** (universal, gitHooks): `.`; part `githooks:universal:husky`
- **github-actions** (universal, continuousIntegration): `.`; part `continuousintegration:universal:github-actions`
- **tanstack-start** (typescript, frontend): `apps/web`; part `frontend:typescript:tanstack-start`

## Setup

Install the SDKs for the selected languages before preparing dependencies. SwiftUI needs macOS, Xcode, and XcodeGen; Kotlin Android apps need a JDK and Android SDK; Flutter needs the Flutter SDK. Rust web apps also need the WebAssembly target and Trunk or Dioxus CLI.

JavaScript dependencies are installed at the workspace root. Each native application keeps its own toolchain. Native package scripts require `bash` on PATH; install Git Bash on Windows. Run the shell commands below in Bash.

If dependencies were not prepared during creation, run:

```sh
pnpm install
(cd apps/server && dotnet restore)
```

Copy each application's `.env.example` to `.env` when present and configure database credentials before starting database-backed services.

## Local development

Start the selected web applications and backend services together:

```sh
pnpm run dev
```

The supervisor stops the other services when one exits. Native mobile applications run separately so you can choose a simulator or device. Open Kotlin applications in Android Studio.

### .NET ASP.NET Core MVC

Run independently from the project root:

```sh
cd apps/server && dotnet run
```

## Connections

- **.NET ASP.NET Core MVC** (default client connection): `http://localhost:5000`, health endpoint `http://localhost:5000/`.

Cross-language clients communicate over HTTP. Framework-specific clients such as tRPC are used only with compatible backends. Generated connection files identify the default backend; additional services retain their own paths and endpoints.

## Backlog (MoSCoW)

| Issue                                                    | User story                                               | Priorité | Client                   |
| -------------------------------------------------------- | -------------------------------------------------------- | -------- | ------------------------ |
| [#1](https://github.com/Nathanmar/gaspirator/issues/1)   | Inscription et connexion via une demande                 | Must     | web, mobile, back-office |
| [#2](https://github.com/Nathanmar/gaspirator/issues/2)   | Publier un lot                                           | Must     | web                      |
| [#3](https://github.com/Nathanmar/gaspirator/issues/3)   | Rechercher des fournisseurs autour de moi                | Must     | mobile                   |
| [#4](https://github.com/Nathanmar/gaspirator/issues/4)   | Réserver un lot                                          | Must     | mobile                   |
| [#5](https://github.com/Nathanmar/gaspirator/issues/5)   | Confirmer la réception d'un lot                          | Must     | web                      |
| [#6](https://github.com/Nathanmar/gaspirator/issues/6)   | Gérer mon profil                                         | Should   | web, mobile              |
| [#7](https://github.com/Nathanmar/gaspirator/issues/7)   | Gérer les rôles et les droits (RBAC)                     | Should   | web, mobile, back-office |
| [#8](https://github.com/Nathanmar/gaspirator/issues/8)   | Gérer les fournisseurs et les associations (back-office) | Should   | back-office              |
| [#9](https://github.com/Nathanmar/gaspirator/issues/9)   | Consulter l'historique des lots et des réservations      | Should   | web, mobile              |
| [#10](https://github.com/Nathanmar/gaspirator/issues/10) | Annuler une réservation                                  | Should   | mobile                   |
| [#11](https://github.com/Nathanmar/gaspirator/issues/11) | Messagerie                                               | Could    | web, mobile              |
| [#12](https://github.com/Nathanmar/gaspirator/issues/12) | Filtrer les lots                                         | Could    | mobile                   |
| [#13](https://github.com/Nathanmar/gaspirator/issues/13) | Exporter un récapitulatif des lots                       | Could    | web                      |
| /                                                        | Internationalisation                                     | Wont     | /                        |
| /                                                        | Paiement                                                 | Wont     | /                        |
| /                                                        | Produits non-alimentaires                                | Wont     | /                        |

## Carte des dépendances

Chaque endpoint est mis en face des écrans qui l'appellent. Un endpoint peut servir à plusieurs écrans, et un écran peut appeler plusieurs endpoints. Les écrans du back-office (BO) font partie du front web.

| Endpoint                                         | Écrans                                                                                         | US           |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------- | ------------ |
| `POST /registration-requests`                    | Web · Demande d'inscription<br>Mobile · Demande d'inscription                                  | US-01        |
| `GET /admin/registration-requests`               | BO · Demandes d'inscription                                                                    | US-01        |
| `POST /admin/registration-requests/{id}/approve` | BO · Demandes d'inscription                                                                    | US-01        |
| `POST /admin/registration-requests/{id}/reject`  | BO · Demandes d'inscription                                                                    | US-01        |
| `POST /auth/login`                               | Web · Connexion<br>Mobile · Connexion                                                          | US-01        |
| `POST /auth/refresh`                             | _Aucun écran_ (voir plus bas)                                                                  | US-01        |
| `POST /auth/logout`                              | Web · Profil<br>Mobile · Profil                                                                | US-01        |
| `GET /me`                                        | Web · Connexion<br>Web · Profil<br>Mobile · Démarrage<br>Mobile · Connexion<br>Mobile · Profil | US-01, US-06 |
| `POST /lots`                                     | Web · Publier un lot                                                                           | US-02        |
| `GET /suppliers`                                 | Mobile · Recherche de fournisseurs                                                             | US-03, US-12 |
| `GET /suppliers/{id}`                            | Mobile · Fiche fournisseur                                                                     | US-03        |
| `GET /suppliers/{id}/lots`                       | Mobile · Fiche fournisseur                                                                     | US-03, US-12 |
| `GET /lots/{id}`                                 | Mobile · Fiche lot<br>Web · Détail d'un lot                                                    | US-03, US-04 |
| `POST /lots/{id}/reservations`                   | Mobile · Réserver un lot                                                                       | US-04        |
| `GET /me/reservations`                           | Mobile · Mes réservations<br>Mobile · Historique                                               | US-04, US-09 |
| `GET /reservations/{id}`                         | Mobile · Code de collecte                                                                      | US-04        |
| `GET /me/lots`                                   | Web · Mes lots<br>Web · Historique                                                             | US-04, US-09 |
| `GET /lots/{id}/reservations`                    | Web · Détail d'un lot<br>Web · Historique                                                      | US-04, US-09 |
| `POST /reservations/{id}/confirm`                | Web · Saisie du code de collecte                                                               | US-05        |
| `PATCH /me`                                      | Web · Profil<br>Mobile · Profil                                                                | US-06        |
| `PUT /me/password`                               | Web · Profil<br>Mobile · Profil                                                                | US-06        |
| `GET /me/organization`                           | Web · Profil<br>Mobile · Profil                                                                | US-06        |
| `PATCH /me/organization`                         | Web · Profil<br>Mobile · Profil                                                                | US-06        |
| `GET /me/organization/members`                   | Web · Membres<br>Mobile · Membres                                                              | US-07        |
| `POST /me/organization/invitations`              | Web · Membres<br>Mobile · Membres                                                              | US-07        |
| `POST /invitations/{token}/accept`               | Web · Acceptation d'une invitation<br>Mobile · Acceptation d'une invitation                    | US-07        |
| `PATCH /me/organization/members/{userId}`        | Web · Membres<br>Mobile · Membres                                                              | US-07        |
| `DELETE /me/organization/members/{userId}`       | Web · Membres<br>Mobile · Membres                                                              | US-07        |
| `GET /admin/organizations`                       | BO · Organisations                                                                             | US-08        |
| `GET /admin/organizations/{id}`                  | BO · Fiche organisation                                                                        | US-08        |
| `PATCH /admin/organizations/{id}`                | BO · Fiche organisation                                                                        | US-08        |
| `POST /admin/organizations/{id}/suspend`         | BO · Fiche organisation                                                                        | US-08        |
| `POST /admin/organizations/{id}/reactivate`      | BO · Fiche organisation                                                                        | US-08        |
| `GET /admin/lots`                                | BO · Lots                                                                                      | US-08        |
| `POST /admin/lots/{id}/withdraw`                 | BO · Lots                                                                                      | US-08        |
| `GET /admin/reservations`                        | BO · Réservations                                                                              | US-08        |
| `POST /reservations/{id}/cancel`                 | Mobile · Mes réservations                                                                      | US-10        |
| `GET /reservations/{id}/messages`                | Web · Messagerie<br>Mobile · Messagerie                                                        | US-11        |
| `POST /reservations/{id}/messages`               | Web · Messagerie<br>Mobile · Messagerie                                                        | US-11        |
| `GET /reservations/{id}/messages/stream`         | Web · Messagerie<br>Mobile · Messagerie                                                        | US-11        |
| `POST /me/exports`                               | Web · Export                                                                                   | US-13        |
| `GET /me/exports/{id}`                           | Web · Export                                                                                   | US-13        |
| `GET /me/exports/{id}/file`                      | Web · Export                                                                                   | US-13        |

#### Endpoint sans écran

- **`POST /auth/refresh`** : aucun écran ne l'appelle directement. Quand le token d'accès expire, le client HTTP du web et du mobile appelle cet endpoint automatiquement, puis rejoue la requête qui a échoué. L'utilisateur ne voit rien.

#### Écrans sans endpoint

- **Web · Demande envoyée** et **Mobile · Demande envoyée** : page de confirmation affichée après l'envoi de la demande d'inscription. Elle réutilise la réponse de `POST /registration-requests`. L'organisation n'a pas encore de compte, il n'y a donc rien d'autre à charger.
- **Mobile · Filtres** (US-12) : l'écran construit seulement les paramètres de recherche, puis l'écran « Recherche de fournisseurs » rappelle `GET /suppliers` avec ces paramètres. Les choix proposés (catégories, allergènes, types de fournisseur) sont des listes fixées dans le contrat, pas des données à charger.
