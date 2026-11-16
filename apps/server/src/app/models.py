"""SQLAlchemy ORM models."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Double,
    Enum,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.schemas import OrganizationType, RegistrationStatus, SupplierType, UserRole


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


class _ManagedEntity:
    """Columns shared by suppliers and associations (contract `SupplierSummary` /
    `AssociationSummary`): `address` and `location` are flattened into columns."""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    # address
    street: Mapped[str] = mapped_column(String(255))
    postal_code: Mapped[str] = mapped_column(String(5))
    city: Mapped[str] = mapped_column(String(120))
    # location (GeoPoint)
    latitude: Mapped[float] = mapped_column(Double)
    longitude: Mapped[float] = mapped_column(Double)
    contact_phone: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Supplier(_ManagedEntity, Base):
    """A food supplier (contract schema `Supplier`)."""

    __tablename__ = "suppliers"
    __table_args__ = (CheckConstraint(r"legal_id ~ '^\d{14}$'", name="legal_id_is_siret"),)

    supplier_type: Mapped[SupplierType] = mapped_column(_str_enum(SupplierType, "supplier_type"))
    # SIRET (14 digits)
    legal_id: Mapped[str] = mapped_column(String(14), unique=True)

    managers: Mapped[list["User"]] = relationship(back_populates="supplier")


class Association(_ManagedEntity, Base):
    """A charity (contract schema `Association`)."""

    __tablename__ = "associations"
    __table_args__ = (CheckConstraint(r"legal_id ~ '^W\d{9}$'", name="legal_id_is_rna"),)

    # RNA number (W + 9 digits)
    legal_id: Mapped[str] = mapped_column(String(10), unique=True)

    managers: Mapped[list["User"]] = relationship(back_populates="association")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        # A user manages a supplier or an association, not both (contract `Me`).
        CheckConstraint("supplier_id IS NULL OR association_id IS NULL", name="manages_one_entity"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    firstname: Mapped[str] = mapped_column(String(255))
    lastname: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(_str_enum(UserRole, "user_role"))
    # Contract `Me.supplier` / `Me.association`: null if the user does not manage one.
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), index=True)
    association_id: Mapped[int | None] = mapped_column(ForeignKey("associations.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    supplier: Mapped[Supplier | None] = relationship(back_populates="managers")
    association: Mapped[Association | None] = relationship(back_populates="managers")

    # The database deletes the request with its user (ON DELETE CASCADE).
    registration_request: Mapped["RegistrationRequest | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


# Case-insensitive unique e-mail.
Index("uq_users_email_lower", func.lower(User.email), unique=True)


class RegistrationRequest(Base):
    """Registration of an organisation and its manager account (US-01)."""

    __tablename__ = "registration_requests"

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
    street: Mapped[str] = mapped_column(String(255))
    postal_code: Mapped[str] = mapped_column(String(5))
    city: Mapped[str] = mapped_column(String(120))
    contact_phone: Mapped[str] = mapped_column(String(20))

    # Organisation created when an admin approves the request (no table yet).
    organization_id: Mapped[int | None] = mapped_column(BigInteger)
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
