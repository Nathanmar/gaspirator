"""POST /admin/registration-requests/{requestId}/approve: 200 `RegistrationRequest`, 401,
403, 404 and 409 (format `Error`). Platform admins only.

Creates the supplier or the association, activates the manager account and tells the
manager by e-mail; 409 if the request was already decided.
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
    return f"/admin/registration-requests/{request_id}/approve"


# ----- 200 -----


def test_approve_supplier(api: httpx2.Client, db: Session, admin_headers: dict, create_request):
    request = create_request("supplier")

    response = api.post(_path(request.id), headers=admin_headers)

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == REGISTRATION_REQUEST_FIELDS
    assert data["id"] == request.id
    assert data["status"] == "approved"
    assert datetime.fromisoformat(data["decided_at"])
    assert data["association_id"] is None
    assert data["association"] is None

    db.expire_all()
    supplier = db.get(Supplier, data["supplier_id"])
    assert supplier is not None
    assert (supplier.name, supplier.legal_id, supplier.supplier_type.value) == (
        "Cantine du lycée Ampère",
        request.legal_id,
        "canteen",
    )
    assert (supplier.street, supplier.postal_code, supplier.city) == (
        "12 rue de la République",
        "69002",
        "Lyon",
    )
    assert (supplier.latitude, supplier.longitude) == (45.7578, 4.832)
    assert supplier.contact_phone == "04 78 00 00 00"
    assert db.get(User, request.user_id).supplier_id == supplier.id


def test_approve_association(api: httpx2.Client, db: Session, admin_headers: dict, create_request):
    request = create_request("association")

    response = api.post(_path(request.id), headers=admin_headers)

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert data["supplier_id"] is None
    db.expire_all()
    association = db.get(Association, data["association_id"])
    assert association.legal_id == request.legal_id
    assert (association.latitude, association.longitude) == (45.7578, 4.832)
    assert db.get(User, request.user_id).association_id == association.id


def test_approve_activates_the_account(api: httpx2.Client, admin_headers: dict, create_request):
    """The manager can log in, and GET /me shows the new supplier."""
    request = create_request("supplier")
    credentials = {"email": request.user.email, "password": PASSWORD}
    assert api.post("/auth/login", json=credentials).status_code == 403  # pending

    api.post(_path(request.id), headers=admin_headers)
    login = api.post("/auth/login", json=credentials)

    assert_contract(login)
    assert login.status_code == 200
    me = api.get("/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert me.json()["supplier"]["legal_id"] == request.legal_id


def test_approve_sends_an_email(
    client: TestClient, admin_headers: dict, create_request, outbox: list
):
    request = create_request("association")

    response = client.post(API_PREFIX + _path(request.id), headers=admin_headers)

    assert response.status_code == 200
    [email] = outbox
    assert email.to == request.user.email
    assert "acceptée" in email.subject
    assert "Restos du Cœur Lyon 2" in email.body


# ----- 401 -----


def test_approve_without_token(api: httpx2.Client, create_request):
    response = api.post(_path(create_request().id))

    assert_contract(response, invalid_request=True)
    assert_error(response, 401, "unauthorized")


def test_approve_invalid_token(api: httpx2.Client, create_request):
    response = api.post(_path(create_request().id), headers={"Authorization": "Bearer not-a-jwt"})

    assert_contract(response)
    assert_error(response, 401, "unauthorized")


# ----- 403 -----


@pytest.mark.parametrize("headers", ["supplier_headers", "association_headers"])
def test_approve_not_admin(api: httpx2.Client, request, headers: str, create_request, outbox: list):
    registration = create_request()

    response = api.post(_path(registration.id), headers=request.getfixturevalue(headers))

    assert_contract(response)
    assert_error(response, 403, "forbidden")
    assert outbox == []


def test_approve_not_admin_unknown_request(api: httpx2.Client, supplier_headers: dict):
    """The role is checked first: other users cannot probe which requests exist."""
    response = api.post(_path(999), headers=supplier_headers)

    assert_contract(response)
    assert_error(response, 403, "forbidden")


# ----- 404 -----


def test_approve_unknown_request(api: httpx2.Client, admin_headers: dict):
    response = api.post(_path(999), headers=admin_headers)

    assert_contract(response)
    assert_error(response, 404, "not_found")


@pytest.mark.parametrize("request_id", ["abc", "0", "-1", str(2**63)])
def test_approve_impossible_id(client: TestClient, admin_headers: dict, request_id: str):
    """No 400/422 in the contract: an id that cannot exist is not found.

    Sent in-process: through Prism, an id that is not an int64 is a request violation.
    """
    response = client.post(API_PREFIX + _path(request_id), headers=admin_headers)

    assert_error(response, 404, "not_found")


# ----- 409 -----


@pytest.mark.parametrize("status", [RegistrationStatus.APPROVED, RegistrationStatus.REJECTED])
def test_approve_already_decided(
    api: httpx2.Client, db: Session, admin_headers: dict, create_request, status, outbox: list
):
    request = create_request(status=status)

    response = api.post(_path(request.id), headers=admin_headers)

    assert_contract(response)
    assert_error(response, 409, "conflict")
    assert outbox == []
    assert db.query(Supplier).count() == 0


def test_approve_twice(api: httpx2.Client, db: Session, admin_headers: dict, create_request):
    request = create_request()

    first = api.post(_path(request.id), headers=admin_headers)
    second = api.post(_path(request.id), headers=admin_headers)

    assert first.status_code == 200
    assert_contract(second)
    assert_error(second, 409, "conflict")
    assert db.query(Supplier).count() == 1
