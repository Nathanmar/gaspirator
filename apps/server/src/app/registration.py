"""US-01: organisation registration requests."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.auth import hash_password
from app.db import get_session
from app.schemas import (
    AccountSummary,
    Address,
    OrganizationCreate,
    RegistrationRequest,
    RegistrationRequestCreate,
    RegistrationStatus,
    UserRole,
)

router = APIRouter(tags=["Registration"])


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


@router.post(
    "/registration-requests",
    status_code=201,
    response_model=RegistrationRequest,
    operation_id="createRegistrationRequest",
)
def create_registration_request(
    payload: RegistrationRequestCreate, session: Annotated[Session, Depends(get_session)]
) -> RegistrationRequest:
    """Create a `pending` registration request for an organisation and its manager."""
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
    session.commit()
    session.refresh(request)
    return _to_schema(request)
