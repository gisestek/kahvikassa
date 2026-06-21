"""Add admin-editable Signal sender/group overrides to app_settings

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-21

"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("app_settings", sa.Column("signal_sender_number", sa.String(32), nullable=True))
    op.add_column("app_settings", sa.Column("signal_group_id", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("app_settings", "signal_group_id")
    op.drop_column("app_settings", "signal_sender_number")
