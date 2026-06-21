from datetime import date

from pydantic import BaseModel

from app.models.audit import AuditEventType


class AuditLogFilter(BaseModel):
    user_id: int | None = None
    event_type: AuditEventType | None = None
    sales_product_id: int | None = None
    inventory_item_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None


class AuditLogEntryOut(BaseModel):
    id: int
    occurred_at: str
    user_name: str | None
    event_type: str
    sales_product_name: str | None
    inventory_item_name: str | None
    quantity: str | None
    amount: str | None
    description: str | None


class InventoryCorrectionRequest(BaseModel):
    inventory_item_id: int
    counted_quantity: str
    description: str


class WastageRequest(BaseModel):
    inventory_item_id: int
    quantity: str
    description: str
