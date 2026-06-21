from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RecipeLine(Base):
    """One ingredient requirement of a sales product's recipe.

    Quantities support decimals (e.g. 0.12 pcs of a filter) so they are stored
    as NUMERIC rather than integers.
    """

    __tablename__ = "recipe_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    sales_product_id: Mapped[int] = mapped_column(ForeignKey("sales_products.id"), nullable=False)
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"), nullable=False)
    quantity_required: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)

    sales_product: Mapped["SalesProduct"] = relationship(back_populates="recipe_lines")
    inventory_item: Mapped["InventoryItem"] = relationship()
