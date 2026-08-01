"""Add DriverAssignment and DriverAttendance models

Revision ID: e1f2a3b4c5d6
Revises: d1e2f3a4b5c6
Create Date: 2026-07-30 18:28:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create driver_assignments and driver_attendances tables."""

    # -----------------------------------------------------------------------
    # Step 1 – Create the AttendanceStatus enum type (idempotent)
    # -----------------------------------------------------------------------
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'attendancestatus') THEN
                CREATE TYPE attendancestatus AS ENUM (
                    'Present',
                    'Absent',
                    'Leave'
                );
            END IF;
        END
        $$;
    """)

    # -----------------------------------------------------------------------
    # Step 2 – Create driver_assignments table
    # -----------------------------------------------------------------------
    op.create_table(
        'driver_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('trip_id', sa.Integer(), nullable=True),
        sa.Column('assignment_date', sa.Date(), nullable=False),
        sa.Column('assignment_status', sa.String(length=50), nullable=False, server_default='Active'),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id']),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id']),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_driver_assignments_id'), 'driver_assignments', ['id'], unique=False)

    # -----------------------------------------------------------------------
    # Step 3 – Create driver_attendances table (TEXT column first, then cast)
    # -----------------------------------------------------------------------
    op.create_table(
        'driver_attendances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('attendance_status', sa.Text(), nullable=False),
        sa.Column('check_in_time', sa.DateTime(), nullable=True),
        sa.Column('check_out_time', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_driver_attendances_id'), 'driver_attendances', ['id'], unique=False)

    # -----------------------------------------------------------------------
    # Step 4 – Cast attendance_status TEXT → attendancestatus enum
    # -----------------------------------------------------------------------
    op.execute("""
        ALTER TABLE driver_attendances
            ALTER COLUMN attendance_status TYPE attendancestatus
                USING attendance_status::attendancestatus;
    """)


def downgrade() -> None:
    """Drop driver_assignments and driver_attendances tables and the enum."""
    op.drop_index(op.f('ix_driver_attendances_id'), table_name='driver_attendances')
    op.drop_table('driver_attendances')

    op.drop_index(op.f('ix_driver_assignments_id'), table_name='driver_assignments')
    op.drop_table('driver_assignments')

    op.execute("DROP TYPE IF EXISTS attendancestatus;")
