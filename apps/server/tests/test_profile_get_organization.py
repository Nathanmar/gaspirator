"""GET /me/organization: my organisation (`Organization`)."""

from fastapi.testclient import TestClient

from app.repositories import StoredUser
from tests.conftest import auth_headers

ORGANIZATION_URL = "/api/v1/me/organization"


def test_get_my_organization_manager(client: TestClient, manager: StoredUser):
    response = client.get(ORGANIZATION_URL, headers=auth_headers(manager))

    assert response.status_code == 200
    data = response.json()
    assert {
        "id",
        "type",
        "name",
        "supplier_type",
        "address",
        "location",
        "contact_phone",
        "legal_id",
        "opening_hours",
        "status",
        "created_at",
    } <= set(data)
    assert data["id"] == manager.organization_id
    assert data["type"] == "supplier"
    assert data["legal_id"] == "19690103400017"
    assert data["status"] == "active"


def test_get_my_organization_member(client: TestClient, member: StoredUser):
    response = client.get(ORGANIZATION_URL, headers=auth_headers(member))

    assert response.status_code == 200
    assert response.json()["id"] == member.organization_id


def test_get_my_organization_admin(client: TestClient, admin: StoredUser):
    response = client.get(ORGANIZATION_URL, headers=auth_headers(admin))

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_get_my_organization_without_token(client: TestClient):
    response = client.get(ORGANIZATION_URL)

    assert response.status_code == 401
