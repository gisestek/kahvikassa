"""Add app_settings table (monthly fee config) and MONTHLY_FEE audit event type

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-21

"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'MONTHLY_FEE'")

    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("monthly_fee_amount", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("monthly_fee_active", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute("INSERT INTO app_settings (id, monthly_fee_amount, monthly_fee_active) VALUES (1, 0.00, false)")


def downgrade() -> None:
    op.drop_table("app_settings")
    # Postgres cannot drop a single enum value; MONTHLY_FEE remains in the type on downgrade.
