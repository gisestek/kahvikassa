from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEventType, AuditLogEntry
from app.models.inventory import InventoryItem, InventoryUnit
from app.models.user import User
from app.services.audit_service import log_system_change
from app.services.notification_service import format_low_stock_message, send_signal_message


async def check_and_maybe_notify_low_stock(db: AsyncSession, item: InventoryItem) -> None:
    """Mutates item.low_stock_notified and fires a Signal message exactly once
    per below-threshold dip — not on every purchase while stock stays low.
    Caller is responsible for committing the session afterwards."""
    if item.low_stock_threshold is None:
        return

    if item.quantity_in_stock <= item.low_stock_threshold:
        if not item.low_stock_notified:
            item.low_stock_notified = True
            await send_signal_message(
                db, format_low_stock_message(item.name, item.unit.value, item.quantity_in_stock)
            )
    else:
        item.low_stock_notified = False


async def list_inventory_with_stock(db: AsyncSession) -> list[InventoryItem]:
    result = await db.execute(select(InventoryItem).order_by(InventoryItem.name))
    return list(result.scalars().all())


async def create_inventory_item(db: AsyncSession, admin_user: User, name: str, unit: InventoryUnit) -> InventoryItem:
    item = InventoryItem(name=name, unit=unit, quantity_in_stock=Decimal("0"))
    db.add(item)
    await log_system_change(
        db, admin_user, f"Varastotuote luotu: {name} ({unit.value})", {"entity": "inventory_item", "action": "create"}
    )
    await db.commit()
    return item


async def update_low_stock_threshold(
    db: AsyncSession, admin_user: User, inventory_item_id: int, threshold: Decimal | None
) -> InventoryItem:
    item = await db.get(InventoryItem, inventory_item_id)
    if item is None:
        raise ValueError("Varastotuotetta ei löytynyt")
    item.low_stock_threshold = threshold
    await check_and_maybe_notify_low_stock(db, item)
    threshold_text = f"{threshold} {item.unit.value}" if threshold is not None else "ei käytössä"
    await log_system_change(
        db,
        admin_user,
        f"Hälytysraja asetettu: {item.name} = {threshold_text}",
        {"entity": "inventory_item", "action": "threshold_update", "id": item.id},
    )
    await db.commit()
    return item


async def record_stocktake_correction(
    db: AsyncSession, admin_user: User, inventory_item_id: int, counted_quantity: Decimal, description: str
) -> InventoryItem:
    """A physical stocktake is absolute truth: it overwrites the theoretical
    quantity_in_stock directly rather than nudging it, and the delta is logged
    so the discrepancy versus the calculated estimate remains visible."""
    item = await db.get(InventoryItem, inventory_item_id)
    if item is None:
        raise ValueError("Varastotuotetta ei löytynyt")

    delta = counted_quantity - item.quantity_in_stock
    item.quantity_in_stock = counted_quantity
    await check_and_maybe_notify_low_stock(db, item)

    db.add(
        AuditLogEntry(
            user_id=admin_user.id,
            event_type=AuditEventType.INVENTORY_CORRECTION,
            inventory_item_id=item.id,
            quantity=delta,
            description=description or f"Inventaario: laskettu määrä {counted_quantity} {item.unit.value}",
        )
    )
    await db.commit()
    return item


async def record_wastage(
    db: AsyncSession, admin_user: User, inventory_item_id: int, quantity: Decimal, description: str
) -> InventoryItem:
    item = await db.get(InventoryItem, inventory_item_id)
    if item is None:
        raise ValueError("Varastotuotetta ei löytynyt")

    item.quantity_in_stock -= quantity
    await check_and_maybe_notify_low_stock(db, item)

    db.add(
        AuditLogEntry(
            user_id=admin_user.id,
            event_type=AuditEventType.WASTAGE,
            inventory_item_id=item.id,
            quantity=-quantity,
            description=description or f"Hävikki: {quantity} {item.unit.value}",
        )
    )
    await db.commit()
    return item
