"""Pydantic schemas for request/response validation (see openapi.yaml)."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationInfo, field_validator
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


class UserRole(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"


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


class GeoPoint(BaseModel):
    latitude: float
    longitude: float


class OrganizationSummary(BaseModel):
    id: int
    type: OrganizationType
    name: str
    supplier_type: SupplierType | None
    address: Address
    location: GeoPoint
    contact_phone: str


class Organization(OrganizationSummary):
    legal_id: str
    created_at: datetime


class Me(BaseModel):
    id: int
    email: EmailStr
    firstname: str
    lastname: str
    role: UserRole
    organization: Organization | None = Field(description="Null pour un admin de la plateforme")


class ErrorDetail(BaseModel):
    field: str
    message: str


class Error(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None


class LoginRequest(StrictModel):
    email: EmailStr
    password: str


class RefreshRequest(StrictModel):
    refresh_token: str


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int = Field(description="Durée de validité du token d'accès en secondes")
