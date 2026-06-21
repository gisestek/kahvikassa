from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEventType, AuditLogEntry
from app.models.inventory import InventoryItem, InventoryUnit
from app.models.user import User
from app.services.inventory_service import check_and_maybe_notify_low_stock
from app.services.notification_service import format_supply_brought_message, send_signal_message


async def list_inventory_items(db: AsyncSession) -> list[InventoryItem]:
    result = await db.execute(select(InventoryItem).order_by(InventoryItem.name))
    return list(result.scalars().all())


async def ingest_supply(
    db: AsyncSession,
    user: User,
    quantity: Decimal,
    total_cost: Decimal,
    inventory_item_id: int | None,
    new_item_name: str | None,
    new_item_unit: InventoryUnit | None,
) -> InventoryItem:
    """Handles 'Toin tavaraa': increases stock and credits the bringer's balance
    with the full cost, since they are reimbursed for what they purchased out of
    pocket for the club."""
    if inventory_item_id is not None:
        inventory_item = await db.get(InventoryItem, inventory_item_id)
        if inventory_item is None:
            raise ValueError("Varastotuotetta ei löytynyt")
    else:
        inventory_item = InventoryItem(name=new_item_name, unit=new_item_unit, quantity_in_stock=Decimal("0"))
        db.add(inventory_item)
        await db.flush()

    inventory_item.quantity_in_stock += quantity
    await check_and_maybe_notify_low_stock(db, inventory_item)
    user.balance += total_cost

    db.add(
        AuditLogEntry(
            user_id=user.id,
            event_type=AuditEventType.SUPPLY_RESTOCK,
            inventory_item_id=inventory_item.id,
            quantity=quantity,
            amount=total_cost,
            description=f"Tuotu tavaraa: {inventory_item.name} ({quantity} {inventory_item.unit.value})",
        )
    )
    await db.commit()
    await send_signal_message(
        db,
        format_supply_brought_message(
            user.full_name, inventory_item.name, quantity, inventory_item.unit.value, total_cost
        ),
    )
    return inventory_item
