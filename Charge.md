# Tests de charge de l'API

Campagne du 17/11/2026 sur la branche `develop` (commit `1d0d72c`). Les scripts, le jeu de
données et les résultats bruts sont dans [`apps/server/loadtest/`](apps/server/loadtest/).

## Ce que l'on juge

| #   | Scénario                                                                                                                     | Outil                                | Question posée                                                                                            |
| --- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| S1  | **Réservation simultanée du dernier lot** : 50 associations réservent au même instant un lot dont il ne reste qu'une portion | locust (barrière de synchronisation) | Le back garantit-il qu'il n'y a jamais de surréservation (contrat de `POST /lots/{lotId}/reservations`) ? |
| S2  | Recherche de fournisseurs `GET /suppliers` (scénario `Association` fourni), montée à 200 utilisateurs                        | locust                               | L'API tient-elle 200 associations qui cherchent en continu ?                                              |
| S3  | Montée en charge de `GET /suppliers` : 10 → 200 connexions simultanées                                                       | oha                                  | Quel débit maximal, et à partir de quand l'API casse-t-elle ?                                             |
| S4  | S1, S2 et S3 avec 4 workers uvicorn                                                                                          | oha, locust                          | Une configuration « production » corrige-t-elle les problèmes de S2 et S3 ?                               |

Référence : `GET /health` (sans base ni authentification) donne le plafond de la pile HTTP,
soit **4 143 req/s avec un p95 de 20 ms** à 50 connexions.

## Machine utilisée

|            |                                                                                          |
| ---------- | ---------------------------------------------------------------------------------------- |
| Poste      | PC portable Windows 11                                                                   |
| CPU        | Intel Core i7-11800H, 8 cœurs / 16 threads, 2,3 GHz                                      |
| RAM        | 32 Go                                                                                    |
| Conteneurs | Docker Desktop 29.8.2 (WSL2) : 16 CPU, 15,5 Go alloués                                   |
| API        | Image `gaspirator-app` (celle de `docker-compose.yml`), Python 3.12, FastAPI, SQLAlchemy |
| Base       | PostgreSQL 18.7 (conteneur `db` du compose), base dédiée `gaspirator_load`               |
| Injecteurs | oha 1.17.0, locust 2.47.0 (`uvx locust`), lancés **sur la même machine**                 |

Configuration de l'API testée par défaut : celle du conteneur `app`, c'est-à-dire
`python -m app.main`. Elle lance **uvicorn en un seul processus avec `reload=True`**, avec le
pool SQLAlchemy par défaut (5 connexions + 10 en débordement, attente maximale de 30 s).
Variante S4 : la même image lancée avec
`uvicorn app.main:app --workers 4`, sans `--reload`.

Données (`loadtest/seed.py`, graine fixe) :

- 50 associations validées à Lyon ;
- 500 fournisseurs répartis à ±30 km autour de Lyon, avec 2 000 lots disponibles ;
- un fournisseur « course » dont les 20 lots n'ont plus qu'une portion : 10 lots indivisibles
  de 1 portion, et 10 lots divisibles de 5 portions dont 1 restante.

> Le script locust fourni tel quel n'aurait mesuré que des erreurs : il appelait
> `/suppliers` sans token (donc 401) et avec `lat`/`lng`, que le contrat ne connaît pas. Les
> paramètres du contrat sont `latitude`/`longitude`. Il a été repris avec ces paramètres et une
> connexion `POST /auth/login` par utilisateur simulé (`loadtest/locustfile.py`).

## Résultats

Les colonnes p95 et req/s ne comptent que les requêtes de l'endpoint testé. Le taux
d'erreur compte les réponses 5xx et les connexions coupées. Pour S1, un `409` est la réponse
attendue des perdants, donc il n'est pas compté comme une erreur.

### S1 — Réservation simultanée du dernier lot

50 associations, connectées à l'avance, attendent à une barrière puis envoient leur
`POST /lots/{id}/reservations` au même instant. On répète l'opération sur les 20 lots du
fournisseur « course », soit 1 000 réservations tentées par run.

