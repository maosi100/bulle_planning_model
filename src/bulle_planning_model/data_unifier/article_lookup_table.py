from pydantic import BaseModel, Field
from typing import Dict
from pathlib import Path
import json


class ArticleLookupTable(BaseModel):
    """Lookup table for mapping article variants to master articles."""

    variant_to_master: Dict[str, str] = Field(
        ..., description="Mapping from variant names to master article names"
    )

    @classmethod
    def from_file(
        cls, file_path: Path = Path("../../data/master/lookup_table.json")
    ) -> "ArticleLookupTable":
        """Load lookup table from JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(variant_to_master=data["variant_to_master_lookup"])

