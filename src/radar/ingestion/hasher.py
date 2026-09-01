"""Content normalization and SHA-256 hashing for deduplication."""

import hashlib
import re
from urllib.parse import urlparse, urlunparse


from typing import Optional


def normalize_text(text: Optional[str] = "") -> str:
    """Normalizes string by stripping leading/trailing whitespace and collapsing internal spaces."""
    if not text:
        return ""
    # Collapse multiple whitespace characters into single space
    return re.sub(r"\s+", " ", str(text)).strip()


def normalize_url(url: str) -> str:
    """Normalizes URL for canonical comparison."""
    if not url:
        return ""
    parsed = urlparse(url.strip().lower())
    scheme = parsed.scheme
    netloc = parsed.netloc
    path = parsed.path.rstrip("/")
    # Filter out utm_* tracking parameters
    query_parts = []
    if parsed.query:
        for q in parsed.query.split("&"):
            if not q.lower().startswith(("utm_", "fbclid", "gclid")):
                query_parts.append(q)
    query = "&".join(query_parts)

    return urlunparse((scheme, netloc, path, parsed.params, query, ""))


def compute_content_hash(title: str, url: str, content: str = "") -> str:
    """Computes a deterministic SHA-256 hex digest for a policy feed item."""
    norm_title = normalize_text(title).lower()
    norm_url = normalize_url(url)
    norm_content = normalize_text(content).lower()

    payload = f"title:{norm_title}|url:{norm_url}|content:{norm_content}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
