"""`suppliers` and `associations` tables (contract `Supplier` / `Association`) and users."""

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from app.models import Association, Supplier
from app.schemas import SupplierType, UserRole

SHARED = {
    "street": "12 rue de la République",
    "postal_code": "69002",
    "city": "Lyon",
    "latitude": 45.7578,
    "longitude": 4.8320,
    "contact_phone": "04 78 00 00 00",
}

# Contract fields, with `address` and `location` flattened into columns.
SUMMARY_COLUMNS = {
    "id",
    "name",
    "street",
    "postal_code",
    "city",
    "latitude",
    "longitude",
    "contact_phone",
}


def _supplier(**overrides) -> Supplier:
    fields = {
        "name": "Cantine du lycée Ampère",
        "supplier_type": SupplierType.CANTEEN,
        "legal_id": "19690103400017",
        **SHARED,
    }
    return Supplier(**{**fields, **overrides})


def _association(**overrides) -> Association:
    fields = {"name": "Restos du Cœur Lyon 2", "legal_id": "W691234567", **SHARED}
    return Association(**{**fields, **overrides})


def _columns(db: Session, table: str) -> set[str]:
    return {column["name"] for column in inspect(db.get_bind()).get_columns(table)}


def test_supplier_columns_match_the_contract(db: Session):
    """`Supplier` = `SupplierSummary` + `legal_id` + `created_at`."""
    assert _columns(db, "suppliers") == SUMMARY_COLUMNS | {
        "supplier_type",
        "legal_id",
        "created_at",
    }


def test_association_columns_match_the_contract(db: Session):
    """`Association` = `AssociationSummary` + `legal_id` + `created_at`."""
    assert _columns(db, "associations") == SUMMARY_COLUMNS | {"legal_id", "created_at"}


def test_create_supplier_and_association(db: Session):
    supplier, association = _supplier(), _association()
    db.add_all([supplier, association])
    db.commit()

    assert supplier.id is not None and supplier.created_at is not None
    assert association.id is not None and association.created_at is not None


def test_supplier_type_is_required(db: Session):
    db.add(_supplier(supplier_type=None))
    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize("legal_id", ["W691234567", "1969010340001", "1969010340001A"])
def test_supplier_legal_id_is_a_siret(db: Session, legal_id: str):
    """Contract `SupplierCreate.legal_id`: `^\\d{14}$`."""
    db.add(_supplier(legal_id=legal_id))
    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize("legal_id", ["19690103400017", "W69123456", "X691234567"])
def test_association_legal_id_is_a_rna(db: Session, legal_id: str):
    """Contract `AssociationCreate.legal_id`: `^W\\d{9}$` (a SIRET is also too long)."""
    db.add(_association(legal_id=legal_id))
    with pytest.raises((IntegrityError, DataError)):
        db.commit()


def test_supplier_legal_id_is_unique(db: Session):
    db.add(_supplier())
    db.commit()
    db.add(_supplier(name="Autre cantine"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_association_legal_id_is_unique(db: Session):
    db.add(_association())
    db.commit()
    db.add(_association(name="Autre association"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_location_is_required(db: Session):
    db.add(_supplier(latitude=None))
    with pytest.raises(IntegrityError):
        db.commit()


def test_users_manage_a_supplier_or_an_association(db: Session, create_user):
    supplier, association = _supplier(), _association()
    db.add_all([supplier, association])
    db.commit()

    supplier_manager = create_user(email="cantine@example.org")
    supplier_manager.supplier = supplier
    association_manager = create_user(email="asso@example.org")
    association_manager.association = association
    admin = create_user(email="admin@gaspirator.fr", role=UserRole.ADMIN)
    db.commit()

    assert supplier.managers == [supplier_manager]
    assert association.managers == [association_manager]
    assert admin.supplier is None and admin.association is None


def test_user_cannot_manage_both(db: Session, create_user):
    supplier, association = _supplier(), _association()
    db.add_all([supplier, association])
    db.commit()

    user = create_user()
    user.supplier = supplier
    user.association = association
    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize("column", ["supplier_id", "association_id"])
def test_user_entity_must_exist(db: Session, create_user, column: str):
    user = create_user()
    setattr(user, column, 999)
    with pytest.raises(IntegrityError):
        db.commit()


def test_supplier_with_managers_cannot_be_deleted(db: Session, create_user):
    supplier = _supplier()
    db.add(supplier)
    db.commit()
    user = create_user()
    user.supplier = supplier
    db.commit()

    with pytest.raises(IntegrityError):
        db.execute(Supplier.__table__.delete().where(Supplier.id == supplier.id))
    db.rollback()
