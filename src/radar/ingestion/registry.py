"""Registry of authoritative government RSS/Atom feeds across NZ and AU."""

from typing import List, Optional
from pydantic import BaseModel


class SourceConfig(BaseModel):
    id: str
    name: str
    jurisdiction: str  # NZ, AU
    feed_url: str
    fixture_filename: str
    description: str


SOURCES: List[SourceConfig] = [
    SourceConfig(
        id="beehive-releases",
        name="Beehive Ministerial Releases",
        jurisdiction="NZ",
        feed_url="https://www.beehive.govt.nz/rss.xml",
        fixture_filename="nz_beehive_fixture.xml",
        description="Official executive announcements, policy launches, and regulatory initiatives from NZ Government Ministers.",
    ),
    SourceConfig(
        id="nz-parliament-bills",
        name="New Zealand Government Policy & Portfolio Releases",
        jurisdiction="NZ",
        feed_url="https://www.beehive.govt.nz/releases/feed",
        fixture_filename="nz_parliament_fixture.xml",
        description="Cabinet policy releases, portfolio announcements, and statutory initiatives in NZ.",
    ),
    SourceConfig(
        id="au-ministers-releases",
        name="Australian Health & Aged Care Policy Updates",
        jurisdiction="AU",
        feed_url="https://www.health.gov.au/news/rss.xml",
        fixture_filename="au_ministers_fixture.xml",
        description="Commonwealth health, aged care, and disability regulatory updates and policy consultations.",
    ),
    SourceConfig(
        id="au-legislation-updates",
        name="Australian Infrastructure & Regional Development Inquiries",
        jurisdiction="AU",
        feed_url="https://www.infrastructure.gov.au/rss.xml",
        fixture_filename="au_legislation_fixture.xml",
        description="Commonwealth infrastructure reviews, regional inquiries, and regulatory policy releases.",
    ),
]


def get_feed_sources(jurisdiction: Optional[str] = "ALL") -> List[SourceConfig]:
    """Returns feed sources filtered by jurisdiction (NZ, AU, or ALL)."""
    if not jurisdiction or jurisdiction == "ALL":
        return list(SOURCES)
    return [s for s in SOURCES if s.jurisdiction == jurisdiction.upper()]


def get_source_by_id(source_id: str) -> Optional[SourceConfig]:
    """Finds a feed source configuration by ID."""
    for s in SOURCES:
        if s.id == source_id:
            return s
    return None
