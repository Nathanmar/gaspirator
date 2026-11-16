"""GET /me: the logged-in user (`Me`)."""

from datetime import timedelta

from fastapi.testclient import TestClient

from app.auth import create_access_token
from app.repositories import StoredUser
from tests.conftest import auth_headers

ME_URL = "/api/v1/me"


def test_get_me_manager(client: TestClient, manager: StoredUser):
    response = client.get(ME_URL, headers=auth_headers(manager))

    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"id", "email", "firstname", "lastname", "role", "organization"}
    assert data["id"] == manager.id
    assert data["email"] == "marie.dupont@example.org"
    assert data["role"] == "manager"
    assert data["organization"]["id"] == manager.organization_id
    assert data["organization"]["status"] == "active"
    assert "password_hash" not in data


def test_get_me_admin_has_no_organization(client: TestClient, admin: StoredUser):
    response = client.get(ME_URL, headers=auth_headers(admin))

    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert response.json()["organization"] is None


def test_get_me_without_token(client: TestClient):
    response = client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_get_me_invalid_token(client: TestClient):
    response = client.get(ME_URL, headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_get_me_expired_token(client: TestClient, manager: StoredUser):
    token = create_access_token({"sub": str(manager.id)}, expires_delta=timedelta(minutes=-1))
    response = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_get_me_unknown_user(client: TestClient):
    token = create_access_token({"sub": "999"})
    response = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
