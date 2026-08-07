"""Add maintenance alerts

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-08-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h2i3j4k5l6m7'
down_revision: Union[str, Sequence[str], None] = 'g1h2i3j4k5l6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'maintenancealertstatus') THEN
                CREATE TYPE maintenancealertstatus AS ENUM ('Pending', 'Sent', 'Completed');
            END IF;
        END
        $$;
        """
    )

    op.create_table(
        'maintenance_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('maintenance_id', sa.Integer(), nullable=False),
        sa.Column('alert_message', sa.Text(), nullable=False),
        sa.Column('alert_type', sa.String(length=100), nullable=False),
        sa.Column('alert_status', sa.Text(), nullable=False),
        sa.Column('generated_date', sa.DateTime(), nullable=False),
        sa.Column('next_service_date', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['maintenance_id'], ['maintenance.id']),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_maintenance_alerts_id'), 'maintenance_alerts', ['id'], unique=False)

    op.execute(
        """
        ALTER TABLE maintenance_alerts
            ALTER COLUMN alert_status TYPE maintenancealertstatus
                USING alert_status::maintenancealertstatus,
            ALTER COLUMN alert_status SET DEFAULT 'Pending'::maintenancealertstatus;
        """
    )

    op.create_index(
        'uq_maintenance_alerts_pending_per_schedule',
        'maintenance_alerts',
        ['maintenance_id'],
        unique=True,
        postgresql_where=sa.text("alert_status = 'Pending'::maintenancealertstatus"),
    )


def downgrade() -> None:
    op.drop_index('uq_maintenance_alerts_pending_per_schedule', table_name='maintenance_alerts')
    op.drop_index(op.f('ix_maintenance_alerts_id'), table_name='maintenance_alerts')
    op.drop_table('maintenance_alerts')
    op.execute("DROP TYPE IF EXISTS maintenancealertstatus;")