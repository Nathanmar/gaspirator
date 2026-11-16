"""US-01: login and session (/auth/*)."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.db import get_session
from app.errors import forbidden, unauthorized
from app.models import RefreshToken, User
from app.schemas import (
    AuthTokens,
    Error,
    LoginRequest,
    RefreshRequest,
    RegistrationStatus,
    UserRole,
)
from app.settings import get_settings

router = APIRouter(prefix="/auth", tags=["Auth"])

DbSession = Annotated[Session, Depends(get_session)]


def _errors(*status_codes: int) -> dict[int | str, dict]:
    """Error responses documented in the generated OpenAPI (/docs)."""
    return {status: {"model": Error} for status in status_codes}


_REGISTRATION_NOT_APPROVED = {
    RegistrationStatus.PENDING: "Votre demande d'inscription est en attente de validation.",
    RegistrationStatus.REJECTED: "Votre demande d'inscription a été refusée.",
}


def _check_can_log_in(user: User) -> None:
    """Managers can only log in once their registration request is approved."""
    if user.role != UserRole.MANAGER:
        return
    request = user.registration_request
    status = request.status if request is not None else RegistrationStatus.PENDING
    if status != RegistrationStatus.APPROVED:
        raise forbidden(_REGISTRATION_NOT_APPROVED[status])


def _issue_tokens(session: Session, user: User) -> AuthTokens:
    """New access token + new refresh token (stored hashed). Commits the session."""
    settings = get_settings()
    refresh_token = generate_refresh_token()
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=datetime.now(UTC) + timedelta(seconds=settings.refresh_token_ttl_seconds),
        )
    )
    session.commit()
    return AuthTokens(
        access_token=create_access_token(user),
        refresh_token=refresh_token,
        expires_in=settings.access_token_ttl_seconds,
    )


@router.post(
    "/login",
    response_model=AuthTokens,
    operation_id="login",
    responses=_errors(400, 401, 403, 422),
)
def login(payload: LoginRequest, session: DbSession) -> AuthTokens:
    """Log in with e-mail and password."""
    user = session.scalar(select(User).where(func.lower(User.email) == payload.email.lower()))
    if not verify_password(payload.password, user.password_hash if user else None):
        raise unauthorized("E-mail ou mot de passe incorrect.")
    _check_can_log_in(user)
    return _issue_tokens(session, user)


@router.post(
    "/refresh",
    response_model=AuthTokens,
    operation_id="refreshToken",
    responses=_errors(400, 401),
)
def refresh_token(payload: RefreshRequest, session: DbSession) -> AuthTokens:
    """Exchange a refresh token for new tokens; the refresh token sent is revoked."""
    now = datetime.now(UTC)
    stored = session.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == hash_refresh_token(payload.refresh_token))
        .with_for_update()
    )
    if stored is None or stored.expires_at <= now:
        raise unauthorized("Refresh token invalide ou expiré.")
    if stored.revoked_at is not None:
        # A rotated token is replayed: it may have been stolen, end all the user's sessions.
        session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == stored.user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        session.commit()
        raise unauthorized("Refresh token invalide ou expiré.")

    stored.revoked_at = now
    return _issue_tokens(session, stored.user)
