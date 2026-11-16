"""US-02, US-04: lots published by the suppliers (/lots, /me/lots)."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.auth import get_current_supplier
from app.db import get_session
from app.schemas import Address, Error, GeoPoint, Lot, LotCreate, LotStatus, SupplierSummary

router = APIRouter(tags=["Lots"])

DbSession = Annotated[Session, Depends(get_session)]
CurrentSupplier = Annotated[models.Supplier, Depends(get_current_supplier)]


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
