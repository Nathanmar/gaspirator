"""Development data (`app.seed`)."""

from collections import Counter
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import seed as seed_module
from app.lots import lot_status
from app.models import Association, Lot, RegistrationRequest, Supplier, User
from app.schemas import LotStatus, RegistrationStatus
from app.seed import ADMIN_EMAIL, DEV_PASSWORD, seed

NOW = datetime(2026, 11, 17, 10, 30, tzinfo=UTC)


def test_seed_inserts_organizations_lots_of_every_status_and_accounts(db: Session) -> None:
    assert seed(db, NOW) is True

    assert db.scalar(select(func.count()).select_from(Supplier)) == len(seed_module.SUPPLIERS)
    assert db.scalar(select(func.count()).select_from(Association)) == len(
        seed_module.ASSOCIATIONS
    )
    statuses = Counter(lot_status(lot, NOW) for lot in db.scalars(select(Lot)).unique())
    assert set(statuses) == set(LotStatus)
    assert db.scalar(
        select(func.count())
        .select_from(RegistrationRequest)
        .where(RegistrationRequest.status == RegistrationStatus.PENDING)
    ) == len(seed_module.PENDING)


def test_seed_runs_only_once(db: Session) -> None:
    assert seed(db, NOW) is True
    assert seed(db, NOW) is False
    assert db.scalar(select(func.count()).select_from(User).where(User.email == ADMIN_EMAIL)) == 1


def test_seeded_accounts_can_log_in(db: Session, client: TestClient) -> None:
    seed(db)
    for email in (ADMIN_EMAIL, seed_module.SUPPLIERS[0].manager.email):
        response = client.post(
            "/api/v1/auth/login", json={"email": email, "password": DEV_PASSWORD}
        )
        assert response.status_code == 200, response.text
