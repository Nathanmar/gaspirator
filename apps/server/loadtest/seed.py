"""Seed a dedicated database for the load tests (see Charge.md).

Creates `--associations` association managers (loadtest-asso-<i>@example.com, approved,
password `loadtest-password`) in Lyon and `--suppliers` suppliers spread at random within
~30 km around Lyon (45.76, 4.83), each with `--lots-per-supplier` available lots.
Supplier 1 ("Fournisseur course") has 2 × `--race-lots` lots with a single portion left
(indivisible lots of 1, divisible lots of 5 with 1 left), for the reservation race.

Never run it against the development database: it wipes the tables first.

    DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/gaspirator_load \
        uv run python loadtest/seed.py --suppliers 500
"""

import argparse
import random
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import text

from app.auth import hash_password
from app.db import SessionLocal, engine
from app.models import Association, Lot, RegistrationRequest, Supplier, User
from app.schemas import (
    LotCategory,
    OrganizationType,
    QuantityUnit,
    RegistrationStatus,
    Storage,
    SupplierType,
    UserRole,
)

LYON = (45.76, 4.83)
PASSWORD = "loadtest-password"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suppliers", type=int, default=500)
    parser.add_argument("--lots-per-supplier", type=int, default=4)
    parser.add_argument("--associations", type=int, default=50)
    parser.add_argument("--race-lots", type=int, default=10)
    args = parser.parse_args()

    if not engine.url.database or not engine.url.database.endswith("_load"):
        raise SystemExit(f"Refusing to seed {engine.url.database!r}: use a *_load database.")

    rng = random.Random(42)
    now = datetime.now(UTC)
    with SessionLocal() as session:
        session.execute(
            text(
                "TRUNCATE reservations, lots, refresh_tokens, registration_requests, users,"
                " suppliers, associations RESTART IDENTITY CASCADE"
            )
        )
        password_hash = hash_password(PASSWORD)

        for i in range(args.associations):
            association = Association(
                name=f"Asso charge {i}",
                legal_id=f"W{i:09d}",
                street="1 place Bellecour",
                postal_code="69002",
                city="Lyon",
                latitude=LYON[0] + rng.uniform(-0.02, 0.02),
                longitude=LYON[1] + rng.uniform(-0.02, 0.02),
                contact_phone="0400000000",
            )
            user = User(
                email=f"loadtest-asso-{i}@example.com",
                password_hash=password_hash,
                firstname="Charge",
                lastname=str(i),
                role=UserRole.MANAGER,
                association=association,
            )
            user.registration_request = RegistrationRequest(
                status=RegistrationStatus.APPROVED,
                organization_type=OrganizationType.ASSOCIATION,
                organization_name=association.name,
                legal_id=association.legal_id,
                contact_phone=association.contact_phone,
                decided_at=now,
            )
            session.add(user)
            session.flush()
            user.registration_request.association_id = association.id

        # Supplier 1: lots with a single unit left, fought over by loadtest/race.py.
        race = Supplier(
            name="Fournisseur course",
            legal_id="9" * 14,
            supplier_type=SupplierType.CANTEEN,
            street="1 rue de la Course",
            postal_code="69002",
            city="Lyon",
            latitude=LYON[0],
            longitude=LYON[1],
            contact_phone="0400000000",
        )
        session.add(race)
        session.flush()
        start = now + timedelta(hours=1)
        for j in range(args.race_lots):
            # Indivisible lot of 1 portion, and divisible lot with 1 portion left out of 5.
            for divisible, quantity in ((False, 1), (True, 5)):
                session.add(
                    Lot(
                        supplier=race,
                        title=f"Course {'divisible' if divisible else 'indivisible'} {j}",
                        category=LotCategory.PREPARED_MEAL,
                        quantity=Decimal(quantity),
                        remaining_quantity=Decimal(1),
                        unit=QuantityUnit.PORTIONS,
                        divisible=divisible,
                        use_by_date=date.today() + timedelta(days=3),
                        storage=Storage.REFRIGERATED,
                        pickup_start=start,
                        pickup_end=start + timedelta(hours=3),
                    )
                )

        for i in range(args.suppliers):
            # ~0.27° of latitude ≈ 30 km: uniform square around Lyon.
            supplier = Supplier(
                name=f"Fournisseur charge {i}",
                legal_id=f"{i:014d}",
                supplier_type=rng.choice(list(SupplierType)),
                street=f"{i} rue de la Charge",
                postal_code="69000",
                city="Lyon",
                latitude=LYON[0] + rng.uniform(-0.27, 0.27),
                longitude=LYON[1] + rng.uniform(-0.38, 0.38),
                contact_phone="0400000000",
            )
            session.add(supplier)
            for j in range(args.lots_per_supplier):
                start = now + timedelta(hours=rng.randint(1, 48))
                quantity = Decimal(rng.randint(5, 50))
                session.add(
                    Lot(
                        supplier=supplier,
                        title=f"Lot {i}-{j}",
                        category=rng.choice(list(LotCategory)),
                        quantity=quantity,
                        remaining_quantity=quantity,
                        unit=QuantityUnit.PORTIONS,
                        divisible=True,
                        use_by_date=date.today() + timedelta(days=rng.randint(2, 7)),
                        storage=rng.choice(list(Storage)),
                        pickup_start=start,
                        pickup_end=start + timedelta(hours=3),
                    )
                )
        session.commit()
    print(
        f"Seeded {args.associations} associations, {args.suppliers} suppliers,"
        f" {args.suppliers * args.lots_per_supplier} lots."
    )


if __name__ == "__main__":
    main()
