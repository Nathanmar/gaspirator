"""Add the geocoded position (latitude, longitude) to registration requests.

The contract geocodes the address on submission; the position is copied to the supplier
or association `location` when an admin approves the request.

Revision ID: 5b1f3c2a9d47
Revises: 3b1f0c2a9d47
Create Date: 2026-11-17 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5b1f3c2a9d47"
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
