"""GET /me: 200 `Me` and 401 (format `Error`). Requires the Bearer access token."""

from datetime import UTC, datetime, timedelta

import httpx2
import jwt
from sqlalchemy.orm import Session

from app.auth import ALGORITHM, create_access_token
from app.schemas import UserRole
from app.settings import get_settings
from tests.prism import assert_contract

ME_PATH = "/me"


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _assert_unauthorized(response) -> None:
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "unauthorized"
    assert isinstance(data["message"], str) and data["message"]


def test_me_supplier_manager(api: httpx2.Client, create_supplier, create_user, auth_headers):
    """The manager of a supplier gets the contract `Supplier`, and no association."""
    supplier = create_supplier()
    manager = create_user(supplier=supplier)

    response = api.get(ME_PATH, headers=auth_headers(manager))

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "id": manager.id,
        "email": "marie.dupont@example.org",
        "firstname": "Marie",
        "lastname": "Dupont",
        "role": "manager",
        "supplier": {
            "id": supplier.id,
            "name": "Cantine du lycée Ampère",
            "supplier_type": "canteen",
            "address": {
                "street": "12 rue de la République",
                "postal_code": "69002",
                "city": "Lyon",
            },
            "location": {"latitude": 45.7578, "longitude": 4.832},
            "contact_phone": "04 78 00 00 00",
            "legal_id": supplier.legal_id,
            "created_at": data["supplier"]["created_at"],
        },
        "association": None,
    }
    assert datetime.fromisoformat(data["supplier"]["created_at"])


def test_me_association_manager(api: httpx2.Client, create_association, create_user, auth_headers):
    """The manager of an association gets the contract `Association`, and no supplier."""
    association = create_association()
    manager = create_user(association=association)

    response = api.get(ME_PATH, headers=auth_headers(manager))

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert data["supplier"] is None
    assert data["association"] == {
        "id": association.id,
        "name": "Restos du Cœur Lyon 2",
        "address": {"street": "3 rue Sainte-Hélène", "postal_code": "69002", "city": "Lyon"},
        "location": {"latitude": 45.7537, "longitude": 4.8286},
        "contact_phone": "04 78 00 00 01",
        "legal_id": association.legal_id,
        "created_at": data["association"]["created_at"],
    }


def test_me_admin(api: httpx2.Client, create_user, auth_headers):
    """A platform admin manages neither a supplier nor an association."""
    admin = create_user(email="admin@gaspirator.fr", role=UserRole.ADMIN)

    response = api.get(ME_PATH, headers=auth_headers(admin))

    assert_contract(response)
    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert response.json()["supplier"] is None
    assert response.json()["association"] is None


def test_me_with_token_from_login(api: httpx2.Client, tokens: dict):
    """The access token returned by POST /auth/login opens GET /me."""
    response = api.get(ME_PATH, headers=_bearer(tokens["access_token"]))

    assert_contract(response)
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
