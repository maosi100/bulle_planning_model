from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional


class MasterArticleData(BaseModel):
    """Represents consolidated data for a single master article."""
    master_name: str = Field(..., description="Master article name")
    total_sales: Decimal = Field(..., description="Total sales amount from fiskal data")
    total_quantity: Decimal = Field(..., description="Total quantity sold from fiskal data")
    leftover: Optional[float] = Field(None, description="Leftover quantity from mengenlisten data")
    sold_out_time: Optional[str] = Field(None, description="Time when sold out from mengenlisten data")
