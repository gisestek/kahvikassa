from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import require_admin_user
from app.models.user import User
from app.routers.admin_products import _serialize
from app.services.admin_service import list_sales_products
from app.services.inventory_service import list_inventory_with_stock

router = APIRouter(prefix="/api/admin/recipes", tags=["admin-recipes"])


@router.get("/products-with-recipes")
async def get_products_with_recipes(
    _: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db_session)
):
    products = await list_sales_products(db)
    return [_serialize(p) for p in products]


@router.get("/inventory-options")
async def get_inventory_options(_: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db_session)):
    items = await list_inventory_with_stock(db)
    return [{"id": i.id, "name": i.name, "unit": i.unit.value} for i in items]
