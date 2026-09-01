import os
import sqlite3
import pytest
from radar.db.database import DatabaseManager
from radar.db.seed import seed_database
from radar.models import ServiceLine, Client, ScanRecord, OpportunityRecord


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_radar.db"
    db = DatabaseManager(str(db_file))
    db.initialize()
    return db


def test_schema_initialization(temp_db):
    """Verify tables exist in initialized database."""
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
    
    assert "service_lines" in tables
    assert "clients" in tables
    assert "scans" in tables
    assert "opportunities" in tables


def test_seed_database_populates_service_lines_and_clients(temp_db):
    """Verify seed_database populates authentic A+C service lines and clients."""
    result = seed_database(temp_db)
    assert result["service_lines_seeded"] >= 8
    assert result["clients_seeded"] >= 15

    # Check service lines
    service_lines = temp_db.get_service_lines()
    assert len(service_lines) >= 8
    service_line_ids = {sl.id for sl in service_lines}
    assert "policy-regulation" in service_line_ids
    assert "evaluation-review" in service_line_ids
    assert "kaupapa-maori-pacific" in service_line_ids

    # Check case studies in service line
    policy_sl = next(sl for sl in service_lines if sl.id == "policy-regulation")
    assert len(policy_sl.case_studies) > 0
    assert any("Therapeutics Products Bill" in cs.get("title", "") or "Fast-Track" in cs.get("title", "") for cs in policy_sl.case_studies)

    # Check clients
    clients = temp_db.get_clients()
    assert len(clients) >= 15
    nz_clients = temp_db.get_clients(jurisdiction="NZ")
    au_clients = temp_db.get_clients(jurisdiction="AU")
    assert len(nz_clients) >= 5
    assert len(au_clients) >= 5


def test_seeding_is_idempotent(temp_db):
    """Running seed_database multiple times should not create duplicate entries or crash."""
    seed1 = seed_database(temp_db)
    count1_sl = len(temp_db.get_service_lines())
    count1_cl = len(temp_db.get_clients())

    seed2 = seed_database(temp_db)
    count2_sl = len(temp_db.get_service_lines())
    count2_cl = len(temp_db.get_clients())

    assert count1_sl == count2_sl
    assert count1_cl == count2_cl


def test_scan_and_opportunity_records(temp_db):
    """Verify scan insertion, retrieval, and duplicate hash checking."""
    scan = ScanRecord(
        id="scan-001",
        content_hash="hash-123456",
        source_id="beehive-releases",
        source_name="Beehive Releases",
        jurisdiction="NZ",
        title="Major Health System Announcement",
        url="https://beehive.govt.nz/release/123",
        published_date="2026-09-01T10:00:00Z",
        summary="Government announces new health reforms",
        raw_content="Full details of health system changes...",
        status="raw"
    )
    temp_db.save_scan(scan)

    # Check duplicate hash check
    assert temp_db.has_content_hash("hash-123456") is True
    assert temp_db.has_content_hash("nonexistent-hash") is False

    retrieved = temp_db.get_scan_by_id("scan-001")
    assert retrieved is not None
    assert retrieved.title == "Major Health System Announcement"
    assert retrieved.jurisdiction == "NZ"


def test_opportunity_crud_and_filtering(temp_db):
    """Verify opportunity saving, retrieval, and score filtering."""
    seed_database(temp_db)
    scan = ScanRecord(
        id="scan-001",
        content_hash="hash-opp-test-1",
        source_id="beehive-releases",
        source_name="Beehive Releases",
        jurisdiction="NZ",
        title="Health Review",
        url="https://beehive.govt.nz/rel1",
        published_date="2026-09-01T10:00:00Z",
        summary="Summary",
        raw_content="Content",
        status="raw",
    )
    temp_db.save_scan(scan)

    opp1 = OpportunityRecord(
        id="opp-001",
        scan_id="scan-001",
        title="Hospital Commissioning Review Advisory",
        jurisdiction="NZ",
        target_client_id="nz-healthnz",
        primary_service_line_id="strategy-planning",
        verified_facts="Cabinet approved terms of reference for review.",
        strategic_interpretation="Opportunity for target operating model support.",
        strategic_fit_score=30,
        urgency_score=25,
        budget_score=25,
        total_score=80,
        conversation_starter="We noticed the recent planned care operating model announcement...",
        target_contact_persona="Director of System Strategy",
        status="identified"
    )
    scan2 = ScanRecord(
        id="scan-002",
        content_hash="hash-opp-test-2",
        source_id="au-ministers-releases",
        source_name="AU Ministers",
        jurisdiction="AU",
        title="Aged Care",
        url="https://ministers.pmc.gov.au/rel2",
        published_date="2026-09-01T10:00:00Z",
        summary="Summary",
        raw_content="Content",
        status="raw",
    )
    temp_db.save_scan(scan2)

    opp2 = OpportunityRecord(
        id="opp-002",
        scan_id="scan-002",
        title="Aged Care Compliance Audit",
        jurisdiction="AU",
        target_client_id="au-health",
        primary_service_line_id="policy-regulation",
        total_score=60,
    )
    temp_db.save_opportunity(opp1)
    temp_db.save_opportunity(opp2)

    all_opps = temp_db.get_opportunities()
    assert len(all_opps) == 2
    assert all_opps[0].total_score >= all_opps[1].total_score  # Sorted descending

    high_opps = temp_db.get_opportunities(min_score=75)
    assert len(high_opps) == 1
    assert high_opps[0].id == "opp-001"

    nz_opps = temp_db.get_opportunities(jurisdiction="NZ")
    assert len(nz_opps) == 1
    assert nz_opps[0].id == "opp-001"
