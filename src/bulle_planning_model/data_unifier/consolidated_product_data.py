from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Dict

from data_unifier.master_article_data import MasterArticleData


class ConsolidatedProductData(BaseModel):
    """Represents consolidated product data for a single day."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    total_revenue: Decimal = Field(..., description="Total revenue for the day")
    master_articles: Dict[str, MasterArticleData] = Field(
        ..., description="Dictionary of master articles with their consolidated data"
    )