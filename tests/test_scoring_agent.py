import pytest
from radar.models import ScanRecord
from radar.pipeline.models import (
    BDOpportunity,
    ImpactAnalysis,
    OpportunityScore,
    ServiceMatch,
)
from radar.pipeline.scoring_agent import PrioritisationAgent


@pytest.fixture
def scoring_agent():
    return PrioritisationAgent()


def test_score_opportunity_nz_rma(scoring_agent):
    scan = ScanRecord(
        id="scan-rma",
        content_hash="hash-rma",
        source_id="nz_beehive",
        source_name="Beehive",
        jurisdiction="NZ",
        title="Minister Bishop introduces Natural and Built Environment Bill with Q4 2026 deadlines",
        url="https://beehive.govt.nz/rma",
        published_date="2026-03-01",
        summary="Major RMA overhaul with statutory local council obligations.",
        raw_content="Major RMA overhaul with statutory local council obligations.",
    )
    impact = ImpactAnalysis(
        verified_facts="Bill introduced March 2026. Transition deadline 1 November 2026.",
        strategic_interpretation="MfE and councils face acute policy drafting shortages.",
        affected_sectors=["Environment & Climate", "Local Government"],
        affected_agencies=["Ministry for the Environment", "Regional Councils"],
        operational_obligations=["Develop regional spatial strategies and secondary regulations."],
        compliance_deadlines=["1 November 2026"],
        citations=["Beehive 2026"],
    )
    match = ServiceMatch(
        primary_service_line_id="policy_regulatory",
        secondary_service_line_ids=["business_change_governance"],
        target_client_id="mfe",
        target_client_name="Ministry for the Environment",
        service_offering_summary="Policy & Regulatory Design advisory support for RMA transition.",
        fit_rationale="Allen + Clarke has deep expertise in resource management reform.",
    )

    opp = scoring_agent.score_opportunity(scan, impact, match)
    assert isinstance(opp, BDOpportunity)
    assert opp.score.strategic_fit_score >= 20 and opp.score.strategic_fit_score <= 35
    assert opp.score.urgency_score >= 20 and opp.score.urgency_score <= 35
    assert opp.score.budget_score >= 15 and opp.score.budget_score <= 30
    assert opp.score.total_score >= 60 and opp.score.total_score <= 100

    # Verify 6 core questions
    assert opp.target_contact_persona != ""
    assert len(opp.conversation_starter) > 30
    assert len(opp.key_pitch_angles) >= 2
    assert opp.primary_service_line_id == "policy_regulatory"
    assert opp.target_client_id == "mfe"


def test_rank_and_cap_strict_max_10(scoring_agent):
    # Generate 15 opportunities with varying scores
    opportunities = []
    for i in range(15):
        opp = BDOpportunity(
            id=f"opp-{i}",
            scan_id=f"scan-{i}",
            title=f"Policy Initiative {i}",
            jurisdiction="NZ" if i % 2 == 0 else "AU",
            published_date="2026-03-01",
            url=f"https://gov.test/{i}",
            change_summary=f"Summary {i}",
            verified_facts=f"Facts {i}",
            strategic_interpretation=f"Interpretation {i}",
            affected_sectors=["Health"],
            target_client_id=f"client-{i}",
            target_client_name=f"Department {i}",
            operational_obligations=["Obligation"],
            compliance_deadlines=["2026"],
            primary_service_line_id="policy_regulatory",
            service_line_name="Policy & Regulatory Design",
            service_offering_summary=f"Offering {i}",
            target_contact_persona="Director Policy",
            conversation_starter=f"Starter {i}",
            key_pitch_angles=["Angle 1", "Angle 2"],
            score=OpportunityScore(
                strategic_fit_score=(i * 2) % 35,
                urgency_score=(i * 2) % 35,
                budget_score=(i * 2) % 30,
            ),
        )
        opportunities.append(opp)

    # Rank and cap at default 10
    capped = scoring_agent.rank_and_cap(opportunities, max_items=10)
    assert len(capped) == 10
    # Must be sorted descending by total_score
    for idx in range(len(capped) - 1):
        assert capped[idx].score.total_score >= capped[idx + 1].score.total_score
