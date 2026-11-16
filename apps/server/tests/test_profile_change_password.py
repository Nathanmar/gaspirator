"""PUT /me/password: change my password (`PasswordChange` -> 204)."""

import asyncio

from fastapi.testclient import TestClient

from app.auth import verify_password
from app.repositories import InMemoryUserRepository, StoredUser
from tests.conftest import PASSWORD, auth_headers

PASSWORD_URL = "/api/v1/me/password"
NEW_PASSWORD = "newPass2!"


def test_change_password(
    client: TestClient, manager: StoredUser, users_repo: InMemoryUserRepository
):
    response = client.put(
        PASSWORD_URL,
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers=auth_headers(manager),
    )

    assert response.status_code == 204
    assert response.content == b""

    stored = asyncio.run(users_repo.get(manager.id))
    assert verify_password(NEW_PASSWORD, stored.password_hash)
    assert not verify_password(PASSWORD, stored.password_hash)


def test_change_password_wrong_current(client: TestClient, manager: StoredUser):
    response = client.put(
        PASSWORD_URL,
        json={"current_password": "wrongPass", "new_password": NEW_PASSWORD},
        headers=auth_headers(manager),
    )

    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "validation_error"
    assert data["details"][0]["field"] == "current_password"


def test_change_password_too_short(client: TestClient, manager: StoredUser):
    response = client.put(
        PASSWORD_URL,
        json={"current_password": PASSWORD, "new_password": "short"},
        headers=auth_headers(manager),
    )

    assert response.status_code == 422
    assert response.json()["details"][0]["field"] == "new_password"


def test_change_password_missing_field(client: TestClient, manager: StoredUser):
    response = client.put(
        PASSWORD_URL, json={"new_password": NEW_PASSWORD}, headers=auth_headers(manager)
    )

    assert response.status_code == 422


def test_change_password_malformed_json(client: TestClient, manager: StoredUser):
    response = client.put(
        PASSWORD_URL,
        content="not json",
        headers={**auth_headers(manager), "Content-Type": "application/json"},
    )

    assert response.status_code == 400


def test_change_password_without_token(client: TestClient):
    response = client.put(
        PASSWORD_URL, json={"current_password": PASSWORD, "new_password": NEW_PASSWORD}
    )

    assert response.status_code == 401
