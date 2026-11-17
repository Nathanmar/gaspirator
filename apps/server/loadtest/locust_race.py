"""Reservation race of Charge.md: RACE_USERS associations reserve, at the same instant, the
last portion of each lot of supplier 1 ("Fournisseur course", see loadtest/seed.py).

    uvx locust -f loadtest/locust_race.py --host http://localhost:8001 --headless \
        -u 50 -r 50 -t 3m --csv loadtest/results/r1-race

Each simulated user logs in as a different association, then for every lot waits at a
barrier until all the users are there and sends its POST /lots/{id}/reservations. Expected
for every lot: exactly one 201 and RACE_USERS - 1 409. 201 and 409 count as successes in
the locust stats, anything else as a failure. The outcome per lot is written to
RACE_OUT (default loadtest/results/race.json); check the database afterwards with
loadtest/race_check.sql.
"""

import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from itertools import count

import requests
from gevent.event import Event
from locust import HttpUser, events, task
from locust.exception import StopUser

PASSWORD = "loadtest-password"
RACE_SUPPLIER_ID = 1
USERS = int(os.getenv("RACE_USERS", "50"))
OUT = os.getenv("RACE_OUT", "loadtest/results/race.json")

lots: list[dict] = []
_ids = count()
_arrived: Counter = Counter()
_go: defaultdict = defaultdict(Event)
released_at: dict[int, float] = {}
last_answer_at: dict[int, float] = {}
outcomes: defaultdict = defaultdict(Counter)
_finished = count(1)


@events.test_start.add_listener
def load_lots(environment, **_):
    base = environment.host
    token = requests.post(
        f"{base}/api/v1/auth/login",
        json={"email": "loadtest-asso-0@example.com", "password": PASSWORD},
        timeout=30,
    ).json()["access_token"]
    response = requests.get(
        f"{base}/api/v1/suppliers/{RACE_SUPPLIER_ID}/lots",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    lots[:] = response.json()["data"]
    print(f"Race on {len(lots)} lots with {USERS} associations each.")


@events.test_stop.add_listener
def report(environment, **_):
    rows = []
    for index, lot in enumerate(lots):
        outcome = outcomes[index]
        duration = last_answer_at.get(index, 0) - released_at.get(index, 0)
        rows.append(
            {
                "lot_id": lot["id"],
                "title": lot["title"],
                "statuses": dict(outcome),
                "burst_seconds": round(duration, 3),
                "ok": outcome.get("201") == 1 and outcome.get("409") == USERS - 1,
            }
        )
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"users": USERS, "lots": rows}, f, indent=2, ensure_ascii=False)
    winners = sum(r["statuses"].get("201", 0) for r in rows)
    print(
        f"Race: {len(rows)} lots, {winners} reservations accepted (expected {len(rows)}),"
        f" {sum(r['ok'] for r in rows)} lots with exactly 1 × 201 and {USERS - 1} × 409."
    )


def _barrier(index: int) -> None:
    """Wait until the USERS users reached lot `index`, then release them together."""
    _arrived[index] += 1
    if _arrived[index] == USERS:
        released_at[index] = time.perf_counter()
        _go[index].set()
    _go[index].wait()


class Concurrent(HttpUser):
    def on_start(self):
        email = f"loadtest-asso-{next(_ids) % USERS}@example.com"
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": PASSWORD},
            name="POST /auth/login",
        )
        self.client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"

    @task
    def rush(self):
        for index, lot in enumerate(lots):
            start = datetime.fromisoformat(lot["pickup_start"])
            body = {"pickup_at": (start + timedelta(minutes=30)).isoformat()}
            if lot["divisible"]:
                body["quantity"] = "1"
            _barrier(index)
            with self.client.post(
                f"/api/v1/lots/{lot['id']}/reservations",
                json=body,
                name="POST /lots/{id}/reservations",
                catch_response=True,
            ) as response:
                status = str(response.status_code)
                outcomes[index][status] += 1
                last_answer_at[index] = time.perf_counter()
                if status in ("201", "409"):
                    response.success()
                else:
                    response.failure(f"unexpected {status}: {response.text[:200]}")
        if next(_finished) == USERS:
            self.environment.runner.quit()
        raise StopUser()
