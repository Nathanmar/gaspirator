"""Fixtures for the Lots tag: a supplier, the users allowed or not to use the routes and
a valid `LotCreate` body."""

from datetime import timedelta

import pytest

from app.models import Supplier
from app.schemas import UserRole
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
