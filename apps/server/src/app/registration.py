"""US-01: organisation registration requests."""

from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.auth import hash_password
from app.schemas import (
    AccountSummary,
    Error,
    RegistrationRequest,
    RegistrationRequestCreate,
    RegistrationStatus,
)

router = APIRouter(tags=["Registration"])


@dataclass
class _StoredRequest:
    request: RegistrationRequest
    password_hash: str


# In-memory storage until the database is wired.
_requests: dict[int, _StoredRequest] = {}


def _conflict_message(payload: RegistrationRequestCreate) -> str | None:
    """Return why the request conflicts with an existing one, or None."""
    email = payload.account.email.lower()
    legal_id = payload.organization.legal_id
    for stored in _requests.values():
        if stored.request.account.email.lower() == email:
            return "Cette adresse e-mail est déjà utilisée."
        if stored.request.organization.legal_id == legal_id:
            return "Ce SIRET ou ce n° RNA est déjà utilisé."
    return None


@router.post(
    "/registration-requests",
    status_code=201,
    response_model=RegistrationRequest,
    operation_id="createRegistrationRequest",
    responses={409: {"model": Error, "description": "SIRET, n° RNA ou e-mail déjà utilisé"}},
)
async def create_registration_request(
    payload: RegistrationRequestCreate,
) -> RegistrationRequest | JSONResponse:
    """Create a `pending` registration request for an organisation and its manager."""
    conflict = _conflict_message(payload)
    if conflict is not None:
        return JSONResponse(
            status_code=409,
            content=Error(code="conflict", message=conflict).model_dump(exclude_none=True),
        )

    request = RegistrationRequest(
        id=len(_requests) + 1,
        status=RegistrationStatus.PENDING,
        organization=payload.organization,
        account=AccountSummary(
            firstname=payload.account.firstname,
            lastname=payload.account.lastname,
            email=payload.account.email,
        ),
        organization_id=None,
        created_at=datetime.now(UTC),
        decided_at=None,
    )
    _requests[request.id] = _StoredRequest(
        request=request, password_hash=hash_password(payload.account.password)
    )
    return request
