"""US-01: registration requests of suppliers and associations."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.auth import hash_password
from app.db import get_session
from app.errors import ApiError
from app.schemas import (
    AccountSummary,
    Address,
    AssociationCreate,
    Error,
    OrganizationType,
    RegistrationRequest,
    RegistrationRequestCreate,
    RegistrationStatus,
    SupplierCreate,
    UserRole,
)

router = APIRouter(tags=["Registration"])

_EMAIL_USED = "Cette adresse e-mail est déjà utilisée."
_LEGAL_ID_USED = "Ce SIRET ou ce n° RNA est déjà utilisé."


def _to_schema(request: models.RegistrationRequest) -> RegistrationRequest:
    address = None
    if request.street is not None:
        address = Address(street=request.street, postal_code=request.postal_code, city=request.city)
    supplier = association = None
    if request.organization_type == OrganizationType.SUPPLIER:
        supplier = SupplierCreate(
            name=request.organization_name,
            legal_id=request.legal_id,
            supplier_type=request.supplier_type,
            address=address,
            contact_phone=request.contact_phone,
        )
    else:
        association = AssociationCreate(
            name=request.organization_name,
            legal_id=request.legal_id,
            address=address,
            contact_phone=request.contact_phone,
        )
    return RegistrationRequest(
        id=request.id,
        status=request.status,
        supplier=supplier,
        association=association,
        account=AccountSummary(
            firstname=request.user.firstname,
            lastname=request.user.lastname,
            email=request.user.email,
        ),
        supplier_id=request.supplier_id,
        association_id=request.association_id,
        created_at=request.created_at,
        decided_at=request.decided_at,
    )


def _conflict_message(session: Session, email: str, legal_id: str) -> str | None:
    """Return why the request conflicts with an existing account or organisation, or None."""
    email_used = session.scalar(
        select(exists().where(func.lower(models.User.email) == email.lower()))
    )
    if email_used:
        return _EMAIL_USED
    legal_id_used = any(
        session.scalar(select(exists().where(model.legal_id == legal_id)))
        for model in (models.RegistrationRequest, models.Supplier, models.Association)
    )
    if legal_id_used:
        return _LEGAL_ID_USED
    return None


@router.post(
    "/registration-requests",
    status_code=201,
    response_model=RegistrationRequest,
    operation_id="createRegistrationRequest",
    responses={409: {"model": Error, "description": "SIRET, n° RNA ou e-mail déjà utilisé"}},
)
def create_registration_request(
    payload: RegistrationRequestCreate, session: Annotated[Session, Depends(get_session)]
) -> RegistrationRequest:
    """Create a `pending` registration request for a supplier or an association."""
    applicant: SupplierCreate | AssociationCreate = payload.supplier or payload.association
    account = payload.account
    conflict = _conflict_message(session, account.email, applicant.legal_id)
    if conflict is not None:
        raise ApiError(409, "conflict", conflict)

    user = models.User(
        email=account.email,
        password_hash=hash_password(account.password),
        firstname=account.firstname,
        lastname=account.lastname,
        role=UserRole.MANAGER,
    )
    request = models.RegistrationRequest(
        status=RegistrationStatus.PENDING,
        user=user,
        organization_type=(
            OrganizationType.SUPPLIER if payload.supplier else OrganizationType.ASSOCIATION
        ),
        organization_name=applicant.name,
        legal_id=applicant.legal_id,
        supplier_type=payload.supplier.supplier_type if payload.supplier else None,
        street=applicant.address.street if applicant.address else None,
        postal_code=applicant.address.postal_code if applicant.address else None,
        city=applicant.address.city if applicant.address else None,
        contact_phone=applicant.contact_phone,
    )
    session.add(request)
    try:
        session.commit()
    except IntegrityError as exc:
        # Concurrent registration with the same e-mail or legal id (unique constraints).
        session.rollback()
        message = _EMAIL_USED if "email" in str(exc.orig) else _LEGAL_ID_USED
        raise ApiError(409, "conflict", message) from exc
    session.refresh(request)
    return _to_schema(request)
