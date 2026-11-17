"""SQLAlchemy ORM models."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Double,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.schemas import (
    LotCategory,
    OrganizationType,
    QuantityUnit,
    RegistrationStatus,
    ReservationStatus,
    Storage,
    SupplierType,
    UserRole,
)


def _str_enum(enum_cls: type, name: str) -> Enum:
    """Enum stored as VARCHAR + CHECK constraint, using the enum values."""
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=32,
        values_callable=lambda members: [member.value for member in members],
    )


class Supplier(Base):
    """A supplier (canteen, hospital, supermarket...) that publishes lots."""

    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    legal_id: Mapped[str] = mapped_column(String(14), unique=True)  # SIRET
    supplier_type: Mapped[SupplierType] = mapped_column(_str_enum(SupplierType, "supplier_type"))
    street: Mapped[str] = mapped_column(String(255))
    postal_code: Mapped[str] = mapped_column(String(5))
    city: Mapped[str] = mapped_column(String(120))
    latitude: Mapped[float] = mapped_column(Double)
    longitude: Mapped[float] = mapped_column(Double)
    contact_phone: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Association(Base):
    """An association that reserves and collects lots."""

    __tablename__ = "associations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    legal_id: Mapped[str] = mapped_column(String(10), unique=True)  # n° RNA
    street: Mapped[str] = mapped_column(String(255))
    postal_code: Mapped[str] = mapped_column(String(5))
    city: Mapped[str] = mapped_column(String(120))
    latitude: Mapped[float] = mapped_column(Double)
    longitude: Mapped[float] = mapped_column(Double)
    contact_phone: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    # A manager runs either a supplier or an association; an admin runs neither.
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(supplier_id, association_id) <= 1", name="at_most_one_organization"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    firstname: Mapped[str] = mapped_column(String(255))
    lastname: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(_str_enum(UserRole, "user_role"))
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), index=True)
    association_id: Mapped[int | None] = mapped_column(ForeignKey("associations.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    supplier: Mapped[Supplier | None] = relationship()
    association: Mapped[Association | None] = relationship()

    # The database deletes the request with its user (ON DELETE CASCADE).
    registration_request: Mapped["RegistrationRequest | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


# Case-insensitive unique e-mail.
Index("uq_users_email_lower", func.lower(User.email), unique=True)


class RegistrationRequest(Base):
    """Registration of a supplier or an association and its manager account (US-01).

    `organization_type` says which one is requested; the other columns describe it.
    """

    __tablename__ = "registration_requests"
    __table_args__ = (
        # Only a supplier has a type of establishment.
        CheckConstraint(
            "(organization_type = 'supplier') = (supplier_type IS NOT NULL)",
            name="supplier_type_for_suppliers_only",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    status: Mapped[RegistrationStatus] = mapped_column(
        _str_enum(RegistrationStatus, "registration_status")
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    organization_type: Mapped[OrganizationType] = mapped_column(
        _str_enum(OrganizationType, "organization_type")
    )
    organization_name: Mapped[str] = mapped_column(String(255))
    legal_id: Mapped[str] = mapped_column(String(14), unique=True)
    supplier_type: Mapped[SupplierType | None] = mapped_column(
        _str_enum(SupplierType, "supplier_type")
    )
    # Address: optional at registration, asked later.
    street: Mapped[str | None] = mapped_column(String(255))
    postal_code: Mapped[str | None] = mapped_column(String(5))
    city: Mapped[str | None] = mapped_column(String(120))
    # Position of the address, geocoded when the request is sent (null without address, or
    # for the requests sent before geocoding existed). Copied to the supplier or association
    # on approval.
    latitude: Mapped[float | None] = mapped_column(Double)
    longitude: Mapped[float | None] = mapped_column(Double)
    contact_phone: Mapped[str] = mapped_column(String(20))

    # Supplier or association created when an admin approves the request.
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    association_id: Mapped[int | None] = mapped_column(ForeignKey("associations.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="registration_request")


class RefreshToken(Base):
    """Opaque refresh token; only its SHA-256 hash is stored."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship()


# Quantities in kg can be fractional: exact decimals, so that reservations never drift.
Quantity = Numeric(12, 3)


class Lot(Base):
    """A lot of food published by a supplier (US-02).

    `remaining_quantity` is what can still be reserved; the status is computed from it
    and from the dates (see `app.lots.lot_status`).
    """

    __tablename__ = "lots"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint(
            "remaining_quantity >= 0 AND remaining_quantity <= quantity",
            name="remaining_quantity_range",
        ),
        CheckConstraint("pickup_end > pickup_start", name="pickup_window"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(120))
    category: Mapped[LotCategory] = mapped_column(_str_enum(LotCategory, "lot_category"))
    quantity: Mapped[Decimal] = mapped_column(Quantity)
    remaining_quantity: Mapped[Decimal] = mapped_column(Quantity)
    unit: Mapped[QuantityUnit] = mapped_column(_str_enum(QuantityUnit, "quantity_unit"))
    divisible: Mapped[bool] = mapped_column(Boolean)
    use_by_date: Mapped[date] = mapped_column(Date)
    allergens: Mapped[list[str]] = mapped_column(ARRAY(String(32)), server_default=text("'{}'"))
    storage: Mapped[Storage] = mapped_column(_str_enum(Storage, "storage"))
    pickup_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    pickup_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    supplier: Mapped[Supplier] = relationship(lazy="joined")
    # Only loaded for the status of a fully reserved lot (`reserved` or `collected`).
    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="lot", passive_deletes=True
    )


class Reservation(Base):
    """A quantity of a lot reserved by an association (US-04), collected with its pickup
    code (US-05). Its quantity is taken off `Lot.remaining_quantity`."""

    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        # Only a collected reservation has a collection time.
        CheckConstraint(
            "(status = 'collected') = (collected_at IS NOT NULL)", name="collected_at_if_collected"
        ),
        # The supplier tells the reservations of a lot apart by their pickup code.
        UniqueConstraint("lot_id", "pickup_code", name="uq_reservations_lot_id_pickup_code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Indexed by the unique constraint (lot_id, pickup_code).
    lot_id: Mapped[int] = mapped_column(ForeignKey("lots.id", ondelete="CASCADE"))
    association_id: Mapped[int] = mapped_column(
        ForeignKey("associations.id", ondelete="CASCADE"), index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Quantity)
    pickup_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[ReservationStatus] = mapped_column(
        _str_enum(ReservationStatus, "reservation_status")
    )
    pickup_code: Mapped[str] = mapped_column(String(6))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Wrong pickup codes in a row (US-05); at the limit, confirming is blocked for a while.
    failed_confirmations: Mapped[int] = mapped_column(
        SmallInteger, default=0, server_default=text("0")
    )
    confirmation_locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    lot: Mapped[Lot] = relationship(lazy="joined", back_populates="reservations")
    association: Mapped[Association] = relationship(lazy="joined")
