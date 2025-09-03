from pydantic import BaseModel


class ExtractMetadata(BaseModel):
    source_file: str
    total_orders: int