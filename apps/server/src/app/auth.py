"""Passwords, JWT access tokens, opaque refresh tokens and the current-user dependency."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import bcrypt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.db import get_session
from app.errors import unauthorized
from app.models import User
from app.settings import get_settings

ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"

# Compared against when the e-mail is unknown, so that the response time does not reveal
# whether an account exists.
_DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt()).decode()


def hash_password(password: str) -> str:
    """Hash a password with bcrypt (bcrypt only uses the first 72 bytes)."""
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str | None) -> bool:
    """Check a password; with no hash, burn the same time and return False."""
    candidate = password.encode()[:72]
    if password_hash is None:
        bcrypt.checkpw(candidate, _DUMMY_PASSWORD_HASH.encode())
        return False
    return bcrypt.checkpw(candidate, password_hash.encode())


def create_access_token(user: User) -> str:
    """Signed JWT identifying the user, valid `access_token_ttl_seconds`."""
    settings = get_settings()
    now = datetime.now(UTC)
    claims = {
        "sub": str(user.id),
        "role": user.role.value,
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(seconds=settings.access_token_ttl_seconds),
    }
    return jwt.encode(claims, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, object] | None:
    """Claims of a valid, unexpired access token; None otherwise."""
    try:
        claims = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None
    if claims.get("type") != ACCESS_TOKEN_TYPE:
        return None
    return claims


def generate_refresh_token() -> str:
    """Opaque, unguessable refresh token (only its hash is stored)."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    """FastAPI dependency: the user of the `Authorization: Bearer` access token, or 401."""
    if credentials is None:
        raise unauthorized("Authentification requise.")
    claims = decode_access_token(credentials.credentials)
    user = None
    if claims is not None and str(claims.get("sub", "")).isdigit():
        user = session.get(User, int(claims["sub"]))
    if user is None:
        raise unauthorized("Token d'accès invalide ou expiré.")
    return user
