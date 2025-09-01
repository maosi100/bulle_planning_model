from pydantic import BaseModel, Field
from typing import Optional, Union


class MengenlisteEntry(BaseModel):
    """Represents a single article entry in a Mengenliste shift report."""
    article_name: str = Field(..., description="Product name")
    stock: Optional[int] = Field(None, description="Current stock quantity (Aktuelle Menge)")
    leftover: Optional[float] = Field(None, description="Leftover quantity (Retoure Anzahl)")
    sold_out: Optional[str] = Field(None, description="Time when sold out (Ausverkauft um)")
