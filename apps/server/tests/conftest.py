"""Shared test fixtures.

Tests run against the PostgreSQL service of docker-compose.yml (`docker compose up -d db`),
in a dedicated `gaspirator_test` database created on the fly and migrated with Alembic.
Override it with `TEST_DATABASE_URL`.
"""

import copy
import itertools
import os
from collections.abc import Callable, Iterator
from pathlib import Path

import httpx2
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, make_url, text
from sqlalchemy.orm import Session, sessionmaker

from app.auth import create_access_token, hash_password
from app.db import Base, get_session
from app.main import app
from app.models import Association, RegistrationRequest, Supplier, User
from app.schemas import OrganizationType, RegistrationStatus, SupplierType, UserRole
from tests.prism import API_PREFIX, prism_proxy, serve_api

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/gaspirator_test",
)

REGISTRATION_URL = "/api/v1/registration-requests"

VALID_SUPPLIER_REGISTRATION = {
    "supplier": {
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

VALID_ASSOCIATION_REGISTRATION = {
    "association": {
        "name": "Restos du Cœur Lyon 2",
        "legal_id": "W691234567",
        "address": {
            "street": "3 rue Sainte-Hélène",
            "postal_code": "69002",
            "city": "Lyon",
        },
        "contact_phone": "04 78 00 00 01",
    },
    "account": {
        "firstname": "Paul",
        "lastname": "Martin",
        "email": "paul.martin@example.org",
        "password": "testPass1.",
    },
}


def _create_database_if_missing(url: str) -> None:
    db_url = make_url(url)
    admin = create_engine(db_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": db_url.database}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{db_url.database}"'))
    admin.dispose()


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    """Fresh test database, migrated to the latest Alembic revision."""
    _create_database_if_missing(TEST_DATABASE_URL)
    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))

    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL.replace("%", "%%"))
    config.attributes["configure_logger"] = False
    command.upgrade(config, "head")

    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> Iterator[sessionmaker[Session]]:
    """Session factory on the test database; tables are emptied after each test."""
    yield sessionmaker(bind=engine, expire_on_commit=False)
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """A session to arrange and inspect the database from a test."""
    with session_factory() as session:
        yield session


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    """Test client whose requests use the test database."""

    def _get_session() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def prism_url(engine: Engine) -> Iterator[str]:
    """The API served over HTTP behind the Prism validation proxy."""
    with serve_api(app) as api_url, prism_proxy(api_url + API_PREFIX) as url:
        yield url


@pytest.fixture
def api(prism_url: str, session_factory: sessionmaker[Session]) -> Iterator[httpx2.Client]:
    """HTTP client going through Prism (paths without `/api/v1`, as in openapi.yaml).

    Check each response with `tests.prism.assert_contract`.
    """

    def _get_session() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _get_session
    with httpx2.Client(base_url=prism_url, timeout=30) as http_client:
        yield http_client
    app.dependency_overrides.clear()


@pytest.fixture
def registration() -> dict:
    """A valid supplier registration request body (deep copy, safe to mutate)."""
    return copy.deepcopy(VALID_SUPPLIER_REGISTRATION)


@pytest.fixture
def association_registration() -> dict:
    """A valid association registration request body (deep copy, safe to mutate)."""
    return copy.deepcopy(VALID_ASSOCIATION_REGISTRATION)


@pytest.fixture
def create_supplier(db: Session) -> Callable[..., Supplier]:
    """Insert a supplier (unique SIRET); keyword arguments override the columns."""
    sirets = itertools.count(19690103400017)

    def _create_supplier(**columns) -> Supplier:
        supplier = Supplier(
            **{
                "name": "Cantine du lycée Ampère",
                "legal_id": str(next(sirets)),
                "supplier_type": SupplierType.CANTEEN,
                "street": "12 rue de la République",
                "postal_code": "69002",
                "city": "Lyon",
                "latitude": 45.7578,
                "longitude": 4.832,
                "contact_phone": "04 78 00 00 00",
                **columns,
            }
        )
        db.add(supplier)
        db.commit()
        return supplier

    return _create_supplier


@pytest.fixture
def create_association(db: Session) -> Callable[..., Association]:
    """Insert an association (unique RNA number); keyword arguments override the columns."""
    rna_numbers = itertools.count(691234567)

    def _create_association(**columns) -> Association:
        association = Association(
            **{
                "name": "Restos du Cœur Lyon 2",
                "legal_id": f"W{next(rna_numbers)}",
                "street": "3 rue Sainte-Hélène",
                "postal_code": "69002",
                "city": "Lyon",
                "latitude": 45.7537,
                "longitude": 4.8286,
                "contact_phone": "04 78 00 00 01",
                **columns,
            }
        )
        db.add(association)
        db.commit()
        return association

    return _create_association


@pytest.fixture
def create_user(db: Session) -> Callable[..., User]:
    """Insert a user. Managers get a registration request with the given status.

    Pass `supplier` or `association` to make the user the manager of it.
    """
    legal_ids = itertools.count(19690103400017)  # unique SIRET per request

    def _create_user(
        email: str = "marie.dupont@example.org",
        password: str = "testPass1.",
        role: UserRole = UserRole.MANAGER,
        registration_status: RegistrationStatus = RegistrationStatus.APPROVED,
        supplier: Supplier | None = None,
        association: Association | None = None,
    ) -> User:
        user = User(
            email=email,
            password_hash=hash_password(password),
            firstname="Marie",
            lastname="Dupont",
            role=role,
            supplier=supplier,
            association=association,
        )
        if role == UserRole.MANAGER:
            user.registration_request = RegistrationRequest(
                status=registration_status,
                organization_type=OrganizationType.SUPPLIER,
                organization_name="Cantine du lycée Ampère",
                legal_id=str(next(legal_ids)),
                supplier_type=SupplierType.CANTEEN,
                street="12 rue de la République",
                postal_code="69002",
                city="Lyon",
                contact_phone="04 78 00 00 00",
            )
        db.add(user)
        db.commit()
        return user

    return _create_user


@pytest.fixture
def tokens(api: httpx2.Client, create_user) -> dict:
    """`AuthTokens` of an approved manager, obtained with POST /auth/login."""
    create_user(email="marie.dupont@example.org", password="testPass1.")
    response = api.post(
        "/auth/login", json={"email": "marie.dupont@example.org", "password": "testPass1."}
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def auth_headers() -> Callable[[User], dict]:
    """`Authorization: Bearer` header with a valid access token for the given user."""

    def _auth_headers(user: User) -> dict:
        return {"Authorization": f"Bearer {create_access_token(user)}"}

    return _auth_headers
