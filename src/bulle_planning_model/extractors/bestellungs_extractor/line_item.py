from pydantic import BaseModel
from decimal import Decimal


class LineItem(BaseModel):
    article_name: str
    quantity: Decimal
    price: Decimal