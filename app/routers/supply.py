from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import require_logged_in_user
from app.models.user import User
from app.schemas.supply import SupplyIngestionRequest
from app.services.supply_service import ingest_supply, list_inventory_items

router = APIRouter(prefix="/api/supply", tags=["supply"])


@router.get("/inventory-items")
async def get_inventory_items(
    current_user: User = Depends(require_logged_in_user), db: AsyncSession = Depends(get_db_session)
):
    items = await list_inventory_items(db)
    return [{"id": i.id, "name": i.name, "unit": i.unit.value} for i in items]


@router.post("/ingest")
async def ingest(
    payload: SupplyIngestionRequest,
    current_user: User = Depends(require_logged_in_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        quantity = Decimal(payload.quantity)
        total_cost = Decimal(payload.total_cost)
    except InvalidOperation as exc:
        raise HTTPException(status_code=400, detail="Virheellinen luku") from exc

    if quantity <= 0 or total_cost < 0:
        raise HTTPException(status_code=400, detail="Määrän on oltava positiivinen ja hinnan ei-negatiivinen")

    try:
        await ingest_supply(
            db,
            current_user,
            quantity=quantity,
            total_cost=total_cost,
            inventory_item_id=payload.inventory_item_id,
            new_item_name=payload.new_item.name if payload.new_item else None,
            new_item_unit=payload.new_item.unit if payload.new_item else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"ok": True}
