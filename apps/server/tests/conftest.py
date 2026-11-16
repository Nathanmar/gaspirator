"""Shared test fixtures."""

import asyncio
import copy
from collections.abc import Callable, Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.auth import create_access_token, hash_password
from app.dependencies import get_organization_repository, get_user_repository
from app.main import app
from app.repositories import (
    InMemoryOrganizationRepository,
    InMemoryUserRepository,
    StoredUser,
)
from app.schemas import (
    Address,
    GeoPoint,
    Organization,
    OrganizationStatus,
    OrganizationType,
    SupplierType,
    UserRole,
)

REGISTRATION_URL = "/api/v1/registration-requests"
PASSWORD = "testPass1."

VALID_REGISTRATION = {
    "organization": {
        "type": "supplier",
        "name": "Cantine du lycée Ampère",
        "legal_id": "19690103400017",
        "supplier_type": "canteen",
        "address": {
            "street": "12 rue de la République",
            "postal_code": "69002",
            "city": "Lyon",
        },
        "contact_phone": "04 78 00 00 00",
    },
    "account": {
        "firstname": "Marie",
        "lastname": "Dupont",
        "email": "marie.dupont@example.org",
        "password": "testPass1.",
    },
}


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def registration() -> dict:
    """A valid registration request body (deep copy, safe to mutate)."""
    return copy.deepcopy(VALID_REGISTRATION)


# ----- Profil : stockage isolé, organisations, utilisateurs et tokens -----


@pytest.fixture
def users_repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def organizations_repo() -> InMemoryOrganizationRepository:
    return InMemoryOrganizationRepository()


@pytest.fixture(autouse=True)
def _isolated_repositories(
    users_repo: InMemoryUserRepository,
    organizations_repo: InMemoryOrganizationRepository,
) -> Iterator[None]:
    """Each test starts with empty users / organisations."""
    app.dependency_overrides[get_user_repository] = lambda: users_repo
    app.dependency_overrides[get_organization_repository] = lambda: organizations_repo
    yield
    app.dependency_overrides.clear()


def auth_headers(user: StoredUser) -> dict[str, str]:
    """`Authorization: Bearer <JWT>` for this user (JWT `sub` = user id)."""
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.id)})}"}


@pytest.fixture
def supplier(organizations_repo: InMemoryOrganizationRepository) -> Organization:
    """An active supplier organisation."""
    organization = Organization(
        id=0,
        type=OrganizationType.SUPPLIER,
        name="Cantine du lycée Ampère",
        supplier_type=SupplierType.CANTEEN,
        address=Address(street="12 rue de la République", postal_code="69002", city="Lyon"),
        location=GeoPoint(latitude=45.7578, longitude=4.8320),
        contact_phone="04 78 00 00 00",
        legal_id="19690103400017",
        opening_hours="Du lundi au vendredi, de 14 h à 16 h",
        status=OrganizationStatus.ACTIVE,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    return asyncio.run(organizations_repo.add(organization))


@pytest.fixture
def create_user(users_repo: InMemoryUserRepository) -> Callable[..., StoredUser]:
    """Factory: create_user(role, organization, email) -> stored user (password: PASSWORD)."""

    def _create(
        role: UserRole,
        organization: Organization | None,
        email: str,
        firstname: str = "Marie",
        lastname: str = "Dupont",
    ) -> StoredUser:
        user = StoredUser(
            id=0,
            email=email,
            firstname=firstname,
            lastname=lastname,
            role=role,
            organization_id=organization.id if organization else None,
            password_hash=hash_password(PASSWORD),
        )
        return asyncio.run(users_repo.add(user))

    return _create


@pytest.fixture
def manager(create_user: Callable[..., StoredUser], supplier: Organization) -> StoredUser:
    return create_user(UserRole.MANAGER, supplier, "marie.dupont@example.org")


@pytest.fixture
def member(create_user: Callable[..., StoredUser], supplier: Organization) -> StoredUser:
    return create_user(UserRole.MEMBER, supplier, "paul.martin@example.org", "Paul", "Martin")


@pytest.fixture
def admin(create_user: Callable[..., StoredUser]) -> StoredUser:
    return create_user(UserRole.ADMIN, None, "admin@gaspirator.fr", "Alice", "Admin")
