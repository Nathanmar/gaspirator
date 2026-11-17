"""Development data: suppliers, associations, lots and reservations around Paris.

Run with `python -m app.seed`. It does nothing unless `SEED_DEV_DATA` is true (set by
docker-compose.yml only), and only once per database: it stops if the seed admin exists.

Every seeded account uses the password `DEV_PASSWORD`. Dates are relative to the moment
of the seed, so lots that are available on the day become expired later on.
"""

import random
from dataclasses import dataclass, field
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.db import SessionLocal
from app.models import (
    Association,
    Lot,
    RegistrationRequest,
    Reservation,
    Supplier,
    User,
)
from app.schemas import (
    LotCategory,
    OrganizationType,
    QuantityUnit,
    RegistrationStatus,
    ReservationStatus,
    Storage,
    SupplierType,
    UserRole,
)
from app.settings import get_settings

DEV_PASSWORD = "gaspirator-dev"
ADMIN_EMAIL = "admin@example.org"


@dataclass(frozen=True)
class Manager:
    email: str
    firstname: str
    lastname: str


@dataclass(frozen=True)
class Org:
    name: str
    legal_id: str  # SIRET (14 digits) for a supplier, RNA number (W + 9 digits) otherwise
    street: str
    postal_code: str
    city: str
    latitude: float
    longitude: float
    contact_phone: str
    manager: Manager
    supplier_type: SupplierType | None = None  # None for an association


SUPPLIERS = [
    Org(
        "Cantine du collège Voltaire", "19750011400011", "101 boulevard Voltaire", "75011",
        "Paris", 48.8590, 2.3790, "01 43 00 00 01",
        Manager("cantine.voltaire@example.org", "Sophie", "Leroy"), SupplierType.CANTEEN,
    ),
    Org(
        "Centre hospitalier Saint-Michel", "26750014500012", "33 rue Olivier Noyer", "75014",
        "Paris", 48.8310, 2.3200, "01 45 00 00 02",
        Manager("cuisine.saint-michel@example.org", "Karim", "Benali"), SupplierType.HOSPITAL,
    ),
    Org(
        "Supermarché Fraîcheur Bastille", "45175011200013", "12 rue de la Roquette", "75011",
        "Paris", 48.8545, 2.3712, "01 48 00 00 03",
        Manager("fraicheur.bastille@example.org", "Julien", "Moreau"), SupplierType.SUPERMARKET,
    ),
    Org(
        "Marché Belleville", "45175020300014", "120 boulevard de Belleville", "75020",
        "Paris", 48.8722, 2.3768, "01 46 00 00 04",
        Manager("marche.belleville@example.org", "Lina", "Haddad"), SupplierType.SUPERMARKET,
    ),
    Org(
        "Boulangerie des Batignolles", "81275017400015", "45 rue des Batignolles", "75017",
        "Paris", 48.8853, 2.3184, "01 42 00 00 05",
        Manager("boulangerie.batignolles@example.org", "Thomas", "Petit"), SupplierType.OTHER,
    ),
    Org(
        "Cuisine centrale de Montreuil", "21930048000016", "10 rue de Paris", "93100",
        "Montreuil", 48.8583, 2.4378, "01 48 70 00 06",
        Manager("cuisine.montreuil@example.org", "Nadia", "Rahmani"), SupplierType.CANTEEN,
    ),
    Org(
        "Hypermarché Porte d'Italie", "45175013500017", "30 avenue d'Italie", "75013",
        "Paris", 48.8280, 2.3565, "01 45 80 00 07",
        Manager("hyper.italie@example.org", "Marc", "Lefèvre"), SupplierType.SUPERMARKET,
    ),
    Org(
        "Traiteur Saint-Germain", "81275006600018", "60 rue de Rennes", "75006",
        "Paris", 48.8510, 2.3290, "01 45 44 00 08",
        Manager("traiteur.saint-germain@example.org", "Claire", "Fontaine"), SupplierType.OTHER,
    ),
    Org(
        "Restaurant universitaire Jussieu", "18750005700019", "4 place Jussieu", "75005",
        "Paris", 48.8462, 2.3546, "01 44 27 00 09",
        Manager("ru.jussieu@example.org", "Hugo", "Garnier"), SupplierType.CANTEEN,
    ),
    Org(
        "Clinique du Parc de Saint-Denis", "26930066000020", "2 rue du Docteur Delafontaine",
        "93200", "Saint-Denis", 48.9362, 2.3574, "01 49 33 00 10",
        Manager("clinique.saint-denis@example.org", "Awa", "Diallo"), SupplierType.HOSPITAL,
    ),
]

