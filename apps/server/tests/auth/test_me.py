"""GET /me: 200 `Me` and 401 (format `Error`). Requires the Bearer access token."""

from datetime import UTC, datetime, timedelta

import httpx2
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.orm import Session

from app.auth import ALGORITHM, create_access_token
from app.models import Organization
from app.schemas import OrganizationType, SupplierType, UserRole
from app.settings import get_settings
from tests.prism import assert_contract

ME_PATH = "/me"
ME_URL = "/api/v1/me"

# The contract declares `Me.organization` and `supplier_type` nullable, but writes them as
# `nullable` + `allOf`, which Prism does not let be null. Responses with one of these null
# are checked with the in-process `client` (as in tests/registration) until it is fixed.


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _assert_unauthorized(response) -> None:
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "unauthorized"
    assert isinstance(data["message"], str) and data["message"]


def _add_organization(db: Session, **overrides) -> Organization:
    fields = {
        "type": OrganizationType.SUPPLIER,
        "name": "Cantine du lycée Ampère",
        "supplier_type": SupplierType.CANTEEN,
        "street": "12 rue de la République",
        "postal_code": "69002",
        "city": "Lyon",
        "latitude": 45.7578,
        "longitude": 4.8320,
        "contact_phone": "04 78 00 00 00",
        "legal_id": "19690103400017",
    }
    organization = Organization(**{**fields, **overrides})
    db.add(organization)
    db.commit()
    return organization


def test_me_manager(api: httpx2.Client, db: Session, create_user):
    """A manager gets their account and their organisation (contract `Organization`)."""
    organization = _add_organization(db)
    manager = create_user()
    manager.organization = organization
    db.commit()

    response = api.get(ME_PATH, headers=_bearer(create_access_token(manager)))

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "id": manager.id,
        "email": "marie.dupont@example.org",
        "firstname": "Marie",
        "lastname": "Dupont",
        "role": "manager",
        "organization": {
            "id": organization.id,
            "type": "supplier",
            "name": "Cantine du lycée Ampère",
            "supplier_type": "canteen",
            "address": {
                "street": "12 rue de la République",
                "postal_code": "69002",
                "city": "Lyon",
            },
            "location": {"latitude": 45.7578, "longitude": 4.832},
            "contact_phone": "04 78 00 00 00",
            "legal_id": "19690103400017",
            "created_at": data["organization"]["created_at"],
        },
    }
    assert datetime.fromisoformat(data["organization"]["created_at"])


def test_me_association_manager(client: TestClient, db: Session, create_user):
    """An association has no supplier_type (null: checked without Prism, see above)."""
    organization = _add_organization(
        db, type=OrganizationType.ASSOCIATION, supplier_type=None, legal_id="W691234567"
    )
    manager = create_user()
    manager.organization = organization
    db.commit()

    response = client.get(ME_URL, headers=_bearer(create_access_token(manager)))

    assert response.status_code == 200
    assert response.json()["organization"]["type"] == "association"
    assert response.json()["organization"]["supplier_type"] is None


def test_me_admin_has_no_organization(client: TestClient, create_user):
    """An admin has no organisation (null: checked without Prism, see above)."""
    admin = create_user(email="admin@gaspirator.fr", role=UserRole.ADMIN)

    response = client.get(ME_URL, headers=_bearer(create_access_token(admin)))

    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert response.json()["organization"] is None


def test_me_with_token_from_login(client: TestClient, tokens: dict):
    """The access token returned by POST /auth/login opens GET /me.

    The `tokens` manager has no organisation yet (null: checked without Prism, see above).
    """
    response = client.get(ME_URL, headers=_bearer(tokens["access_token"]))

    assert response.status_code == 200
    assert response.json()["email"] == "marie.dupont@example.org"


def test_me_without_token(api: httpx2.Client):
    response = api.get(ME_PATH)

    assert_contract(response, invalid_request=True)
    _assert_unauthorized(response)


def test_me_invalid_token(api: httpx2.Client):
    response = api.get(ME_PATH, headers=_bearer("not-a-jwt"))

    assert_contract(response)
    _assert_unauthorized(response)


def test_me_expired_token(api: httpx2.Client, create_user):
    user = create_user()
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(user.id),
            "role": "manager",
            "type": "access",
            "iat": now - timedelta(hours=1),
            "exp": now - timedelta(minutes=1),
        },
        get_settings().secret_key,
        algorithm=ALGORITHM,
    )

    response = api.get(ME_PATH, headers=_bearer(token))

    assert_contract(response)
    _assert_unauthorized(response)


def test_me_refresh_token_is_not_an_access_token(api: httpx2.Client, tokens: dict):
    response = api.get(ME_PATH, headers=_bearer(tokens["refresh_token"]))

    assert_contract(response)
    _assert_unauthorized(response)


def test_me_deleted_user(api: httpx2.Client, db: Session, create_user):
    user = create_user()
    token = create_access_token(user)
    db.delete(user)
    db.commit()

    response = api.get(ME_PATH, headers=_bearer(token))

    assert_contract(response)
    _assert_unauthorized(response)
