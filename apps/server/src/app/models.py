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


class Organization(Base):
    """A supplier or an association (contract schema `Organization`).

    `address` and `location` of the contract are flattened into columns.
    """

    __tablename__ = "organizations"
    __table_args__ = (
        # Contract: `supplier_type` is required for a supplier, null for an association.
        CheckConstraint(
            "(type = 'supplier' AND supplier_type IS NOT NULL)"
            " OR (type = 'association' AND supplier_type IS NULL)",
            name="supplier_type_matches_type",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type: Mapped[OrganizationType] = mapped_column(_str_enum(OrganizationType, "organization_type"))
    name: Mapped[str] = mapped_column(String(255))
    supplier_type: Mapped[SupplierType | None] = mapped_column(
        _str_enum(SupplierType, "supplier_type")
    )
    # address
    street: Mapped[str] = mapped_column(String(255))
    postal_code: Mapped[str] = mapped_column(String(5))
    city: Mapped[str] = mapped_column(String(120))
    # location (GeoPoint)
    latitude: Mapped[float] = mapped_column(Double)
    longitude: Mapped[float] = mapped_column(Double)
    contact_phone: Mapped[str] = mapped_column(String(20))
    # SIRET (14 digits) or RNA number (W + 9 digits)
    legal_id: Mapped[str] = mapped_column(String(14), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    members: Mapped[list["User"]] = relationship(back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    firstname: Mapped[str] = mapped_column(String(255))
    lastname: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(_str_enum(UserRole, "user_role"))
    # Null for a platform admin (contract `Me.organization`).
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped[Organization | None] = relationship(back_populates="members")

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

    # Organisation created when an admin approves the request.
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="registration_request")
    organization: Mapped[Organization | None] = relationship()


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
