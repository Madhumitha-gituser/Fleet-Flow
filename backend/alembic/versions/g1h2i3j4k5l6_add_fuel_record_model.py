"""Add FuelRecord model

Revision ID: g1h2i3j4k5l6
Revises: f1a2b3c4d5e6
Create Date: 2026-08-01 19:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g1h2i3j4k5l6'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the fuel_records table."""
    op.create_table(
        'fuel_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('fuel_quantity', sa.Float(), nullable=False),
        sa.Column('fuel_cost', sa.Float(), nullable=False),
        sa.Column('odometer_reading', sa.Float(), nullable=False),
        sa.Column('fuel_date', sa.Date(), nullable=False),
        sa.Column('fuel_station', sa.String(length=255), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id']),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fuel_records_id'), 'fuel_records', ['id'], unique=False)


def downgrade() -> None:
    """Drop the fuel_records table."""
    op.drop_index(op.f('ix_fuel_records_id'), table_name='fuel_records')
    op.drop_table('fuel_records')
