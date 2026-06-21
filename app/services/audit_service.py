from datetime import date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit import AuditEventType, AuditLogEntry
from app.models.user import User


def _apply_filters(
    query,
    user_id: int | None,
    event_type: AuditEventType | None,
    sales_product_id: int | None,
    inventory_item_id: int | None,
    date_from: date | None,
    date_to: date | None,
):
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
    return query


async def count_audit_log(
    db: AsyncSession,
    user_id: int | None = None,
    event_type: AuditEventType | None = None,
    sales_product_id: int | None = None,
    inventory_item_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> int:
    query = _apply_filters(
        select(func.count(AuditLogEntry.id)), user_id, event_type, sales_product_id, inventory_item_id, date_from, date_to
    )
    result = await db.execute(query)
    return result.scalar_one()


async def query_audit_log(
    db: AsyncSession,
    user_id: int | None = None,
    event_type: AuditEventType | None = None,
    sales_product_id: int | None = None,
    inventory_item_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int | None = 100,
    offset: int = 0,
) -> list[AuditLogEntry]:
    query = select(AuditLogEntry).options(
        selectinload(AuditLogEntry.user),
        selectinload(AuditLogEntry.sales_product),
        selectinload(AuditLogEntry.inventory_item),
    )
    query = _apply_filters(query, user_id, event_type, sales_product_id, inventory_item_id, date_from, date_to)
    query = query.order_by(AuditLogEntry.occurred_at.desc()).offset(offset)
    if limit is not None:
        query = query.limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


async def log_system_change(
    db: AsyncSession, admin_user: User, description: str, extra_data: dict | None = None
) -> None:
    """Records a generic admin/self-service CRUD action (user, category,
    product, inventory item, threshold, or settings change) in the audit
    log. Caller is responsible for committing the session afterwards —
    this just stages the entry so it lands in the same transaction as the
    actual change it's describing."""
    db.add(
        AuditLogEntry(
            user_id=admin_user.id,
            event_type=AuditEventType.SYSTEM_CHANGE,
            description=description,
            extra_data=extra_data or {},
        )
    )
