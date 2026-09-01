"""Data structures for report generation and metadata."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field


class ReportMetadata(BaseModel):
    """Metadata for opportunity radar reports and digests."""

    period: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("Fortnight Ending %d %B %Y"))
    jurisdiction: str = "ALL"
    scanned_count: int = 0
    new_items_count: int = 0
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    @classmethod
    def from_dict(cls, data: Optional[Union[Dict[str, Any], "ReportMetadata"]]) -> "ReportMetadata":
        if isinstance(data, cls):
            return data
        if not data:
            return cls()
        return cls(**data)

    @property
    def jurisdiction_label(self) -> str:
        if self.jurisdiction == "NZ":
            return "New Zealand"
        elif self.jurisdiction == "AU":
            return "Australia"
        return "New Zealand & Australia"
