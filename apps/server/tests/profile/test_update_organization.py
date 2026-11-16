"""PATCH /me/organization: update my organisation (`OrganizationUpdate` -> `Organization`)."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.repositories import InMemoryOrganizationRepository, StoredUser
from app.schemas import (
    Address,
    GeoPoint,
    Organization,
    OrganizationStatus,
    OrganizationType,
    UserRole,
)
from tests.conftest import auth_headers

ORGANIZATION_URL = "/api/v1/me/organization"
NEW_ADDRESS = {"street": "3 place Bellecour", "postal_code": "69002", "city": "Lyon"}


def _add_association(repo: InMemoryOrganizationRepository, legal_id: str) -> Organization:
    association = Organization(
        id=0,
        type=OrganizationType.ASSOCIATION,
        name="Restos du Coeur Lyon",
        supplier_type=None,
        address=Address(street="5 rue Merciere", postal_code="69002", city="Lyon"),
        location=GeoPoint(latitude=45.76, longitude=4.83),
        contact_phone="04 72 00 00 00",
        legal_id=legal_id,
        opening_hours=None,
        status=OrganizationStatus.ACTIVE,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    return asyncio.run(repo.add(association))


def test_update_organization(client: TestClient, manager: StoredUser):
    response = client.patch(
        ORGANIZATION_URL,
        json={
            "name": "Cantine Ampère",
            "address": NEW_ADDRESS,
            "contact_phone": "04 78 11 11 11",
            "opening_hours": None,
        },
        headers=auth_headers(manager),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Cantine Ampère"
    assert data["address"] == NEW_ADDRESS
    assert data["contact_phone"] == "04 78 11 11 11"
    assert data["opening_hours"] is None
    assert data["legal_id"] == "19690103400017"
    assert data["status"] == "active"

    # The change is stored
    stored = client.get(ORGANIZATION_URL, headers=auth_headers(manager)).json()
    assert stored["name"] == "Cantine Ampère"


def test_update_organization_new_legal_id_needs_review(client: TestClient, manager: StoredUser):
    response = client.patch(
        ORGANIZATION_URL, json={"legal_id": "19690103400025"}, headers=auth_headers(manager)
    )

    assert response.status_code == 200
    assert response.json()["legal_id"] == "19690103400025"
    assert response.json()["status"] == "pending_review"


def test_update_organization_same_legal_id_stays_active(client: TestClient, manager: StoredUser):
    response = client.patch(
        ORGANIZATION_URL, json={"legal_id": "19690103400017"}, headers=auth_headers(manager)
    )

    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_update_organization_legal_id_already_used(
    client: TestClient, manager: StoredUser, organizations_repo: InMemoryOrganizationRepository
):
    _add_association(organizations_repo, "W691234567")

    response = client.patch(
        ORGANIZATION_URL, json={"legal_id": "W691234567"}, headers=auth_headers(manager)
    )

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_update_organization_member_forbidden(client: TestClient, member: StoredUser):
    response = client.patch(ORGANIZATION_URL, json={"name": "Autre"}, headers=auth_headers(member))

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_update_organization_admin_forbidden(client: TestClient, admin: StoredUser):
    response = client.patch(ORGANIZATION_URL, json={"name": "Autre"}, headers=auth_headers(admin))

    assert response.status_code == 403


def test_update_organization_supplier_type_on_association(
    client: TestClient,
    create_user: Callable[..., StoredUser],
    organizations_repo: InMemoryOrganizationRepository,
):
    association = _add_association(organizations_repo, "W691234567")
    manager = create_user(UserRole.MANAGER, association, "asso@example.org")

    response = client.patch(
        ORGANIZATION_URL, json={"supplier_type": "canteen"}, headers=auth_headers(manager)
    )

    assert response.status_code == 422
    assert response.json()["details"][0]["field"] == "supplier_type"


def test_update_organization_empty_body(client: TestClient, manager: StoredUser):
    response = client.patch(ORGANIZATION_URL, json={}, headers=auth_headers(manager))

    assert response.status_code == 422


def test_update_organization_invalid_fields(client: TestClient, manager: StoredUser):
    response = client.patch(
        ORGANIZATION_URL,
        json={"legal_id": "123", "address": {"street": "x"}, "status": "active"},
        headers=auth_headers(manager),
    )

    assert response.status_code == 422
    fields = {detail["field"] for detail in response.json()["details"]}
    assert {"legal_id", "address.street", "address.postal_code", "status"} <= fields


def test_update_organization_malformed_json(client: TestClient, manager: StoredUser):
    response = client.patch(
        ORGANIZATION_URL,
        content="{",
        headers={**auth_headers(manager), "Content-Type": "application/json"},
    )

    assert response.status_code == 400


def test_update_organization_without_token(client: TestClient):
    response = client.patch(ORGANIZATION_URL, json={"name": "Autre"})

    assert response.status_code == 401
