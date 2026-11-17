# Gaspirator

A Too Good To Go for donations: food **suppliers** (canteens, hospitals, supermarkets…) publish their surplus as lots, and **charities** book them and come to collect them.

Links: [GitHub Project](https://github.com/users/Nathanmar/projects/3) · [Notion](https://app.notion.com/p/Projet-409243b4cee0809bb06ee2814d7a2789)

## Stack

| Part                | Tech                                                                      | Path          |
| ------------------- | ------------------------------------------------------------------------- | ------------- |
| Web front end       | TanStack Router + Vite, Tailwind, daisyUI, Zustand, TanStack Form, GSAP   | `apps/web`    |
| Mobile app          | Expo (React Native), Expo Router                                          | `apps/mobile` |
| Back end            | Python FastAPI, Pydantic, JWT auth, Ruff, pytest, uv                      | `apps/server` |
| Database            | PostgreSQL 18                                                             | —             |
| Shared env / config | TypeScript packages                                                       | `packages/*`  |
| Tooling             | pnpm workspaces, Turborepo, Docker Compose, Dev Container, GitHub Actions | `.`           |

The project was generated with Better Fullstack; `bts.jsonc` describes the stack.

## Prerequisites

| Tool                                                      | Version                       | Notes                                                                 |
| --------------------------------------------------------- | ----------------------------- | --------------------------------------------------------------------- |
| Node.js                                                   | 24 (LTS)                      | Version of the CI and of the web image                                |
| [pnpm](https://pnpm.io)                                   | 10.19.0                       | Pinned in `package.json` (`packageManager`)                           |
| Python                                                    | 3.12 (3.11 minimum)           | Version of the API image, minimum set in `apps/server/pyproject.toml` |
| [uv](https://docs.astral.sh/uv/)                          | 0.9.17 or later               | Version of the API image                                              |
| [Docker](https://docs.docker.com/get-started/get-docker/) | Compose v2 (`docker compose`) | PostgreSQL, Prism and Mailpit, or the whole stack                     |
| [Expo Go](https://expo.dev/go)                            | SDK 58                        | Optional: runs the mobile app on a phone                              |

## Setup

```sh
pnpm install
pnpm setup:server
```

Copy `apps/server/.env.example` to `apps/server/.env` and set `SECRET_KEY` and `DATABASE_URL`.

A registration request sent without address gets the address of its SIRET or RNA number from the Sirene base, through the [API Recherche d'entreprises](https://recherche-entreprises.api.gouv.fr) (free, no key; associations with an RNA number only are not in it and must give their address). The address is then geocoded with the [Géoplateforme](https://data.geopf.fr/geocodage) of the IGN (free, no key). The API needs outbound internet access; override the services with `COMPANY_REGISTRY_URL`, `GEOCODING_URL` and `COMPANY_REGISTRY_TIMEOUT_SECONDS` (default 10 s), `GEOCODING_TIMEOUT_SECONDS` (default 5 s). The tests use fakes and never call them.

Copy `apps/web/.env.example` to `apps/web/.env`. `VITE_API_URL` is the base URL of the API contract: `http://127.0.0.1:4010` is Prism, either the mock (`pnpm mock`) or the validation proxy in front of the API (see [Web app on the real API](#web-app-on-the-real-api)). The web app refuses to start without it.

## Local development

```sh
pnpm dev
```

This starts the web app and the API together; if one stops, the other stops too. To run them separately:

| Command             | What it does                                 |
| ------------------- | -------------------------------------------- |
| `pnpm dev:web`      | Web app only                                 |
| `pnpm dev:server`   | API only (FastAPI with auto-reload)          |
| `pnpm build`        | Build the web app                            |
| `pnpm test`         | Web tests (Vitest)                           |
| `pnpm mock`         | Mock API from `openapi.yaml` (port 4010)     |
| `pnpm test:server`  | API tests (pytest)                           |
| `pnpm check:server` | Lint the API (Ruff)                          |

### Web app on the real API

```sh
docker compose up -d db app prism
pnpm dev:web
```

The web app (`http://localhost:5173`) talks to the API through the Prism validation proxy on `http://127.0.0.1:4010`, the default `VITE_API_URL`: Prism answers CORS for the dev server and checks every exchange against `openapi.yaml`. Stop `pnpm mock` first, both use port 4010.

A new account stays `pending` until an admin approves it. Until the admin routes exist, approve one in the local database: like the approve route, this creates the association from the request (its address and geocoded position) and links it to the request and the user.

```sh
docker compose exec -T db psql -U postgres -d gaspirator -v email=marie.dupont@example.org <<'SQL'
begin;
with request as (
  select r.* from registration_requests r join users u on u.id = r.user_id
  where lower(u.email) = lower(:'email')
), created as (
  insert into associations (name, legal_id, street, postal_code, city, latitude, longitude, contact_phone)
  select organization_name, legal_id, street, postal_code, city, latitude, longitude, contact_phone from request
  returning id
)
update registration_requests
set status = 'approved', association_id = (select id from created), decided_at = now()
where id = (select id from request);
update users u set association_id = r.association_id
from registration_requests r where r.user_id = u.id and lower(u.email) = lower(:'email');
commit;
SQL
```

For a supplier, insert into `suppliers` (adding `supplier_type` to both column lists) and set `supplier_id` instead of `association_id`. Requests sent before the address lookup may have no position: send them again.

## Connections

- **Web app**: `http://localhost:5173`
- **API**: `http://localhost:8000`, interactive docs at `http://localhost:8000/docs`
- **Mailpit** (e-mails caught in development): `http://localhost:8025`

## Docker

```sh
docker compose up --build
```

Runs the web app on `http://localhost:3001` and the API on `http://localhost:8000`. Create `apps/web/.env` and `apps/server/.env` first.

### Development data

In compose, the API starts with `SEED_DEV_DATA=true`: after the migrations, `python -m app.seed` fills an empty database with 10 suppliers and 5 associations around Paris, 30 lots (available, partly reserved, reserved, collected, expired) with their reservations, and 2 pending registration requests. It runs once: as soon as the seed admin exists, it is skipped. Lot dates are relative to the day of the seed; to start over, drop the volume with `docker compose down -v`.

Every account uses the password `gaspirator-dev`: `admin@example.org` (admin), the managers of the suppliers (e.g. `cantine.voltaire@example.org`) and of the associations (e.g. `solidarite.paris-est@example.org`); the full list is in `apps/server/src/app/seed.py`. The production image never seeds: `SEED_DEV_DATA` is false by default.

PostgreSQL 18 runs in the `db` service on `localhost:5432` (user `postgres`, password `postgres`, database `gaspirator`; override with `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`). Data is kept in the `db-data` volume. In compose, the API gets `DATABASE_URL` pointing to `db`. To run only the database for local dev:

```sh
docker compose up -d db
```

### E-mails in development (Mailpit)

The contract notifies the applicant by e-mail when an admin approves or rejects a registration request. In development, e-mails go to [Mailpit](https://mailpit.axllent.org/), a fake SMTP server that catches every message and never delivers it to the real address:

```sh
docker compose up -d mailpit
```

| What        | Address                                                   |
| ----------- | --------------------------------------------------------- |
| Web UI      | `http://localhost:8025` (inbox of every e-mail sent)      |
| SMTP        | `localhost:1025` from the host, `mailpit:1025` in compose |
| Credentials | none (no authentication, no TLS)                          |

Nothing is stored: the inbox is emptied when the container is recreated.

## Versioning

Releases follow [Semantic Versioning](https://semver.org). When `develop` is merged into `main`, [git-cliff](https://git-cliff.org) (`cliff.toml`) computes the next version from the [Conventional Commits](https://www.conventionalcommits.org) since the last release:

| Commits since the last release          | Bump  | Example           |
| --------------------------------------- | ----- | ----------------- |
| `feat!:` or a `BREAKING CHANGE:` footer | major | `1.4.2` → `2.0.0` |
| `feat:`                                 | minor | `1.4.2` → `1.5.0` |
| `fix:` and the other types              | patch | `1.4.2` → `1.4.3` |

The first release is `v0.1.0`. Each release creates the `vX.Y.Z` tag, a GitHub Release with the changelog, and the Docker images `X.Y.Z`, `X.Y`, `sha-<commit>` and `latest` on GHCR. Preview the changelog with `pnpm changelog`; the commit rules are in [CONTRIBUTING.md](CONTRIBUTING.md#committing-changes).

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
