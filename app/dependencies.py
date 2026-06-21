from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models.user import User
from app.security import SESSION_COOKIE_NAME, read_session_token

DbSession = AsyncSession


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db_session)
) -> User | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    user_id = read_session_token(token)
    if user_id is None:
        return None
    return await db.get(User, user_id)


async def require_logged_in_user(
    current_user: User | None = Depends(get_current_user),
) -> User:
    if current_user is None or not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kirjautuminen vaaditaan")
    return current_user


async def require_admin_user(
    current_user: User | None = Depends(get_current_user),
) -> User:
    if current_user is None or not current_user.is_active or not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vain ylläpitäjille")
    return current_user
