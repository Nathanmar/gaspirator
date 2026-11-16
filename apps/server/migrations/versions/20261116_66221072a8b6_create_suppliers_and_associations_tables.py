"""Create the suppliers and associations tables and link users to them.

Contract schemas `Supplier` and `Association`; a user manages one of them (`Me`).

Revision ID: 66221072a8b6
Revises: ae38020d8920
Create Date: 2026-11-16 15:36:47.584307

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "66221072a8b6"
down_revision: str | Sequence[str] | None = "ae38020d8920"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _shared_columns() -> list[sa.Column]:
    """Columns of `SupplierSummary` / `AssociationSummary` (address and location flattened)."""
    return [
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("street", sa.String(length=255), nullable=False),
        sa.Column("postal_code", sa.String(length=5), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("latitude", sa.Double(), nullable=False),
        sa.Column("longitude", sa.Double(), nullable=False),
        sa.Column("contact_phone", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "suppliers",
        *_shared_columns(),
        sa.Column(
            "supplier_type",
            sa.Enum(
                "canteen",
                "hospital",
                "supermarket",
                "other",
                name="supplier_type",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("legal_id", sa.String(length=14), nullable=False),
        sa.CheckConstraint("legal_id ~ '^\\d{14}$'", name=op.f("ck_suppliers_legal_id_is_siret")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_suppliers")),
        sa.UniqueConstraint("legal_id", name=op.f("uq_suppliers_legal_id")),
    )
    op.create_table(
        "associations",
        *_shared_columns(),
        sa.Column("legal_id", sa.String(length=10), nullable=False),
        sa.CheckConstraint("legal_id ~ '^W\\d{9}$'", name=op.f("ck_associations_legal_id_is_rna")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_associations")),
        sa.UniqueConstraint("legal_id", name=op.f("uq_associations_legal_id")),
    )

    op.add_column("users", sa.Column("supplier_id", sa.BigInteger(), nullable=True))
    op.add_column("users", sa.Column("association_id", sa.BigInteger(), nullable=True))
    op.create_index(op.f("ix_users_supplier_id"), "users", ["supplier_id"], unique=False)
    op.create_index(op.f("ix_users_association_id"), "users", ["association_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_users_supplier_id_suppliers"), "users", "suppliers", ["supplier_id"], ["id"]
    )
    op.create_foreign_key(
        op.f("fk_users_association_id_associations"),
        "users",
        "associations",
        ["association_id"],
        ["id"],
    )
    # Not detected by autogenerate (CHECK on an existing table).
    op.create_check_constraint(
        op.f("ck_users_manages_one_entity"),
        "users",
        "supplier_id IS NULL OR association_id IS NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f("ck_users_manages_one_entity"), "users", type_="check")
    op.drop_constraint(op.f("fk_users_association_id_associations"), "users", type_="foreignkey")
    op.drop_constraint(op.f("fk_users_supplier_id_suppliers"), "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_association_id"), table_name="users")
    op.drop_index(op.f("ix_users_supplier_id"), table_name="users")
    op.drop_column("users", "association_id")
    op.drop_column("users", "supplier_id")
    op.drop_table("associations")
    op.drop_table("suppliers")
