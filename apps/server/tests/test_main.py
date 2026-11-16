"""Tests for main application."""

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
