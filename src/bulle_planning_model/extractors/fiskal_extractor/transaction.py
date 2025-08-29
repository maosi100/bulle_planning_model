from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import List

from extractors.fiskal_extractor.line_item import LineItem


class Transaction(BaseModel):
    """Represents a complete sale transaction."""

    uuid: str = Field(..., description="Unique transaction identifier")
    date: datetime = Field(..., description="Transaction timestamp")
    bill_number: int = Field(..., description="Receipt sequence number")
    items: List[LineItem] = Field(..., description="Items sold in this transaction")
    total_gross: Decimal = Field(..., description="Total amount including tax")

