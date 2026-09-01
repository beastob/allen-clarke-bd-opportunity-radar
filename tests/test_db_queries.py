import pytest
from radar.db.database import DatabaseManager
from radar.db.seed import seed_database
from radar.models import Client, OpportunityRecord, ScanRecord, ServiceLine


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_queries.db"
    db = DatabaseManager(str(db_file))
    db.initialize()
    seed_database(db)
    return db


def test_get_client_by_id(temp_db):
    client = temp_db.get_client_by_id("nz-healthnz")
    assert client is not None
    assert client.id == "nz-healthnz"
    assert "Health New Zealand" in client.name
    assert client.jurisdiction == "NZ"

    assert temp_db.get_client_by_id("non-existent-id") is None


def test_get_client_by_name(temp_db):
    client = temp_db.get_client_by_name("Health New Zealand")
    assert client is not None
    assert client.id == "nz-healthnz"

    # Case-insensitive partial / fuzzy match
    client_partial = temp_db.get_client_by_name("health nz")
    assert client_partial is not None
    assert client_partial.id == "nz-healthnz"

    assert temp_db.get_client_by_name("NonExistent Department") is None


def test_get_service_line_by_id(temp_db):
    sl = temp_db.get_service_line_by_id("policy-regulation")
    assert sl is not None
    assert sl.id == "policy-regulation"
    assert "Policy" in sl.name

    assert temp_db.get_service_line_by_id("non-existent-service-line") is None


def test_get_opportunity_by_id(temp_db):
    opp = OpportunityRecord(
        id="opp-test-123",
        scan_id=None,
        title="Health Systems Review",
        jurisdiction="NZ",
        target_client_id="nz-healthnz",
        primary_service_line_id="policy-regulation",
        verified_facts="Cabinet approved TOR.",
        strategic_interpretation="Opportunity for advisory support.",
        strategic_fit_score=30,
        urgency_score=30,
        budget_score=25,
        total_score=85,
        conversation_starter="We noted the recent reforms announcement...",
        target_contact_persona="Chief Executive",
        status="identified",
    )
    temp_db.save_opportunity(opp)

    retrieved = temp_db.get_opportunity_by_id("opp-test-123")
    assert retrieved is not None
    assert retrieved.id == "opp-test-123"
    assert retrieved.title == "Health Systems Review"
    assert retrieved.total_score == 85

    assert temp_db.get_opportunity_by_id("non-existent-opp") is None


def test_update_client_relationship_notes(temp_db):
    # Initial client notes
    initial_client = temp_db.get_client_by_id("nz-healthnz")
    assert initial_client is not None

    # Append notes
    updated = temp_db.update_client_relationship_notes(
        client_id="nz-healthnz",
        relationship_notes="Met with Deputy Director regarding planned care procurement.",
        append=True,
    )
    assert updated is not None
    assert "Met with Deputy Director" in updated.relationship_notes
    if initial_client.relationship_notes:
        assert initial_client.relationship_notes in updated.relationship_notes

    # Overwrite notes
    overwritten = temp_db.update_client_relationship_notes(
        client_id="nz-healthnz",
        relationship_notes="Fresh reset of relationship notes.",
        append=False,
    )
    assert overwritten is not None
    assert overwritten.relationship_notes == "Fresh reset of relationship notes."


def test_query_opportunities_with_filters(temp_db):
    opp1 = OpportunityRecord(
        id="opp-filter-1",
        title="NZ Health Policy Review",
        jurisdiction="NZ",
        target_client_id="nz-healthnz",
        primary_service_line_id="policy-regulation",
        strategic_fit_score=30,
        urgency_score=30,
        budget_score=30,
        total_score=90,
    )
    opp2 = OpportunityRecord(
        id="opp-filter-2",
        title="NZ Environment Resource Management Transition",
        jurisdiction="NZ",
        target_client_id="nz-mfe",
        primary_service_line_id="policy-regulation",
        strategic_fit_score=25,
        urgency_score=25,
        budget_score=20,
        total_score=70,
    )
    opp3 = OpportunityRecord(
        id="opp-filter-3",
        title="AU Aged Care Evaluation",
        jurisdiction="AU",
        target_client_id="au-health",
        primary_service_line_id="evaluation-review",
        strategic_fit_score=20,
        urgency_score=20,
        budget_score=20,
        total_score=60,
    )
    temp_db.save_opportunity(opp1)
    temp_db.save_opportunity(opp2)
    temp_db.save_opportunity(opp3)

    # 1. Min score filter
    high_score_opps = temp_db.query_opportunities(min_score=75)
    assert len(high_score_opps) == 1
    assert high_score_opps[0]["id"] == "opp-filter-1"
    assert high_score_opps[0]["client_name"] == "Health New Zealand (Te Whatu Ora)"
    assert high_score_opps[0]["service_line_name"] == "Policy + Regulation"

    # 2. Sector filter (e.g. Health)
    health_opps = temp_db.query_opportunities(sector="Health")
    assert len(health_opps) >= 2
    opp_ids = {o["id"] for o in health_opps}
    assert "opp-filter-1" in opp_ids
    assert "opp-filter-3" in opp_ids

    # 3. Client filter
    mfe_opps = temp_db.query_opportunities(client="Ministry for the Environment")
    assert len(mfe_opps) == 1
    assert mfe_opps[0]["id"] == "opp-filter-2"

    # 4. Jurisdiction filter
    au_opps = temp_db.query_opportunities(jurisdiction="AU")
    assert len(au_opps) == 1
    assert au_opps[0]["id"] == "opp-filter-3"
