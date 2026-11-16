"""FastAPI dependencies shared by the routes.

When PostgreSQL is wired, only `get_user_repository` and `get_organization_repository`
change: they return the database repositories instead of the in-memory ones.
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth import verify_token
from app.errors import ApiError
from app.repositories import (
    InMemoryOrganizationRepository,
    InMemoryUserRepository,
    OrganizationRepository,
    StoredUser,
    UserRepository,
)

_users = InMemoryUserRepository()
_organizations = InMemoryOrganizationRepository()


def get_user_repository() -> UserRepository:
    return _users


def get_organization_repository() -> OrganizationRepository:
    return _organizations


Users = Annotated[UserRepository, Depends(get_user_repository)]
Organizations = Annotated[OrganizationRepository, Depends(get_organization_repository)]

# `bearerAuth` in the contract: `Authorization: Bearer <JWT>`, the JWT `sub` is the user id.
_bearer = HTTPBearer(scheme_name="bearerAuth", auto_error=False)


def _unauthorized() -> ApiError:
    return ApiError(401, "unauthorized", "Token absent, invalide ou expiré.")


async def get_current_user(
    users: Users,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> StoredUser:
    """The user owning the Bearer token, or 401."""
    if credentials is None:
        raise _unauthorized()
    payload = verify_token(credentials.credentials)
    subject = payload.get("sub") if payload else None
    if not isinstance(subject, str) or not subject.isdigit():
        raise _unauthorized()
    user = await users.get(int(subject))
    if user is None:
        raise _unauthorized()
    return user


CurrentUser = Annotated[StoredUser, Depends(get_current_user)]
