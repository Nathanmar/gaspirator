"""Fixtures for the Reservations tag: the supplier and lots of the Lots tag, an association
and its manager, and reservations inserted in the database."""

import itertools
from collections.abc import Callable
from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models import Association, Lot, Reservation
from app.schemas import ReservationStatus
from tests.lots.conftest import (  # noqa: F401 (fixtures)
    admin_headers,
    create_lot,
    supplier,
    supplier_headers,
)


@pytest.fixture
def association(create_association) -> Association:
    return create_association()


@pytest.fixture
def association_headers(create_user, association: Association, auth_headers) -> dict:
    """Bearer header of the manager of `association`."""
    return auth_headers(create_user(email="asso@example.org", association=association))


@pytest.fixture
def create_reservation(db: Session) -> Callable[..., Reservation]:
    """Insert a `booked` reservation and take its quantity off the lot.

    Picked up 30 minutes after the start of the pickup window; keyword arguments override
    the columns.
    """
    pickup_codes = itertools.count(100000)

    def _create_reservation(
        lot: Lot, association: Association, quantity=10, **columns
    ) -> Reservation:
        quantity = Decimal(quantity)
        reservation = Reservation(
            **{
                "lot": lot,
                "association": association,
                "quantity": quantity,
                "pickup_at": lot.pickup_start + timedelta(minutes=30),
                "status": ReservationStatus.BOOKED,
                "pickup_code": str(next(pickup_codes)),
                **columns,
            }
        )
        lot.remaining_quantity -= quantity
        db.add(reservation)
        db.commit()
        return reservation

    return _create_reservation
