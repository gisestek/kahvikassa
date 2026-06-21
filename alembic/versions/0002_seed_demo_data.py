"""Seed initial categories, an admin user, and example products/recipes

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-20

"""
from alembic import op
import sqlalchemy as sa
from argon2 import PasswordHasher

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

_hasher = PasswordHasher()


def upgrade() -> None:
    bind = op.get_bind()

    bind.execute(
        sa.text(
            "INSERT INTO product_categories (name, sort_order) VALUES "
            "('Perustuotteet', 1), ('Naposteltavat', 2), ('Muut', 3)"
        )
    )

    admin_pin_hash = _hasher.hash("1234")
    bind.execute(
        sa.text(
            "INSERT INTO users (full_name, pin_hash, balance, is_active, is_admin) "
            "VALUES (:name, :pin_hash, 0, true, true)"
        ),
        {"name": "Ylläpitäjä", "pin_hash": admin_pin_hash},
    )

    bind.execute(
        sa.text(
            "INSERT INTO inventory_items (name, unit, quantity_in_stock) VALUES "
            "('Kahvijauhe', 'g', 2000), "
            "('Maito', 'ml', 3000), "
            "('Kahvinsuodatin', 'pcs', 100), "
            "('Energiajuomatölkki', 'pcs', 24)"
        )
    )

    perustuotteet_id = bind.execute(
        sa.text("SELECT id FROM product_categories WHERE name = 'Perustuotteet'")
    ).scalar_one()
    muut_id = bind.execute(sa.text("SELECT id FROM product_categories WHERE name = 'Muut'")).scalar_one()

    bind.execute(
        sa.text(
            "INSERT INTO sales_products (name, category_id, price, is_active, is_on_sale) VALUES "
            "('Musta kahvi', :perus, 0.50, true, true), "
            "('Café au lait', :perus, 0.80, true, true), "
            "('Energiajuoma', :muut, 1.50, true, true)"
        ),
        {"perus": perustuotteet_id, "muut": muut_id},
    )

    coffee_grounds_id = bind.execute(sa.text("SELECT id FROM inventory_items WHERE name = 'Kahvijauhe'")).scalar_one()
    milk_id = bind.execute(sa.text("SELECT id FROM inventory_items WHERE name = 'Maito'")).scalar_one()
    filter_id = bind.execute(sa.text("SELECT id FROM inventory_items WHERE name = 'Kahvinsuodatin'")).scalar_one()
    energy_can_id = bind.execute(
        sa.text("SELECT id FROM inventory_items WHERE name = 'Energiajuomatölkki'")
    ).scalar_one()

    black_coffee_id = bind.execute(sa.text("SELECT id FROM sales_products WHERE name = 'Musta kahvi'")).scalar_one()
    cafe_au_lait_id = bind.execute(sa.text("SELECT id FROM sales_products WHERE name = 'Café au lait'")).scalar_one()
    energy_drink_id = bind.execute(sa.text("SELECT id FROM sales_products WHERE name = 'Energiajuoma'")).scalar_one()

    bind.execute(
        sa.text(
            "INSERT INTO recipe_lines (sales_product_id, inventory_item_id, quantity_required) VALUES "
            "(:black, :grounds, 10), (:black, :filter, 0.12), "
            "(:cafe, :grounds, 10), (:cafe, :milk, 30), (:cafe, :filter, 0.12), "
            "(:energy, :can, 1)"
        ),
        {
            "black": black_coffee_id,
            "cafe": cafe_au_lait_id,
            "energy": energy_drink_id,
            "grounds": coffee_grounds_id,
            "milk": milk_id,
            "filter": filter_id,
            "can": energy_can_id,
        },
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM recipe_lines"))
    bind.execute(sa.text("DELETE FROM sales_products"))
    bind.execute(sa.text("DELETE FROM inventory_items"))
    bind.execute(sa.text("DELETE FROM users WHERE full_name = 'Ylläpitäjä'"))
    bind.execute(sa.text("DELETE FROM product_categories"))
