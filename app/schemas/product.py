from pydantic import BaseModel, Field

from app.models.inventory import InventoryUnit


class KioskProduct(BaseModel):
    id: int
    name: str
    price: str


class KioskCategoryGroup(BaseModel):
    category_name: str
    products: list[KioskProduct]


class CategoryUpsert(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    sort_order: int = 0


class RecipeLineInput(BaseModel):
    inventory_item_id: int
    quantity_required: str


class SalesProductUpsert(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category_id: int
    price: str
    is_active: bool = True
    is_on_sale: bool = True
    recipe_lines: list[RecipeLineInput] = Field(default_factory=list)


class InventoryItemUpsert(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    unit: InventoryUnit
