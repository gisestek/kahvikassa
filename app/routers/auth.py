from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import require_logged_in_user
from app.models.user import User
from app.schemas.auth import ChangePinRequest, CurrentUserResponse, LoginRequest
from app.security import SESSION_COOKIE_NAME, create_session_token
from app.services.auth_service import authenticate_with_pin, change_own_pin

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db_session)):
    user = await authenticate_with_pin(db, payload.user_id, payload.pin)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Väärä PIN-koodi")

    token = create_session_token(user.id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 8,
    )
    return {"redirect_to": "/kioski"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"ok": True}


@router.get("/me", response_model=CurrentUserResponse)
async def whoami(current_user: User = Depends(require_logged_in_user)):
    return CurrentUserResponse(
        id=current_user.id,
        full_name=current_user.full_name,
        balance=str(current_user.balance),
        is_admin=current_user.is_admin,
    )


@router.post("/change-pin")
async def change_pin(
    payload: ChangePinRequest,
    current_user: User = Depends(require_logged_in_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        await change_own_pin(db, current_user, payload.current_pin, payload.new_pin)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}
