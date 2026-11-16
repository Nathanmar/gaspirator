"""`suppliers` and `associations` tables against the contract `Supplier` / `Association`."""

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.schemas import UserRole

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


def test_supplier_type_is_required(db: Session, create_supplier):
    with pytest.raises(IntegrityError):
        create_supplier(supplier_type=None)


def test_location_is_required(db: Session, create_association):
    with pytest.raises(IntegrityError):
        create_association(latitude=None)


def test_supplier_legal_id_is_unique(db: Session, create_supplier):
    create_supplier(legal_id="19690103400017")
    with pytest.raises(IntegrityError):
        create_supplier(legal_id="19690103400017")


def test_association_legal_id_is_unique(db: Session, create_association):
    create_association(legal_id="W691234567")
    with pytest.raises(IntegrityError):
        create_association(legal_id="W691234567")


def test_user_cannot_manage_both(db: Session, create_supplier, create_association, create_user):
    """Contract `Me`: a user manages a supplier or an association, not both."""
    with pytest.raises(IntegrityError):
        create_user(supplier=create_supplier(), association=create_association())


def test_admin_manages_nothing(create_user):
    admin = create_user(email="admin@gaspirator.fr", role=UserRole.ADMIN)

    assert admin.supplier is None
    assert admin.association is None
