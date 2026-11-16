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


def test_create_item(client: TestClient):
    """Test creating an item with valid data."""
    response = client.post(
        "/items",
        json={"name": "Test Item", "description": "A test item", "price": 9.99, "quantity": 5},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["price"] == 9.99
    assert data["quantity"] == 5
    assert "id" in data


def test_create_item_validation_error(client: TestClient):
    """Test validation error for invalid item data."""
    # Price must be positive
    response = client.post(
        "/items",
        json={"name": "Test Item", "price": -1.0},
    )
    assert response.status_code == 422


def test_create_item_missing_required_field(client: TestClient):
    """Test validation error for missing required field."""
    response = client.post(
        "/items",
        json={"description": "No name or price"},
    )
    assert response.status_code == 422


def test_list_items(client: TestClient):
    """Test listing items."""
    # Create an item first
    client.post("/items", json={"name": "Item 1", "price": 10.0})
    response = client.get("/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_item_not_found(client: TestClient):
    """Test getting non-existent item."""
    response = client.get("/items/99999")
    assert response.status_code == 404


def test_send_message(client: TestClient):
    """Test sending a contact message with validated email."""
    response = client.post(
        "/contact",
        json={
            "email": "test@example.com",
            "subject": "Test Subject",
            "content": "Test message content",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "test@example.com" in data["message"]


def test_send_message_invalid_email(client: TestClient):
    """Test validation error for invalid email."""
    response = client.post(
        "/contact",
        json={
            "email": "not-an-email",
            "subject": "Test Subject",
            "content": "Test message content",
        },
    )
    assert response.status_code == 422
