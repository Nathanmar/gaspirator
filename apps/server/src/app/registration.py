"""US-01: organisation registration requests."""

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
    Error,
    OrganizationCreate,
    RegistrationRequest,
    RegistrationRequestCreate,
    RegistrationStatus,
    UserRole,
)

router = APIRouter(tags=["Registration"])

_EMAIL_USED = "Cette adresse e-mail est déjà utilisée."
_LEGAL_ID_USED = "Ce SIRET ou ce n° RNA est déjà utilisé."


def _to_schema(request: models.RegistrationRequest) -> RegistrationRequest:
    return RegistrationRequest(
        id=request.id,
        status=request.status,
        organization=OrganizationCreate(
            type=request.organization_type,
            name=request.organization_name,
            legal_id=request.legal_id,
            supplier_type=request.supplier_type,
            address=Address(
                street=request.street, postal_code=request.postal_code, city=request.city
            ),
            contact_phone=request.contact_phone,
        ),
        account=AccountSummary(
            firstname=request.user.firstname,
            lastname=request.user.lastname,
            email=request.user.email,
        ),
        organization_id=request.organization_id,
        created_at=request.created_at,
        decided_at=request.decided_at,
    )


def _conflict_message(session: Session, payload: RegistrationRequestCreate) -> str | None:
    """Return why the request conflicts with an existing account or request, or None."""
    email_used = session.scalar(
        select(exists().where(func.lower(models.User.email) == payload.account.email.lower()))
    )
    if email_used:
        return _EMAIL_USED
    legal_id_used = session.scalar(
        select(exists().where(models.RegistrationRequest.legal_id == payload.organization.legal_id))
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
    """Create a `pending` registration request for an organisation and its manager."""
    conflict = _conflict_message(session, payload)
    if conflict is not None:
        raise ApiError(409, "conflict", conflict)

    organization, account = payload.organization, payload.account
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
        organization_type=organization.type,
        organization_name=organization.name,
        legal_id=organization.legal_id,
        supplier_type=organization.supplier_type,
        street=organization.address.street,
        postal_code=organization.address.postal_code,
        city=organization.address.city,
        contact_phone=organization.contact_phone,
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
