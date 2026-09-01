"""Domain models for Allen + Clarke Opportunity Radar."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


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
    jurisdiction: str  # NZ, AU, ALL
    tier: str  # Commonwealth, Ministry, Crown Entity, State/Territory, Local
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
    jurisdiction: str  # NZ, AU
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
    jurisdiction: str
    title: str
    url: str
    published_date: str
    summary: str
    raw_content: str
    ingested_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "raw"  # raw, processed, filtered_noise, error


class OpportunityRecord(BaseModel):
    id: str
    scan_id: Optional[str] = None
    title: str
    jurisdiction: str
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
    status: str = "identified"  # identified, pitched, won, archived
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class IngestionResult(BaseModel):
    total_fetched: int = 0
    new_items: int = 0
    duplicates_skipped: int = 0
    errors: List[str] = Field(default_factory=list)
