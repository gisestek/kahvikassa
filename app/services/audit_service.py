from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit import AuditEventType, AuditLogEntry


async def query_audit_log(
    db: AsyncSession,
    user_id: int | None = None,
    event_type: AuditEventType | None = None,
    sales_product_id: int | None = None,
    inventory_item_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 500,
) -> list[AuditLogEntry]:
    query = select(AuditLogEntry).options(
        selectinload(AuditLogEntry.user),
        selectinload(AuditLogEntry.sales_product),
        selectinload(AuditLogEntry.inventory_item),
    )

    if user_id is not None:
        query = query.where(AuditLogEntry.user_id == user_id)
    if event_type is not None:
        query = query.where(AuditLogEntry.event_type == event_type)
    if sales_product_id is not None:
        query = query.where(AuditLogEntry.sales_product_id == sales_product_id)
    if inventory_item_id is not None:
        query = query.where(AuditLogEntry.inventory_item_id == inventory_item_id)
    if date_from is not None:
        query = query.where(AuditLogEntry.occurred_at >= datetime.combine(date_from, time.min))
    if date_to is not None:
        query = query.where(AuditLogEntry.occurred_at <= datetime.combine(date_to, time.max))

    query = query.order_by(AuditLogEntry.occurred_at.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())
