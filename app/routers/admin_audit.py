import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import require_admin_user
from app.models.audit import AuditEventType, AuditLogEntry
from app.models.user import User
from app.services.audit_service import count_audit_log, query_audit_log

router = APIRouter(prefix="/api/admin/audit", tags=["admin-audit"])

PAGE_SIZE = 100


def _serialize(e: AuditLogEntry) -> dict:
    return {
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


@router.get("")
async def get_audit_log(
    page: int = 1,
    user_id: int | None = None,
    event_type: AuditEventType | None = None,
    sales_product_id: int | None = None,
    inventory_item_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    _: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db_session),
):
    page = max(page, 1)
    filters = dict(
        user_id=user_id,
        event_type=event_type,
        sales_product_id=sales_product_id,
        inventory_item_id=inventory_item_id,
        date_from=date_from,
        date_to=date_to,
    )
    total = await count_audit_log(db, **filters)
    entries = await query_audit_log(db, **filters, limit=PAGE_SIZE, offset=(page - 1) * PAGE_SIZE)
    return {
        "items": [_serialize(e) for e in entries],
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
        "total_pages": max(1, -(-total // PAGE_SIZE)),
    }


@router.get("/export.csv")
async def export_audit_log_csv(
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
        limit=None,
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Aika", "Käyttäjä", "Tyyppi", "Tuote", "Varastotuote", "Määrä", "Summa", "Kommentti"])
    for e in entries:
        row = _serialize(e)
        writer.writerow(
            [
                row["occurred_at"],
                row["user_name"] or "",
                row["event_type"],
                row["sales_product_name"] or "",
                row["inventory_item_name"] or "",
                row["quantity"] or "",
                row["amount"] or "",
                row["description"] or "",
            ]
        )

    return Response(
        # Leading BOM so Excel detects UTF-8 correctly (ä/ö etc. in descriptions).
        content="﻿" + buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=kahvikassa_tapahtumaloki.csv"},
    )
