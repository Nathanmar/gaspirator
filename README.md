# Gaspirator

A platform that connects food **suppliers** (canteens, hospitals, supermarkets…) with **charities**, so surplus food is donated instead of thrown away.

- **Web front end**: suppliers and admin back office
- **Mobile app**: charities
- **Back end** + **database**

Links: [GitHub Project](https://github.com/users/Nathanmar/projects/3) · [Notion](https://app.notion.com/p/Projet-409243b4cee0809bb06ee2814d7a2789)

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

| Issue                                                    | User story                                   | Priority | Client                   |
| -------------------------------------------------------- | -------------------------------------------- | -------- | ------------------------ |
| [#1](https://github.com/Nathanmar/gaspirator/issues/1)   | Sign up and log in via a request             | Must     | web, mobile, back-office |
| [#2](https://github.com/Nathanmar/gaspirator/issues/2)   | Publish a donation                           | Must     | web                      |
| [#3](https://github.com/Nathanmar/gaspirator/issues/3)   | Search for suppliers near me                 | Must     | mobile                   |
| [#4](https://github.com/Nathanmar/gaspirator/issues/4)   | Reserve a donation                           | Must     | mobile                   |
| [#5](https://github.com/Nathanmar/gaspirator/issues/5)   | Confirm receipt of a donation                | Must     | web                      |
| [#6](https://github.com/Nathanmar/gaspirator/issues/6)   | Manage my profile                            | Should   | web, mobile              |
| [#7](https://github.com/Nathanmar/gaspirator/issues/7)   | Manage roles and permissions (RBAC)          | Should   | web, mobile, back-office |
| [#8](https://github.com/Nathanmar/gaspirator/issues/8)   | Manage suppliers and charities (back office) | Should   | back-office              |
| [#9](https://github.com/Nathanmar/gaspirator/issues/9)   | View donation and reservation history        | Should   | web, mobile              |
| [#10](https://github.com/Nathanmar/gaspirator/issues/10) | Cancel a reservation                         | Should   | mobile                   |
| [#11](https://github.com/Nathanmar/gaspirator/issues/11) | Messaging                                    | Could    | web, mobile              |
| [#12](https://github.com/Nathanmar/gaspirator/issues/12) | Filter donations                             | Could    | mobile                   |
| [#13](https://github.com/Nathanmar/gaspirator/issues/13) | Export a donation summary                    | Could    | web                      |
| /                                                        | Internationalization                         | Won't    | /                        |
| /                                                        | Payment                                      | Won't    | /                        |
| /                                                        | Non-food products                            | Won't    | /                        |

## Dependency map

Each endpoint is listed next to the screens that call it. An endpoint can serve several screens, and a screen can call several endpoints. Back-office (BO) screens are part of the web front end.

| Endpoint                                         | Screens                                                                                | US           |
| ------------------------------------------------ | -------------------------------------------------------------------------------------- | ------------ |
| `POST /registration-requests`                    | Web · Registration request<br>Mobile · Registration request                            | US-01        |
| `GET /admin/registration-requests`               | BO · Registration requests                                                             | US-01        |
| `POST /admin/registration-requests/{id}/approve` | BO · Registration requests                                                             | US-01        |
| `POST /admin/registration-requests/{id}/reject`  | BO · Registration requests                                                             | US-01        |
| `POST /auth/login`                               | Web · Login<br>Mobile · Login                                                          | US-01        |
| `POST /auth/refresh`                             | _No screen_ (see below)                                                                | US-01        |
| `POST /auth/logout`                              | Web · Profile<br>Mobile · Profile                                                      | US-01        |
| `GET /me`                                        | Web · Login<br>Web · Profile<br>Mobile · Startup<br>Mobile · Login<br>Mobile · Profile | US-01, US-06 |
| `POST /donations`                                | Web · Publish a donation                                                               | US-02        |
| `GET /suppliers`                                 | Mobile · Supplier search                                                               | US-03, US-12 |
| `GET /suppliers/{id}`                            | Mobile · Supplier page                                                                 | US-03        |
| `GET /suppliers/{id}/donations`                  | Mobile · Supplier page                                                                 | US-03, US-12 |
| `GET /donations/{id}`                            | Mobile · Donation page<br>Web · Donation details                                       | US-03, US-04 |
| `POST /donations/{id}/reservations`              | Mobile · Reserve a donation                                                            | US-04        |
| `GET /me/reservations`                           | Mobile · My reservations<br>Mobile · History                                           | US-04, US-09 |
| `GET /reservations/{id}`                         | Mobile · Pickup code                                                                   | US-04        |
| `GET /me/donations`                              | Web · My donations<br>Web · History                                                    | US-04, US-09 |
| `GET /donations/{id}/reservations`               | Web · Donation details<br>Web · History                                                | US-04, US-09 |
| `POST /reservations/{id}/confirm`                | Web · Pickup code entry                                                                | US-05        |
| `PATCH /me`                                      | Web · Profile<br>Mobile · Profile                                                      | US-06        |
| `PUT /me/password`                               | Web · Profile<br>Mobile · Profile                                                      | US-06        |
| `GET /me/organization`                           | Web · Profile<br>Mobile · Profile                                                      | US-06        |
| `PATCH /me/organization`                         | Web · Profile<br>Mobile · Profile                                                      | US-06        |
| `GET /me/organization/members`                   | Web · Members<br>Mobile · Members                                                      | US-07        |
| `POST /me/organization/invitations`              | Web · Members<br>Mobile · Members                                                      | US-07        |
| `POST /invitations/{token}/accept`               | Web · Accept an invitation<br>Mobile · Accept an invitation                            | US-07        |
| `PATCH /me/organization/members/{userId}`        | Web · Members<br>Mobile · Members                                                      | US-07        |
| `DELETE /me/organization/members/{userId}`       | Web · Members<br>Mobile · Members                                                      | US-07        |
| `GET /admin/organizations`                       | BO · Organizations                                                                     | US-08        |
| `GET /admin/organizations/{id}`                  | BO · Organization page                                                                 | US-08        |
| `PATCH /admin/organizations/{id}`                | BO · Organization page                                                                 | US-08        |
| `POST /admin/organizations/{id}/suspend`         | BO · Organization page                                                                 | US-08        |
| `POST /admin/organizations/{id}/reactivate`      | BO · Organization page                                                                 | US-08        |
| `GET /admin/donations`                           | BO · Donations                                                                         | US-08        |
| `POST /admin/donations/{id}/withdraw`            | BO · Donations                                                                         | US-08        |
| `GET /admin/reservations`                        | BO · Reservations                                                                      | US-08        |
| `POST /reservations/{id}/cancel`                 | Mobile · My reservations                                                               | US-10        |
| `GET /reservations/{id}/messages`                | Web · Messaging<br>Mobile · Messaging                                                  | US-11        |
| `POST /reservations/{id}/messages`               | Web · Messaging<br>Mobile · Messaging                                                  | US-11        |
| `GET /reservations/{id}/messages/stream`         | Web · Messaging<br>Mobile · Messaging                                                  | US-11        |
| `POST /me/exports`                               | Web · Export                                                                           | US-13        |
| `GET /me/exports/{id}`                           | Web · Export                                                                           | US-13        |
| `GET /me/exports/{id}/file`                      | Web · Export                                                                           | US-13        |

#### Endpoint without a screen

- **`POST /auth/refresh`**: no screen calls it directly. When the access token expires, the web and mobile HTTP clients call this endpoint automatically, then replay the request that failed. The user sees nothing.

#### Screens without an endpoint

- **Web · Request sent** and **Mobile · Request sent**: confirmation page shown after the registration request is submitted. It reuses the response from `POST /registration-requests`. The organization doesn't have an account yet, so there is nothing else to load.
- **Mobile · Filters** (US-12): the screen only builds the search parameters, then the "Supplier search" screen calls `GET /suppliers` again with those parameters. The available options (categories, allergens, supplier types) are fixed lists defined in the contract, not data to load.
