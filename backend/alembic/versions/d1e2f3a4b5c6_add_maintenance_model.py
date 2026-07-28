"""Add Maintenance model

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b6
Create Date: 2026-07-28 16:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the maintenance table with category and status enums."""

    # Step 1 – Create enum types only if they don't already exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'maintenancecategory') THEN
                CREATE TYPE maintenancecategory AS ENUM (
                    'Oil Change',
                    'Tyre Replacement',
                    'Brake Service',
                    'Engine Service',
                    'General Inspection'
                );
            END IF;
        END
        $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'maintenancestatus') THEN
                CREATE TYPE maintenancestatus AS ENUM (
                    'Scheduled',
                    'In Progress',
                    'Completed',
                    'Cancelled'
                );
            END IF;
        END
        $$;
    """)

    # Step 2 – Create table using plain TEXT columns for the enum fields
    #          (avoids SQLAlchemy attempting to re-create the enum types)
    op.create_table(
        'maintenance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('service_date', sa.Date(), nullable=False),
        sa.Column('next_service_date', sa.Date(), nullable=True),
        sa.Column('service_cost', sa.Float(), nullable=True),
        sa.Column('service_provider', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_maintenance_id'), 'maintenance', ['id'], unique=False)

    # Step 3 – Cast TEXT columns to the proper enum types
    op.execute("""
        ALTER TABLE maintenance
            ALTER COLUMN category TYPE maintenancecategory
                USING category::maintenancecategory,
            ALTER COLUMN status   TYPE maintenancestatus
                USING status::maintenancestatus;
    """)

    # Step 4 – Set default for status column
    op.execute("""
        ALTER TABLE maintenance
            ALTER COLUMN status SET DEFAULT 'Scheduled'::maintenancestatus;
    """)


def downgrade() -> None:
    """Drop the maintenance table and its enums."""
    op.drop_index(op.f('ix_maintenance_id'), table_name='maintenance')
    op.drop_table('maintenance')

    op.execute("DROP TYPE IF EXISTS maintenancecategory;")
    op.execute("DROP TYPE IF EXISTS maintenancestatus;")
