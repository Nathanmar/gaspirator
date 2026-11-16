"""US-01: the logged-in user (GET /me)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app import models
from app.auth import get_current_user
from app.schemas import Address, Association, Error, GeoPoint, Me, Supplier

# The contract puts GET /me under the `Auth` tag.
router = APIRouter(tags=["Auth"])

CurrentUser = Annotated[models.User, Depends(get_current_user)]


def _address(entity: models.Supplier | models.Association) -> Address:
    return Address(street=entity.street, postal_code=entity.postal_code, city=entity.city)


def _location(entity: models.Supplier | models.Association) -> GeoPoint:
    return GeoPoint(latitude=entity.latitude, longitude=entity.longitude)


def to_supplier(supplier: models.Supplier) -> Supplier:
    """Contract `Supplier` from the `suppliers` row (address and location nested)."""
    return Supplier(
        id=supplier.id,
        name=supplier.name,
        supplier_type=supplier.supplier_type,
        address=_address(supplier),
        location=_location(supplier),
        contact_phone=supplier.contact_phone,
        legal_id=supplier.legal_id,
        created_at=supplier.created_at,
    )


def to_association(association: models.Association) -> Association:
    """Contract `Association` from the `associations` row (address and location nested)."""
    return Association(
        id=association.id,
        name=association.name,
        address=_address(association),
        location=_location(association),
        contact_phone=association.contact_phone,
        legal_id=association.legal_id,
        created_at=association.created_at,
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
        supplier=to_supplier(user.supplier) if user.supplier else None,
        association=to_association(user.association) if user.association else None,
    )
