"""Add low-stock threshold/notified tracking to inventory_items

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-21

"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("inventory_items", sa.Column("low_stock_threshold", sa.Numeric(12, 3), nullable=True))
    op.add_column(
        "inventory_items",
        sa.Column("low_stock_notified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("inventory_items", "low_stock_notified")
    op.drop_column("inventory_items", "low_stock_threshold")
