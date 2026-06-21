"""Initial schema for Kahvikassa

Revision ID: 0001
Revises:
Create Date: 2026-06-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # create_type=False: these ENUMs are created implicitly by create_table()
    # below when first referenced by a column. Creating them explicitly here
    # as well caused a DuplicateObject error.
    inventory_unit = postgresql.ENUM("g", "ml", "pcs", name="inventory_unit", create_type=False)
    audit_event_type = postgresql.ENUM(
        "PURCHASE", "SUPPLY_RESTOCK", "INVENTORY_CORRECTION", "WASTAGE", "ADMIN_ADJUSTMENT",
        name="audit_event_type",
        create_type=False,
    )
    inventory_unit.create(op.get_bind())
    audit_event_type.create(op.get_bind())

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("pin_hash", sa.String(255), nullable=False),
        sa.Column("balance", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False, server_default="{}"),
    )

    op.create_table(
        "product_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(60), nullable=False, unique=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "inventory_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("unit", inventory_unit, nullable=False),
        sa.Column("quantity_in_stock", sa.Numeric(12, 3), nullable=False, server_default="0"),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False, server_default="{}"),
    )

    op.create_table(
        "sales_products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("product_categories.id"), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_on_sale", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False, server_default="{}"),
    )

    op.create_table(
        "recipe_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sales_product_id", sa.Integer(), sa.ForeignKey("sales_products.id"), nullable=False),
        sa.Column("inventory_item_id", sa.Integer(), sa.ForeignKey("inventory_items.id"), nullable=False),
        sa.Column("quantity_required", sa.Numeric(12, 3), nullable=False),
    )

    op.create_table(
        "audit_log_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_type", audit_event_type, nullable=False),
        sa.Column("sales_product_id", sa.Integer(), sa.ForeignKey("sales_products.id"), nullable=True),
        sa.Column("inventory_item_id", sa.Integer(), sa.ForeignKey("inventory_items.id"), nullable=True),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_audit_occurred_at", "audit_log_entries", ["occurred_at"])
    op.create_index("ix_audit_user_id", "audit_log_entries", ["user_id"])
    op.create_index("ix_audit_event_type", "audit_log_entries", ["event_type"])
    op.create_index("ix_audit_sales_product_id", "audit_log_entries", ["sales_product_id"])
    op.create_index("ix_audit_inventory_item_id", "audit_log_entries", ["inventory_item_id"])


def downgrade() -> None:
    op.drop_table("audit_log_entries")
    op.drop_table("recipe_lines")
    op.drop_table("sales_products")
    op.drop_table("inventory_items")
    op.drop_table("product_categories")
    op.drop_table("users")
    postgresql.ENUM(name="audit_event_type").drop(op.get_bind())
    postgresql.ENUM(name="inventory_unit").drop(op.get_bind())
