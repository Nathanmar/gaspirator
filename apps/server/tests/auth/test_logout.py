"""POST /auth/logout: 204 and 401 (format `Error`). Requires the Bearer access token."""

from datetime import UTC, datetime, timedelta

import httpx2
from jose import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import ALGORITHM, hash_refresh_token
from app.models import RefreshToken, User
from app.settings import get_settings
from tests.prism import assert_contract

LOGOUT_PATH = "/auth/logout"
REFRESH_PATH = "/auth/refresh"


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _assert_unauthorized(response) -> None:
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "unauthorized"
    assert isinstance(data["message"], str) and data["message"]


def _stored(db: Session, refresh_token: str) -> RefreshToken:
    return db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(refresh_token))
    )


def _login(api: httpx2.Client, email: str) -> dict:
    response = api.post("/auth/login", json={"email": email, "password": "testPass1."})
    assert response.status_code == 200
    return response.json()


# ----- 204 -----


def test_logout(api: httpx2.Client, tokens: dict, db: Session):
    response = api.post(
        LOGOUT_PATH,
        json={"refresh_token": tokens["refresh_token"]},
        headers=_bearer(tokens["access_token"]),
    )

    assert_contract(response)
    assert response.status_code == 204
    assert response.content == b""
    assert _stored(db, tokens["refresh_token"]).revoked_at is not None


def test_logout_revokes_the_refresh_token(api: httpx2.Client, tokens: dict):
    api.post(
        LOGOUT_PATH,
        json={"refresh_token": tokens["refresh_token"]},
        headers=_bearer(tokens["access_token"]),
    )

    response = api.post(REFRESH_PATH, json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 401


def test_logout_is_idempotent(api: httpx2.Client, tokens: dict):
    for _ in range(2):
        response = api.post(
            LOGOUT_PATH,
            json={"refresh_token": tokens["refresh_token"]},
            headers=_bearer(tokens["access_token"]),
        )
        assert_contract(response)
        assert response.status_code == 204


def test_logout_unknown_refresh_token(api: httpx2.Client, tokens: dict):
    response = api.post(
        LOGOUT_PATH,
        json={"refresh_token": "not-a-real-token"},
        headers=_bearer(tokens["access_token"]),
    )

    assert_contract(response)
    assert response.status_code == 204


def test_logout_keeps_other_users_sessions(
    api: httpx2.Client, tokens: dict, create_user, db: Session
):
    """A user cannot revoke the refresh token of someone else."""
    create_user(email="paul.martin@example.org")
    other_tokens = _login(api, "paul.martin@example.org")

    response = api.post(
        LOGOUT_PATH,
        json={"refresh_token": other_tokens["refresh_token"]},
        headers=_bearer(tokens["access_token"]),
    )

    assert_contract(response)
    assert response.status_code == 204
    assert _stored(db, other_tokens["refresh_token"]).revoked_at is None


def test_logout_keeps_other_sessions_of_the_user(api: httpx2.Client, tokens: dict, db: Session):
    other_device = _login(api, "marie.dupont@example.org")

    api.post(
        LOGOUT_PATH,
        json={"refresh_token": tokens["refresh_token"]},
        headers=_bearer(tokens["access_token"]),
    )

    assert _stored(db, other_device["refresh_token"]).revoked_at is None


# ----- 401 -----


def test_logout_without_access_token(api: httpx2.Client, tokens: dict, db: Session):
    response = api.post(LOGOUT_PATH, json={"refresh_token": tokens["refresh_token"]})

    assert_contract(response, invalid_request=True)
    _assert_unauthorized(response)
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert _stored(db, tokens["refresh_token"]).revoked_at is None


def test_logout_without_access_token_and_body(api: httpx2.Client):
    """Authentication is checked before the body."""
    response = api.post(LOGOUT_PATH, json={})

    assert_contract(response, invalid_request=True)
    _assert_unauthorized(response)


def test_logout_invalid_access_token(api: httpx2.Client, tokens: dict):
    response = api.post(
        LOGOUT_PATH,
        json={"refresh_token": tokens["refresh_token"]},
        headers=_bearer("not-a-jwt"),
    )

    assert_contract(response)
    _assert_unauthorized(response)


def test_logout_with_refresh_token_as_bearer(api: httpx2.Client, tokens: dict):
    response = api.post(
        LOGOUT_PATH,
        json={"refresh_token": tokens["refresh_token"]},
        headers=_bearer(tokens["refresh_token"]),
    )

    assert_contract(response)
    _assert_unauthorized(response)


def test_logout_expired_access_token(api: httpx2.Client, tokens: dict, db: Session):
    user = db.scalar(select(User))
    past = datetime.now(UTC) - timedelta(hours=1)
    expired = jwt.encode(
        {"sub": str(user.id), "role": "manager", "type": "access", "iat": past, "exp": past},
        get_settings().secret_key,
        algorithm=ALGORITHM,
    )

    response = api.post(
        LOGOUT_PATH, json={"refresh_token": tokens["refresh_token"]}, headers=_bearer(expired)
    )

    assert_contract(response)
    _assert_unauthorized(response)


def test_logout_access_token_signed_with_another_key(api: httpx2.Client, tokens: dict, db: Session):
    user = db.scalar(select(User))
    forged = jwt.encode(
        {"sub": str(user.id), "role": "admin", "type": "access"}, "not-the-secret", ALGORITHM
    )

    response = api.post(
        LOGOUT_PATH, json={"refresh_token": tokens["refresh_token"]}, headers=_bearer(forged)
    )

    assert_contract(response)
    _assert_unauthorized(response)


def test_logout_deleted_user(api: httpx2.Client, tokens: dict, db: Session):
    db.delete(db.scalar(select(User)))
    db.commit()

    response = api.post(
        LOGOUT_PATH,
        json={"refresh_token": tokens["refresh_token"]},
        headers=_bearer(tokens["access_token"]),
    )

    assert_contract(response)
    _assert_unauthorized(response)
