import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.settings import AppSettings

logger = logging.getLogger(__name__)

# signal-cli-rest-api addresses a group as "group.<base64 group id>" in the
# recipients list — see https://github.com/bbernhard/signal-cli-rest-api.
_GROUP_RECIPIENT_PREFIX = "group."

# id of the singleton app_settings row, seeded by migration 0003.
_APP_SETTINGS_ROW_ID = 1


async def _resolve_signal_config(db: AsyncSession) -> tuple[str, str]:
    """DB-stored sender/group (editable in Asetukset) take priority over the
    .env defaults, so the admin can hand off the bot to a new linked Signal
    account without a redeploy. Empty DB fields fall back to .env untouched."""
    db_settings = await db.get(AppSettings, _APP_SETTINGS_ROW_ID)
    sender_number = (db_settings.signal_sender_number if db_settings else None) or settings.signal_sender_number
    group_id = (db_settings.signal_group_id if db_settings else None) or settings.signal_group_id
    return sender_number, group_id


async def send_signal_message(db: AsyncSession, text: str) -> None:
    """Best-effort Signal notification. Silently does nothing if Signal isn't
    configured (no sender number / group id set), and never raises — a failed
    notification must not break a purchase, restock, or fee charge."""
    sender_number, group_id = await _resolve_signal_config(db)
    if not sender_number or not group_id:
        logger.info("Signal not configured, skipping notification: %s", text)
        return

    recipient = group_id
    if not recipient.startswith(_GROUP_RECIPIENT_PREFIX):
        recipient = _GROUP_RECIPIENT_PREFIX + recipient

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.signal_rest_api_url}/v2/send",
                json={"message": text, "number": sender_number, "recipients": [recipient]},
            )
            response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("Failed to send Signal notification")


def format_low_stock_message(item_name: str, unit: str, quantity_in_stock) -> str:
    return f"⚠️ Kahvikassa: {item_name} on vähissä ({quantity_in_stock} {unit} jäljellä)."


def format_monthly_fee_message(charged_count: int, amount) -> str:
    return f"💰 Kahvikassa: kuukausimaksu ({amount} €) veloitettu {charged_count} käyttäjältä."


def format_supply_brought_message(bringer_name: str, item_name: str, quantity, unit: str, total_cost) -> str:
    return (
        f"📦 Kahvikassa: {bringer_name} toi tavaraa — {item_name} "
        f"({quantity} {unit}), hinta {total_cost} €."
    )
