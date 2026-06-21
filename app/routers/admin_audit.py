from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import require_admin_user
from app.models.audit import AuditEventType
from app.models.user import User
from app.services.audit_service import query_audit_log

router = APIRouter(prefix="/api/admin/audit", tags=["admin-audit"])


@router.get("")
async def get_audit_log(
    user_id: int | None = None,
    event_type: AuditEventType | None = None,
    sales_product_id: int | None = None,
    inventory_item_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    _: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db_session),
):
    entries = await query_audit_log(
        db,
        user_id=user_id,
        event_type=event_type,
        sales_product_id=sales_product_id,
        inventory_item_id=inventory_item_id,
        date_from=date_from,
        date_to=date_to,
    )
    return [
        {
            "id": e.id,
            "occurred_at": e.occurred_at.isoformat(),
            "user_name": e.user.full_name if e.user else None,
            "event_type": e.event_type.value,
            "sales_product_name": e.sales_product.name if e.sales_product else None,
            "inventory_item_name": e.inventory_item.name if e.inventory_item else None,
            "quantity": str(e.quantity) if e.quantity is not None else None,
            "amount": str(e.amount) if e.amount is not None else None,
            "description": e.description,
        }
        for e in entries
    ]
