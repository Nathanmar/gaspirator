"""US-02, US-04: lots published by the suppliers (/lots, /me/lots)."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app import models
from app.auth import get_current_supplier, get_current_user
from app.db import get_session
from app.errors import forbidden, not_found
from app.schemas import Address, Error, GeoPoint, Lot, LotCreate, LotStatus, SupplierSummary

router = APIRouter(tags=["Lots"])

DbSession = Annotated[Session, Depends(get_session)]
CurrentSupplier = Annotated[models.Supplier, Depends(get_current_supplier)]

# Path parameters of the contract are int64.
LotId = Annotated[int, Path(alias="lotId", ge=1, le=2**63 - 1)]


def get_lot_reader(user: Annotated[models.User, Depends(get_current_user)]) -> models.User:
    """FastAPI dependency: the current user if they run a supplier or an association, or 403.

    Checked before the lot is looked up, so that other users cannot probe which lots exist.
    """
    if user.supplier_id is None and user.association_id is None:
        raise forbidden("Action réservée aux fournisseurs et aux associations.")
    return user


def _errors(*status_codes: int) -> dict[int | str, dict]:
    """Error responses documented in the generated OpenAPI (/docs)."""
    return {status: {"model": Error} for status in status_codes}


def lot_status(lot: models.Lot, now: datetime) -> LotStatus:
    """`LotStatus` of the contract, computed from the remaining quantity and the dates.

    `collected` needs the reservations (US-04, US-05): until then, a lot with nothing left
    to reserve is `reserved`.
    """
    if lot.remaining_quantity == 0:
        return LotStatus.RESERVED
    if lot.pickup_end <= now or lot.use_by_date < now.date():
        return LotStatus.EXPIRED
    return LotStatus.AVAILABLE


def supplier_summary(supplier: models.Supplier) -> SupplierSummary:
    return SupplierSummary(
        id=supplier.id,
        name=supplier.name,
        supplier_type=supplier.supplier_type,
        address=Address(
            street=supplier.street, postal_code=supplier.postal_code, city=supplier.city
        ),
        location=GeoPoint(latitude=supplier.latitude, longitude=supplier.longitude),
        contact_phone=supplier.contact_phone,
    )


def to_schema(lot: models.Lot, now: datetime) -> Lot:
    return Lot(
        id=lot.id,
        supplier=supplier_summary(lot.supplier),
        title=lot.title,
        category=lot.category,
        quantity=lot.quantity,
        remaining_quantity=lot.remaining_quantity,
        unit=lot.unit,
        divisible=lot.divisible,
        use_by_date=lot.use_by_date,
        allergens=lot.allergens,
        storage=lot.storage,
        pickup_start=lot.pickup_start,
        pickup_end=lot.pickup_end,
        status=lot_status(lot, now),
        created_at=lot.created_at,
    )


@router.post(
    "/lots",
    status_code=201,
    response_model=Lot,
    operation_id="createLot",
    responses=_errors(400, 401, 403, 422),
)
def create_lot(payload: LotCreate, supplier: CurrentSupplier, session: DbSession) -> Lot:
    """Publish a lot of the current supplier, `available` with its whole quantity."""
    lot = models.Lot(
        supplier=supplier,
        title=payload.title,
        category=payload.category,
        quantity=payload.quantity,
        remaining_quantity=payload.quantity,
        unit=payload.unit,
        divisible=payload.divisible,
        use_by_date=payload.use_by_date,
        allergens=[allergen.value for allergen in payload.allergens],
        storage=payload.storage,
        pickup_start=payload.pickup_start,
        pickup_end=payload.pickup_end,
    )
    session.add(lot)
    session.commit()
    session.refresh(lot)
    return to_schema(lot, datetime.now(UTC))


@router.get(
    "/lots/{lotId}",
    response_model=Lot,
    operation_id="getLot",
    responses=_errors(401, 403, 404),
)
def get_lot(
    lot_id: LotId,
    user: Annotated[models.User, Depends(get_lot_reader)],
    session: DbSession,
) -> Lot:
    """A lot, for any association or for the supplier that published it."""
    lot = session.get(models.Lot, lot_id)
    if lot is None:
        raise not_found("Lot introuvable.")
    if user.supplier_id is not None and lot.supplier_id != user.supplier_id:
        raise forbidden("Ce lot a été publié par un autre fournisseur.")
    return to_schema(lot, datetime.now(UTC))
