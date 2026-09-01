import pytest
from radar.db.database import DatabaseManager
from radar.db.seed import seed_database
from radar.ingestion.engine import IngestionEngine
from radar.models import ScanRecord
from radar.pipeline.orchestrator import OpportunityPipeline


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_pipeline.db"
    db = DatabaseManager(str(db_file))
    db.initialize()
    seed_database(db)
    return db


def test_pipeline_end_to_end_with_fixtures(temp_db):
    # 1. Ingest fixture feeds into DB
    ingestion_engine = IngestionEngine(db_manager=temp_db)
    ingest_result = ingestion_engine.run_scan(use_fixtures=True)
    assert ingest_result.total_fetched > 0

    # 2. Run multi-agent pipeline
    pipeline = OpportunityPipeline(db_manager=temp_db)
    result = pipeline.run(max_items=10)

    assert result.processed_count > 0
    assert len(result.opportunities) <= 10
    assert result.saved_count == len(result.opportunities)

    # 3. Check DB opportunities
    stored_opps = temp_db.get_opportunities(limit=10)
    assert len(stored_opps) == len(result.opportunities)

    for opp in result.opportunities:
        # Verify 6 core questions
        assert opp.title != ""
        assert opp.change_summary != ""
        assert opp.verified_facts != ""
        assert opp.strategic_interpretation != ""
        assert opp.target_client_name != ""
        assert opp.primary_service_line_id != ""
        assert opp.target_contact_persona != ""
        assert opp.conversation_starter != ""
        assert len(opp.key_pitch_angles) >= 1
        assert opp.score.total_score >= 0 and opp.score.total_score <= 100

    # 4. Check that items are sorted descending by score
    scores = [o.score.total_score for o in result.opportunities]
    assert scores == sorted(scores, reverse=True)


def test_pipeline_jurisdiction_filtering(temp_db):
    # Ingest fixture feeds
    ingestion_engine = IngestionEngine(db_manager=temp_db)
    ingestion_engine.run_scan(use_fixtures=True)

    pipeline = OpportunityPipeline(db_manager=temp_db)

    # NZ only
    nz_result = pipeline.run(jurisdiction="NZ", max_items=10)
    assert len(nz_result.opportunities) > 0
    assert all(o.jurisdiction == "NZ" for o in nz_result.opportunities)

    # AU only
    au_result = pipeline.run(jurisdiction="AU", max_items=10)
    assert len(au_result.opportunities) > 0
    assert all(o.jurisdiction == "AU" for o in au_result.opportunities)


def test_pipeline_filters_ceremonial_noise_scans(temp_db):
    pipeline = OpportunityPipeline(db_manager=temp_db)

    noisy_scan = ScanRecord(
        id="scan-noise-test",
        content_hash="hash-noise-test",
        source_id="nz_beehive",
        source_name="Beehive",
        jurisdiction="NZ",
        title="Minister congratulates national netball team on gold medal triumph",
        url="https://beehive.govt.nz/sports-award",
        published_date="2026-03-01",
        summary="A celebratory reception was held in Wellington honoring the players.",
        raw_content="A celebratory reception was held in Wellington honoring the players.",
    )
    temp_db.save_scan(noisy_scan)

    result = pipeline.run(scans=[noisy_scan])
    assert result.filtered_noise_count == 1
    assert len(result.opportunities) == 0

    # Verify scan status updated in DB
    updated_scan = temp_db.get_scan_by_id("scan-noise-test")
    assert updated_scan is not None
    assert updated_scan.status == "filtered_noise"
