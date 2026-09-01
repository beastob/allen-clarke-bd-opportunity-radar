"""Shared pytest fixtures for Allen + Clarke BD Opportunity Radar tests."""

import pytest
from radar.pipeline.models import BDOpportunity, OpportunityScore


@pytest.fixture(autouse=True)
def default_test_environment(monkeypatch):
    """Ensures test suite runs in deterministic offline mode by default."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


@pytest.fixture
def sample_opportunity_nz():
    """Sample high-scoring NZ opportunity."""
    return BDOpportunity(
        id="opp-nz-001",
        scan_id="scan-nz-101",
        title="NZ Resource Management System Reform Guidelines & Transition",
        jurisdiction="NZ",
        published_date="2026-03-15",
        url="https://beehive.govt.nz/release/rma-reform-2026",
        change_summary="Government released national planning framework directives requiring regional council alignment.",
        verified_facts="Resource Management Directive 2026 gazetted on 15 March 2026 with statutory transition deadline of 1 December 2026.",
        strategic_interpretation="Ministry for the Environment policy teams are stretched across multiple reform packages; regional councils need implementation frameworks.",
        affected_sectors=["Environment", "Local Government"],
        target_client_id="nz-mfe",
        target_client_name="Ministry for the Environment",
        operational_obligations=[
            "Establish regional spatial strategy transition plans",
            "Update council consenting frameworks by Q4 2026",
        ],
        compliance_deadlines=["1 December 2026", "31 March 2027"],
        primary_service_line_id="policy-regulation",
        service_line_name="Policy + Regulation",
        service_offering_summary="Policy drafting, regulatory design, and local government transition roadmaps.",
        target_contact_persona="Deputy Secretary, Environmental Strategy & Regulatory Reform",
        conversation_starter="We noted the December 2026 deadline for the national planning framework transition—our team previously supported the transition architecture...",
        key_pitch_angles=[
            "Deep experience in NZ statutory drafting and RIA",
            "Proven track record with MfE and regional councils",
        ],
        score=OpportunityScore(
            strategic_fit_score=33,
            urgency_score=30,
            budget_score=25,
            rationale={
                "strategic_fit": "Core A+C policy and regulatory reform expertise",
                "urgency": "Statutory deadline within 9 months",
                "budget": "High commissioning likelihood from MfE policy budget",
            },
        ),
    )


@pytest.fixture
def sample_opportunity_au():
    """Sample high-scoring AU opportunity."""
    return BDOpportunity(
        id="opp-au-002",
        scan_id="scan-au-202",
        title="Australian Aged Care Quality & Safety Commission Governance Review",
        jurisdiction="AU",
        published_date="2026-03-10",
        url="https://www.legislation.gov.au/Details/C2026A00045",
        change_summary="Commonwealth Parliament enacted new Aged Care Act establishing enhanced oversight and governance standards.",
        verified_facts="Aged Care Act 2026 Section 45 mandates independent clinical governance audits for all approved providers by November 2026.",
        strategic_interpretation="Department of Health and Aged Care requires external review capability to assess provider readiness across regional sectors.",
        affected_sectors=["Health & Aged Care", "Public Sector Governance"],
        target_client_id="au-health",
        target_client_name="Department of Health and Aged Care",
        operational_obligations=[
            "Deploy clinical governance audit tools",
            "Publish provider compliance benchmarks",
        ],
        compliance_deadlines=["1 November 2026"],
        primary_service_line_id="evaluation-review",
        service_line_name="Evaluation + Review",
        service_offering_summary="Independent clinical governance evaluations and regulatory compliance reviews.",
        target_contact_persona="First Assistant Secretary, Ageing and Aged Care Group",
        conversation_starter="With the Section 45 audit requirements taking effect in November, our team's recent governance review framework can help establish baseline compliance...",
        key_pitch_angles=[
            "Extensive public health and aged care evaluation credentials",
            "Specialized mixed-methods audit methodologies",
        ],
        score=OpportunityScore(
            strategic_fit_score=31,
            urgency_score=32,
            budget_score=26,
            rationale={
                "strategic_fit": "Direct alignment with evaluation and public sector review practice",
                "urgency": "Statutory audit mandate effective November 2026",
                "budget": "Funded statutory review line item",
            },
        ),
    )


@pytest.fixture
def sample_opp(sample_opportunity_nz):
    """Alias for sample_opportunity_nz."""
    return sample_opportunity_nz