ASSOCIATIONS = [
    Org(
        "Solidarité Paris Est", "W751000001", "25 rue Oberkampf", "75011", "Paris",
        48.8648, 2.3720, "01 43 55 00 11",
        Manager("solidarite.paris-est@example.org", "Paul", "Martin"),
    ),
    Org(
        "Les Paniers du 18e", "W751000002", "40 rue Ordener", "75018", "Paris",
        48.8925, 2.3490, "01 42 55 00 12",
        Manager("paniers.18e@example.org", "Fatou", "Ndiaye"),
    ),
    Org(
        "Entraide Alimentaire Paris 13", "W751000003", "50 rue du Château des Rentiers",
        "75013", "Paris", 48.8270, 2.3660, "01 45 85 00 13",
        Manager("entraide.paris13@example.org", "Louis", "Bernard"),
    ),
    Org(
        "Le Repas Partagé Montreuil", "W931000004", "5 rue Kléber", "93100", "Montreuil",
        48.8620, 2.4430, "01 48 57 00 14",
        Manager("repas.montreuil@example.org", "Inès", "Garcia"),
    ),
    Org(
        "Aide aux Étudiants Paris Centre", "W751000005", "15 rue Saint-Jacques", "75005",
        "Paris", 48.8505, 2.3460, "01 43 26 00 15",
        Manager("etudiants.paris-centre@example.org", "Léa", "Roux"),
    ),
]

# Registration requests still waiting for an admin (back office).
PENDING = [
    Org(
        "Cantine du lycée Hélène Boucher", "19750020800021", "75 cours de Vincennes", "75020",
        "Paris", 48.8478, 2.4040, "01 43 70 00 16",
        Manager("cantine.boucher@example.org", "Éric", "Lambert"), SupplierType.CANTEEN,
    ),
    Org(
        "La Main Tendue Clichy", "W921000006", "12 rue Martre", "92110", "Clichy",
        48.9030, 2.3060, "01 47 37 00 17",
        Manager("main-tendue.clichy@example.org", "Chloé", "Mercier"),
    ),
]


@dataclass(frozen=True)
class Booking:
    association: int  # index in ASSOCIATIONS
    quantity: str
    collected: bool = False


@dataclass(frozen=True)
class LotSeed:
    """`day` is the pickup day, from today (0: a window around now, < 0: in the past).

    The lot status follows from the day and the bookings: available, partly reserved,
    reserved (nothing left), collected (all bookings collected) or expired.
    """

    supplier: int  # index in SUPPLIERS
    title: str
    category: LotCategory
    quantity: str
    unit: QuantityUnit
    divisible: bool
    storage: Storage
    day: int
    shelf_days: int = 2  # use-by date, in days after the pickup day
    allergens: tuple[str, ...] = ()
    bookings: tuple[Booking, ...] = field(default_factory=tuple)


