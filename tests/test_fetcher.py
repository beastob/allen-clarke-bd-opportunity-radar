import pytest
from unittest.mock import patch
import httpx
from radar.ingestion.fetcher import FeedFetcher
from radar.ingestion.registry import get_feed_sources, SourceConfig
from radar.models import FeedItem


def test_feed_registry_sources():
    """Verify registry provides configured NZ and AU government sources."""
    all_sources = get_feed_sources("ALL")
    assert len(all_sources) >= 4
    
    nz_sources = get_feed_sources("NZ")
    au_sources = get_feed_sources("AU")
    
    assert all(s.jurisdiction == "NZ" for s in nz_sources)
    assert all(s.jurisdiction == "AU" for s in au_sources)
    assert len(nz_sources) >= 2
    assert len(au_sources) >= 2

    source_ids = {s.id for s in all_sources}
    assert "beehive-releases" in source_ids
    assert "nz-parliament-bills" in source_ids
    assert "au-ministers-releases" in source_ids
    assert "au-legislation-updates" in source_ids


def test_fetch_source_with_curated_fixtures():
    """Verify fixture fallback loads and parses high quality offline XML fixtures."""
    fetcher = FeedFetcher()
    
    # NZ Beehive
    items = fetcher.fetch_source("beehive-releases", use_fixtures=True)
    assert len(items) > 0
    assert all(isinstance(i, FeedItem) for i in items)
    assert all(i.jurisdiction == "NZ" for i in items)
    assert all(len(i.content_hash) == 64 for i in items)

    # AU Ministers
    au_items = fetcher.fetch_source("au-ministers-releases", use_fixtures=True)
    assert len(au_items) > 0
    assert all(i.jurisdiction == "AU" for i in au_items)


def test_fetch_all_with_fixtures_and_jurisdiction():
    """Verify fetching across jurisdictions in fixture mode."""
    fetcher = FeedFetcher()
    
    nz_items = fetcher.fetch_all(jurisdiction="NZ", use_fixtures=True)
    au_items = fetcher.fetch_all(jurisdiction="AU", use_fixtures=True)
    all_items = fetcher.fetch_all(jurisdiction="ALL", use_fixtures=True)

    assert len(nz_items) > 0
    assert len(au_items) > 0
    assert len(all_items) == len(nz_items) + len(au_items)


def test_network_failure_falls_back_to_fixture():
    """Verify network error automatically falls back to curated fixtures."""
    fetcher = FeedFetcher()
    
    # Mock httpx.get to raise RequestError
    with patch("httpx.get", side_effect=httpx.ConnectError("Connection refused")):
        items = fetcher.fetch_source("beehive-releases", use_fixtures=False)
        assert len(items) > 0
        assert items[0].source_id == "beehive-releases"
