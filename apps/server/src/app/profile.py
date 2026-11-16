"""US-01: the logged-in user (GET /me)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app import models
from app.auth import get_current_user
from app.lots import supplier_summary
from app.schemas import Address, Association, Error, GeoPoint, Me, Supplier

# The contract puts GET /me under the `Auth` tag.
router = APIRouter(tags=["Auth"])

CurrentUser = Annotated[models.User, Depends(get_current_user)]


def to_supplier(supplier: models.Supplier) -> Supplier:
    """Contract `Supplier`: `SupplierSummary` + `legal_id` + `created_at`."""
    return Supplier(
        **supplier_summary(supplier).model_dump(),
        legal_id=supplier.legal_id,
        created_at=supplier.created_at,
    )


def to_association(association: models.Association) -> Association:
    """Contract `Association` from the `associations` row (address and location nested)."""
    return Association(
        id=association.id,
        name=association.name,
        address=Address(
            street=association.street,
            postal_code=association.postal_code,
            city=association.city,
        ),
        location=GeoPoint(latitude=association.latitude, longitude=association.longitude),
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
