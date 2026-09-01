"""Ingestion engine orchestrating government feed fetching, deduplication, and persistence."""

import logging
import uuid
from typing import Optional
from radar.db.database import DatabaseManager
from radar.ingestion.fetcher import FeedFetcher
from radar.models import FeedItem, IngestionResult, ScanRecord

logger = logging.getLogger(__name__)


class IngestionEngine:
    """Orchestrates policy feed retrieval, SHA-256 deduplication, and storage."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        fetcher: Optional[FeedFetcher] = None,
    ):
        self.db = db_manager
        self.fetcher = fetcher or FeedFetcher()

    def run_scan(
        self,
        jurisdiction: Optional[str] = "ALL",
        use_fixtures: bool = False,
        timeout: float = 10.0,
    ) -> IngestionResult:
        """Runs a policy scan across configured government feeds with content deduplication."""
        result = IngestionResult()

        try:
            items = self.fetcher.fetch_all(
                jurisdiction=jurisdiction,
                use_fixtures=use_fixtures,
                timeout=timeout,
            )
            result.total_fetched = len(items)

            for item in items:
                try:
                    if self.db.has_content_hash(item.content_hash):
                        logger.debug(f"Skipping duplicate content hash: {item.content_hash} ({item.title})")
                        result.duplicates_skipped += 1
                        continue

                    # Create new scan record
                    scan_id = f"scan-{uuid.uuid4().hex[:12]}"
                    scan_record = ScanRecord(
                        id=scan_id,
                        content_hash=item.content_hash,
                        source_id=item.source_id,
                        source_name=item.source_name,
                        jurisdiction=item.jurisdiction,
                        title=item.title,
                        url=item.url,
                        published_date=item.published_date,
                        summary=item.summary,
                        raw_content=item.raw_content,
                        status="raw",
                    )
                    self.db.save_scan(scan_record)
                    result.new_items += 1

                except Exception as item_err:
                    err_msg = f"Failed to persist item '{item.title}': {item_err}"
                    logger.error(err_msg)
                    result.errors.append(err_msg)

        except Exception as e:
            err_msg = f"Scan failed for jurisdiction '{jurisdiction}': {e}"
            logger.error(err_msg)
            result.errors.append(err_msg)

        logger.info(
            f"Scan completed: {result.total_fetched} fetched, "
            f"{result.new_items} new inserted, "
            f"{result.duplicates_skipped} duplicates skipped, "
            f"{len(result.errors)} errors."
        )
        return result
