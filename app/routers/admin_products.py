from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import require_admin_user
from app.models.user import User
from app.schemas.product import SalesProductUpsert
from app.services.admin_service import list_sales_products, upsert_sales_product

router = APIRouter(prefix="/api/admin/products", tags=["admin-products"])


def _serialize(product) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "category_id": product.category_id,
        "category_name": product.category.name if product.category else None,
        "price": str(product.price),
        "is_active": product.is_active,
        "is_on_sale": product.is_on_sale,
        "recipe_lines": [
            {
                "inventory_item_id": rl.inventory_item_id,
                "inventory_item_name": rl.inventory_item.name if rl.inventory_item else None,
                "unit": rl.inventory_item.unit.value if rl.inventory_item else None,
                "quantity_required": str(rl.quantity_required),
            }
            for rl in product.recipe_lines
        ],
    }


@router.get("")
async def get_products(_: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db_session)):
    products = await list_sales_products(db)
    return [_serialize(p) for p in products]


@router.post("")
async def post_product(
    payload: SalesProductUpsert,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db_session),
):
    product = await upsert_sales_product(
        db,
        admin_user,
        None,
        payload.name,
        payload.category_id,
        Decimal(payload.price),
        payload.is_active,
        payload.is_on_sale,
        [(rl.inventory_item_id, Decimal(rl.quantity_required)) for rl in payload.recipe_lines],
    )
    return {"id": product.id}


@router.put("/{product_id}")
async def put_product(
    product_id: int,
    payload: SalesProductUpsert,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db_session),
):
    await upsert_sales_product(
        db,
        admin_user,
        product_id,
        payload.name,
        payload.category_id,
        Decimal(payload.price),
        payload.is_active,
        payload.is_on_sale,
        [(rl.inventory_item_id, Decimal(rl.quantity_required)) for rl in payload.recipe_lines],
    )
    return {"ok": True}
