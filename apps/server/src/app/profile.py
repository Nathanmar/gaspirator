"""US-01 / US-06: account and organisation of the logged-in user (tag `Profile`)."""

from fastapi import APIRouter, Response

from app.auth import hash_password, verify_password
from app.dependencies import CurrentUser, Organizations, Users
from app.errors import ApiError
from app.repositories import OrganizationRepository, StoredUser
from app.schemas import Error, ErrorDetail, Me, MeUpdate, Organization, PasswordChange

router = APIRouter(tags=["Profile"])

_UNAUTHORIZED = {401: {"model": Error, "description": "Token absent, invalide ou expiré"}}
_BAD_REQUEST = {400: {"model": Error, "description": "Requête malformée"}}
_VALIDATION = {422: {"model": Error, "description": "Contraintes de validation non respectées"}}
_NOT_FOUND = {404: {"model": Error, "description": "Ressource introuvable"}}


def _conflict(description: str) -> dict:
    return {409: {"model": Error, "description": description}}


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


@router.patch(
    "/me",
    response_model=Me,
    operation_id="updateMe",
    responses={
        **_BAD_REQUEST,
        **_UNAUTHORIZED,
        **_conflict("Le nouvel e-mail est déjà utilisé"),
        **_VALIDATION,
    },
)
async def update_me(
    payload: MeUpdate, user: CurrentUser, users: Users, organizations: Organizations
) -> Me:
    """Modifier mon compte."""
    changes = payload.model_dump(exclude_unset=True)

    if "email" in changes:
        owner = await users.get_by_email(changes["email"])
        if owner is not None and owner.id != user.id:
            raise ApiError(409, "conflict", "Cette adresse e-mail est déjà utilisée.")

    updated = await users.update(user.model_copy(update=changes))
    return await _to_me(updated, organizations)


@router.put(
    "/me/password",
    status_code=204,
    response_class=Response,
    operation_id="changePassword",
    responses={**_BAD_REQUEST, **_UNAUTHORIZED, **_VALIDATION},
)
async def change_password(payload: PasswordChange, user: CurrentUser, users: Users) -> Response:
    """Changer mon mot de passe."""
    if not verify_password(payload.current_password, user.password_hash):
        raise ApiError(
            422,
            "validation_error",
            "Certains champs sont invalides.",
            details=[ErrorDetail(field="current_password", message="mot de passe incorrect")],
        )

    await users.update(
        user.model_copy(update={"password_hash": hash_password(payload.new_password)})
    )
    return Response(status_code=204)


async def _my_organization(user: StoredUser, organizations: OrganizationRepository) -> Organization:
    """The user's organisation, or 404 (an admin belongs to no organisation)."""
    organization = (
        await organizations.get(user.organization_id) if user.organization_id is not None else None
    )
    if organization is None:
        raise ApiError(404, "not_found", "Vous n'appartenez à aucune organisation.")
    return organization


@router.get(
    "/me/organization",
    response_model=Organization,
    operation_id="getMyOrganization",
    responses={**_UNAUTHORIZED, **_NOT_FOUND},
)
async def get_my_organization(user: CurrentUser, organizations: Organizations) -> Organization:
    """Récupérer mon organisation."""
    return await _my_organization(user, organizations)