| Config                | Requêtes | req/s (pendant la rafale) | p95    | % erreur | Lots avec exactement 1 × 201 et 49 × 409 | Surréservations en base |
| --------------------- | -------- | ------------------------- | ------ | -------- | ---------------------------------------- | ----------------------- |
| 1 processus (compose) | 1 000    | 201                       | 290 ms | 0 %      | **20 / 20**                              | **0**                   |
| 4 workers             | 1 000    | 259                       | 200 ms | 0 %      | **20 / 20**                              | **0**                   |

Vérification en base (`loadtest/race_check.sql`) : chaque lot a exactement 1 réservation de
1 portion, une quantité restante de 0, et ce qui a été retiré du stock correspond à ce qui a
été réservé. Toutes les rafales sont absorbées en moins de 0,44 s.

### S2 — Recherche de fournisseurs, 200 utilisateurs (locust)

Scénario `Association` : chaque utilisateur cherche autour de Lyon toutes les 0,1 à 0,5 s.
On monte de 5 utilisateurs/s jusqu'à 200, puis on tient 3 min.

| Config                | Requêtes `/suppliers` | req/s                   | p95           | % erreur                                |
| --------------------- | --------------------- | ----------------------- | ------------- | --------------------------------------- |
| 1 processus (compose) | 1 626                 | 9,7 (moyenne sur 3 min) | **30 000 ms** | **5,9 %**, et 40 % des logins en erreur |
| 4 workers             | 46 828                | 262                     | 700 ms        | **0 %**                                 |

Avec un seul processus, tout va bien jusqu'à ~165 utilisateurs (~117 req/s, p95 < 1,2 s).
À 200 utilisateurs, l'API **se fige complètement** : 0 req/s pendant plus de 2 min, des 500
toutes les 30 s, et un login qui dépasse 80 s en médiane.

### S3 — Montée en charge de `GET /suppliers` (oha)

Recherche par défaut : rayon de 10 km, pages de 20. Un utilisateur, et l'API redémarrée avant
chaque palier.

| Connexions        | Durée | req/s (2xx) | p50    | p95    | p99      | % erreur |
| ----------------- | ----- | ----------- | ------ | ------ | -------- | -------- |
| 10                | 30 s  | 144         | 67 ms  | 91 ms  | 107 ms   | 0 %      |
| 25                | 30 s  | 149         | 160 ms | 247 ms | 304 ms   | 0 %      |
| 50                | 30 s  | 135         | 362 ms | 589 ms | 692 ms   | 0 %      |
| 75                | 90 s  | **0,7**     | 30 s   | 60 s   | 60 s     | **71 %** |
| 100               | 90 s  | **0,3**     | 30 s   | 60 s   | 60 s     | **81 %** |
| 200               | 90 s  | **0,2**     | 30 s   | 60 s   | 60 s     | **91 %** |
| _4 workers_ — 50  | 60 s  | 330         | 137 ms | 238 ms | 295 ms   | 0 %      |
| _4 workers_ — 100 | 60 s  | 351         | 282 ms | 422 ms | 522 ms   | 0 %      |
| _4 workers_ — 200 | 60 s  | 298         | 522 ms | 933 ms | 1 375 ms | 0,4 %    |

Le débit plafonne autour de 145 req/s par processus. Au-delà de ~50 requêtes simultanées, il
ne se dégrade pas : il s'effondre. Les erreurs sont des 500
`QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00`.

## Conclusion

1. **La réservation concurrente est correcte.** Sur 2 × 20 courses à 50 associations, il y a
   toujours exactement un gagnant, les autres reçoivent un `409` propre, et il n'y a jamais
   de surréservation ni d'incohérence de stock, y compris avec 4 processus en parallèle. Le
   verrou `SELECT … FOR UPDATE` sur le lot fait son travail, et la latence reste basse
   (p95 ≤ 290 ms).

