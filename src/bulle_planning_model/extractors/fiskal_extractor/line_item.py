from pydantic import BaseModel, Field
from decimal import Decimal


class LineItem(BaseModel):
    """Represents a single product sold in a transaction."""
    article_number: int = Field(..., description="Article ID from parentheses")
    article_name: str = Field(..., description="Product name")
    quantity: Decimal = Field(..., description="Amount sold (can be fractional)")
    category: str = Field(..., description="Warengruppe name")
    category_number: int = Field(..., description="Warengruppe ID")
    price: Decimal = Field(..., description="Total price for this line item")