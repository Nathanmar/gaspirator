"""POST /admin/registration-requests/{requestId}/reject: 200 `RegistrationRequest`, 401,
403, 404 and 409 (format `Error`). Platform admins only.

Rejects the request (nothing is created) and tells the applicant by e-mail; 409 if the
request was already decided.
"""

from datetime import datetime

import httpx2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Association, Supplier, User
from app.schemas import RegistrationStatus
from tests.admin.conftest import PASSWORD
from tests.admin.helpers import REGISTRATION_REQUEST_FIELDS, assert_error
from tests.prism import API_PREFIX, assert_contract


def _path(request_id) -> str:
    return f"/admin/registration-requests/{request_id}/reject"


# ----- 200 -----


@pytest.mark.parametrize("kind", ["supplier", "association"])
def test_reject(api: httpx2.Client, db: Session, admin_headers: dict, create_request, kind):
    request = create_request(kind)

    response = api.post(_path(request.id), headers=admin_headers)

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == REGISTRATION_REQUEST_FIELDS
    assert data["id"] == request.id
    assert data["status"] == "rejected"
    assert datetime.fromisoformat(data["decided_at"])
    assert data["supplier_id"] is None
    assert data["association_id"] is None
    assert data[kind]["legal_id"] == request.legal_id

    db.expire_all()
    assert db.query(Supplier).count() == 0
    assert db.query(Association).count() == 0
    user = db.get(User, request.user_id)
    assert user.supplier_id is None and user.association_id is None


def test_reject_keeps_the_account_locked(api: httpx2.Client, admin_headers: dict, create_request):
    request = create_request()

    api.post(_path(request.id), headers=admin_headers)
    login = api.post("/auth/login", json={"email": request.user.email, "password": PASSWORD})

    assert_contract(login)
    assert_error(login, 403, "forbidden")


def test_reject_sends_an_email(
    client: TestClient, admin_headers: dict, create_request, outbox: list
):
    request = create_request("supplier")

    response = client.post(API_PREFIX + _path(request.id), headers=admin_headers)

    assert response.status_code == 200
    [email] = outbox
    assert email.to == request.user.email
    assert "refusée" in email.subject
    assert "Cantine du lycée Ampère" in email.body


def test_reject_leaves_the_other_requests_pending(
    api: httpx2.Client, admin_headers: dict, create_request
):
    rejected, other = create_request(), create_request()

    api.post(_path(rejected.id), headers=admin_headers)
    pending = api.get("/admin/registration-requests", headers=admin_headers)

    assert [item["id"] for item in pending.json()["data"]] == [other.id]


# ----- 401 -----


def test_reject_without_token(api: httpx2.Client, create_request):
    response = api.post(_path(create_request().id))

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")


def test_reject_invalid_token(api: httpx2.Client, create_request):
    response = api.post(_path(create_request().id), headers={"Authorization": "Bearer not-a-jwt"})

    assert_contract(response)
    assert_error(response, 401, "unauthorized")


# ----- 403 -----


@pytest.mark.parametrize("headers", ["supplier_headers", "association_headers"])
def test_reject_not_admin(
    api: httpx2.Client, db: Session, request, headers: str, create_request, outbox: list
):
    registration = create_request()

    response = api.post(_path(registration.id), headers=request.getfixturevalue(headers))

    assert_contract(response)
    assert_error(response, 403, "forbidden")
    assert outbox == []
    db.expire_all()
    assert registration.status == RegistrationStatus.PENDING


def test_reject_not_admin_unknown_request(api: httpx2.Client, association_headers: dict):
    """The role is checked first: other users cannot probe which requests exist."""
    response = api.post(_path(999), headers=association_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


# ----- 404 -----


def test_reject_unknown_request(api: httpx2.Client, admin_headers: dict):
    response = api.post(_path(999), headers=admin_headers)

    assert_contract(response)
    assert_error(response, 404, "not_found")


@pytest.mark.parametrize("request_id", ["abc", "0", "-1", str(2**63)])
def test_reject_impossible_id(client: TestClient, admin_headers: dict, request_id: str):
    """No 400/422 in the contract: an id that cannot exist is not found.

    Sent in-process: through Prism, an id that is not an int64 is a request violation.
    """
    response = client.post(API_PREFIX + _path(request_id), headers=admin_headers)

    assert_error(response, 404, "not_found")


# ----- 409 -----


@pytest.mark.parametrize("status", [RegistrationStatus.APPROVED, RegistrationStatus.REJECTED])
def test_reject_already_decided(
    api: httpx2.Client, admin_headers: dict, create_request, status, outbox: list
):
    request = create_request(status=status)

    response = api.post(_path(request.id), headers=admin_headers)

    assert_contract(response)
    assert_error(response, 409, "conflict")
    assert outbox == []


def test_reject_after_approve(api: httpx2.Client, db: Session, admin_headers: dict, create_request):
    """An approved request cannot be rejected: its supplier stays."""
    request = create_request()
    api.post(f"/admin/registration-requests/{request.id}/approve", headers=admin_headers)

    response = api.post(_path(request.id), headers=admin_headers)

    assert_contract(response)
    assert_error(response, 409, "conflict")
    assert db.query(Supplier).count() == 1
