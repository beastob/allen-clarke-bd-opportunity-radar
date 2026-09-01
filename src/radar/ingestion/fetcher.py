"""Government RSS/Atom feed fetcher with offline fallback support."""

import logging
from pathlib import Path
from typing import List, Optional
import feedparser
import httpx
from radar.ingestion.parser import parse_feed_entry
from radar.ingestion.registry import SourceConfig, get_feed_sources, get_source_by_id
from radar.models import FeedItem

logger = logging.getLogger(__name__)


class FeedFetcher:
    """Fetches and parses government policy RSS/Atom feeds with fixture fallback."""

    def __init__(self, fixtures_dir: Optional[Path] = None):
        if fixtures_dir:
            self.fixtures_dir = fixtures_dir
        else:
            self.fixtures_dir = Path(__file__).parent.parent / "data" / "fixtures"

    def _parse_entries(self, parsed: feedparser.FeedParserDict, source: SourceConfig) -> List[FeedItem]:
        """Transforms parsed feed entries into structured FeedItem models."""
        items = []
        for entry in parsed.entries:
            item = parse_feed_entry(
                entry=entry,
                source_or_id=source,
            )
            items.append(item)
        return items

    def fetch_source(
        self,
        source_id: str,
        use_fixtures: bool = False,
        timeout: float = 10.0,
    ) -> List[FeedItem]:
        """Fetches and parses a single feed source."""
        source = get_source_by_id(source_id)
        if not source:
            raise ValueError(f"Unknown feed source ID: {source_id}")

        if use_fixtures:
            return self._fetch_fixture(source)

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "application/rss+xml, application/xml, text/xml, application/atom+xml, text/html, */*",
            }
            response = httpx.get(source.feed_url, timeout=timeout, headers=headers, follow_redirects=True)
            response.raise_for_status()
            parsed = feedparser.parse(response.text)

            # If there was a parsing error/malformed feed, fall back to fixture
            if getattr(parsed, "bozo", 0) and not parsed.entries:
                logger.warning(f"Feed parser error for {source.id}; falling back to fixture.")
                return self._fetch_fixture(source)

            return self._parse_entries(parsed, source)

        except Exception as e:
            logger.warning(f"Network fetch failed for {source.id} ({e}); falling back to offline fixture.")
            return self._fetch_fixture(source)

    def _fetch_fixture(self, source: SourceConfig) -> List[FeedItem]:
        """Loads and parses a curated fallback XML fixture."""
        fixture_path = self.fixtures_dir / source.fixture_filename
        if not fixture_path.exists():
            logger.error(f"Fixture file not found: {fixture_path}")
            return []

        xml_content = fixture_path.read_text(encoding="utf-8")
        parsed = feedparser.parse(xml_content)
        return self._parse_entries(parsed, source)

    def fetch_all(
        self,
        jurisdiction: Optional[str] = "ALL",
        use_fixtures: bool = False,
        timeout: float = 10.0,
    ) -> List[FeedItem]:
        """Fetches entries across all registered sources matching the given jurisdiction."""
        sources = get_feed_sources(jurisdiction)
        all_items: List[FeedItem] = []

        for source in sources:
            source_items = self.fetch_source(
                source_id=source.id,
                use_fixtures=use_fixtures,
                timeout=timeout,
            )
            all_items.extend(source_items)

        return all_items
