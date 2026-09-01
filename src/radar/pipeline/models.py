"""Pydantic schemas and state models for the 4-Agent LangChain Opportunity Reasoning Pipeline."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, computed_field
from radar.models import JurisdictionType, OpportunityRecord, ScanRecord


class FilterResult(BaseModel):
    """Result of Ingestion & De-duplication noise filtering (Agent 1)."""

    is_actionable: bool
    rejection_reason: Optional[str] = None
    novelty_score: float = Field(ge=0.0, le=1.0, default=1.0)
    actionable_summary: Optional[str] = None


class ImpactAnalysis(BaseModel):
    """Result of Impact & Sector Analysis (Agent 2), isolating Facts from Interpretations."""

    verified_facts: str = Field(description="Strict verified facts with dates, bill names, and statutory mandates.")
    strategic_interpretation: str = Field(description="Consulting interpretation of capacity constraints and pain points.")
    affected_sectors: List[str] = Field(default_factory=list)
    affected_agencies: List[str] = Field(default_factory=list)
    operational_obligations: List[str] = Field(default_factory=list)
    compliance_deadlines: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)


class ServiceMatch(BaseModel):
    """Result of A+C Service Line & Client Matching (Agent 3)."""

    primary_service_line_id: str
    secondary_service_line_ids: List[str] = Field(default_factory=list)
    target_client_id: Optional[str] = None
    target_client_name: str
    service_offering_summary: str
    fit_rationale: str


class OpportunityScore(BaseModel):
    """Score breakdown adhering to the 0-100 Allen + Clarke BD Opportunity scoring model."""

    strategic_fit_score: int = Field(ge=0, le=35, description="Strategic fit with A+C capability (0-35)")
    urgency_score: int = Field(ge=0, le=35, description="Urgency & statutory deadlines (0-35)")
    budget_score: int = Field(ge=0, le=30, description="Budget likelihood & commissioning probability (0-30)")
    rationale: Dict[str, str] = Field(default_factory=dict)

    @computed_field
    @property
    def total_score(self) -> int:
        return self.strategic_fit_score + self.urgency_score + self.budget_score


class LLMScoringOutput(BaseModel):
    """Structured LLM output for scoring and action plan generation."""

    strategic_fit_score: int = Field(ge=0, le=35)
    urgency_score: int = Field(ge=0, le=35)
    budget_score: int = Field(ge=0, le=30)
    scoring_rationale: Dict[str, str] = Field(default_factory=dict)
    target_contact_persona: str
    conversation_starter: str
    key_pitch_angles: List[str] = Field(default_factory=list)


class BDOpportunity(BaseModel):
    """Comprehensive opportunity structure enforcing all 6 mandatory BD questions."""

    id: str
    scan_id: Optional[str] = None
    title: str
    jurisdiction: JurisdictionType
    published_date: str
    url: str

    # Q1: What has changed or is changing?
    change_summary: str

    # Q2: Verified Facts vs Strategic Interpretation
    verified_facts: str
    strategic_interpretation: str

    # Q3: Which public sector organisations or sectors are directly affected?
    affected_sectors: List[str] = Field(default_factory=list)
    target_client_id: Optional[str] = None
    target_client_name: str

    # Q4: What will affected organisations need to do to operationalize/comply?
    operational_obligations: List[str] = Field(default_factory=list)
    compliance_deadlines: List[str] = Field(default_factory=list)

    # Q5: Which Allen + Clarke service line fits the client need?
    primary_service_line_id: str
    service_line_name: str
    service_offering_summary: str

    # Q6: Who to approach and with what? (Action Plan)
    target_contact_persona: str
    conversation_starter: str
    key_pitch_angles: List[str] = Field(default_factory=list)

    # Scoring & Status
    score: OpportunityScore
    status: Literal["identified", "pitched", "won", "archived"] = "identified"
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def six_questions(self) -> Dict[str, Any]:
        """Returns structured dictionary answering the 6 mandatory BD questions."""
        return {
            "q1_what_changed": self.change_summary,
            "q2_facts_vs_interpretation": {
                "verified_facts": self.verified_facts,
                "strategic_interpretation": self.strategic_interpretation,
            },
            "q3_affected_organisations": {
                "affected_sectors": self.affected_sectors,
                "target_client_id": self.target_client_id,
                "target_client_name": self.target_client_name,
            },
            "q4_operational_obligations": {
                "operational_obligations": self.operational_obligations,
                "compliance_deadlines": self.compliance_deadlines,
            },
            "q5_ac_service_line": {
                "primary_service_line_id": self.primary_service_line_id,
                "service_line_name": self.service_line_name,
                "service_offering_summary": self.service_offering_summary,
            },
            "q6_who_to_approach": {
                "target_contact_persona": self.target_contact_persona,
                "conversation_starter": self.conversation_starter,
                "key_pitch_angles": self.key_pitch_angles,
            },
        }

    def to_db_record(self) -> OpportunityRecord:
        """Converts BDOpportunity to SQLite OpportunityRecord."""
        return OpportunityRecord(
            id=self.id,
            scan_id=self.scan_id,
            title=self.title,
            jurisdiction=self.jurisdiction,
            target_client_id=self.target_client_id,
            primary_service_line_id=self.primary_service_line_id,
            verified_facts=self.verified_facts,
            strategic_interpretation=self.strategic_interpretation,
            strategic_fit_score=self.score.strategic_fit_score,
            urgency_score=self.score.urgency_score,
            budget_score=self.score.budget_score,
            total_score=self.score.total_score,
            conversation_starter=self.conversation_starter,
            target_contact_persona=self.target_contact_persona,
            status=self.status,
            created_at=self.created_at,
        )


class PipelineResult(BaseModel):
    """Aggregate result from executing the multi-agent reasoning pipeline."""

    processed_count: int = 0
    filtered_noise_count: int = 0
    opportunities: List[BDOpportunity] = Field(default_factory=list)
    saved_count: int = 0
