"""Prioritisation & BD Action Agent (Agent 4).

Applies an objective 0–100 scoring model (Strategic Fit 35%, Urgency 35%, Budget Likelihood 30%),
strictly enforces the max-10 opportunity cap, and formulates actionable outreach plans.
"""

import uuid
from typing import Any, Dict, List, Optional
from radar.models import ScanRecord
from radar.pipeline.models import (
    BDOpportunity,
    ImpactAnalysis,
    LLMScoringOutput,
    OpportunityScore,
    ServiceMatch,
)

# Persona mapping covering all 8 Allen + Clarke practice lines
PERSONA_MAP: Dict[str, str] = {
    # Policy + Regulation
    "policy-regulation": "Deputy Secretary / Executive Director, Policy & Regulatory Reform",
    "policy_regulatory": "Deputy Secretary / Executive Director, Policy & Regulatory Reform",
    # Evaluation + Review
    "evaluation-review": "General Manager / Director, Evidence, Insights & Evaluation",
    "evaluation_research": "General Manager / Director, Evidence, Insights & Evaluation",
    # Strategy + Planning
    "strategy-planning": "Deputy Chief Executive / Director, Strategy & Enterprise Architecture",
    # Business Change & Governance
    "transformation-governance": "Deputy Chief Executive / Director, Transformation & Governance",
    "business_change_governance": "Deputy Chief Executive / Director, Transformation & Governance",
    # Kaupapa Māori & Pacific Policy
    "kaupapa-maori-pacific": "Chief Advisor / Director, Māori Strategy & Pacific Partnerships",
    "kaupapa_maori_pacific": "Chief Advisor / Director, Māori Strategy & Pacific Partnerships",
    # Performance + Optimisation
    "performance-optimisation": "Chief Operating Officer / Director, Service Delivery & Performance",
    # Risk Management
    "risk-management": "Chief Risk Officer / General Counsel / Director, Regulatory Assurance",
    # Secretariat + Service Delivery
    "secretariat-service-delivery": "Head of Secretariat / General Manager, Advisory Panels & Inquiries",
}

# Service Line canonical display name mapping
SERVICE_LINE_NAMES: Dict[str, str] = {
    "policy-regulation": "Policy + Regulation",
    "policy_regulatory": "Policy & Regulatory Design",
    "evaluation-review": "Evaluation + Review",
    "evaluation_research": "Evaluation & Applied Research",
    "strategy-planning": "Strategy + Planning",
    "transformation-governance": "Business Change & Public Sector Governance",
    "business_change_governance": "Business Change & Public Sector Governance",
    "kaupapa-maori-pacific": "Kaupapa Māori & Pacific Policy",
    "kaupapa_maori_pacific": "Kaupapa Māori & Pacific Policy",
    "performance-optimisation": "Performance + Optimisation",
    "risk-management": "Risk Management",
    "secretariat-service-delivery": "Secretariat + Service Delivery",
}


