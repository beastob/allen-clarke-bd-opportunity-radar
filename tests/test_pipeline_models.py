import pytest
from pydantic import ValidationError
from radar.models import ScanRecord, OpportunityRecord
from radar.pipeline.models import (
    FilterResult,
    ImpactAnalysis,
    ServiceMatch,
    OpportunityScore,
    BDOpportunity,
    PipelineResult,
)


def test_filter_result_validation():
    # Valid actionable result
    res = FilterResult(
        is_actionable=True,
        novelty_score=0.9,
        actionable_summary="Significant regulatory review announced by Ministry of Health.",
    )
    assert res.is_actionable is True
    assert res.rejection_reason is None

    # Valid rejected result
    rej = FilterResult(
        is_actionable=False,
        rejection_reason="Ceremonial announcement without policy or regulatory change.",
        novelty_score=0.1,
    )
    assert rej.is_actionable is False
    assert "Ceremonial" in rej.rejection_reason


def test_impact_analysis_fact_vs_interpretation():
    impact = ImpactAnalysis(
        verified_facts="Cabinet approved the draft Natural and Built Environment Bill on 15 March 2026.",
        strategic_interpretation="Ministry for the Environment lacks capacity to draft subordinate regulations before Q3.",
        affected_sectors=["Environment", "Local Government"],
        affected_agencies=["Ministry for the Environment", "Regional Councils"],
        operational_obligations=["Draft regional spatial strategy guidelines", "Consult with iwi"],
        compliance_deadlines=["1 October 2026"],
        citations=["Beehive Ministerial Release 2026/03/15", "Cabinet Minute CAB-26-MIN-0042"],
    )
    assert "Cabinet approved" in impact.verified_facts
    assert "lacks capacity" in impact.strategic_interpretation
    assert len(impact.affected_sectors) == 2
    assert len(impact.citations) == 2


def test_service_match_model():
    match = ServiceMatch(
        primary_service_line_id="policy_regulatory",
        secondary_service_line_ids=["kaupapa_maori_pacific"],
        target_client_id="mfe",
        target_client_name="Ministry for the Environment",
        service_offering_summary="Regulatory impact analysis and secondary legislation drafting support",
        fit_rationale="Allen + Clarke has extensive RMA reform and environmental policy experience.",
    )
    assert match.primary_service_line_id == "policy_regulatory"
    assert match.target_client_id == "mfe"


def test_opportunity_score_validation():
    # Valid scores within bounds (0-35, 0-35, 0-30 => 0-100)
    score = OpportunityScore(
        strategic_fit_score=30,
        urgency_score=28,
        budget_score=25,
    )
    assert score.total_score == 83

    # Invalid strategic fit (>35)
    with pytest.raises(ValidationError):
        OpportunityScore(strategic_fit_score=36, urgency_score=20, budget_score=20)

    # Invalid urgency (>35)
    with pytest.raises(ValidationError):
        OpportunityScore(strategic_fit_score=20, urgency_score=36, budget_score=20)

    # Invalid budget (>30)
    with pytest.raises(ValidationError):
        OpportunityScore(strategic_fit_score=20, urgency_score=20, budget_score=31)


def test_bd_opportunity_enforces_6_questions_and_conversion():
    opp = BDOpportunity(
        id="opp-123",
        scan_id="scan-456",
        title="NZ RMA Replacement Regulatory Support",
        jurisdiction="NZ",
        published_date="2026-03-15",
        url="https://beehive.govt.nz/release/rma-reform",
        # Q1: What changed?
        change_summary="Government introduced new Resource Management reform legislation.",
        # Q2: Verified Facts vs Strategic Interpretation
        verified_facts="Statutory transition deadline is 1 December 2026.",
        strategic_interpretation="MfE policy teams are overstretched with simultaneous reform bills.",
        # Q3: Affected organisations & sectors
        affected_sectors=["Environment", "Local Government"],
        target_client_id="mfe",
        target_client_name="Ministry for the Environment",
        # Q4: What affected organisations need to do
        operational_obligations=["Produce implementation guides for 67 territorial authorities."],
        compliance_deadlines=["1 December 2026"],
        # Q5: A+C Service Line
        primary_service_line_id="policy_regulatory",
        service_line_name="Policy & Regulatory Design",
        service_offering_summary="Policy drafting, regulatory design, and local government transition roadmaps.",
        # Q6: Who to approach and with what
        target_contact_persona="Deputy Secretary, Environment and Climate Policy",
        conversation_starter="We noticed the December deadline for national standards rollout—our team previously supported the transition framework...",
        key_pitch_angles=[
            "Deep expertise in statutory drafting and RIA",
            "Established relationship with MfE policy leads",
        ],
        # Scoring
        score=OpportunityScore(strategic_fit_score=32, urgency_score=30, budget_score=26),
    )

    assert opp.six_questions["q1_what_changed"] == "Government introduced new Resource Management reform legislation."
    assert "Statutory transition deadline" in opp.six_questions["q2_facts_vs_interpretation"]["verified_facts"]
    assert "Ministry for the Environment" in opp.six_questions["q3_affected_organisations"]["target_client_name"]
    assert len(opp.six_questions["q4_operational_obligations"]["operational_obligations"]) == 1
    assert opp.six_questions["q5_ac_service_line"]["service_line_name"] == "Policy & Regulatory Design"
    assert "Deputy Secretary" in opp.six_questions["q6_who_to_approach"]["target_contact_persona"]

    # Convert to database record
    record = opp.to_db_record()
    assert isinstance(record, OpportunityRecord)
    assert record.id == "opp-123"
    assert record.total_score == 88
    assert record.strategic_fit_score == 32
    assert record.urgency_score == 30
    assert record.budget_score == 26
    assert record.target_client_id == "mfe"


def test_pipeline_result_model():
    res = PipelineResult(
        processed_count=15,
        filtered_noise_count=5,
        opportunities=[],
        saved_count=0,
    )
    assert res.processed_count == 15
    assert res.filtered_noise_count == 5
