"""POST /auth/refresh: 200 `AuthTokens`, 400 and 401 (format `Error`)."""

from datetime import UTC, datetime, timedelta

import httpx2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import decode_access_token, hash_refresh_token
from app.models import RefreshToken
from tests.prism import API_PREFIX, assert_contract

REFRESH_PATH = "/auth/refresh"


def _assert_error(response, status: int, code: str) -> dict:
    assert response.status_code == status
    data = response.json()
    assert data["code"] == code
    assert isinstance(data["message"], str) and data["message"]
    return data


def _stored(db: Session, refresh_token: str) -> RefreshToken:
    return db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(refresh_token))
    )


# ----- 200 -----


def test_refresh(api: httpx2.Client, tokens: dict):
    response = api.post(REFRESH_PATH, json={"refresh_token": tokens["refresh_token"]})

    assert_contract(response)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"access_token", "refresh_token", "token_type", "expires_in"}
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] == 900
    assert data["refresh_token"] != tokens["refresh_token"]
    claims = decode_access_token(data["access_token"])
    assert claims is not None
    assert claims["sub"] == decode_access_token(tokens["access_token"])["sub"]


def test_refresh_rotates_the_token(api: httpx2.Client, tokens: dict, db: Session):
    """The refresh token sent is invalidated and replaced."""
    new_tokens = api.post(REFRESH_PATH, json={"refresh_token": tokens["refresh_token"]}).json()

    assert _stored(db, tokens["refresh_token"]).revoked_at is not None
    assert _stored(db, new_tokens["refresh_token"]).revoked_at is None

    response = api.post(REFRESH_PATH, json={"refresh_token": new_tokens["refresh_token"]})
    assert_contract(response)
    assert response.status_code == 200


# ----- 400 -----


@pytest.mark.parametrize("body", ["{", '{"refresh_token": "abc",}', "not json"])
def test_refresh_malformed_json(client: TestClient, body: str):
    """Sent in-process: Prism never answers a malformed JSON body."""
    response = client.post(
        API_PREFIX + REFRESH_PATH, content=body, headers={"Content-Type": "application/json"}
    )

    _assert_error(response, 400, "bad_request")


@pytest.mark.parametrize(
    "body",
    [{}, {"refresh_token": 123}, {"refresh_token": "abc", "access_token": "abc"}],
    ids=["missing", "not-a-string", "unknown-field"],
)
def test_refresh_invalid_body(api: httpx2.Client, body: dict):
    """The contract has no 422 here: an incorrect parameter is a 400."""
    response = api.post(REFRESH_PATH, json=body)

    assert_contract(response, invalid_request=True)
    _assert_error(response, 400, "bad_request")


# ----- 401 -----


def test_refresh_unknown_token(api: httpx2.Client):
    response = api.post(REFRESH_PATH, json={"refresh_token": "not-a-real-token"})

    assert_contract(response)
    _assert_error(response, 401, "unauthorized")


def test_refresh_with_access_token(api: httpx2.Client, tokens: dict):
    response = api.post(REFRESH_PATH, json={"refresh_token": tokens["access_token"]})

    assert_contract(response)
    _assert_error(response, 401, "unauthorized")


def test_refresh_expired_token(api: httpx2.Client, tokens: dict, db: Session):
    _stored(db, tokens["refresh_token"]).expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()

    response = api.post(REFRESH_PATH, json={"refresh_token": tokens["refresh_token"]})

    assert_contract(response)
    _assert_error(response, 401, "unauthorized")


def test_refresh_already_used_token(api: httpx2.Client, tokens: dict):
    api.post(REFRESH_PATH, json={"refresh_token": tokens["refresh_token"]})

    response = api.post(REFRESH_PATH, json={"refresh_token": tokens["refresh_token"]})

    assert_contract(response)
    _assert_error(response, 401, "unauthorized")


def test_refresh_reuse_revokes_the_session(api: httpx2.Client, tokens: dict):
    """Reusing a rotated token (likely stolen) also revokes the token that replaced it."""
    new_tokens = api.post(REFRESH_PATH, json={"refresh_token": tokens["refresh_token"]}).json()
    api.post(REFRESH_PATH, json={"refresh_token": tokens["refresh_token"]})

    response = api.post(REFRESH_PATH, json={"refresh_token": new_tokens["refresh_token"]})

    assert_contract(response)
    _assert_error(response, 401, "unauthorized")
