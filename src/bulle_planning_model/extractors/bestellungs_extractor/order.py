from pydantic import BaseModel
from typing import List
from decimal import Decimal
from datetime import date

from extractors.bestellungs_extractor.line_item import LineItem


class Order(BaseModel):
    id: str
    pickup_date: date
    sales: List[LineItem]
    sum: Decimal

