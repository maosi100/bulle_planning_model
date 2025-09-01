from pydantic import BaseModel, Field
from datetime import datetime
from typing import List


class MengenlisteMetadata(BaseModel):
    """Metadata about the Mengenliste extraction process."""
    source_file: str = Field(..., description="Original PDF filename")
    processed_at: datetime = Field(default_factory=datetime.now)
    errors: List[str] = Field(default_factory=list, description="Processing errors")