C, U, S = LotCategory, QuantityUnit, Storage
LOTS = [
    # Cantine du collège Voltaire
    LotSeed(0, "Hachis parmentier", C.PREPARED_MEAL, "40", U.PORTIONS, True, S.REFRIGERATED, 0,
            1, ("milk",)),
    LotSeed(0, "Yaourts nature", C.DAIRY, "120", U.PIECES, True, S.REFRIGERATED, 1, 5, ("milk",),
            (Booking(0, "60"),)),
    LotSeed(0, "Pommes Golden", C.FRESH_PRODUCE, "25", U.KG, True, S.AMBIENT, -3, 10,
            bookings=(Booking(0, "15", True), Booking(4, "10", True))),
    # Centre hospitalier Saint-Michel
    LotSeed(1, "Plateaux repas poulet-riz", C.PREPARED_MEAL, "30", U.PORTIONS, False,
            S.REFRIGERATED, 0, 1, bookings=(Booking(2, "30"),)),
    LotSeed(1, "Compotes en gourde", C.OTHER_FOOD, "200", U.PIECES, True, S.AMBIENT, 2, 60),
    LotSeed(1, "Soupe de légumes", C.PREPARED_MEAL, "15", U.KG, True, S.REFRIGERATED, -2, 1,
            ("celery",)),
    # Supermarché Fraîcheur Bastille
    LotSeed(2, "Fruits et légumes invendus", C.FRESH_PRODUCE, "18.5", U.KG, True, S.AMBIENT, 0,
            3),
    LotSeed(2, "Fromages à la coupe", C.DAIRY, "6.2", U.KG, True, S.REFRIGERATED, 1, 7,
            ("milk",), (Booking(0, "2.5"), Booking(1, "1.7"))),
    LotSeed(2, "Filets de saumon", C.MEAT_FISH, "4", U.KG, False, S.FROZEN, -1, 30, ("fish",),
            (Booking(0, "4", True),)),
    LotSeed(2, "Jus d'orange", C.BEVERAGES, "48", U.PIECES, True, S.AMBIENT, 3, 20),
    # Marché Belleville
    LotSeed(3, "Cagettes de tomates", C.FRESH_PRODUCE, "30", U.KG, True, S.AMBIENT, 1, 4),
    LotSeed(3, "Pâtes et riz", C.DRY_GOODS, "40", U.KG, True, S.AMBIENT, 4, 180, ("gluten",),
            (Booking(1, "20"),)),
    LotSeed(3, "Poulets rôtis", C.MEAT_FISH, "12", U.PIECES, False, S.REFRIGERATED, -4, 1,
            bookings=(Booking(1, "12", True),)),
    # Boulangerie des Batignolles
    LotSeed(4, "Baguettes de la veille", C.BAKERY, "60", U.PIECES, True, S.AMBIENT, 0, 1,
            ("gluten",), (Booking(1, "60"),)),
    LotSeed(4, "Viennoiseries", C.BAKERY, "45", U.PIECES, True, S.AMBIENT, 1, 1,
            ("gluten", "eggs", "milk")),
    LotSeed(4, "Pains de mie", C.BAKERY, "20", U.PIECES, True, S.AMBIENT, -1, 2,
            ("gluten", "milk", "sesame")),
    # Cuisine centrale de Montreuil
    LotSeed(5, "Lasagnes bolognaises", C.PREPARED_MEAL, "80", U.PORTIONS, True, S.REFRIGERATED,
            1, 2, ("gluten", "milk", "eggs"), (Booking(3, "50"),)),
    LotSeed(5, "Carottes râpées", C.FRESH_PRODUCE, "10", U.KG, True, S.REFRIGERATED, 0, 1),
    LotSeed(5, "Gratin de pâtes", C.PREPARED_MEAL, "50", U.PORTIONS, True, S.REFRIGERATED, -2,
            1, ("gluten", "milk"), (Booking(3, "30", True), Booking(0, "20", True))),
    # Hypermarché Porte d'Italie
    LotSeed(6, "Conserves de légumes", C.DRY_GOODS, "96", U.PIECES, True, S.AMBIENT, 5, 365),
    LotSeed(6, "Steaks hachés surgelés", C.MEAT_FISH, "10", U.KG, True, S.FROZEN, 2, 90,
            bookings=(Booking(2, "10"),)),
    LotSeed(6, "Packs de lait", C.DAIRY, "72", U.PIECES, True, S.AMBIENT, 1, 30, ("milk",)),
    LotSeed(6, "Salades en sachet", C.FRESH_PRODUCE, "35", U.PIECES, True, S.REFRIGERATED, -5,
            1, bookings=(Booking(2, "20", True),)),
    # Traiteur Saint-Germain
    LotSeed(7, "Plateaux de canapés", C.PREPARED_MEAL, "8", U.PIECES, False, S.REFRIGERATED, 0,
            1, ("gluten", "fish", "eggs")),
    LotSeed(7, "Quiches lorraines", C.PREPARED_MEAL, "24", U.PORTIONS, True, S.REFRIGERATED, 2,
            2, ("gluten", "eggs", "milk"), (Booking(4, "12"),)),
    # Restaurant universitaire Jussieu
    LotSeed(8, "Chili sin carne", C.PREPARED_MEAL, "60", U.PORTIONS, True, S.REFRIGERATED, 0, 1,
            bookings=(Booking(4, "25"),)),
    LotSeed(8, "Desserts lactés", C.DAIRY, "90", U.PIECES, True, S.REFRIGERATED, 1, 6,
            ("milk",)),
    LotSeed(8, "Couscous légumes", C.PREPARED_MEAL, "45", U.PORTIONS, True, S.REFRIGERATED, -1,
            1, ("gluten", "celery"), (Booking(4, "45", True),)),
    # Clinique du Parc de Saint-Denis
    LotSeed(9, "Purée et poisson pané", C.PREPARED_MEAL, "25", U.PORTIONS, True, S.REFRIGERATED,
            1, 1, ("fish", "gluten", "milk")),
    LotSeed(9, "Bouteilles d'eau", C.BEVERAGES, "144", U.PIECES, True, S.AMBIENT, 3, 365,
            bookings=(Booking(1, "144"),)),
]


def _pickup_window(day: int, now: datetime) -> tuple[datetime, datetime]:
    """Today: a window open since an hour; another day: 8h to 20h UTC that day."""
    if day == 0:
        start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
        return start, start + timedelta(hours=8)
    start = datetime.combine(now.date() + timedelta(days=day), time(8), tzinfo=UTC)
    return start, start + timedelta(hours=12)


