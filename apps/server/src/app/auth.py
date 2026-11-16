"""Authentication module using python-jose JWT."""

import os
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    """Hash a password with bcrypt (bcrypt only uses the first 72 bytes)."""
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Check a password against a bcrypt hash made by `hash_password`."""
    return bcrypt.checkpw(password.encode()[:72], password_hash.encode())


def create_access_token(data: dict[str, object], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token using python-jose."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.now(UTC)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict[str, object] | None:
    """Verify and decode a JWT token using python-jose."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
