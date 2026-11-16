"""POST /registration-requests: 409 when the SIRET or the e-mail is already used."""

import uuid

from fastapi.testclient import TestClient

from tests.conftest import REGISTRATION_URL


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
