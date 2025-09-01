from pydantic import BaseModel, Field
from datetime import date
from typing import List

from extractors.mengenlisten_extractor.mengenliste_entry import MengenlisteEntry


class Mengenliste(BaseModel):
    """Represents a complete Mengenliste shift report."""

    report_date: date = Field(..., description="Date of the shift report")
    production_day: str = Field(..., description="Production day (Backtag)")
    sales_day: str = Field(..., description="Sales day (Für Tag)")
    articles: List[MengenlisteEntry] = Field(
        ..., description="List of articles with quantities"
    )

