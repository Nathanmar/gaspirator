"""Locust scenarios of Charge.md.

    uvx locust -f loadtest/locustfile.py --host http://localhost:8001 --headless \
        -u 200 -r 5 -t 3m --csv loadtest/results/l1-association Association

`Association` is the scenario of the brief, with the parameters and the authentication of
the contract (`latitude` / `longitude`, Bearer token).
"""

from itertools import count

from locust import HttpUser, between, task

PASSWORD = "loadtest-password"
ASSOCIATIONS = 50  # loadtest/seed.py --associations
_ids = count()


class _LoggedIn(HttpUser):
    abstract = True

    def on_start(self):
        # Each simulated user logs in as one of the seeded associations.
        email = f"loadtest-asso-{next(_ids) % ASSOCIATIONS}@example.com"
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": PASSWORD},
            name="POST /auth/login",
        )
        token = response.json()["access_token"]
        self.client.headers["Authorization"] = f"Bearer {token}"


class Association(_LoggedIn):
    wait_time = between(0.1, 0.5)

    @task
    def chercher_fournisseurs(self):
        self.client.get(
            "/api/v1/suppliers",
            params={"latitude": 45.76, "longitude": 4.83},
            name="GET /suppliers",
        )
