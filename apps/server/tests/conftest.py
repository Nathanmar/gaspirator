"""Shared test fixtures."""

import copy

import pytest
from fastapi.testclient import TestClient

from app.main import app

REGISTRATION_URL = "/api/v1/registration-requests"

VALID_REGISTRATION = {
    "organization": {
        "type": "supplier",
        "name": "Cantine du lycée Ampère",
        "legal_id": "19690103400017",
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
        "email": "marie.dupont@example.org",
        "password": "testPass1.",
    },
}


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def registration() -> dict:
    """A valid registration request body (deep copy, safe to mutate)."""
    return copy.deepcopy(VALID_REGISTRATION)
