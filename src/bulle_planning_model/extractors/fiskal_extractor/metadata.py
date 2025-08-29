from pydantic import BaseModel, Field
from datetime import datetime
from typing import List


class ExtractMetadata(BaseModel):
    """Metadata about the extraction process."""
    source_file: str = Field(..., description="Original filename")
    processed_at: datetime = Field(default_factory=datetime.now)
    total_transactions: int = Field(..., description="Number of transactions found")
    errors: List[str] = Field(default_factory=list, description="Processing errors")