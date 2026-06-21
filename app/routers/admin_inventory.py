from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import require_admin_user
from app.models.user import User
from app.schemas.audit import InventoryCorrectionRequest, WastageRequest
from app.schemas.product import InventoryItemUpsert
from app.services.inventory_service import (
    create_inventory_item,
    list_inventory_with_stock,
    record_stocktake_correction,
    record_wastage,
    update_low_stock_threshold,
)

router = APIRouter(prefix="/api/admin/inventory", tags=["admin-inventory"])


class LowStockThresholdRequest(BaseModel):
    threshold: str | None = None


@router.get("")
async def get_inventory(_: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db_session)):
    items = await list_inventory_with_stock(db)
    return [
        {
            "id": i.id,
            "name": i.name,
            "unit": i.unit.value,
            "quantity_in_stock": str(i.quantity_in_stock),
            "low_stock_threshold": str(i.low_stock_threshold) if i.low_stock_threshold is not None else None,
        }
        for i in items
    ]


@router.put("/{inventory_item_id}/low-stock-threshold")
async def put_low_stock_threshold(
    inventory_item_id: int,
    payload: LowStockThresholdRequest,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        threshold = Decimal(payload.threshold) if payload.threshold else None
    except InvalidOperation as exc:
        raise HTTPException(status_code=400, detail="Virheellinen raja-arvo") from exc

    try:
        item = await update_low_stock_threshold(db, admin_user, inventory_item_id, threshold)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"id": item.id, "low_stock_threshold": str(item.low_stock_threshold) if item.low_stock_threshold else None}


@router.post("")
async def post_inventory_item(
    payload: InventoryItemUpsert,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db_session),
):
    item = await create_inventory_item(db, admin_user, payload.name, payload.unit)
    return {"id": item.id}


@router.post("/correction")
async def post_correction(
    payload: InventoryCorrectionRequest,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        await record_stocktake_correction(
            db, admin_user, payload.inventory_item_id, Decimal(payload.counted_quantity), payload.description
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/wastage")
async def post_wastage(
    payload: WastageRequest,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        await record_wastage(db, admin_user, payload.inventory_item_id, Decimal(payload.quantity), payload.description)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}
