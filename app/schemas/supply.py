from pydantic import BaseModel, Field, model_validator

from app.models.inventory import InventoryUnit


class NewInventoryItemInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    unit: InventoryUnit


class SupplyIngestionRequest(BaseModel):
    """A 'Toin tavaraa' submission. Either restocks an existing inventory item
    (inventory_item_id set) or defines a brand new one (new_item set) — never both."""

    inventory_item_id: int | None = None
    new_item: NewInventoryItemInput | None = None
    quantity: str
    total_cost: str

    @model_validator(mode="after")
    def exactly_one_target(self) -> "SupplyIngestionRequest":
        if bool(self.inventory_item_id) == bool(self.new_item):
            raise ValueError("Valitse olemassa oleva tuote TAI luo uusi, ei molempia.")
        return self
