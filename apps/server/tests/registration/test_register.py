"""POST /registration-requests: 201 `RegistrationRequest`, 400, 409 and 422 (format `Error`)."""

import uuid

import pytest
from fastapi.testclient import TestClient

from tests.conftest import REGISTRATION_URL

# ----- 201 -----


def test_register(client: TestClient, registration: dict):
    """A supplier registration creates a `pending` request."""
    response = client.post(REGISTRATION_URL, json=registration)

    assert response.status_code == 201
    data = response.json()
    assert set(data) == {
        "id",
        "status",
        "organization",
        "account",
        "organization_id",
        "created_at",
        "decided_at",
    }
    assert isinstance(data["id"], int)
    assert data["status"] == "pending"
    assert data["organization"] == registration["organization"]
    assert data["account"] == {
        "firstname": "Marie",
        "lastname": "Dupont",
        "email": "marie.dupont@example.org",
    }
    assert data["organization_id"] is None
    assert data["created_at"]
    assert data["decided_at"] is None


def test_register_association(client: TestClient, registration: dict):
    """An association has an RNA number and no supplier_type."""
    registration["organization"].update(
        {"type": "association", "legal_id": "W691234567", "supplier_type": None}
    )
    registration["account"]["email"] = "asso.dupont@example.org"
    response = client.post(REGISTRATION_URL, json=registration)

    assert response.status_code == 201
    assert response.json()["organization"]["supplier_type"] is None


# ----- 400 -----


@pytest.mark.parametrize(
    "body",
    [
        "{",
        '{"organization": {"type": "supplier"},}',
        '{"account": {"email": "marie.dupont@example.org" "password": "testPass1."}}',
        "{'organization': {}, 'account': {}}",
        "not json",
    ],
    ids=["unclosed", "trailing-comma", "missing-comma", "single-quotes", "plain-text"],
)
def test_register_malformed_json(client: TestClient, body: str):
    response = client.post(
        REGISTRATION_URL,
        content=body,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "bad_request"
    assert isinstance(data["message"], str) and data["message"]


# ----- 409 -----


def _unique_siret() -> str:
    """14-digit SIRET, different on every call."""
    return str(uuid.uuid4().int)[:14]


def _unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:8]}@example.com"


def _with(registration: dict, email: str, legal_id: str) -> dict:
    registration["account"]["email"] = email
    registration["organization"]["legal_id"] = legal_id
    return registration


def test_register_email_already_used(client: TestClient, registration: dict):
    """Same e-mail, different SIRET: 409."""
    email = _unique_email()

    first = client.post(REGISTRATION_URL, json=_with(registration, email, _unique_siret()))
    assert first.status_code == 201

    second = client.post(REGISTRATION_URL, json=_with(registration, email, _unique_siret()))
    assert second.status_code == 409
    assert second.json()["code"] == "conflict"


def test_register_siret_already_used(client: TestClient, registration: dict):
    """Same SIRET, different e-mail: 409."""
    siret = _unique_siret()

    first = client.post(REGISTRATION_URL, json=_with(registration, _unique_email(), siret))
    assert first.status_code == 201

    second = client.post(REGISTRATION_URL, json=_with(registration, _unique_email(), siret))
    assert second.status_code == 409
    assert second.json()["code"] == "conflict"


# ----- 422 -----


def _assert_validation_error(response, field: str) -> None:
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "validation_error"
    assert isinstance(data["message"], str) and data["message"]
    assert field in [detail["field"] for detail in data["details"]]
    for detail in data["details"]:
        assert set(detail) == {"field", "message"}


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("account", "email", "invalid-email"),
        ("account", "password", "weak"),
        ("account", "firstname", ""),
        ("organization", "name", "A"),
        ("organization", "legal_id", "123456789"),
        ("organization", "type", "restaurant"),
        ("organization", "supplier_type", "restaurant"),
        ("organization", "contact_phone", "555-1234"),
    ],
)
def test_register_invalid_field(
    client: TestClient, registration: dict, section: str, field: str, value: str
):
    registration[section][field] = value
    response = client.post(REGISTRATION_URL, json=registration)
    _assert_validation_error(response, f"{section}.{field}")


def test_register_invalid_postal_code(client: TestClient, registration: dict):
    registration["organization"]["address"]["postal_code"] = "6900"
    response = client.post(REGISTRATION_URL, json=registration)
    _assert_validation_error(response, "organization.address.postal_code")


@pytest.mark.parametrize("field", ["firstname", "lastname", "email", "password"])
def test_register_missing_account_field(client: TestClient, registration: dict, field: str):
    del registration["account"][field]
    response = client.post(REGISTRATION_URL, json=registration)
    _assert_validation_error(response, f"account.{field}")


def test_register_missing_organization(client: TestClient, registration: dict):
    del registration["organization"]
    response = client.post(REGISTRATION_URL, json=registration)
    _assert_validation_error(response, "organization")


def test_register_unknown_field(client: TestClient, registration: dict):
    """additionalProperties: false"""
    registration["organization"]["opening_hours"] = "9h-17h"
    response = client.post(REGISTRATION_URL, json=registration)
    _assert_validation_error(response, "organization.opening_hours")


def test_register_supplier_without_supplier_type(client: TestClient, registration: dict):
    registration["organization"]["supplier_type"] = None
    response = client.post(REGISTRATION_URL, json=registration)
    _assert_validation_error(response, "organization.supplier_type")


def test_register_association_with_supplier_type(client: TestClient, registration: dict):
    registration["organization"].update({"type": "association", "legal_id": "W691234567"})
    response = client.post(REGISTRATION_URL, json=registration)
    _assert_validation_error(response, "organization.supplier_type")
