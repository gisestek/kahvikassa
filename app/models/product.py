from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProductCategory(Base):
    """One of the three fixed display groups: Perustuotteet, Naposteltavat, Muut."""

    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    sales_products: Mapped[list["SalesProduct"]] = relationship(back_populates="category")


class SalesProduct(Base):
    """An end-user purchasable item, e.g. 'Musta kahvi'. Distinct from InventoryItem:
    a sales product is consumed via its RecipeLine entries against inventory items."""

    __tablename__ = "sales_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("product_categories.id"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_on_sale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    extra_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    category: Mapped["ProductCategory"] = relationship(back_populates="sales_products")
    recipe_lines: Mapped[list["RecipeLine"]] = relationship(
        back_populates="sales_product", cascade="all, delete-orphan"
    )
