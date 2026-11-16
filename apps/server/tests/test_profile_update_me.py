"""PATCH /me: update my account (`MeUpdate` -> `Me`)."""

from collections.abc import Callable

from fastapi.testclient import TestClient

from app.repositories import StoredUser
from app.schemas import Organization, UserRole
from tests.conftest import auth_headers

ME_URL = "/api/v1/me"


def test_update_me_names(client: TestClient, manager: StoredUser):
    response = client.patch(
        ME_URL, json={"firstname": "Marion", "lastname": "Durand"}, headers=auth_headers(manager)
    )

    assert response.status_code == 200
    data = response.json()
    assert data["firstname"] == "Marion"
    assert data["lastname"] == "Durand"
    assert data["email"] == "marie.dupont@example.org"
    assert data["organization"]["id"] == manager.organization_id

    # The change is stored
    me = client.get(ME_URL, headers=auth_headers(manager)).json()
    assert me["firstname"] == "Marion"


def test_update_me_email(client: TestClient, manager: StoredUser):
    response = client.patch(
        ME_URL, json={"email": "marion@example.org"}, headers=auth_headers(manager)
    )

    assert response.status_code == 200
    assert response.json()["email"] == "marion@example.org"


def test_update_me_same_email_is_not_a_conflict(client: TestClient, manager: StoredUser):
    response = client.patch(
        ME_URL, json={"email": "MARIE.DUPONT@example.org"}, headers=auth_headers(manager)
    )

    assert response.status_code == 200


def test_update_me_email_already_used(
    client: TestClient,
    manager: StoredUser,
    create_user: Callable[..., StoredUser],
    supplier: Organization,
):
    create_user(UserRole.MEMBER, supplier, "paul.martin@example.org")

    response = client.patch(
        ME_URL, json={"email": "Paul.Martin@example.org"}, headers=auth_headers(manager)
    )

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_update_me_empty_body(client: TestClient, manager: StoredUser):
    response = client.patch(ME_URL, json={}, headers=auth_headers(manager))

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_update_me_invalid_fields(client: TestClient, manager: StoredUser):
    response = client.patch(
        ME_URL,
        json={"firstname": "", "email": "not-an-email", "role": "admin"},
        headers=auth_headers(manager),
    )

    assert response.status_code == 422
    fields = {detail["field"] for detail in response.json()["details"]}
    assert fields == {"firstname", "email", "role"}


def test_update_me_null_field(client: TestClient, manager: StoredUser):
    response = client.patch(ME_URL, json={"lastname": None}, headers=auth_headers(manager))

    assert response.status_code == 422


def test_update_me_malformed_json(client: TestClient, manager: StoredUser):
    response = client.patch(
        ME_URL,
        content="{",
        headers={**auth_headers(manager), "Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "bad_request"


def test_update_me_without_token(client: TestClient):
    response = client.patch(ME_URL, json={"firstname": "Marion"})

    assert response.status_code == 401
