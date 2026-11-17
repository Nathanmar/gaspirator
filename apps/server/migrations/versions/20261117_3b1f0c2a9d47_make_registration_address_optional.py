"""Make the address of a registration request optional (asked later).

Revision ID: 3b1f0c2a9d47
Revises: 09c05c76d8ae
Create Date: 2026-11-17 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3b1f0c2a9d47"
down_revision: str | Sequence[str] | None = "09c05c76d8ae"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = (("street", 255), ("postal_code", 5), ("city", 120))


def upgrade() -> None:
    """Upgrade schema."""
    for name, length in _COLUMNS:
        op.alter_column(
            "registration_requests", name, existing_type=sa.String(length), nullable=True
        )


def downgrade() -> None:
    """Downgrade schema (fails if a request has no address)."""
    for name, length in _COLUMNS:
        op.alter_column(
            "registration_requests", name, existing_type=sa.String(length), nullable=False
        )
