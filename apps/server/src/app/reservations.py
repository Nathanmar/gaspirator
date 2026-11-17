"""US-04: reservations of lots by the associations
(/lots/{lotId}/reservations, /me/reservations, /reservations/{reservationId})."""

import secrets
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import func, select

from app import models
from app.auth import get_current_association
from app.errors import conflict, forbidden, invalid_fields, not_found
from app.lots import (
    CurrentSupplier,
    DbSession,
    LotId,
    get_lot_reader,
    lot_status,
    supplier_summary,
)
from app.schemas import (
    Address,
    AssociationSummary,
    Error,
    ErrorDetail,
    GeoPoint,
    LotStatus,
    LotSummary,
    PageMeta,
    Reservation,
    ReservationCreate,
    ReservationList,
    ReservationPage,
    ReservationStatus,
)

router = APIRouter(tags=["Reservations"])

CurrentAssociation = Annotated[models.Association, Depends(get_current_association)]

# Path parameters of the contract are int64.
ReservationId = Annotated[int, Path(alias="reservationId", ge=1, le=2**63 - 1)]


def _errors(*status_codes: int) -> dict[int | str, dict]:
    """Error responses documented in the generated OpenAPI (/docs)."""
    return {status: {"model": Error} for status in status_codes}


def association_summary(association: models.Association) -> AssociationSummary:
    return AssociationSummary(
        id=association.id,
        name=association.name,
        address=Address(
            street=association.street,
            postal_code=association.postal_code,
            city=association.city,
        ),
        location=GeoPoint(latitude=association.latitude, longitude=association.longitude),
        contact_phone=association.contact_phone,
    )


def lot_summary(lot: models.Lot) -> LotSummary:
    return LotSummary(
        id=lot.id,
        title=lot.title,
        unit=lot.unit,
        divisible=lot.divisible,
        use_by_date=lot.use_by_date,
        storage=lot.storage,
        pickup_start=lot.pickup_start,
        pickup_end=lot.pickup_end,
        supplier=supplier_summary(lot.supplier),
    )


def to_schema(reservation: models.Reservation, *, with_pickup_code: bool) -> Reservation:
    """`with_pickup_code` only for the association that reserved."""
    return Reservation(
        id=reservation.id,
        lot=lot_summary(reservation.lot),
        association=association_summary(reservation.association),
        quantity=reservation.quantity,
        pickup_at=reservation.pickup_at,
        status=reservation.status,
        pickup_code=reservation.pickup_code if with_pickup_code else None,
        created_at=reservation.created_at,
        collected_at=reservation.collected_at,
    )


@router.get(
    "/lots/{lotId}/reservations",
    response_model=ReservationList,
    operation_id="listLotReservations",
    responses=_errors(401, 403, 404),
)
def list_lot_reservations(
    lot_id: LotId, supplier: CurrentSupplier, session: DbSession
) -> ReservationList:
    """The reservations of a lot of the current supplier, most recent first, without their
    pickup codes."""
    lot = session.get(models.Lot, lot_id)
    if lot is None:
        raise not_found("Lot introuvable.")
    if lot.supplier_id != supplier.id:
        raise forbidden("Ce lot a été publié par un autre fournisseur.")
    reservations = session.scalars(
        select(models.Reservation)
        .where(models.Reservation.lot_id == lot.id)
        .order_by(models.Reservation.created_at.desc(), models.Reservation.id.desc())
    ).all()
    return ReservationList(
        data=[to_schema(reservation, with_pickup_code=False) for reservation in reservations]
    )


def _reserved_quantity(lot: models.Lot, payload: ReservationCreate, now: datetime) -> Decimal:
    """The quantity to take off the lot, or 422 for every field that breaks a rule."""
    details: list[ErrorDetail] = []
    quantity = payload.quantity
    if not lot.divisible:
        if quantity is not None and quantity != lot.quantity:
            message = (
                f"un lot indivisible est réservé en entier ({lot.quantity.normalize():f} ou rien)"
            )
            details.append(ErrorDetail(field="quantity", message=message))
        quantity = lot.quantity
    elif quantity is None:
        details.append(
            ErrorDetail(field="quantity", message="champ obligatoire pour un lot divisible")
        )

    if not lot.pickup_start <= payload.pickup_at <= lot.pickup_end:
        details.append(
            ErrorDetail(
                field="pickup_at", message="doit être comprise dans le créneau de collecte du lot"
            )
        )
    elif payload.pickup_at < now:
        details.append(ErrorDetail(field="pickup_at", message="ne doit pas être déjà passée"))

    if details:
        raise invalid_fields(details)
    return quantity


