from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AppSettings(Base):
    """Singleton row (id is always 1) holding system-wide configuration that
    doesn't belong to any other entity, such as the optional monthly fee and
    the Signal notification sender/group.

    signal_sender_number/signal_group_id, when set, override the .env-provided
    defaults (app.config.settings) without requiring a redeploy — e.g. when
    the club's admin/bot-account owner changes. NULL means "use the .env
    default", so an empty DB row never breaks an already-working setup.
    """

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    monthly_fee_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    monthly_fee_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    signal_sender_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    signal_group_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
