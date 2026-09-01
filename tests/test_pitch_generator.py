import pytest
from radar.briefing.pitch_generator import PitchGenerator
from radar.models import Client, OpportunityRecord, ServiceLine


@pytest.fixture
def sample_opportunity():
    return OpportunityRecord(
        id="opp-nz-health-001",
        scan_id="scan-health-001",
        title="Health New Zealand Planned Care Delivery Model Advisory",
        jurisdiction="NZ",
        target_client_id="nz-healthnz",
        primary_service_line_id="strategy-planning",
        verified_facts="Cabinet approved updated operating model directives for regional hospital networks and waitlist reductions with statutory milestones by Q4.",
        strategic_interpretation="Health NZ regions face acute capacity bottlenecks translating ministerial directives into operational commissioning plans.",
        strategic_fit_score=32,
        urgency_score=28,
        budget_score=25,
        total_score=85,
        conversation_starter="We noticed the recent Cabinet directive on regional planned care operating models and wanted to share our insights on cross-regional resource allocation.",
        target_contact_persona="Director of System Strategy / Regional Commissioning Lead",
        status="identified",
    )


@pytest.fixture
def sample_client():
    return Client(
        id="nz-healthnz",
        name="Health New Zealand (Te Whatu Ora)",
        jurisdiction="NZ",
        tier="Crown Entity",
        sector="Health",
        key_divisions=["Hospital & Specialist Services", "Commissioning", "System Strategy"],
        past_engagements=["Clinical Services Capability Review", "Regional Service Delivery Blueprint"],
        relationship_notes="Ongoing dialogue with Commissioning teams following 2025 review.",
    )


@pytest.fixture
def sample_service_line():
    return ServiceLine(
        id="strategy-planning",
        name="Strategy + Planning",
        description="Target operating model (TOM) design, whole-of-system architecture, organizational strategy, and strategic roadmaps.",
        keywords=["operating model", "target operating model", "TOM", "strategic planning"],
        case_studies=[
            {
                "title": "Demystifying Operating Models: Aligning Strategy and Execution in Public Agencies",
                "client": "Cross-Agency Public Sector Leaders",
                "summary": "Developed target operating model frameworks linking legislative mandates, capabilities, and service delivery channels.",
                "impact": "Streamlined service delivery structures across public entities.",
            }
        ],
    )


def test_generate_pitch_brief_structure(sample_opportunity, sample_client, sample_service_line):
    generator = PitchGenerator()
    brief = generator.generate_brief(
        opportunity=sample_opportunity,
        client=sample_client,
        service_line=sample_service_line,
        contact_name="Dr. Sarah Jenkins",
    )

    # Check top-level dictionary keys
    assert "opportunity_id" in brief
    assert brief["opportunity_id"] == "opp-nz-health-001"
    assert "pitch_brief_markdown" in brief
    assert "email_draft" in brief
    assert "talking_points" in brief
    assert "recommended_next_steps" in brief

    # Check email draft contents
    email = brief["email_draft"]
    assert "subject" in email
    assert "body" in email
    assert "recipient" in email
    assert "Dr. Sarah Jenkins" in email["recipient"]
    assert "Dr. Jenkins" in email["body"] or "Dr. Sarah Jenkins" in email["body"]
    assert "Health New Zealand" in email["body"]
    assert "Strategy + Planning" in email["body"] or "operating model" in email["body"].lower()

    # Check verified facts & strategic interpretation are represented
    md = brief["pitch_brief_markdown"]
    assert "Executive BD Brief" in md
    assert "Cabinet approved updated operating model" in md
    assert "Health NZ regions face acute capacity bottlenecks" in md
    assert "Strategy + Planning" in md
    assert "85/100" in md

    # Check talking points
    assert len(brief["talking_points"]) >= 2
    assert any("operating model" in tp.lower() or "planned care" in tp.lower() for tp in brief["talking_points"])


def test_generate_pitch_brief_with_custom_angle(sample_opportunity, sample_client, sample_service_line):
    generator = PitchGenerator()
    brief = generator.generate_brief(
        opportunity=sample_opportunity,
        client=sample_client,
        service_line=sample_service_line,
        custom_angle="Focus specifically on regional waitlist data governance and clinical throughput.",
    )

    md = brief["pitch_brief_markdown"]
    email = brief["email_draft"]

    assert "regional waitlist data governance" in md or "regional waitlist data governance" in email["body"]


def test_generate_pitch_brief_handles_none_collaborators(sample_opportunity):
    generator = PitchGenerator()
    # Should work gracefully even if client or service_line is None (standalone opportunity record)
    brief = generator.generate_brief(
        opportunity=sample_opportunity,
        client=None,
        service_line=None,
    )
    assert brief is not None
    assert brief["opportunity_id"] == "opp-nz-health-001"
    assert "Health New Zealand Planned Care" in brief["email_draft"]["subject"]
    assert len(brief["talking_points"]) >= 1
