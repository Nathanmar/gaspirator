"""Fixtures for the Suppliers tag: an association in Lyon centre, suppliers around it and
lots inserted in the database."""

from collections.abc import Callable
from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models import Association, Lot, Supplier
from app.schemas import LotCategory, QuantityUnit, Storage, UserRole
from tests.lots.helpers import at, today

# (latitude, longitude) of the places used by the tests.
LYON_CENTRE = (45.7578, 4.8320)  # the association
PART_DIEU = (45.7605, 4.8590)  # ~2.1 km
VILLEURBANNE = (45.7719, 4.8902)  # ~4.8 km
NEUVILLE = (45.8900, 4.8320)  # ~14.7 km: outside the default 10 km radius
GRENOBLE = (45.1885, 5.7245)  # ~95 km: outside any radius from Lyon


@pytest.fixture
def association(create_association) -> Association:
    latitude, longitude = LYON_CENTRE
    return create_association(latitude=latitude, longitude=longitude)


@pytest.fixture
def association_headers(create_user, association: Association, auth_headers) -> dict:
    """Bearer header of the manager of `association`."""
    return auth_headers(create_user(email="asso@example.org", association=association))


@pytest.fixture
def supplier_headers(create_user, create_supplier, auth_headers) -> dict:
    """Bearer header of the manager of a supplier."""
    return auth_headers(create_user(email="cantine@example.org", supplier=create_supplier()))


@pytest.fixture
def admin_headers(create_user, auth_headers) -> dict:
    return auth_headers(create_user(email="admin@gaspirator.fr", role=UserRole.ADMIN))


@pytest.fixture
def supplier_at(create_supplier) -> Callable[..., Supplier]:
    """Factory: a supplier at (latitude, longitude)."""

    def _supplier_at(place: tuple[float, float], **columns) -> Supplier:
        latitude, longitude = place
        return create_supplier(latitude=latitude, longitude=longitude, **columns)

    return _supplier_at


@pytest.fixture
def add_lot(db: Session) -> Callable[..., Lot]:
    """Factory: a lot of `supplier`, available tomorrow; keyword arguments override columns."""

    def _add_lot(supplier: Supplier, **columns) -> Lot:
        tomorrow = today() + timedelta(days=1)
        quantity = Decimal(columns.pop("quantity", 30))
        lot = Lot(
            **{
                "supplier": supplier,
                "title": "Hachis parmentier",
                "category": LotCategory.PREPARED_MEAL,
                "quantity": quantity,
                "remaining_quantity": quantity,
                "unit": QuantityUnit.PORTIONS,
                "divisible": True,
                "use_by_date": tomorrow + timedelta(days=1),
                "allergens": ["milk"],
                "storage": Storage.REFRIGERATED,
                "pickup_start": at(tomorrow, 13),
                "pickup_end": at(tomorrow, 15),
                **columns,
            }
        )
        db.add(lot)
        db.commit()
        return lot

    return _add_lot
