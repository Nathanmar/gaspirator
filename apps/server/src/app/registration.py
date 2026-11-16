"""US-01: organisation registration requests."""

from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import APIRouter

from app.auth import hash_password
from app.schemas import (
    AccountSummary,
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


@router.post(
    "/registration-requests",
    status_code=201,
    response_model=RegistrationRequest,
    operation_id="createRegistrationRequest",
)
async def create_registration_request(payload: RegistrationRequestCreate) -> RegistrationRequest:
    """Create a `pending` registration request for an organisation and its manager."""
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
