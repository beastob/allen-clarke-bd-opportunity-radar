import pytest
from radar.db.database import DatabaseManager
from radar.ingestion.engine import IngestionEngine
from radar.ingestion.fetcher import FeedFetcher
from radar.models import IngestionResult


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "engine_test.db"
    db = DatabaseManager(str(db_file))
    db.initialize()
    return db


def test_engine_initial_run_inserts_scans(test_db):
    """Verify first run of IngestionEngine saves all items to scans table."""
    fetcher = FeedFetcher()
    engine = IngestionEngine(db_manager=test_db, fetcher=fetcher)

    result = engine.run_scan(jurisdiction="ALL", use_fixtures=True)

    assert isinstance(result, IngestionResult)
    assert result.total_fetched >= 8
    assert result.new_items == result.total_fetched
    assert result.duplicates_skipped == 0
    assert len(result.errors) == 0

    scans = test_db.get_scans()
    assert len(scans) == result.new_items
    assert any(s.jurisdiction == "NZ" for s in scans)
    assert any(s.jurisdiction == "AU" for s in scans)


def test_engine_deduplication_idempotency(test_db):
    """Verify running the engine consecutively skips already ingested items."""
    fetcher = FeedFetcher()
    engine = IngestionEngine(db_manager=test_db, fetcher=fetcher)

    # First run
    res1 = engine.run_scan(jurisdiction="ALL", use_fixtures=True)
    initial_count = len(test_db.get_scans())
    assert res1.new_items > 0

    # Second run with exact same data
    res2 = engine.run_scan(jurisdiction="ALL", use_fixtures=True)
    second_count = len(test_db.get_scans())

    assert res2.total_fetched == res1.total_fetched
    assert res2.new_items == 0
    assert res2.duplicates_skipped == res1.total_fetched
    assert initial_count == second_count


def test_engine_jurisdiction_filtering(test_db):
    """Verify engine runs scans for a specific jurisdiction only."""
    fetcher = FeedFetcher()
    engine = IngestionEngine(db_manager=test_db, fetcher=fetcher)

    res_nz = engine.run_scan(jurisdiction="NZ", use_fixtures=True)
    nz_scans = test_db.get_scans(jurisdiction="NZ")

    assert res_nz.new_items == len(nz_scans)
    assert all(s.jurisdiction == "NZ" for s in nz_scans)

    res_au = engine.run_scan(jurisdiction="AU", use_fixtures=True)
    au_scans = test_db.get_scans(jurisdiction="AU")

    assert res_au.new_items == len(au_scans)
    assert all(s.jurisdiction == "AU" for s in au_scans)
