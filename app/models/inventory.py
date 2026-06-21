import enum
from decimal import Decimal

from sqlalchemy import Boolean, Enum, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InventoryUnit(str, enum.Enum):
    GRAMS = "g"
    MILLILITERS = "ml"
    PIECES = "pcs"


class InventoryItem(Base):
    """A raw stock-keeping unit (ingredient or supply), e.g. coffee grounds in grams.

    quantity_in_stock is the theoretical/calculated level, kept up to date by
    sales deductions, supply restocks, and admin corrections. It is always an
    estimate between physical stocktakes, which are themselves logged as
    INVENTORY_CORRECTION audit entries representing absolute truth.
    """

    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    # values_callable: send the enum *value* ("g"/"ml"/"pcs") to Postgres, not
    # the member name ("GRAMS"/...) which SQLAlchemy uses by default and which
    # does not match the values the inventory_unit DB enum was created with.
    unit: Mapped[InventoryUnit] = mapped_column(
        Enum(InventoryUnit, name="inventory_unit", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
    )
    quantity_in_stock: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, default=Decimal("0"))
    # NULL means "no low-stock alerting configured" for this item.
    low_stock_threshold: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    # Tracks whether we've already alerted for the current below-threshold
    # dip, so a Signal message isn't sent on every single purchase while
    # stock stays low — only once when it first crosses the threshold, reset
    # once stock is replenished back above it.
    low_stock_notified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    extra_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
