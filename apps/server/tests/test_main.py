"""Tests for main application."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


def test_root(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to gaspirator!"}


def test_health(client: TestClient):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_register(client: TestClient):
    """Test register endpoint 201"""
    account = {
        "email": "test@example.com",
        "password": "testPass1.",
        "first_name": "Test",
        "last_name": "User"
    }
    organisation = {
        "type": "supplier",
        "name": "Test Company",
        "legal_id": "123456789",
        "address": "123 Test St",
        "contact_phone": "555-1234",
        "opening_hours": "9am-5pm",
        "supplier_type": "canteen",
    }

    user_data = {"account": account, "organisation": organisation}

    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201


# ---------- US-01 · POST /registration-requests ----------


def _registration_payload(email: str, legal_id: str) -> dict:
    """Corps valide de RegistrationRequestCreate (cf. openapi.yaml)."""
    return {
        "organization": {
            "type": "supplier",
            "name": "Cantine du lycée Ampère",
            "legal_id": legal_id,
            "supplier_type": "canteen",
            "address": {
                "street": "12 rue de la République",
                "postal_code": "69002",
                "city": "Lyon",
            },
            "contact_phone": "04 78 00 00 00",
        },
        "account": {
            "firstname": "Marie",
            "lastname": "Dupont",
            "email": email,
            "password": "testPass1.",
        },
    }


def _unique_siret() -> str:
    """SIRET de 14 chiffres, différent à chaque appel."""
    return str(uuid.uuid4().int)[:14]


def _unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:8]}@example.com"


def test_registration_request_email_deja_utilise_409(client: TestClient):
    """409 si l'e-mail du compte est déjà utilisé."""
    email = _unique_email()

    first = client.post("/registration-requests", json=_registration_payload(email, _unique_siret()))
    assert first.status_code == 201

    # Même e-mail, SIRET différent
    second = client.post("/registration-requests", json=_registration_payload(email, _unique_siret()))
    assert second.status_code == 409
    assert second.json()["code"] == "conflict"


def test_registration_request_siret_deja_utilise_409(client: TestClient):
    """409 si le SIRET de l'organisation est déjà utilisé."""
    siret = _unique_siret()

    first = client.post("/registration-requests", json=_registration_payload(_unique_email(), siret))
    assert first.status_code == 201

    # Même SIRET, e-mail différent
    second = client.post("/registration-requests", json=_registration_payload(_unique_email(), siret))
    assert second.status_code == 409
    assert second.json()["code"] == "conflict"
