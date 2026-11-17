"""Helpers shared by the Admin tests."""

REGISTRATION_REQUEST_FIELDS = {
    "id",
    "status",
    "supplier",
    "association",
    "account",
    "supplier_id",
    "association_id",
    "created_at",
    "decided_at",
}


def assert_error(response, status: int, code: str) -> dict:
    """The response is an `Error` with this status and code, and a message."""
    assert response.status_code == status
    data = response.json()
    assert data["code"] == code
    assert isinstance(data["message"], str) and data["message"]
    return data
