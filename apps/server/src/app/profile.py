"""US-01 / US-06: account and organisation of the logged-in user (tag `Profile`)."""

from fastapi import APIRouter

from app.dependencies import CurrentUser, Organizations
from app.repositories import OrganizationRepository, StoredUser
from app.schemas import Error, Me

router = APIRouter(tags=["Profile"])

_UNAUTHORIZED = {401: {"model": Error, "description": "Token absent, invalide ou expiré"}}


async def _to_me(user: StoredUser, organizations: OrganizationRepository) -> Me:
    organization = (
        await organizations.get(user.organization_id) if user.organization_id is not None else None
    )
    return Me(
        id=user.id,
        email=user.email,
        firstname=user.firstname,
        lastname=user.lastname,
        role=user.role,
        organization=organization,
    )


@router.get("/me", response_model=Me, operation_id="getMe", responses=_UNAUTHORIZED)
async def get_me(user: CurrentUser, organizations: Organizations) -> Me:
    """Récupérer l'utilisateur connecté."""
    return await _to_me(user, organizations)
