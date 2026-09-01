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
        feed_url="https://www.beehive.govt.nz/rss/all",
        fixture_filename="nz_beehive_fixture.xml",
        description="Official executive announcements, policy launches, and regulatory initiatives from NZ Government Ministers.",
    ),
    SourceConfig(
        id="nz-parliament-bills",
        name="New Zealand Parliament - Bills and Laws",
        jurisdiction="NZ",
        feed_url="https://www.parliament.nz/en/pb/bills-and-laws/bills-proposed-laws/rss",
        fixture_filename="nz_parliament_fixture.xml",
        description="Newly introduced legislation, select committee calls for public submissions, and statutory amendments in NZ.",
    ),
    SourceConfig(
        id="au-ministers-releases",
        name="Australian Ministers Media Releases",
        jurisdiction="AU",
        feed_url="https://www.pmc.gov.au/news/rss.xml",
        fixture_filename="au_ministers_fixture.xml",
        description="Media releases, strategic reform announcements, and review appointments from Commonwealth Ministers.",
    ),
    SourceConfig(
        id="au-legislation-updates",
        name="Federal Register of Legislation Updates",
        jurisdiction="AU",
        feed_url="https://www.legislation.gov.au/rss/latest-acts",
        fixture_filename="au_legislation_fixture.xml",
        description="Enacted Commonwealth legislation, statutory instruments, and regulatory model standards.",
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
