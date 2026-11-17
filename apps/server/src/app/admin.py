"""US-01: registration requests handled by the platform admins (/admin/registration-requests)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app import models
from app.auth import get_current_admin
from app.db import get_session
from app.registration import to_schema
from app.schemas import Error, PageMeta, RegistrationRequestPage, RegistrationStatus

router = APIRouter(prefix="/admin/registration-requests", tags=["Admin"])

DbSession = Annotated[Session, Depends(get_session)]
CurrentAdmin = Annotated[models.User, Depends(get_current_admin)]


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
