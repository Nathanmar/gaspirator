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
    SerializerFunctionWrapHandler,
    ValidationInfo,
    field_serializer,
    field_validator,
    model_serializer,
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


class ReservationStatus(StrEnum):
    BOOKED = "booked"
    COLLECTED = "collected"


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


class Supplier(SupplierSummary):
    """Full supplier, seen by its manager (`Supplier` of the contract)."""

    legal_id: str
    created_at: datetime


class AssociationSummary(BaseModel):
    """Association as seen by the suppliers (`AssociationSummary` of the contract)."""

    id: int
    name: str
    address: Address
    location: GeoPoint
    contact_phone: str


class Association(AssociationSummary):
    """Full association, seen by its manager (`Association` of the contract)."""

    legal_id: str
    created_at: datetime


class Me(BaseModel):
    """The logged-in user (`Me` of the contract)."""

    id: int
    email: EmailStr
    firstname: str
    lastname: str
    role: UserRole
    supplier: Supplier | None = Field(
        description="Fournisseur dont l'utilisateur est responsable, null sinon"
    )
    association: Association | None = Field(
        description="Association dont l'utilisateur est responsable, null sinon"
    )


class SupplierCreate(StrictModel):
    name: str = Field(min_length=2, max_length=255)
    legal_id: str = Field(pattern=r"^\d{14}$", description="SIRET (14 chiffres)")
    supplier_type: SupplierType
    address: Address
    contact_phone: str = Field(min_length=10, max_length=20)


class AssociationCreate(StrictModel):
    name: str = Field(min_length=2, max_length=255)
    legal_id: str = Field(pattern=r"^W\d{9}$", description="N° RNA (W suivi de 9 chiffres)")
    address: Address
    contact_phone: str = Field(min_length=10, max_length=20)


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
    """`SupplierRegistrationCreate` or `AssociationRegistrationCreate` of the contract.

    One model with both keys optional rather than a union, so that the errors keep the
    field paths of the body (`supplier.legal_id`, not the name of a union member).
    """

    supplier: SupplierCreate | None = None
    association: AssociationCreate | None = None
    account: AccountCreate

    @model_validator(mode="after")
    def supplier_or_association(self) -> "RegistrationRequestCreate":
        if self.supplier is None and self.association is None:
            raise PydanticCustomError(
                "registration_applicant_missing",
                "obligatoire : un fournisseur (supplier) ou une association (association)",
                {"field": "supplier"},
            )
        if self.supplier is not None and self.association is not None:
            raise PydanticCustomError(
                "registration_applicant_twice",
                "une demande porte sur un fournisseur ou une association, pas les deux",
                {"field": "association"},
            )
        return self


class RegistrationRequest(BaseModel):
    id: int
    status: RegistrationStatus
    supplier: SupplierCreate | None
    association: AssociationCreate | None
    account: AccountSummary
    supplier_id: int | None
    association_id: int | None
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


# ----- Reservations -----


class ReservationCreate(StrictModel):
    """`quantity` is required for a divisible lot; omitted, an indivisible lot is reserved
    as a whole. Both rules need the lot: they are checked by the route."""

    quantity: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=3)
    pickup_at: AwareDatetime = Field(description="Heure de passage, dans le créneau de collecte")


class LotSummary(BaseModel):
    """Lot as it appears in a reservation."""

    id: int
    title: str
    unit: QuantityUnit
    divisible: bool
    use_by_date: date
    storage: Storage
    pickup_start: datetime
    pickup_end: datetime
    supplier: SupplierSummary

    @field_serializer("pickup_start", "pickup_end")
    def _serialize_utc(self, value: datetime) -> datetime:
        return _to_utc(value)


class Reservation(BaseModel):
    id: int
    lot: LotSummary
    association: AssociationSummary
    quantity: float
    pickup_at: datetime
    status: ReservationStatus
    pickup_code: str | None = Field(
        default=None,
        pattern=r"^\d{6}$",
        description="Code de collecte, renvoyé uniquement à l'association qui a réservé",
    )
    created_at: datetime
    collected_at: datetime | None

    @field_serializer("pickup_at", "created_at", "collected_at")
    def _serialize_utc(self, value: datetime | None) -> datetime | None:
        return None if value is None else _to_utc(value)

    @model_serializer(mode="wrap")
    def _omit_hidden_pickup_code(self, handler: SerializerFunctionWrapHandler):
        """The pickup code is left out, not null, for whoever must not see it.

        No return annotation: pydantic then keeps the model schema in the OpenAPI.
        """
        data = handler(self)
        if data.get("pickup_code") is None:
            data.pop("pickup_code", None)
        return data


class ReservationList(BaseModel):
    data: list[Reservation]


# ----- Pagination -----


class PageMeta(BaseModel):
    page: int
    per_page: int
    total: int


class LotPage(BaseModel):
    data: list[Lot]
    meta: PageMeta


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