2. **Point bloquant : l'API se fige au-delà de ~50 requêtes simultanées par processus.** Ce
   n'est pas une lenteur mais un interblocage. Les routes et la dépendance `get_session` sont
   synchrones, donc FastAPI les exécute dans un pool de 40 threads, alors que le pool
   SQLAlchemy n'a que 15 connexions. Une requête qui a obtenu sa connexion (dans
   `get_current_user`) a encore besoin d'un thread libre pour exécuter la route, puis pour
   libérer la session. Quand les 40 threads sont tous occupés par des requêtes qui attendent
   une connexion, plus rien n'avance. On l'a observé directement : 15 connexions
   « idle in transaction » côté PostgreSQL, et un `/health` (asynchrone, sans base) qui
   répond toujours. Il faut attendre le timeout de 30 s du pool, qui renvoie des 500. Une
   seule rafale suffit à déclencher ce blocage, même quand le débit moyen reste sous la
   capacité. Il touche toutes les routes qui utilisent la base, login compris.

3. **Corrections recommandées**, par ordre d'impact :
   - **Rendre le pool cohérent avec le pool de threads**, dans `app/db.py`
     (`create_engine(..., pool_size=20, max_overflow=20)`), ou limiter le nombre de requêtes
     traitées en parallèle. On peut aussi réduire `pool_timeout` pour échouer vite plutôt que
     de bloquer 30 s.
   - **Ne pas déployer avec `reload=True` et un seul processus** : `python -m app.main` est
     une commande de développement. Avec 4 workers, mesurés dans S4, le débit est ×2,4
     (~330 req/s), et 200 utilisateurs locust passent sans erreur avec un p95 de 700 ms. C'est
     un palliatif : chaque worker garde la même limite, qui ne fait que reculer, ici jusqu'à
     ~200 connexions où les premiers 500 réapparaissent.

4. **Capacité actuelle**, avec 1 processus et 500 fournisseurs : environ 145 recherches/s,
   avec un p95 < 250 ms jusqu'à 25 requêtes simultanées. C'est largement suffisant pour
   l'usage attendu (quelques dizaines d'associations), **à condition de corriger le point 2**.
   Sinon, une seule rafale de requêtes rend l'API indisponible pendant au moins 30 s.

Limites de la campagne : les injecteurs tournent sur la même machine que l'API et la base,
ce qui pénalise un peu les débits ; le réseau passe par Docker Desktop (WSL2) ; le jeu de
données ne contient que 500 fournisseurs ; aucune limite CPU ou mémoire n'est imposée aux
conteneurs.

## Rejouer les tests

Depuis `apps/server`, avec le `db` du compose démarré :

```bash
docker exec gaspirator-db-1 psql -U postgres -c "create database gaspirator_load"
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/gaspirator_load
uv run alembic upgrade head && uv run python loadtest/seed.py
docker run -d --name gaspirator-load-api --network gaspirator_default --env-file .env \
  -e DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/gaspirator_load \
  -p 8001:8000 gaspirator-app:latest
```

```bash
# S1 : relancer seed.py avant chaque run (les lots « course » sont consommés)
RACE_OUT=loadtest/results/r1-race-1worker.json uvx locust -f loadtest/locust_race.py \
  --host http://localhost:8001 --headless -u 50 -r 50 -t 3m --csv loadtest/results/r1-race-1worker
docker exec -i gaspirator-db-1 psql -U postgres -d gaspirator_load < loadtest/race_check.sql
# S2
bash loadtest/run_locust.sh http://localhost:8001 loadtest/results l1
# S3
bash loadtest/run_oha.sh http://localhost:8001 loadtest/results o1 o2 o2long
# Tableau de synthèse
uv run python loadtest/summarize.py loadtest/results
```

S4 : même image lancée avec
`uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4` sur le port 8002, puis
`CONTAINER=gaspirator-load-api-w4` devant `run_oha.sh … o6` et `run_locust.sh … l1w4`.
