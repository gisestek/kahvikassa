from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import require_admin_user
from app.models.user import User
from app.services.admin_service import get_app_settings
from app.services.theme_service import activate_theme, list_available_themes

router = APIRouter(prefix="/api/admin/themes", tags=["admin-themes"])


class ThemeActivateRequest(BaseModel):
    slug: str


@router.get("")
async def get_themes(_: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db_session)):
    settings = await get_app_settings(db)
    return {"themes": list_available_themes(), "active": settings.active_theme}


@router.put("")
async def put_active_theme(
    payload: ThemeActivateRequest,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        slug = await activate_theme(db, admin_user, payload.slug)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"active": slug}
