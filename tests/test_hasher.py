import pytest
from radar.ingestion.hasher import compute_content_hash, normalize_text
from radar.ingestion.parser import parse_feed_entry, clean_html_text
from radar.models import FeedItem


def test_normalize_text():
    """Verify text normalization strips excess whitespace and normalizes spaces."""
    raw = "  Government   announces \n\n new health \t policy  "
    assert normalize_text(raw) == "Government announces new health policy"


def test_compute_content_hash_deterministic():
    """Verify SHA-256 content hashing is deterministic and case/URL insensitive."""
    title = "New Aged Care Regulatory Framework"
    url = "https://www.health.gov.au/news/aged-care-reform"
    content = "The Commonwealth Government today released new standards."

    hash1 = compute_content_hash(title, url, content)
    hash2 = compute_content_hash(title, url, content)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length

    # URL with trailing slash or casing should produce same hash
    hash_alt_url = compute_content_hash(title, "HTTPS://WWW.HEALTH.GOV.AU/NEWS/AGED-CARE-REFORM/", content)
    assert hash1 == hash_alt_url

    # Different title or content should produce different hash
    hash_diff = compute_content_hash("Different Title", url, content)
    assert hash1 != hash_diff


def test_clean_html_text():
    """Verify clean_html_text strips HTML tags, decodes entities, and normalizes text."""
    html_snippet = "<p>The Minister for <strong>Health</strong> &amp; Aged Care announced &lt;new&gt; guidelines.</p>"
    cleaned = clean_html_text(html_snippet)
    assert cleaned == "The Minister for Health & Aged Care announced <new> guidelines."


def test_parse_feed_entry():
    """Verify parse_feed_entry correctly maps feedparser dictionary to FeedItem model."""
    entry = {
        "id": "item-001",
        "title": "Fast-Track Consenting Approvals Released",
        "link": "https://www.beehive.govt.nz/release/fast-track",
        "published": "Tue, 01 Sep 2026 09:30:00 +1200",
        "summary": "<p>A new list of projects for fast-track processing has been released.</p>",
        "content": [{"value": "<div>Full press release text here with extra details.</div>"}],
    }

    item = parse_feed_entry(
        entry=entry,
        source_id="beehive-releases",
        source_name="Beehive Ministerial Releases",
        jurisdiction="NZ",
    )

    assert isinstance(item, FeedItem)
    assert item.title == "Fast-Track Consenting Approvals Released"
    assert item.url == "https://www.beehive.govt.nz/release/fast-track"
    assert item.source_id == "beehive-releases"
    assert item.jurisdiction == "NZ"
    assert "Full press release text here with extra details." in item.raw_content
    assert item.summary == "A new list of projects for fast-track processing has been released."
    assert item.published_date.startswith("2026-09-01")
    assert len(item.content_hash) == 64
