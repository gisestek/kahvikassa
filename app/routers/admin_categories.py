from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import require_admin_user
from app.models.user import User
from app.services.admin_service import list_categories, upsert_category

router = APIRouter(prefix="/api/admin/categories", tags=["admin-categories"])


class CategoryRequest(BaseModel):
    name: str
    sort_order: int = 0


@router.get("")
async def get_categories(_: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db_session)):
    categories = await list_categories(db)
    return [{"id": c.id, "name": c.name, "sort_order": c.sort_order} for c in categories]


@router.post("")
async def post_category(
    payload: CategoryRequest, _: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db_session)
):
    category = await upsert_category(db, None, payload.name, payload.sort_order)
    return {"id": category.id}


@router.put("/{category_id}")
async def put_category(
    category_id: int,
    payload: CategoryRequest,
    _: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db_session),
):
    await upsert_category(db, category_id, payload.name, payload.sort_order)
    return {"ok": True}
