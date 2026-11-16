"""POST /auth/login: 200 `AuthTokens`, 400, 401, 403 and 422 (format `Error`)."""

import httpx2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import decode_access_token
from app.models import RefreshToken, RegistrationRequest
from app.schemas import RegistrationStatus, UserRole
from tests.prism import API_PREFIX, assert_contract

LOGIN_PATH = "/auth/login"
CREDENTIALS = {"email": "marie.dupont@example.org", "password": "testPass1."}


def _assert_error(response, status: int, code: str) -> dict:
    assert response.status_code == status
    data = response.json()
    assert data["code"] == code
    assert isinstance(data["message"], str) and data["message"]
    return data


def _refresh_token_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(RefreshToken))


# ----- 200 -----


def test_login_approved_manager(api: httpx2.Client, create_user, db: Session):
    user = create_user()

    response = api.post(LOGIN_PATH, json=CREDENTIALS)

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"access_token", "refresh_token", "token_type", "expires_in"}
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] == 900
    claims = decode_access_token(data["access_token"])
    assert claims is not None
    assert claims["sub"] == str(user.id)
    assert claims["role"] == "manager"
    assert data["refresh_token"]
    assert _refresh_token_count(db) == 1


def test_login_admin(api: httpx2.Client, create_user):
    """A platform admin has no registration request."""
    create_user(email="admin@gaspirator.fr", role=UserRole.ADMIN)

    response = api.post(LOGIN_PATH, json={**CREDENTIALS, "email": "admin@gaspirator.fr"})

    assert_contract(response)
    assert response.status_code == 200
    assert decode_access_token(response.json()["access_token"])["role"] == "admin"


def test_login_email_is_case_insensitive(api: httpx2.Client, create_user):
    create_user()

    response = api.post(LOGIN_PATH, json={**CREDENTIALS, "email": "Marie.Dupont@Example.org"})

    assert_contract(response)
    assert response.status_code == 200


def test_login_twice_opens_two_sessions(api: httpx2.Client, create_user, db: Session):
    create_user()

    first = api.post(LOGIN_PATH, json=CREDENTIALS).json()
    second = api.post(LOGIN_PATH, json=CREDENTIALS).json()

    assert first["refresh_token"] != second["refresh_token"]
    assert _refresh_token_count(db) == 2


def test_login_after_registration_and_approval(api: httpx2.Client, registration: dict, db: Session):
    """The account created by a registration request can log in once approved."""
    created = api.post("/registration-requests", json=registration).json()
    request = db.get(RegistrationRequest, created["id"])
    request.status = RegistrationStatus.APPROVED
    db.commit()

    response = api.post(LOGIN_PATH, json=CREDENTIALS)

    assert_contract(response)
    assert response.status_code == 200


# ----- 400 -----


@pytest.mark.parametrize(
    "body",
    ["{", '{"email": "marie.dupont@example.org",}', "not json"],
    ids=["unclosed", "trailing-comma", "plain-text"],
)
def test_login_malformed_json(client: TestClient, body: str):
    """Sent in-process: Prism never answers a malformed JSON body."""
    response = client.post(
        API_PREFIX + LOGIN_PATH, content=body, headers={"Content-Type": "application/json"}
    )

    _assert_error(response, 400, "bad_request")


# ----- 401 -----


def test_login_wrong_password(api: httpx2.Client, create_user, db: Session):
    create_user()

    response = api.post(LOGIN_PATH, json={**CREDENTIALS, "password": "wrongPass1."})

    assert_contract(response)
    _assert_error(response, 401, "unauthorized")
    assert _refresh_token_count(db) == 0


def test_login_unknown_email(api: httpx2.Client):
    response = api.post(LOGIN_PATH, json={**CREDENTIALS, "email": "nobody@example.org"})

    assert_contract(response)
    _assert_error(response, 401, "unauthorized")


def test_login_does_not_reveal_whether_email_exists(api: httpx2.Client, create_user):
    create_user()

    wrong_password = api.post(LOGIN_PATH, json={**CREDENTIALS, "password": "wrongPass1."})
    unknown_email = api.post(LOGIN_PATH, json={**CREDENTIALS, "email": "nobody@example.org"})

    assert wrong_password.json() == unknown_email.json()


@pytest.mark.parametrize("status", [RegistrationStatus.PENDING, RegistrationStatus.REJECTED])
def test_login_wrong_password_on_unapproved_account(
    api: httpx2.Client, create_user, status: RegistrationStatus
):
    """Without the right password, the registration status is not revealed (401, not 403)."""
    create_user(registration_status=status)

    response = api.post(LOGIN_PATH, json={**CREDENTIALS, "password": "wrongPass1."})

    assert_contract(response)
    _assert_error(response, 401, "unauthorized")


# ----- 403 -----


@pytest.mark.parametrize("status", [RegistrationStatus.PENDING, RegistrationStatus.REJECTED])
def test_login_unapproved_registration(
    api: httpx2.Client, create_user, db: Session, status: RegistrationStatus
):
    create_user(registration_status=status)

    response = api.post(LOGIN_PATH, json=CREDENTIALS)

    assert_contract(response)
    _assert_error(response, 403, "forbidden")
    assert _refresh_token_count(db) == 0


# ----- 422 -----


def _assert_validation_error(response, field: str) -> None:
    assert_contract(response, invalid_request=True)
    data = _assert_error(response, 422, "validation_error")
    assert field in [detail["field"] for detail in data["details"]]
    for detail in data["details"]:
        assert set(detail) == {"field", "message"}


def test_login_invalid_email(api: httpx2.Client):
    response = api.post(LOGIN_PATH, json={**CREDENTIALS, "email": "invalid-email"})
    _assert_validation_error(response, "email")


@pytest.mark.parametrize("field", ["email", "password"])
def test_login_missing_field(api: httpx2.Client, field: str):
    body = {key: value for key, value in CREDENTIALS.items() if key != field}
    response = api.post(LOGIN_PATH, json=body)
    _assert_validation_error(response, field)


def test_login_unknown_field(api: httpx2.Client):
    """additionalProperties: false"""
    response = api.post(LOGIN_PATH, json={**CREDENTIALS, "remember_me": True})
    _assert_validation_error(response, "remember_me")
