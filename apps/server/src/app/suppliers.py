"""US-03: suppliers searched by the associations (/suppliers)."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from app import models
from app.auth import get_current_association, get_current_user
from app.db import get_session
from app.errors import ApiError, not_found
from app.lots import supplier_summary
from app.schemas import (
    Error,
    PageMeta,
    SupplierProfile,
    SupplierSearchPage,
    SupplierSearchResult,
)

router = APIRouter(tags=["Suppliers"])

DbSession = Annotated[Session, Depends(get_session)]
CurrentAssociation = Annotated[models.Association, Depends(get_current_association)]
CurrentUser = Annotated[models.User, Depends(get_current_user)]

# Path parameters of the contract are int64.
SupplierId = Annotated[int, Path(alias="supplierId", ge=1, le=2**63 - 1)]

EARTH_RADIUS_KM = 6371.0


def _errors(*status_codes: int) -> dict[int | str, dict]:
    """Error responses documented in the generated OpenAPI (/docs)."""
    return {status: {"model": Error} for status in status_codes}


def is_available(now: datetime) -> ColumnElement[bool]:
    """SQL version of `lots.lot_status(...) == available`: something left to reserve, pickup
    window not over and use-by date not passed (contract `LotStatus`)."""
    return (
        (models.Lot.remaining_quantity > 0)
        & (models.Lot.pickup_end > now)
        & (models.Lot.use_by_date >= now.date())
    )


def available_lots_counts(now: datetime):
    """Subquery `(supplier_id, available_lots_count)` of the suppliers with available lots."""
    return (
        select(
            models.Lot.supplier_id,
            func.count().label("available_lots_count"),
        )
        .where(is_available(now))
        .group_by(models.Lot.supplier_id)
        .subquery()
    )


def distance_km(latitude: float, longitude: float) -> ColumnElement[float]:
    """Great-circle distance in km from (latitude, longitude) to the supplier (haversine).

    distance = R × θ, with θ = 2 × asin(√a) the angle seen from the centre of the Earth and
    a = sin²(Δlat / 2) + cos(lat1) × cos(lat2) × sin²(Δlon / 2), angles in radians.
    `least(1, ...)` keeps rounding errors inside the domain of asin.
    """
    supplier = models.Supplier
    a = func.power(func.sin(func.radians(supplier.latitude - latitude) / 2), 2) + func.cos(
        func.radians(latitude)
    ) * func.cos(func.radians(supplier.latitude)) * func.power(
        func.sin(func.radians(supplier.longitude - longitude) / 2), 2
    )
    return 2 * EARTH_RADIUS_KM * func.asin(func.least(1.0, func.sqrt(a)))


@router.get(
    "/suppliers",
    response_model=SupplierSearchPage,
    operation_id="searchSuppliers",
    responses=_errors(400, 401, 403),
)
def search_suppliers(
    association: CurrentAssociation,
    session: DbSession,
    latitude: Annotated[float | None, Query(ge=-90, le=90)] = None,
    longitude: Annotated[float | None, Query(ge=-180, le=180)] = None,
    radius_km: Annotated[int, Query(ge=1, le=50)] = 10,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> SupplierSearchPage:
    """Suppliers with at least one available lot within `radius_km`, nearest first.

    Without `latitude` and `longitude`, the position of the current association is used.
    """
    if (latitude is None) != (longitude is None):
        raise ApiError(400, "bad_request", "latitude et longitude doivent être données ensemble.")
    if latitude is None or longitude is None:
        latitude, longitude = association.latitude, association.longitude

    counts = available_lots_counts(datetime.now(UTC))
    distance = distance_km(latitude, longitude)
    nearby = (
        select(models.Supplier, counts.c.available_lots_count, distance.label("distance_km"))
        .join(counts, counts.c.supplier_id == models.Supplier.id)
        .where(distance <= radius_km)
    )

    total = session.scalar(select(func.count()).select_from(nearby.subquery()))
    offset = (page - 1) * per_page
    rows = []
    if offset < total:  # also keeps a huge page from overflowing the SQL OFFSET
        rows = session.execute(
            nearby.order_by(distance, models.Supplier.id).offset(offset).limit(per_page)
        ).all()

    return SupplierSearchPage(
        data=[
            SupplierSearchResult(
                **supplier_summary(supplier).model_dump(),
                distance_km=round(supplier_distance, 3),
                available_lots_count=count,
            )
            for supplier, count, supplier_distance in rows
        ],
        meta=PageMeta(page=page, per_page=per_page, total=total),
    )


def _get_supplier(session: Session, supplier_id: int) -> models.Supplier:
    supplier = session.get(models.Supplier, supplier_id)
    if supplier is None:
        raise not_found("Fournisseur introuvable.")
    return supplier


@router.get(
    "/suppliers/{supplierId}",
    response_model=SupplierProfile,
    operation_id="getSupplier",
    responses=_errors(401, 404),
)
def get_supplier(supplier_id: SupplierId, _: CurrentUser, session: DbSession) -> SupplierProfile:
    """The page of a supplier, with its number of available lots (0 or more)."""
    supplier = _get_supplier(session, supplier_id)
    count = session.scalar(
        select(func.count())
        .select_from(models.Lot)
        .where(models.Lot.supplier_id == supplier.id, is_available(datetime.now(UTC)))
    )
    return SupplierProfile(**supplier_summary(supplier).model_dump(), available_lots_count=count)
