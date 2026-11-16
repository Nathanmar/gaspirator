"""`organizations` table (contract schema `Organization`) and its links to users and requests."""

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Organization, RegistrationRequest, User
from app.schemas import OrganizationType, SupplierType, UserRole


def _organization(**overrides) -> Organization:
    fields = {
        "type": OrganizationType.SUPPLIER,
        "name": "Cantine du lycée Ampère",
        "supplier_type": SupplierType.CANTEEN,
        "street": "12 rue de la République",
        "postal_code": "69002",
        "city": "Lyon",
        "latitude": 45.7578,
        "longitude": 4.8320,
        "contact_phone": "04 78 00 00 00",
        "legal_id": "19690103400017",
    }
    return Organization(**{**fields, **overrides})


def test_columns_match_the_contract(db: Session):
    """Every field of the contract `Organization` is stored (address/location flattened)."""
    columns = {column["name"] for column in inspect(db.get_bind()).get_columns("organizations")}

    assert columns == {
        "id",
        "type",
        "name",
        "supplier_type",
        "street",
        "postal_code",
        "city",
        "latitude",
        "longitude",
        "contact_phone",
        "legal_id",
        "created_at",
    }


def test_create_supplier(db: Session):
    organization = _organization()
    db.add(organization)
    db.commit()

    assert organization.id is not None
    assert organization.created_at is not None


def test_create_association(db: Session):
    db.add(
        _organization(type=OrganizationType.ASSOCIATION, supplier_type=None, legal_id="W691234567")
    )
    db.commit()


def test_legal_id_is_unique(db: Session):
    db.add(_organization())
    db.commit()

    db.add(_organization(name="Autre cantine"))
    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize(
    ("org_type", "supplier_type"),
    [
        (OrganizationType.SUPPLIER, None),
        (OrganizationType.ASSOCIATION, SupplierType.CANTEEN),
    ],
    ids=["supplier-without-supplier-type", "association-with-supplier-type"],
)
def test_supplier_type_must_match_type(
    db: Session, org_type: OrganizationType, supplier_type: SupplierType | None
):
    db.add(_organization(type=org_type, supplier_type=supplier_type))
    with pytest.raises(IntegrityError):
        db.commit()


def test_location_is_required(db: Session):
    db.add(_organization(latitude=None))
    with pytest.raises(IntegrityError):
        db.commit()


def test_user_belongs_to_an_organization(db: Session, create_user):
    organization = _organization()
    db.add(organization)
    db.commit()

    manager = create_user()
    manager.organization = organization
    admin = create_user(email="admin@gaspirator.fr", role=UserRole.ADMIN)
    db.commit()

    assert manager.organization_id == organization.id
    assert organization.members == [manager]
    assert admin.organization is None


def test_user_organization_must_exist(db: Session, create_user):
    user = create_user()
    user.organization_id = 999
    with pytest.raises(IntegrityError):
        db.commit()


def test_registration_request_points_to_its_organization(db: Session, create_user):
    organization = _organization(legal_id="19690103400099")
    db.add(organization)
    manager = create_user()
    manager.registration_request.organization = organization
    db.commit()

    request = db.get(RegistrationRequest, manager.registration_request.id)
    assert request.organization_id == organization.id

    request.organization_id = 999
    with pytest.raises(IntegrityError):
        db.commit()


def test_organization_with_members_cannot_be_deleted(db: Session, create_user):
    organization = _organization()
    db.add(organization)
    db.commit()
    user = create_user()
    user.organization = organization
    db.commit()

    with pytest.raises(IntegrityError):
        db.execute(Organization.__table__.delete().where(Organization.id == organization.id))
    db.rollback()

    assert db.get(User, user.id).organization_id == organization.id
