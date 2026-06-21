from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import require_logged_in_user
from app.models.user import User
from app.schemas.cart import CheckoutRequest
from app.schemas.product import KioskCategoryGroup, KioskProduct
from app.security import SESSION_COOKIE_NAME
from app.services.kiosk_service import InsufficientCartError, checkout_cart, get_sellable_categories

router = APIRouter(prefix="/api/kiosk", tags=["kiosk"])


@router.get("/products", response_model=list[KioskCategoryGroup])
async def get_kiosk_products(
    current_user: User = Depends(require_logged_in_user), db: AsyncSession = Depends(get_db_session)
):
    categories = await get_sellable_categories(db)
    return [
        KioskCategoryGroup(
            category_name=category.name,
            products=[
                KioskProduct(id=p.id, name=p.name, price=str(p.price)) for p in category.sales_products
            ],
        )
        for category in categories
    ]


@router.post("/checkout")
async def checkout(
    payload: CheckoutRequest,
    response: Response,
    current_user: User = Depends(require_logged_in_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        total_charged = await checkout_cart(
            db, current_user, [(item.sales_product_id, item.quantity) for item in payload.items]
        )
    except InsufficientCartError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"total_charged": str(total_charged)}


@router.post("/cancel")
async def cancel(response: Response, current_user: User = Depends(require_logged_in_user)):
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"ok": True}
