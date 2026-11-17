"""Fixtures for the Admin tag: an admin, other users, and registration requests of suppliers
and associations (with the position geocoded on submission)."""

import itertools
from collections.abc import Callable
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.models import RegistrationRequest, User
from app.schemas import OrganizationType, RegistrationStatus, SupplierType, UserRole

PASSWORD = "testPass1."


@pytest.fixture
def admin(create_user) -> User:
    return create_user(email="admin@gaspirator.fr", role=UserRole.ADMIN)


@pytest.fixture
def admin_headers(admin: User, auth_headers) -> dict:
    return auth_headers(admin)


@pytest.fixture
def supplier_headers(create_user, create_supplier, auth_headers) -> dict:
    """Bearer header of the manager of a supplier."""
    return auth_headers(create_user(email="cantine@example.org", supplier=create_supplier()))


@pytest.fixture
def association_headers(create_user, create_association, auth_headers) -> dict:
    """Bearer header of the manager of an association."""
    return auth_headers(create_user(email="asso@example.org", association=create_association()))


@pytest.fixture
def create_request(db: Session) -> Callable[..., RegistrationRequest]:
    """Factory: the registration request of a new manager.

    `kind` is "supplier" or "association"; keyword arguments override the columns.
    """
    numbers = itertools.count(1)

    def _create_request(
        kind: str = "supplier",
        status: RegistrationStatus = RegistrationStatus.PENDING,
        created_at: datetime | None = None,
        **columns,
    ) -> RegistrationRequest:
        number = next(numbers)
        user = User(
            email=f"demandeur{number}@example.org",
            password_hash=hash_password(PASSWORD),
            firstname="Marie",
            lastname="Dupont",
            role=UserRole.MANAGER,
        )
        if kind == "supplier":
            organization = {
                "organization_type": OrganizationType.SUPPLIER,
                "organization_name": "Cantine du lycée Ampère",
                "legal_id": f"{19690103400000 + number}",
                "supplier_type": SupplierType.CANTEEN,
            }
        else:
            organization = {
                "organization_type": OrganizationType.ASSOCIATION,
                "organization_name": "Restos du Cœur Lyon 2",
                "legal_id": f"W{691234000 + number}",
                "supplier_type": None,
            }
        request = RegistrationRequest(
            user=user,
            status=status,
            **organization,
            street="12 rue de la République",
            postal_code="69002",
            city="Lyon",
            contact_phone="04 78 00 00 00",
            latitude=45.7578,
            longitude=4.832,
            **({"created_at": created_at} if created_at else {}),
            **columns,
        )
        db.add(request)
        db.commit()
        return request

    return _create_request
