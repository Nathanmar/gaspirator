"""SQLAlchemy ORM models."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, String, func
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


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    firstname: Mapped[str] = mapped_column(String(255))
    lastname: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(_str_enum(UserRole, "user_role"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    registration_request: Mapped["RegistrationRequest | None"] = relationship(back_populates="user")


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
    legal_id: Mapped[str] = mapped_column(String(14))
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
