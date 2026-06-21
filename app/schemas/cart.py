from pydantic import BaseModel, Field


class CartLineItem(BaseModel):
    sales_product_id: int
    quantity: int = Field(gt=0, le=99)


class CheckoutRequest(BaseModel):
    items: list[CartLineItem] = Field(min_length=1)
