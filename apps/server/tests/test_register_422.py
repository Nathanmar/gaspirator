"""POST /registration-requests: 422 `ValidationError` (format `Error`)."""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import REGISTRATION_URL


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
