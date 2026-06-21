from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.security import hash_pin, verify_pin
from app.services.audit_service import log_system_change


async def list_active_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).where(User.is_active.is_(True)).order_by(User.full_name))
    return list(result.scalars().all())


async def authenticate_with_pin(db: AsyncSession, user_id: int, pin: str) -> User | None:
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    if not verify_pin(pin, user.pin_hash):
        return None
    return user


async def change_own_pin(db: AsyncSession, user: User, current_pin: str, new_pin: str) -> None:
    if not verify_pin(current_pin, user.pin_hash):
        raise ValueError("Nykyinen PIN-koodi on väärin")
    if not new_pin or len(new_pin) < 4:
        raise ValueError("Uuden PIN-koodin on oltava vähintään 4 merkkiä")

    user.pin_hash = hash_pin(new_pin)
    await log_system_change(db, user, "PIN-koodi vaihdettu", {"entity": "user", "action": "pin_change"})
    await db.commit()
