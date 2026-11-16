"""US-01: the logged-in user (GET /me)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app import models
from app.auth import get_current_user
from app.schemas import Address, Error, GeoPoint, Me, Organization

# The contract puts GET /me under the `Auth` tag.
router = APIRouter(tags=["Auth"])

CurrentUser = Annotated[models.User, Depends(get_current_user)]


def to_organization(organization: models.Organization) -> Organization:
    """Contract `Organization` from the `organizations` row (address and location nested)."""
    return Organization(
        id=organization.id,
        type=organization.type,
        name=organization.name,
        supplier_type=organization.supplier_type,
        address=Address(
            street=organization.street,
            postal_code=organization.postal_code,
            city=organization.city,
        ),
        location=GeoPoint(latitude=organization.latitude, longitude=organization.longitude),
        contact_phone=organization.contact_phone,
        legal_id=organization.legal_id,
        created_at=organization.created_at,
    )


@router.get(
    "/me",
    response_model=Me,
    operation_id="getMe",
    responses={401: {"model": Error}},
)
def get_me(user: CurrentUser) -> Me:
    """Récupérer l'utilisateur connecté."""
    return Me(
        id=user.id,
        email=user.email,
        firstname=user.firstname,
        lastname=user.lastname,
        role=user.role,
        organization=to_organization(user.organization) if user.organization else None,
    )
