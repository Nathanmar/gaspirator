"""Pydantic schemas for request/response validation (see openapi.yaml)."""

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    ValidationInfo,
    field_serializer,
    field_validator,
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


class UserRole(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"


class LotCategory(StrEnum):
    """Food categories only (non-food donations are out of scope)."""

    FRESH_PRODUCE = "fresh_produce"
    DAIRY = "dairy"
    MEAT_FISH = "meat_fish"
    BAKERY = "bakery"
    PREPARED_MEAL = "prepared_meal"
    DRY_GOODS = "dry_goods"
    BEVERAGES = "beverages"
    OTHER_FOOD = "other_food"


class Allergen(StrEnum):
    """The 14 allergens that must be declared."""

    GLUTEN = "gluten"
    CRUSTACEANS = "crustaceans"
    EGGS = "eggs"
    FISH = "fish"
    PEANUTS = "peanuts"
    SOYBEANS = "soybeans"
    MILK = "milk"
    NUTS = "nuts"
    CELERY = "celery"
    MUSTARD = "mustard"
    SESAME = "sesame"
    SULPHITES = "sulphites"
    LUPIN = "lupin"
    MOLLUSCS = "molluscs"


class Storage(StrEnum):
    AMBIENT = "ambient"
    REFRIGERATED = "refrigerated"
    FROZEN = "frozen"


class QuantityUnit(StrEnum):
    PORTIONS = "portions"
    KG = "kg"
    PIECES = "pieces"


class LotStatus(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    COLLECTED = "collected"
    EXPIRED = "expired"


class StrictModel(BaseModel):
    """Request body model: unknown fields are rejected (additionalProperties: false)."""

    model_config = ConfigDict(extra="forbid")


class Address(StrictModel):
    street: str = Field(min_length=3, max_length=255)
    postal_code: str = Field(pattern=r"^\d{5}$")
    city: str = Field(min_length=1, max_length=120)


class GeoPoint(BaseModel):
    latitude: float
    longitude: float


class SupplierSummary(BaseModel):
    """Supplier as seen by the associations (`SupplierSummary` of the contract)."""

    id: int
    name: str
    supplier_type: SupplierType
    address: Address
    location: GeoPoint
    contact_phone: str


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


# ----- Lots -----


def _utc_today() -> date:
    return datetime.now(UTC).date()


class LotCreate(StrictModel):
    title: str = Field(min_length=3, max_length=120)
    category: LotCategory
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    unit: QuantityUnit
    divisible: bool = True
    use_by_date: date = Field(description="Date limite de consommation (DLC)")
    allergens: list[Allergen] = Field(default_factory=list)
    storage: Storage
    pickup_start: AwareDatetime
    pickup_end: AwareDatetime

    @field_validator("use_by_date")
    @classmethod
    def use_by_date_not_passed(cls, value: date) -> date:
        if value < _utc_today():
            raise PydanticCustomError(
                "lot_use_by_date_passed", "doit être aujourd'hui ou plus tard"
            )
        return value

    @field_validator("allergens")
    @classmethod
    def allergens_unique(cls, value: list[Allergen]) -> list[Allergen]:
        if len(set(value)) != len(value):
            raise PydanticCustomError("lot_allergens_duplicated", "ne doit pas contenir de doublon")
        return value

    @field_validator("pickup_end")
    @classmethod
    def pickup_window(cls, value: datetime, info: ValidationInfo) -> datetime:
        start, use_by_date = info.data.get("pickup_start"), info.data.get("use_by_date")
        if start is not None and value <= start:
            raise PydanticCustomError("lot_pickup_end_before_start", "doit être après pickup_start")
        if use_by_date is not None:
            end_of_use_by_day = datetime.combine(use_by_date + timedelta(days=1), time(), UTC)
            if value > end_of_use_by_day:
                raise PydanticCustomError(
                    "lot_pickup_end_after_use_by_date",
                    "doit être au plus tard à la fin du jour de la DLC",
                )
        return value


def _to_utc(value: datetime) -> datetime:
    return value.astimezone(UTC)


class Lot(BaseModel):
    id: int
    supplier: SupplierSummary
    title: str
    category: LotCategory
    quantity: float
    remaining_quantity: float
    unit: QuantityUnit
    divisible: bool
    use_by_date: date
    allergens: list[Allergen]
    storage: Storage
    pickup_start: datetime
    pickup_end: datetime
    status: LotStatus
    created_at: datetime

    @field_serializer("pickup_start", "pickup_end", "created_at")
    def _serialize_utc(self, value: datetime) -> datetime:
        """Date-times are answered in UTC, whatever the time zone of the database session."""
        return _to_utc(value)


# ----- Erreurs -----


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
