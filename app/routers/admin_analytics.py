from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import require_admin_user
from app.models.user import User
from app.services.analytics_service import (
    estimate_coffee_pots_brewed,
    milk_consumption_per_week,
    total_wastage_by_item,
    user_usage_patterns,
    weekly_product_sales_volume,
)

router = APIRouter(prefix="/api/admin/analytics", tags=["admin-analytics"])


@router.get("/sales-volume")
async def get_sales_volume(weeks_back: int = 8, _: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db_session)):
    rows = await weekly_product_sales_volume(db, weeks_back)
    return [{"product_name": r["product_name"], "units_sold": r["units_sold"], "revenue": str(r["revenue"])} for r in rows]


@router.get("/wastage")
async def get_wastage(weeks_back: int = 8, _: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db_session)):
    rows = await total_wastage_by_item(db, weeks_back)
    return [{"item_name": r["item_name"], "unit": r["unit"], "quantity": str(r["quantity"])} for r in rows]


@router.get("/user-usage")
async def get_user_usage(weeks_back: int = 8, _: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db_session)):
    rows = await user_usage_patterns(db, weeks_back)
    return [{"user_name": r["user_name"], "purchase_count": r["purchase_count"], "total_spent": str(r["total_spent"])} for r in rows]


@router.get("/milk-consumption")
async def get_milk_consumption(weeks_back: int = 8, _: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db_session)):
    rows = await milk_consumption_per_week(db, weeks_back)
    return [{"week": r["week"], "milk_ml": str(r["milk_ml"])} for r in rows]


@router.get("/coffee-pots")
async def get_coffee_pots(weeks_back: int = 4, _: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db_session)):
    return await estimate_coffee_pots_brewed(db, weeks_back)
