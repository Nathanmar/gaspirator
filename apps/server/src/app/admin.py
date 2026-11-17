"""US-01: registration requests handled by the platform admins (/admin/registration-requests)."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app import models
from app.auth import get_current_admin
from app.db import get_session
from app.errors import ApiError, not_found
from app.mail import Email, Mailer, get_mailer, send_safely
from app.registration import to_schema
from app.schemas import (
    Error,
    OrganizationType,
    PageMeta,
    RegistrationRequest,
    RegistrationRequestPage,
    RegistrationStatus,
)

router = APIRouter(prefix="/admin/registration-requests", tags=["Admin"])

DbSession = Annotated[Session, Depends(get_session)]
CurrentAdmin = Annotated[models.User, Depends(get_current_admin)]
AppMailer = Annotated[Mailer, Depends(get_mailer)]

# Path parameters of the contract are int64.
RequestId = Annotated[int, Path(alias="requestId", ge=1, le=2**63 - 1)]


def _errors(*status_codes: int) -> dict[int | str, dict]:
    """Error responses documented in the generated OpenAPI (/docs)."""
    return {status: {"model": Error} for status in status_codes}


@router.get(
    "",
    response_model=RegistrationRequestPage,
    operation_id="listRegistrationRequests",
    responses=_errors(401, 403),
)
def list_registration_requests(
    _: CurrentAdmin,
    session: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> RegistrationRequestPage:
    """The `pending` registration requests, oldest first (the order they are handled in)."""
    pending = models.RegistrationRequest.status == RegistrationStatus.PENDING
    total = session.scalar(
        select(func.count()).select_from(models.RegistrationRequest).where(pending)
    )
    offset = (page - 1) * per_page
    requests = []
    if offset < total:  # also keeps a huge page from overflowing the SQL OFFSET
        requests = session.scalars(
            select(models.RegistrationRequest)
            .options(selectinload(models.RegistrationRequest.user))
            .where(pending)
            .order_by(models.RegistrationRequest.created_at, models.RegistrationRequest.id)
            .offset(offset)
            .limit(per_page)
        ).all()
    return RegistrationRequestPage(
        data=[to_schema(request) for request in requests],
        meta=PageMeta(page=page, per_page=per_page, total=total),
    )


def _pending_request(session: Session, request_id: int) -> models.RegistrationRequest:
    """The request, locked until the end of the transaction; 404 or 409 if not pending.

    The lock keeps two admins from deciding the same request at the same time.
    """
    request = session.scalar(
        select(models.RegistrationRequest)
        .where(models.RegistrationRequest.id == request_id)
        .with_for_update()
    )
    if request is None:
        raise not_found("Demande d'inscription introuvable.")
    if request.status != RegistrationStatus.PENDING:
        raise ApiError(409, "conflict", "Cette demande d'inscription a déjà été traitée.")
    return request


def _entity_columns(request: models.RegistrationRequest) -> dict:
    """Columns shared by `suppliers` and `associations`, copied from the request."""
    return {
        "name": request.organization_name,
        "legal_id": request.legal_id,
        "street": request.street,
        "postal_code": request.postal_code,
        "city": request.city,
        "latitude": request.latitude,  # geocoded on submission
        "longitude": request.longitude,
        "contact_phone": request.contact_phone,
    }


def _approved_email(request: models.RegistrationRequest) -> Email:
    user = request.user
    return Email(
        to=user.email,
        subject="Votre inscription sur Gaspirator est acceptée",
        body=(
            f"Bonjour {user.firstname},\n\n"
            f"La demande d'inscription de « {request.organization_name} » a été acceptée.\n"
            "Vous pouvez maintenant vous connecter à Gaspirator avec votre adresse e-mail "
            "et votre mot de passe.\n\n"
            "L'équipe Gaspirator"
        ),
    )


@router.post(
    "/{requestId}/approve",
    response_model=RegistrationRequest,
    operation_id="approveRegistrationRequest",
    responses=_errors(401, 403, 404, 409),
)
def approve_registration_request(
    request_id: RequestId,
    _: CurrentAdmin,
    session: DbSession,
    mailer: AppMailer,
    background_tasks: BackgroundTasks,
) -> RegistrationRequest:
    """Create the supplier or the association and activate the manager account.

    The manager can log in from now on (see `auth_routes._check_can_log_in`) and is told
    by e-mail, sent once the response is out.
    """
    request = _pending_request(session, request_id)
    if request.organization_type == OrganizationType.SUPPLIER:
        supplier = models.Supplier(**_entity_columns(request), supplier_type=request.supplier_type)
        request.user.supplier = supplier
        session.flush()
        request.supplier_id = supplier.id
    else:
        association = models.Association(**_entity_columns(request))
        request.user.association = association
        session.flush()
        request.association_id = association.id
    request.status = RegistrationStatus.APPROVED
    request.decided_at = datetime.now(UTC)
    session.commit()
    session.refresh(request)

    background_tasks.add_task(send_safely, mailer, _approved_email(request))
    return to_schema(request)


def _rejected_email(request: models.RegistrationRequest) -> Email:
    user = request.user
    return Email(
        to=user.email,
        subject="Votre inscription sur Gaspirator est refusée",
        body=(
            f"Bonjour {user.firstname},\n\n"
            f"La demande d'inscription de « {request.organization_name} » a été refusée.\n"
            "Votre compte ne peut donc pas être utilisé.\n\n"
            "L'équipe Gaspirator"
        ),
    )


@router.post(
    "/{requestId}/reject",
    response_model=RegistrationRequest,
    operation_id="rejectRegistrationRequest",
    responses=_errors(401, 403, 404, 409),
)
def reject_registration_request(
    request_id: RequestId,
    _: CurrentAdmin,
    session: DbSession,
    mailer: AppMailer,
    background_tasks: BackgroundTasks,
) -> RegistrationRequest:
    """Reject the request: nothing is created and the account cannot log in.

    The applicant is told by e-mail, sent once the response is out.
    """
    request = _pending_request(session, request_id)
    request.status = RegistrationStatus.REJECTED
    request.decided_at = datetime.now(UTC)
    session.commit()
    session.refresh(request)

    background_tasks.add_task(send_safely, mailer, _rejected_email(request))
    return to_schema(request)
