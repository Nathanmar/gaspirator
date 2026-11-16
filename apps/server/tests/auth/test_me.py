"""GET /me: 200 `Me` and 401 (format `Error`). Requires the Bearer access token."""

from datetime import UTC, datetime, timedelta

import httpx2
from jose import jwt
from sqlalchemy.orm import Session

from app.auth import ALGORITHM, create_access_token
from app.models import Association, Supplier
from app.schemas import SupplierType, UserRole
from app.settings import get_settings
from tests.prism import assert_contract

ME_PATH = "/me"

ADDRESS = {"street": "12 rue de la République", "postal_code": "69002", "city": "Lyon"}


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _assert_unauthorized(response) -> None:
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "unauthorized"
    assert isinstance(data["message"], str) and data["message"]


def _add_supplier(db: Session) -> Supplier:
    supplier = Supplier(
        name="Cantine du lycée Ampère",
        supplier_type=SupplierType.CANTEEN,
        **ADDRESS,
        latitude=45.7578,
        longitude=4.8320,
        contact_phone="04 78 00 00 00",
        legal_id="19690103400017",
    )
    db.add(supplier)
    db.commit()
    return supplier


def _add_association(db: Session) -> Association:
    association = Association(
        name="Restos du Cœur Lyon 2",
        **ADDRESS,
        latitude=45.75,
        longitude=4.85,
        contact_phone="04 78 00 00 01",
        legal_id="W691234567",
    )
    db.add(association)
    db.commit()
    return association


def test_me_supplier_manager(api: httpx2.Client, db: Session, create_user):
    """The manager of a supplier gets the contract `Supplier`, and no association."""
    supplier = _add_supplier(db)
    manager = create_user()
    manager.supplier = supplier
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
        "supplier": {
            "id": supplier.id,
            "name": "Cantine du lycée Ampère",
            "supplier_type": "canteen",
            "address": ADDRESS,
            "location": {"latitude": 45.7578, "longitude": 4.832},
            "contact_phone": "04 78 00 00 00",
            "legal_id": "19690103400017",
            "created_at": data["supplier"]["created_at"],
        },
        "association": None,
    }
    assert datetime.fromisoformat(data["supplier"]["created_at"])


def test_me_association_manager(api: httpx2.Client, db: Session, create_user):
    """The manager of an association gets the contract `Association`, and no supplier."""
    association = _add_association(db)
    manager = create_user()
    manager.association = association
    db.commit()

    response = api.get(ME_PATH, headers=_bearer(create_access_token(manager)))

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert data["supplier"] is None
    assert data["association"] == {
        "id": association.id,
        "name": "Restos du Cœur Lyon 2",
        "address": ADDRESS,
        "location": {"latitude": 45.75, "longitude": 4.85},
        "contact_phone": "04 78 00 00 01",
        "legal_id": "W691234567",
        "created_at": data["association"]["created_at"],
    }


def test_me_admin(api: httpx2.Client, create_user):
    """A platform admin manages neither a supplier nor an association."""
    admin = create_user(email="admin@gaspirator.fr", role=UserRole.ADMIN)

    response = api.get(ME_PATH, headers=_bearer(create_access_token(admin)))

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
