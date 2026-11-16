"""POST /registration-requests: 201 `RegistrationRequest`."""

from fastapi.testclient import TestClient

from tests.conftest import REGISTRATION_URL


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
