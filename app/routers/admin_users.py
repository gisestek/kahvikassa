from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import require_admin_user
from app.models.user import User
from app.services.admin_service import adjust_user_balance, create_user, list_all_users, update_user

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


class UserCreateRequest(BaseModel):
    full_name: str
    pin: str
    is_admin: bool = False


class UserUpdateRequest(BaseModel):
    full_name: str
    is_active: bool
    is_admin: bool
    new_pin: str | None = None


class BalanceAdjustmentRequest(BaseModel):
    amount: str
    description: str = ""


@router.get("")
async def get_users(_: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db_session)):
    users = await list_all_users(db)
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "balance": str(u.balance),
            "is_active": u.is_active,
            "is_admin": u.is_admin,
        }
        for u in users
    ]


@router.post("")
async def post_user(
    payload: UserCreateRequest,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db_session),
):
    user = await create_user(db, admin_user, payload.full_name, payload.pin, payload.is_admin)
    return {"id": user.id}


@router.put("/{user_id}")
async def put_user(
    user_id: int,
    payload: UserUpdateRequest,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db_session),
):
    await update_user(
        db, admin_user, user_id, payload.full_name, payload.is_active, payload.is_admin, payload.new_pin
    )
    return {"ok": True}


@router.post("/{user_id}/adjust-balance")
async def post_balance_adjustment(
    user_id: int,
    payload: BalanceAdjustmentRequest,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        amount = Decimal(payload.amount)
    except InvalidOperation as exc:
        raise HTTPException(status_code=400, detail="Virheellinen summa") from exc

    try:
        user = await adjust_user_balance(db, admin_user, user_id, amount, payload.description)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"id": user.id, "balance": str(user.balance)}
