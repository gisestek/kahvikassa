from fastapi import APIRouter, Depends

from app.dependencies import require_admin_user
from app.models.user import User
from app.services.version_service import get_current_version, get_latest_remote_commit

router = APIRouter(prefix="/api/admin/version", tags=["admin-version"])


@router.get("")
async def get_version(_: User = Depends(require_admin_user)):
    current = get_current_version()
    latest = await get_latest_remote_commit()
    return {
        "current": current,
        "latest": latest,
        "update_available": latest is not None and latest != current,
    }
