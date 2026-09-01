import pytest
from radar.models import Client, ScanRecord, ServiceLine
from radar.pipeline.matcher_agent import ServiceMatcherAgent
from radar.pipeline.models import ImpactAnalysis, ServiceMatch


@pytest.fixture
def sample_service_lines():
    return [
        ServiceLine(
            id="policy_regulatory",
            name="Policy & Regulatory Design",
            description="Specialist policy development, regulatory reform, RIA, and legislative drafting assistance.",
            keywords=["policy", "regulatory", "legislation", "bill", "standards", "statutory", "guidelines"],
        ),
        ServiceLine(
            id="evaluation_research",
            name="Evaluation & Applied Research",
            description="Independent program evaluations, outcome monitoring, and qualitative/quantitative research.",
            keywords=["evaluation", "research", "review", "monitoring", "audit", "inquiry", "evidence"],
        ),
        ServiceLine(
            id="business_change_governance",
            name="Business Change & Public Sector Governance",
            description="Operating model design, public sector governance reviews, and transition delivery.",
            keywords=["governance", "operating model", "business change", "transition", "restructure", "machinery of government"],
        ),
        ServiceLine(
            id="kaupapa_maori_pacific",
            name="Kaupapa Māori & Pacific Policy",
            description="Te Tiriti / Treaty analysis, Kaupapa Māori research, and Pacific cultural advisory.",
            keywords=["māori", "maori", "treaty", "tiriti", "iwi", "pacific", "pasifika", "first nations"],
        ),
    ]


@pytest.fixture
def sample_clients():
    return [
        Client(
            id="mfe",
            name="Ministry for the Environment",
            jurisdiction="NZ",
            tier="Ministry",
            sector="Environment",
            key_divisions=["Resource Management Reform", "Climate Change"],
            past_engagements=["RMA national direction review", "Waste minimisation RIA"],
        ),
        Client(
            id="dohac",
            name="Department of Health and Aged Care",
            jurisdiction="AU",
            tier="Commonwealth",
            sector="Health",
            key_divisions=["Aged Care Quality and Assurance", "Primary Care"],
            past_engagements=["Aged Care Quality Standards implementation review"],
        ),
    ]


@pytest.fixture
def matcher_agent():
    return ServiceMatcherAgent()


def test_match_services_policy_and_client_nz(matcher_agent, sample_service_lines, sample_clients):
    scan = ScanRecord(
        id="scan-1",
        content_hash="h1",
        source_id="nz_beehive",
        source_name="Beehive",
        jurisdiction="NZ",
        title="Resource Management reform bill introduced with local council obligations",
        url="https://beehive.govt.nz/rma-bill",
        published_date="2026-03-01",
        summary="Ministry for the Environment releases new policy and legislative design guidelines.",
        raw_content="Ministry for the Environment releases new policy and legislative design guidelines.",
    )
    impact = ImpactAnalysis(
        verified_facts="Statutory deadline November 2026.",
        strategic_interpretation="MfE needs regulatory drafting support.",
        affected_sectors=["Environment & Climate", "Local Government"],
        affected_agencies=["Ministry for the Environment"],
        operational_obligations=["Draft spatial planning regulations."],
        compliance_deadlines=["November 2026"],
        citations=["Beehive 2026"],
    )

    match = matcher_agent.match_services(scan, impact, sample_service_lines, sample_clients)
    assert isinstance(match, ServiceMatch)
    assert match.primary_service_line_id == "policy_regulatory"
    assert match.target_client_id == "mfe"
    assert "Ministry for the Environment" in match.target_client_name
    assert len(match.service_offering_summary) > 15
    assert len(match.fit_rationale) > 15


def test_match_services_evaluation_au(matcher_agent, sample_service_lines, sample_clients):
    scan = ScanRecord(
        id="scan-2",
        content_hash="h2",
        source_id="au_ministers",
        source_name="Ministers",
        jurisdiction="AU",
        title="Health Minister announces statutory independent evaluation of new Aged Care Act compliance",
        url="https://ministers.pmc.gov.au/aged-care",
        published_date="2026-03-01",
        summary="Department of Health and Aged Care is commissioning a nationwide evaluation.",
        raw_content="Department of Health and Aged Care is commissioning a nationwide evaluation.",
    )
    impact = ImpactAnalysis(
        verified_facts="Evaluation framework mandated by July 2026.",
        strategic_interpretation="DoHAC requires external evaluation capacity.",
        affected_sectors=["Health"],
        affected_agencies=["Department of Health and Aged Care"],
        operational_obligations=["Conduct statutory programme review and evidence-based performance evaluation."],
        compliance_deadlines=["July 2026"],
        citations=["PMC 2026"],
    )

    match = matcher_agent.match_services(scan, impact, sample_service_lines, sample_clients)
    assert isinstance(match, ServiceMatch)
    assert match.primary_service_line_id == "evaluation_research"
    assert match.target_client_id == "dohac"
    assert "Department of Health and Aged Care" in match.target_client_name
