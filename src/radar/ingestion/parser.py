"""Feed entry parsing and HTML sanitization."""

import html
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from bs4 import BeautifulSoup
from radar.ingestion.hasher import compute_content_hash, normalize_text
from radar.ingestion.registry import SourceConfig
from radar.models import FeedItem


def clean_html_text(html_content: Optional[str]) -> str:
    """Strips HTML markup and unescapes HTML entities, returning clean plain text."""
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator=" ")
    except Exception:
        # Fallback to regex tag stripping
        text = re.sub(r"<[^>]+>", " ", html_content)

    text = html.unescape(text)
    return normalize_text(text)


def extract_published_date(entry: Dict[str, Any]) -> str:
    """Extracts an ISO 8601 timestamp from a feed entry."""
    parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed_time:
        try:
            dt = datetime.fromtimestamp(time.mktime(parsed_time), tz=timezone.utc)
            return dt.isoformat()
        except Exception:
            pass

    # Try raw string
    raw_date = entry.get("published") or entry.get("updated")
    if raw_date:
        for fmt in (
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                dt = datetime.strptime(raw_date.strip(), fmt)
                if not dt.tzinfo:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.isoformat()
            except Exception:
                continue

    return datetime.now(timezone.utc).isoformat()


def parse_feed_entry(
    entry: Dict[str, Any],
    source_or_id: Optional[Union[SourceConfig, str]] = None,
    source_name: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    source_id: Optional[str] = None,
) -> FeedItem:
    """Parses a feedparser entry into a structured FeedItem."""
    if isinstance(source_or_id, SourceConfig):
        resolved_source_id = source_or_id.id
        resolved_name = source_or_id.name
        resolved_jur = source_or_id.jurisdiction
    else:
        resolved_source_id = source_id or (source_or_id if isinstance(source_or_id, str) else "unknown-source")
        resolved_name = source_name or resolved_source_id
        resolved_jur = jurisdiction or "NZ"

    title = clean_html_text(entry.get("title", "Untitled Policy Announcement"))
    url = entry.get("link", "")
    entry_id = str(entry.get("id") or entry.get("guid") or url)

    # Extract summary
    summary_raw = entry.get("summary") or entry.get("description") or ""
    summary = clean_html_text(summary_raw)

    # Extract raw content
    raw_content_parts = []
    if "content" in entry and isinstance(entry["content"], list):
        for c in entry["content"]:
            if isinstance(c, dict) and "value" in c:
                raw_content_parts.append(clean_html_text(c["value"]))
    if not raw_content_parts and summary:
        raw_content_parts.append(summary)

    raw_content = "\n\n".join(raw_content_parts) if raw_content_parts else summary
    published_date = extract_published_date(entry)

    # Compute deterministic content hash
    content_hash = compute_content_hash(title, url, raw_content)

    return FeedItem(
        id=entry_id,
        source_id=resolved_source_id,
        source_name=resolved_name,
        jurisdiction=resolved_jur,  # type: ignore
        title=title,
        url=url,
        published_date=published_date,
        summary=summary,
        raw_content=raw_content,
        content_hash=content_hash,
    )
