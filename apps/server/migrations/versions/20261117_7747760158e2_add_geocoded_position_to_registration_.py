"""Add geocoded position to registration requests.

Nullable: the requests sent before geocoding existed have no position.

Revision ID: 7747760158e2
Revises: 3b1f0c2a9d47
Create Date: 2026-11-17 11:01:27.130024

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7747760158e2"
down_revision: str | Sequence[str] | None = "3b1f0c2a9d47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("registration_requests", sa.Column("latitude", sa.Double(), nullable=True))
    op.add_column("registration_requests", sa.Column("longitude", sa.Double(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("registration_requests", "longitude")
    op.drop_column("registration_requests", "latitude")
