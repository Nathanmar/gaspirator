"""POST /registration-requests: 400 `BadRequest` (malformed JSON, format `Error`)."""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import REGISTRATION_URL


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
