"""Domain models for Allen + Clarke Opportunity Radar."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

JurisdictionType = Literal["NZ", "AU", "ALL"]
ScanStatusType = Literal["raw", "processed", "filtered_noise", "error"]
OpportunityStatusType = Literal["identified", "pitched", "won", "archived"]
ClientTierType = Literal["Commonwealth", "Ministry", "Crown Entity", "State/Territory", "Local", "Other"]


class ServiceLine(BaseModel):
    id: str
    name: str
    description: str
    keywords: List[str] = Field(default_factory=list)
    case_studies: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Client(BaseModel):
    id: str
    name: str
    jurisdiction: JurisdictionType  # NZ, AU, ALL
    tier: ClientTierType
    sector: str
    key_divisions: List[str] = Field(default_factory=list)
    past_engagements: List[str] = Field(default_factory=list)
    relationship_notes: Optional[str] = ""
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FeedItem(BaseModel):
    id: str
    source_id: str
    source_name: str
    jurisdiction: Literal["NZ", "AU"]
    title: str
    url: str
    published_date: str
    summary: str
    raw_content: str
    content_hash: str


class ScanRecord(BaseModel):
    id: str
    content_hash: str
    source_id: str
    source_name: str
    jurisdiction: Literal["NZ", "AU"]
    title: str
    url: str
    published_date: str
    summary: str
    raw_content: str
    ingested_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: ScanStatusType = "raw"


class OpportunityRecord(BaseModel):
    id: str
    scan_id: Optional[str] = None
    title: str
    jurisdiction: JurisdictionType
    target_client_id: Optional[str] = None
    primary_service_line_id: Optional[str] = None
    verified_facts: str = ""
    strategic_interpretation: str = ""
    strategic_fit_score: int = Field(ge=0, le=35, default=0)
    urgency_score: int = Field(ge=0, le=35, default=0)
    budget_score: int = Field(ge=0, le=30, default=0)
    total_score: int = Field(ge=0, le=100, default=0)
    conversation_starter: str = ""
    target_contact_persona: str = ""
    status: OpportunityStatusType = "identified"
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class IngestionResult(BaseModel):
    total_fetched: int = 0
    new_items: int = 0
    duplicates_skipped: int = 0
    errors: List[str] = Field(default_factory=list)
