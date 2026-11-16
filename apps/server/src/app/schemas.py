"""Pydantic schemas for request/response validation (see openapi.yaml)."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError


class OrganizationType(StrEnum):
    SUPPLIER = "supplier"
    ASSOCIATION = "association"


class SupplierType(StrEnum):
    CANTEEN = "canteen"
    HOSPITAL = "hospital"
    SUPERMARKET = "supermarket"
    OTHER = "other"


class RegistrationStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class StrictModel(BaseModel):
    """Request body model: unknown fields are rejected (additionalProperties: false)."""

    model_config = ConfigDict(extra="forbid")


class Address(StrictModel):
    street: str = Field(min_length=3, max_length=255)
    postal_code: str = Field(pattern=r"^\d{5}$")
    city: str = Field(min_length=1, max_length=120)


class OrganizationCreate(StrictModel):
    type: OrganizationType
    name: str = Field(min_length=2, max_length=255)
    legal_id: str = Field(
        pattern=r"^(\d{14}|W\d{9})$",
        description="SIRET (14 chiffres) pour un fournisseur, n° RNA (W + 9 chiffres) pour une association",
    )
    supplier_type: SupplierType | None = Field(default=None, validate_default=True)
    address: Address
    contact_phone: str = Field(min_length=10, max_length=20)

    @field_validator("supplier_type")
    @classmethod
    def supplier_type_matches_type(
        cls, value: SupplierType | None, info: ValidationInfo
    ) -> SupplierType | None:
        org_type = info.data.get("type")
        if org_type == OrganizationType.SUPPLIER and value is None:
            raise PydanticCustomError("supplier_type_required", "obligatoire pour un fournisseur")
        if org_type == OrganizationType.ASSOCIATION and value is not None:
            raise PydanticCustomError(
                "supplier_type_forbidden", "doit être null pour une association"
            )
        return value


class AccountCreate(StrictModel):
    firstname: str = Field(min_length=1, max_length=255)
    lastname: str = Field(min_length=1, max_length=255)
    email: Annotated[EmailStr, Field(max_length=255)]
    password: str = Field(min_length=8, max_length=128)


class AccountSummary(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr


class RegistrationRequestCreate(StrictModel):
    organization: OrganizationCreate
    account: AccountCreate


class RegistrationRequest(BaseModel):
    id: int
    status: RegistrationStatus
    organization: OrganizationCreate
    account: AccountSummary
    organization_id: int | None
    created_at: datetime
    decided_at: datetime | None


# ----- Profil (US-01, US-06) -----


class OrganizationStatus(StrEnum):
    ACTIVE = "active"
    PENDING_REVIEW = "pending_review"
    SUSPENDED = "suspended"


class UserRole(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"


class GeoPoint(BaseModel):
    latitude: float
    longitude: float


class Organization(BaseModel):
    """`Organization` of the contract (also the shape stored until the database is wired)."""

    id: int
    type: OrganizationType
    name: str
    supplier_type: SupplierType | None
    address: Address
    location: GeoPoint
    contact_phone: str
    legal_id: str
    opening_hours: str | None
    status: OrganizationStatus
    suspension_reason: str | None = None
    created_at: datetime


class Me(BaseModel):
    id: int
    email: EmailStr
    firstname: str
    lastname: str
    role: UserRole
    organization: Organization | None


def _at_least_one_field(model: BaseModel) -> BaseModel:
    """minProperties: 1."""
    if not model.model_fields_set:
        raise PydanticCustomError("min_properties", "au moins un champ doit être renseigné")
    return model


# In the update bodies below, a field may be omitted but not sent as null (except
# `opening_hours`, nullable in the contract): the type is not optional, only the default.


class MeUpdate(StrictModel):
    firstname: str = Field(default=None, min_length=1, max_length=255)
    lastname: str = Field(default=None, min_length=1, max_length=255)
    email: Annotated[EmailStr, Field(max_length=255)] = None

    @model_validator(mode="after")
    def check_not_empty(self) -> "MeUpdate":
        return _at_least_one_field(self)


class PasswordChange(StrictModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class OrganizationUpdate(StrictModel):
    name: str = Field(default=None, min_length=2, max_length=255)
    legal_id: str = Field(default=None, pattern=r"^(\d{14}|W\d{9})$")
    supplier_type: SupplierType = None
    address: Address = None
    contact_phone: str = Field(default=None, min_length=10, max_length=20)
    opening_hours: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def check_not_empty(self) -> "OrganizationUpdate":
        return _at_least_one_field(self)


# ----- Erreurs -----


class ErrorDetail(BaseModel):
    field: str
    message: str


class Error(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None
