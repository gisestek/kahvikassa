import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AuditEventType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    SUPPLY_RESTOCK = "SUPPLY_RESTOCK"
    INVENTORY_CORRECTION = "INVENTORY_CORRECTION"
    WASTAGE = "WASTAGE"
    ADMIN_ADJUSTMENT = "ADMIN_ADJUSTMENT"
    MONTHLY_FEE = "MONTHLY_FEE"
    # Catch-all for admin/self-service CRUD that isn't a financial or stock
    # event of its own (user/category/product/inventory-item management,
    # threshold and settings changes, PIN changes). Kept as one generic type
    # with a descriptive `description` rather than one enum value per entity,
    # so adding a new admin feature never requires another enum migration.
    SYSTEM_CHANGE = "SYSTEM_CHANGE"


class AuditLogEntry(Base):
    """The single immutable transaction ledger (Tapahtumaloki).

    Entries are append-only by design: nothing here is ever updated or deleted
    by application code. Corrections are made with new offsetting entries, so
    the table is always a complete, replayable history of every balance and
    stock change in the system.
    """

    __tablename__ = "audit_log_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    event_type: Mapped[AuditEventType] = mapped_column(Enum(AuditEventType, name="audit_event_type"), index=True)
    sales_product_id: Mapped[int | None] = mapped_column(ForeignKey("sales_products.id"), nullable=True, index=True)
    inventory_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("inventory_items.id"), nullable=True, index=True
    )
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    user: Mapped["User"] = relationship()
    sales_product: Mapped["SalesProduct"] = relationship()
    inventory_item: Mapped["InventoryItem"] = relationship()
