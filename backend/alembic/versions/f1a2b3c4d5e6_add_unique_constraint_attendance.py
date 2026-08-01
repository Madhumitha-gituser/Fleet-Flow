"""Add unique constraint driver_id+date on driver_attendances; add UniqueConstraint to model

Revision ID: f1a2b3c4d5e6
Revises: e1f2a3b4c5d6
Create Date: 2026-07-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint on (driver_id, date) in driver_attendances to prevent
    duplicate attendance records for the same driver on the same date (Task 5).
    """
    op.create_unique_constraint(
        'uq_driver_attendances_driver_date',
        'driver_attendances',
        ['driver_id', 'date'],
    )


def downgrade() -> None:
    """Remove the unique constraint."""
    op.drop_constraint(
        'uq_driver_attendances_driver_date',
        'driver_attendances',
        type_='unique',
    )