def _new_pickup_code(session: DbSession, lot: models.Lot) -> str:
    """A random 6-digit code, unique among the reservations of the lot."""
    taken = set(
        session.scalars(
            select(models.Reservation.pickup_code).where(models.Reservation.lot_id == lot.id)
        )
    )
    while (code := f"{secrets.randbelow(10**6):06d}") in taken:
        pass
    return code


@router.post(
    "/lots/{lotId}/reservations",
    status_code=201,
    response_model=Reservation,
    operation_id="createReservation",
    responses=_errors(400, 401, 403, 404, 409, 422),
)
def create_reservation(
    lot_id: LotId,
    payload: ReservationCreate,
    association: CurrentAssociation,
    session: DbSession,
) -> Reservation:
    """Reserve a lot for the current association, with a new pickup code.

    The lot row stays locked until the commit, so simultaneous reservations of a lot are
    checked one after the other against its remaining quantity: never overbooked.
    """
    lot = session.scalar(
        select(models.Lot).where(models.Lot.id == lot_id).with_for_update(of=models.Lot)
    )
    if lot is None:
        raise not_found("Lot introuvable.")
    now = datetime.now(UTC)
    status = lot_status(lot, now)
    if status == LotStatus.RESERVED:
        raise conflict("Ce lot a déjà été entièrement réservé.")
    if status != LotStatus.AVAILABLE:
        raise conflict("Ce lot n'est plus disponible : son créneau ou sa DLC est passé.")

    quantity = _reserved_quantity(lot, payload, now)
    if quantity > lot.remaining_quantity:
        raise conflict(
            f"Il ne reste que {lot.remaining_quantity.normalize():f} {lot.unit.value} sur ce lot."
        )

    lot.remaining_quantity -= quantity
    reservation = models.Reservation(
        lot=lot,
        association=association,
        quantity=quantity,
        pickup_at=payload.pickup_at,
        status=ReservationStatus.BOOKED,
        pickup_code=_new_pickup_code(session, lot),
    )
    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    return to_schema(reservation, with_pickup_code=True)


@router.get(
    "/me/reservations",
    response_model=ReservationPage,
    operation_id="listMyReservations",
    responses=_errors(400, 401, 403),
)
def list_my_reservations(
    association: CurrentAssociation,
    session: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ReservationPage:
    """The reservations of the current association, most recent first, with their pickup
    codes."""
    mine = models.Reservation.association_id == association.id
    total = session.scalar(select(func.count()).select_from(models.Reservation).where(mine))
    offset = (page - 1) * per_page
    reservations = []
    if offset < total:  # also keeps a huge page from overflowing the SQL OFFSET
        reservations = session.scalars(
            select(models.Reservation)
            .where(mine)
            .order_by(models.Reservation.created_at.desc(), models.Reservation.id.desc())
            .offset(offset)
            .limit(per_page)
        ).all()
    return ReservationPage(
        data=[to_schema(reservation, with_pickup_code=True) for reservation in reservations],
        meta=PageMeta(page=page, per_page=per_page, total=total),
    )


@router.get(
    "/reservations/{reservationId}",
    response_model=Reservation,
    operation_id="getReservation",
    responses=_errors(401, 403, 404),
)
def get_reservation(
    reservation_id: ReservationId,
    user: Annotated[models.User, Depends(get_lot_reader)],
    session: DbSession,
) -> Reservation:
    """A reservation, for the association that made it (with the pickup code) or for the
    supplier of the lot (without it)."""
    reservation = session.get(models.Reservation, reservation_id)
    if reservation is None:
        raise not_found("Réservation introuvable.")
    if user.association_id is not None:
        if reservation.association_id != user.association_id:
            raise forbidden("Cette réservation a été faite par une autre association.")
        return to_schema(reservation, with_pickup_code=True)
    if reservation.lot.supplier_id != user.supplier_id:
        raise forbidden("Cette réservation porte sur le lot d'un autre fournisseur.")
    return to_schema(reservation, with_pickup_code=False)
