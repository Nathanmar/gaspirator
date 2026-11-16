# CI

Pipeline : [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

Déclenchement : `push` et `pull_request` sur `main` / `master`.

## Jobs

Les jobs tournent en parallèle, sur Node 24.

| Job | Rôle | Bloquant |
|-----|------|----------|
| `ci` | `pnpm install --frozen-lockfile`, `check-types`, `build` (turbo) | Oui |
| `server` | `uv sync --frozen --extra dev`, `ruff check`, `pytest` (FastAPI) | Oui |
| `dependency-review` | Sur les PR uniquement : signale les dépendances ajoutées ou modifiées qui ont des CVE connues | Non |
| `audit-web` | `pnpm audit` sur tout le lockfile pnpm (TanStack Router/Form, Vite, etc.) | Non |
| `audit-python` | `pip-audit` sur les dépendances runtime du serveur FastAPI (`uv.lock`) | Non |
| `image` (matrice `web`, `server`) | Build Docker, scan Trivy | Build : oui · Scan : non |

### Analyse CVE des dépendances

- **Web** : `pnpm audit` lit `pnpm-lock.yaml` et interroge la base GitHub Advisory.
- **PR** : `actions/dependency-review-action` compare les dépendances de la PR à celles de la branche cible. Il faut que le dependency graph soit activé sur le repo (c'est le cas par défaut sur un repo public).
- **Python** : `uv export --frozen --no-dev` génère un `requirements.txt` épinglé à partir de `uv.lock`, puis `pip-audit` (base PyPI / OSV) l'analyse. Seules les dépendances de prod sont auditées, les extras `dev` ne le sont pas.

Ces deux étapes, comme `dependency-review`, sont en `continue-on-error: true` : les vulnérabilités s'affichent dans les logs, mais le job reste vert, **quelle que soit la sévérité**.

### Build et scan des images

| Image | Contexte | Dockerfile |
|-------|----------|------------|
| `web` | `.` | `apps/web/Dockerfile.vite` |
| `server` | `apps/server` | `apps/server/Dockerfile` |

Pour chaque image :

1. Build avec Buildx (cache GitHub Actions, un scope par image), export en tarball local au runner, sans push vers un registry ni artefact.
2. Scan Trivy du tarball (OS + librairies), `exit-code: 0` donc jamais bloquant. Le rapport est visible dans le résumé du job.

### Pinning de Trivy

`aquasecurity/trivy-action` est épinglé en `0.35.0` et Trivy en `v0.76.2` (release immuable). En mars 2026, une attaque supply chain (CVE-2026-33634) a réécrit presque tous les tags de `trivy-action` et publié un binaire Trivy `v0.69.4` malveillant. `0.35.0` est le seul tag qui n'a pas été touché (release immuable). Ne pas passer sur un tag flottant sans avoir vérifié avant. Pour aller plus loin, épingler sur un SHA de commit.

## Lancer les vérifications en local

```bash
pnpm install --frozen-lockfile
```

```bash
cd apps/server && uv sync --frozen --extra dev && uv run --frozen ruff check . && uv run --frozen pytest
```

```bash
pnpm audit
```

```bash
cd apps/server && uv export --frozen --no-dev --no-hashes --no-emit-project -o /tmp/req.txt && uvx pip-audit -r /tmp/req.txt --no-deps --disable-pip
```

```bash
docker compose build && trivy image gaspirator-app
```

## Évolutions prévues

- Rendre les audits bloquants à partir d'un certain seuil (`pnpm audit --audit-level high`, `pip-audit` sans `continue-on-error`, Trivy `exit-code: 1` + `severity: CRITICAL,HIGH`).
- Publier les images : artefact (`actions/upload-artifact`) ou push vers un registry (GHCR).
- Upload SARIF vers l'onglet GitHub Security.
