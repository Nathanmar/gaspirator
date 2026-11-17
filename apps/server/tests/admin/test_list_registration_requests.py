"""GET /admin/registration-requests: 200 `RegistrationRequestPage`, 401 and 403 (`Error`).

Platform admins only. The `pending` requests, oldest first.
"""

from datetime import UTC, datetime, timedelta

import httpx2
import pytest
from fastapi.testclient import TestClient

from app.schemas import RegistrationStatus
from tests.admin.helpers import REGISTRATION_REQUEST_FIELDS, assert_error
from tests.prism import API_PREFIX, assert_contract

LIST_PATH = "/admin/registration-requests"


def _ids(response) -> list[int]:
    return [request["id"] for request in response.json()["data"]]


# ----- 200 -----


def test_list_registration_requests(api: httpx2.Client, admin_headers: dict, create_request):
    request = create_request()

    response = api.get(LIST_PATH, headers=admin_headers)

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"data", "meta"}
    assert data["meta"] == {"page": 1, "per_page": 20, "total": 1}
    [item] = data["data"]
    assert set(item) == REGISTRATION_REQUEST_FIELDS
    assert item["id"] == request.id
    assert item["status"] == "pending"
    assert item["supplier"] == {
        "name": "Cantine du lycée Ampère",
        "legal_id": request.legal_id,
        "supplier_type": "canteen",
        "address": {"street": "12 rue de la République", "postal_code": "69002", "city": "Lyon"},
        "contact_phone": "04 78 00 00 00",
    }
    assert item["association"] is None
    assert item["account"] == {
        "firstname": "Marie",
        "lastname": "Dupont",
        "email": request.user.email,
    }
    assert item["supplier_id"] is None
    assert item["association_id"] is None
    assert item["decided_at"] is None


def test_list_registration_requests_association(
    api: httpx2.Client, admin_headers: dict, create_request
):
    request = create_request("association")

    response = api.get(LIST_PATH, headers=admin_headers)

    assert_contract(response)
    [item] = response.json()["data"]
    assert item["supplier"] is None
    assert item["association"]["legal_id"] == request.legal_id


def test_list_registration_requests_pending_only(
    api: httpx2.Client, admin_headers: dict, create_request
):
    pending = create_request()
    create_request(status=RegistrationStatus.APPROVED)
    create_request(status=RegistrationStatus.REJECTED)

    response = api.get(LIST_PATH, headers=admin_headers)

    assert_contract(response)
    assert _ids(response) == [pending.id]
    assert response.json()["meta"]["total"] == 1


def test_list_registration_requests_oldest_first(
    api: httpx2.Client, admin_headers: dict, create_request
):
    now = datetime.now(UTC)
    newer = create_request(created_at=now - timedelta(hours=1))
    older = create_request(created_at=now - timedelta(days=1))

    response = api.get(LIST_PATH, headers=admin_headers)

    assert_contract(response)
    assert _ids(response) == [older.id, newer.id]


def test_list_registration_requests_empty(api: httpx2.Client, admin_headers: dict):
    response = api.get(LIST_PATH, headers=admin_headers)

    assert_contract(response)
    assert response.json() == {"data": [], "meta": {"page": 1, "per_page": 20, "total": 0}}


def test_list_registration_requests_pagination(
    api: httpx2.Client, admin_headers: dict, create_request
):
    start = datetime.now(UTC) - timedelta(days=1)
    requests = [create_request(created_at=start + timedelta(hours=i)) for i in range(3)]

    first = api.get(LIST_PATH, params={"per_page": 2}, headers=admin_headers)
    second = api.get(LIST_PATH, params={"per_page": 2, "page": 2}, headers=admin_headers)
    beyond = api.get(LIST_PATH, params={"per_page": 2, "page": 9}, headers=admin_headers)

    for response in (first, second, beyond):
        assert_contract(response)
    assert _ids(first) == [requests[0].id, requests[1].id]
    assert _ids(second) == [requests[2].id]
    assert _ids(beyond) == []
    assert first.json()["meta"] == {"page": 1, "per_page": 2, "total": 3}


# ----- 400 (no 400 in the contract: `BadRequest` covers an incorrect parameter) -----


@pytest.mark.parametrize(
    "params",
    [{"page": 0}, {"page": "abc"}, {"per_page": 0}, {"per_page": 101}],
    ids=["page-0", "page-text", "per-page-0", "per-page-101"],
)
def test_list_registration_requests_invalid_pagination(
    client: TestClient, admin_headers: dict, params: dict
):
    """Sent in-process: through Prism, the undocumented status would be a violation."""
    response = client.get(API_PREFIX + LIST_PATH, params=params, headers=admin_headers)

    data = assert_error(response, 400, "bad_request")
    assert {detail["field"] for detail in data["details"]} <= {"page", "per_page"}


# ----- 401 -----


def test_list_registration_requests_without_token(api: httpx2.Client):
    response = api.get(LIST_PATH)

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_list_registration_requests_invalid_token(api: httpx2.Client):
    response = api.get(LIST_PATH, headers={"Authorization": "Bearer not-a-jwt"})

    assert_contract(response)
    assert_error(response, 401, "unauthorized")


# ----- 403 -----


@pytest.mark.parametrize("headers", ["supplier_headers", "association_headers"])
def test_list_registration_requests_not_admin(api: httpx2.Client, request, headers: str):
    response = api.get(LIST_PATH, headers=request.getfixturevalue(headers))

    assert_contract(response)
    assert_error(response, 403, "forbidden")
