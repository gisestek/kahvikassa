from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit import AuditEventType, AuditLogEntry
from app.models.inventory import InventoryItem
from app.models.product import ProductCategory, SalesProduct
from app.models.recipe import RecipeLine
from app.models.user import User
from app.services.inventory_service import check_and_maybe_notify_low_stock

# Fixed display order for the three mandated kiosk categories.
CATEGORY_DISPLAY_ORDER = ["Perustuotteet", "Naposteltavat", "Muut"]


async def get_sellable_categories(db: AsyncSession) -> list[ProductCategory]:
    """Returns categories with their currently sellable products attached.

    A product is shown on the kiosk only if it is active, marked on sale, AND
    has at least one recipe line — otherwise checkout could never deduct stock
    correctly, so we hide it rather than risk an inconsistent sale.
    """
    result = await db.execute(
        select(ProductCategory)
        .options(selectinload(ProductCategory.sales_products).selectinload(SalesProduct.recipe_lines))
        .order_by(ProductCategory.sort_order)
    )
    categories = list(result.scalars().all())

    for category in categories:
        category.sales_products = [
            p for p in category.sales_products if p.is_active and p.is_on_sale and len(p.recipe_lines) > 0
        ]

    categories.sort(
        key=lambda c: CATEGORY_DISPLAY_ORDER.index(c.name) if c.name in CATEGORY_DISPLAY_ORDER else 99
    )
    return categories


class InsufficientCartError(Exception):
    pass


async def checkout_cart(
    db: AsyncSession, user: User, cart_items: list[tuple[int, int]]
) -> Decimal:
    """Processes the OK action: deducts recipe ingredients from inventory, deducts
    the total from the user's balance, and writes one audit entry per cart line.

    cart_items is a list of (sales_product_id, quantity) pairs. Returns the total
    amount charged. Inventory is allowed to go negative — this is a trust-based
    kiosk, and theoretical stock is treated as an estimate corrected at physical
    stocktakes, never a hard purchase gate.
    """
    if not cart_items:
        raise InsufficientCartError("Ostoskori on tyhjä")

    product_ids = [pid for pid, _ in cart_items]
    result = await db.execute(
        select(SalesProduct)
        .where(SalesProduct.id.in_(product_ids))
        .options(selectinload(SalesProduct.recipe_lines).selectinload(RecipeLine.inventory_item))
    )
    products_by_id = {p.id: p for p in result.scalars().all()}

    total_amount = Decimal("0.00")
    inventory_deltas: dict[int, Decimal] = {}

    for sales_product_id, quantity in cart_items:
        product = products_by_id.get(sales_product_id)
        if product is None or not product.is_active or not product.is_on_sale:
            raise InsufficientCartError(f"Tuotetta ei voi ostaa: {sales_product_id}")

        line_total = product.price * quantity
        total_amount += line_total

        for recipe_line in product.recipe_lines:
            needed = recipe_line.quantity_required * quantity
            inventory_deltas[recipe_line.inventory_item_id] = (
                inventory_deltas.get(recipe_line.inventory_item_id, Decimal("0")) + needed
            )

        db.add(
            AuditLogEntry(
                user_id=user.id,
                event_type=AuditEventType.PURCHASE,
                sales_product_id=product.id,
                quantity=Decimal(quantity),
                amount=-line_total,
                description=f"Ostettu {quantity} x {product.name}",
            )
        )

    for inventory_item_id, deduction in inventory_deltas.items():
        inventory_item = await db.get(InventoryItem, inventory_item_id)
        if inventory_item is not None:
            inventory_item.quantity_in_stock -= deduction
            await check_and_maybe_notify_low_stock(db, inventory_item)

    user.balance -= total_amount
    await db.commit()
    return total_amount