class PrioritisationAgent:
    """Agent 4: Prioritisation & BD Action Agent."""

    def __init__(self, llm: Optional[Any] = None):
        """Initializes the prioritisation agent with optional LangChain LLM."""
        self.llm = llm

    def score_opportunity(
        self,
        scan: ScanRecord,
        impact: ImpactAnalysis,
        match: ServiceMatch,
    ) -> BDOpportunity:
        """Scores an opportunity against the 0-100 rubric and formats the BD action plan."""
        if self.llm is not None:
            try:
                return self._score_with_llm(scan, impact, match)
            except Exception:
                return self._score_with_heuristics(scan, impact, match)

        return self._score_with_heuristics(scan, impact, match)

    def rank_and_cap(
        self,
        opportunities: List[BDOpportunity],
        max_items: int = 10,
    ) -> List[BDOpportunity]:
        """Ranks opportunities by total score descending and enforces a strict cap of max_items (default 10)."""
        sorted_opps = sorted(
            opportunities,
            key=lambda opp: opp.score.total_score,
            reverse=True,
        )
        return sorted_opps[:max_items]

    def _score_with_heuristics(
        self,
        scan: ScanRecord,
        impact: ImpactAnalysis,
        match: ServiceMatch,
    ) -> BDOpportunity:
        """Deterministic rubric scoring across Strategic Fit (0-35), Urgency (0-35), Budget (0-30)."""
        # 1. Strategic Fit (0-35)
        fit_score = 20  # Base score for matching a core practice line
        fit_rationale_parts = ["Direct alignment with Allen + Clarke core service line."]

        if match.target_client_id:
            fit_score += 7
            fit_rationale_parts.append("Target entity is an active/historical client relationship.")
        if match.secondary_service_line_ids:
            fit_score += 4
            fit_rationale_parts.append("Multi-disciplinary cross-service potential.")
        if any("Māori" in s or "Pacific" in s for s in impact.affected_sectors):
            fit_score += 4
            fit_rationale_parts.append("High strategic synergy with Kaupapa Māori & Pacific advisory capability.")

        strategic_fit = min(35, max(0, fit_score))

        # 2. Urgency (0-35)
        urgency_score = 15  # Base urgency
        urgency_rationale_parts = []

        if any("2026" in d or "2027" in d or "month" in d.lower() for d in impact.compliance_deadlines):
            urgency_score += 10
            urgency_rationale_parts.append(f"Near-term statutory/regulatory milestone ({impact.compliance_deadlines[0]}).")
        if len(impact.operational_obligations) >= 2:
            urgency_score += 6
            urgency_rationale_parts.append("Multiple complex operational deliverables required.")
        if "reform" in scan.title.lower() or "bill" in scan.title.lower():
            urgency_score += 4
            urgency_rationale_parts.append("Active legislative momentum drives immediate commissioning need.")

        urgency = min(35, max(0, urgency_score))

        # 3. Budget Likelihood (0-30)
        budget_score = 15  # Base budget probability
        budget_rationale_parts = []

        if match.target_client_id:
            budget_score += 6
            budget_rationale_parts.append("Established departmental procurement route.")
        if any("statutory" in ob.lower() or "evaluation" in ob.lower() for ob in impact.operational_obligations):
            budget_score += 5
            budget_rationale_parts.append("Mandated statutory activity with allocated operational budget.")
        if scan.jurisdiction in ("NZ", "AU"):
            budget_score += 4
            budget_rationale_parts.append("High public sector consulting spend propensity in this domain.")

        budget = min(30, max(0, budget_score))

        score = OpportunityScore(
            strategic_fit_score=strategic_fit,
            urgency_score=urgency,
            budget_score=budget,
            rationale={
                "strategic_fit": " ".join(fit_rationale_parts),
                "urgency": " ".join(urgency_rationale_parts) if urgency_rationale_parts else "Standard policy timeline.",
                "budget": " ".join(budget_rationale_parts) if budget_rationale_parts else "Standard public sector funding envelope.",
            },
        )

        # 4. Determine Target Contact Persona
        target_persona = PERSONA_MAP.get(
            match.primary_service_line_id,
            "Deputy Secretary / General Manager, Policy & Strategy",
        )

        # 5. Determine Service Line Name
        service_line_name = SERVICE_LINE_NAMES.get(
            match.primary_service_line_id,
            "Policy & Advisory Services",
        )

        # 6. Formulate Action Plan: Conversation Starter
        deadline_ref = f" ahead of the {impact.compliance_deadlines[0]} milestone" if impact.compliance_deadlines else ""
        conversation_starter = (
            f"Kia ora / Dear {target_persona.split('/')[0].strip()}, following the recent announcement regarding '{scan.title}', "
            f"we understand {match.target_client_name} is navigating key operational requirements{deadline_ref}. "
            f"Allen + Clarke has extensive experience assisting public sector leaders with {match.service_offering_summary.lower()} "
            f"— would you have 15 minutes next week for an exploratory discussion on how we can support your delivery team?"
        )

        # 7. Formulate Key Pitch Angles
        key_pitch_angles = [
            f"Proven track record in {service_line_name} across {scan.jurisdiction} public sector agencies.",
            f"Immediate capacity to absorb workload surge without compromising regulatory quality.",
            f"Direct capability to bridge policy intent with practical operational implementation.",
        ]

        opp_id = f"opp-{uuid.uuid4().hex[:8]}"

        return BDOpportunity(
            id=opp_id,
            scan_id=scan.id,
            title=scan.title,
            jurisdiction=scan.jurisdiction,
            published_date=scan.published_date,
            url=scan.url,
            change_summary=scan.summary or scan.title,
            verified_facts=impact.verified_facts,
            strategic_interpretation=impact.strategic_interpretation,
            affected_sectors=impact.affected_sectors,
            target_client_id=match.target_client_id,
            target_client_name=match.target_client_name,
            operational_obligations=impact.operational_obligations,
            compliance_deadlines=impact.compliance_deadlines,
            primary_service_line_id=match.primary_service_line_id,
            service_line_name=service_line_name,
            service_offering_summary=match.service_offering_summary,
            target_contact_persona=target_persona,
            conversation_starter=conversation_starter,
            key_pitch_angles=key_pitch_angles,
            score=score,
            status="identified",
        )

    def _score_with_llm(
        self,
        scan: ScanRecord,
        impact: ImpactAnalysis,
        match: ServiceMatch,
    ) -> BDOpportunity:
        """LangChain LLM-based scoring and action formulation."""
        from radar.pipeline.prompts import SCORING_SYSTEM_PROMPT
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", SCORING_SYSTEM_PROMPT),
            ("human", "Scan: {title} ({jurisdiction})\nSummary: {summary}\nFacts: {facts}\nInterpretation: {interpretation}\nSectors: {sectors}\nClient: {client}\nService Line: {sl}\nOffering: {offering}"),
        ])

        structured_llm = self.llm.with_structured_output(LLMScoringOutput)
        chain = prompt | structured_llm
        llm_out: LLMScoringOutput = chain.invoke({
            "title": scan.title,
            "jurisdiction": scan.jurisdiction,
            "summary": scan.summary,
            "facts": impact.verified_facts,
            "interpretation": impact.strategic_interpretation,
            "sectors": ", ".join(impact.affected_sectors),
            "client": match.target_client_name,
            "sl": match.primary_service_line_id,
            "offering": match.service_offering_summary,
        })

        # Clamp scores safely within allowable rubric boundaries
        fit = max(0, min(35, llm_out.strategic_fit_score))
        urgency = max(0, min(35, llm_out.urgency_score))
        budget = max(0, min(30, llm_out.budget_score))

        score = OpportunityScore(
            strategic_fit_score=fit,
            urgency_score=urgency,
            budget_score=budget,
            rationale=llm_out.scoring_rationale,
        )

        service_line_name = SERVICE_LINE_NAMES.get(
            match.primary_service_line_id,
            "Policy & Advisory Services",
        )

        opp_id = f"opp-{uuid.uuid4().hex[:8]}"

        return BDOpportunity(
            id=opp_id,
            scan_id=scan.id,
            title=scan.title,
            jurisdiction=scan.jurisdiction,
            published_date=scan.published_date,
            url=scan.url,
            change_summary=scan.summary or scan.title,
            verified_facts=impact.verified_facts,
            strategic_interpretation=impact.strategic_interpretation,
            affected_sectors=impact.affected_sectors,
            target_client_id=match.target_client_id,
            target_client_name=match.target_client_name,
            operational_obligations=impact.operational_obligations,
            compliance_deadlines=impact.compliance_deadlines,
            primary_service_line_id=match.primary_service_line_id,
            service_line_name=service_line_name,
            service_offering_summary=match.service_offering_summary,
            target_contact_persona=llm_out.target_contact_persona,
            conversation_starter=llm_out.conversation_starter,
            key_pitch_angles=llm_out.key_pitch_angles,
            score=score,
            status="identified",
        )
