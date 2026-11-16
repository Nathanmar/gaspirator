"""Fixtures for the Lots tag: a supplier, the users allowed or not to use the routes, a
valid `LotCreate` body and lots inserted in the database."""

from collections.abc import Callable
from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models import Lot, Supplier
from app.schemas import LotCategory, QuantityUnit, Storage, UserRole
from tests.lots.helpers import at, iso, today


@pytest.fixture
def supplier(create_supplier) -> Supplier:
    return create_supplier()


@pytest.fixture
def supplier_headers(create_user, supplier: Supplier, auth_headers) -> dict:
    """Bearer header of the manager of `supplier`."""
    return auth_headers(create_user(email="cantine@example.org", supplier=supplier))


@pytest.fixture
def association_headers(create_user, create_association, auth_headers) -> dict:
    """Bearer header of the manager of an association."""
    association = create_association()
    return auth_headers(create_user(email="asso@example.org", association=association))


@pytest.fixture
def admin_headers(create_user, auth_headers) -> dict:
    return auth_headers(create_user(email="admin@gaspirator.fr", role=UserRole.ADMIN))


@pytest.fixture
def lot_body() -> dict:
    """A valid `LotCreate` body: picked up tomorrow, eaten by the day after."""
    tomorrow = today() + timedelta(days=1)
    return {
        "title": "Hachis parmentier",
        "category": "prepared_meal",
        "quantity": 30,
        "unit": "portions",
        "divisible": True,
        "use_by_date": (tomorrow + timedelta(days=1)).isoformat(),
        "allergens": ["milk", "celery"],
        "storage": "refrigerated",
        "pickup_start": iso(at(tomorrow, 13)),
        "pickup_end": iso(at(tomorrow, 15)),
    }


@pytest.fixture
def create_lot(db: Session, supplier: Supplier) -> Callable[..., Lot]:
    """Insert a lot of `supplier`, available tomorrow; keyword arguments override the columns."""

    def _create_lot(**columns) -> Lot:
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

    return _create_lot
