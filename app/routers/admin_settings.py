from decimal import Decimal, InvalidOperation
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings as app_config
from app.database import get_db_session
from app.dependencies import require_admin_user
from app.models.user import User
from app.services.admin_service import charge_monthly_fee_to_all_active_users, get_app_settings, update_app_settings

router = APIRouter(prefix="/api/admin/settings", tags=["admin-settings"])


class SettingsUpdateRequest(BaseModel):
    monthly_fee_amount: str
    monthly_fee_active: bool
    signal_sender_number: str | None = None
    signal_group_id: str | None = None


@router.get("")
async def get_settings(_: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db_session)):
    settings = await get_app_settings(db)
    return {
        "monthly_fee_amount": str(settings.monthly_fee_amount),
        "monthly_fee_active": settings.monthly_fee_active,
        "signal_sender_number": settings.signal_sender_number,
        "signal_group_id": settings.signal_group_id,
    }


@router.put("")
async def put_settings(
    payload: SettingsUpdateRequest,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        amount = Decimal(payload.monthly_fee_amount)
    except InvalidOperation as exc:
        raise HTTPException(status_code=400, detail="Virheellinen summa") from exc

    settings = await update_app_settings(
        db, admin_user, amount, payload.monthly_fee_active, payload.signal_sender_number, payload.signal_group_id
    )
    return {
        "monthly_fee_amount": str(settings.monthly_fee_amount),
        "monthly_fee_active": settings.monthly_fee_active,
        "signal_sender_number": settings.signal_sender_number,
        "signal_group_id": settings.signal_group_id,
    }


@router.post("/charge-monthly-fee")
async def post_charge_monthly_fee(
    admin_user: User = Depends(require_admin_user), db: AsyncSession = Depends(get_db_session)
):
    try:
        charged_count = await charge_monthly_fee_to_all_active_users(db, admin_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"charged_count": charged_count}


@router.get("/signal-qrcode")
async def get_signal_qrcode(
    device_name: str = "Kahvikassa-Bot", _: User = Depends(require_admin_user)
):
    """Proxies signal-cli-rest-api's linking QR code so an admin can scan it
    straight from the browser instead of fetching it over SSH. The token
    inside the code expires within roughly a minute — generate it right
    before scanning, not in advance."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{app_config.signal_rest_api_url}/v1/qrcodelink", params={"device_name": device_name}
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Signal-palveluun ei saatu yhteyttä") from exc

    return Response(content=response.content, media_type="image/png")


@router.get("/signal-accounts")
async def get_signal_accounts(_: User = Depends(require_admin_user)):
    """Lists phone numbers currently linked to the signal-cli instance, so an
    admin can find the right value for 'Lähettäjän numero' after linking."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{app_config.signal_rest_api_url}/v1/accounts")
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Signal-palveluun ei saatu yhteyttä") from exc

    return response.json()


@router.get("/signal-groups")
async def get_signal_groups(number: str, _: User = Depends(require_admin_user)):
    """Lists the Signal groups a linked account belongs to (name + id), so an
    admin can find the right value for 'Ryhmän ID' without raw API calls."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{app_config.signal_rest_api_url}/v1/groups/{quote(number, safe='')}")
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Signal-palveluun ei saatu yhteyttä") from exc

    return [{"name": g["name"], "id": g["id"]} for g in response.json()]