def _add_manager(
    session: Session,
    org: Org,
    password_hash: str,
    now: datetime,
    status: RegistrationStatus,
    entity: Supplier | Association | None,
) -> None:
    is_supplier = org.supplier_type is not None
    user = User(
        email=org.manager.email,
        password_hash=password_hash,
        firstname=org.manager.firstname,
        lastname=org.manager.lastname,
        role=UserRole.MANAGER,
        supplier=entity if is_supplier else None,
        association=None if is_supplier else entity,
    )
    user.registration_request = RegistrationRequest(
        status=status,
        organization_type=OrganizationType.SUPPLIER if is_supplier else OrganizationType.ASSOCIATION,
        organization_name=org.name,
        legal_id=org.legal_id,
        supplier_type=org.supplier_type,
        street=org.street,
        postal_code=org.postal_code,
        city=org.city,
        latitude=org.latitude,
        longitude=org.longitude,
        contact_phone=org.contact_phone,
        supplier_id=entity.id if is_supplier and entity else None,
        association_id=entity.id if not is_supplier and entity else None,
        decided_at=None if status == RegistrationStatus.PENDING else now,
    )
    session.add(user)


def _entity_columns(org: Org) -> dict:
    return {
        "name": org.name,
        "legal_id": org.legal_id,
        "street": org.street,
        "postal_code": org.postal_code,
        "city": org.city,
        "latitude": org.latitude,
        "longitude": org.longitude,
        "contact_phone": org.contact_phone,
    }


def _add_lot(
    session: Session,
    spec: LotSeed,
    supplier: Supplier,
    associations: list[Association],
    rng: random.Random,
    now: datetime,
) -> None:
    start, end = _pickup_window(spec.day, now)
    created_at = min(now, start) - timedelta(days=1)
    quantity = Decimal(spec.quantity)
    booked = sum((Decimal(b.quantity) for b in spec.bookings), Decimal(0))
    lot = Lot(
        supplier=supplier,
        title=spec.title,
        category=spec.category,
        quantity=quantity,
        remaining_quantity=quantity - booked,
        unit=spec.unit,
        divisible=spec.divisible,
        use_by_date=start.date() + timedelta(days=spec.shelf_days),
        allergens=list(spec.allergens),
        storage=spec.storage,
        pickup_start=start,
        pickup_end=end,
        created_at=created_at,
    )
    session.add(lot)

    codes = rng.sample(range(10**6), len(spec.bookings))
    for i, booking in enumerate(spec.bookings):
        # Spread the pickups over the window, ahead of now for a window still open.
        first = max(start, now) if not booking.collected else start
        pickup_at = first + (end - first) * (i + 1) / (len(spec.bookings) + 1)
        session.add(
            Reservation(
                lot=lot,
                association=associations[booking.association],
                quantity=Decimal(booking.quantity),
                pickup_at=pickup_at.replace(second=0, microsecond=0),
                status=ReservationStatus.COLLECTED if booking.collected else ReservationStatus.BOOKED,
                pickup_code=f"{codes[i]:06d}",
                created_at=created_at + timedelta(hours=2 + i),
                collected_at=pickup_at + timedelta(minutes=10) if booking.collected else None,
            )
        )


def seed(session: Session, now: datetime | None = None) -> bool:
    """Insert the development data; False (nothing done) if it is already there."""
    exists = session.scalar(select(User.id).where(func.lower(User.email) == ADMIN_EMAIL))
    if exists is not None:
        return False
    now = now or datetime.now(UTC)
    password_hash = hash_password(DEV_PASSWORD)  # one bcrypt hash for every account
    rng = random.Random(42)

    session.add(
        User(
            email=ADMIN_EMAIL,
            password_hash=password_hash,
            firstname="Admin",
            lastname="Gaspirator",
            role=UserRole.ADMIN,
        )
    )

    suppliers = [Supplier(supplier_type=org.supplier_type, **_entity_columns(org)) for org in SUPPLIERS]
    associations = [Association(**_entity_columns(org)) for org in ASSOCIATIONS]
    session.add_all([*suppliers, *associations])
    session.flush()  # ids for the registration requests

    for org, entity in [*zip(SUPPLIERS, suppliers, strict=True), *zip(ASSOCIATIONS, associations, strict=True)]:
        _add_manager(session, org, password_hash, now, RegistrationStatus.APPROVED, entity)
    for org in PENDING:
        _add_manager(session, org, password_hash, now, RegistrationStatus.PENDING, None)

    for spec in LOTS:
        _add_lot(session, spec, suppliers[spec.supplier], associations, rng, now)

    session.commit()
    return True


def main() -> None:
    if not get_settings().seed_dev_data:
        print("Seed: skipped (SEED_DEV_DATA is not set).")
        return
    with SessionLocal() as session:
        if not seed(session):
            print("Seed: skipped (development data already there).")
            return
    print(
        f"Seed: {len(SUPPLIERS)} suppliers, {len(ASSOCIATIONS)} associations, "
        f"{len(LOTS)} lots. Accounts and their password: see the README "
        "(Development data)."
    )


if __name__ == "__main__":
    main()
