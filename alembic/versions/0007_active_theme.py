"""Add active_theme column to app_settings

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-22

"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "app_settings",
        sa.Column("active_theme", sa.String(50), nullable=False, server_default="gootti"),
    )


def downgrade() -> None:
    op.drop_column("app_settings", "active_theme")
