"""SQLite Database Manager for Allen + Clarke Opportunity Radar."""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional
from radar.models import ServiceLine, Client, ScanRecord, OpportunityRecord


class DatabaseManager:
    """Manages SQLite storage for the Allen + Clarke Knowledge Base."""

    def __init__(self, db_path: str = "radar.db"):
        self.db_path = db_path
        self._ensure_dir()

    def _ensure_dir(self):
        db_file = Path(self.db_path)
        if db_file.parent and str(db_file.parent) != ".":
            db_file.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """Context manager yielding an SQLite connection with WAL and Row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self):
        """Applies schema.sql to the database."""
        schema_path = Path(__file__).parent / "schema.sql"
        schema_sql = schema_path.read_text(encoding="utf-8")
        with self.get_connection() as conn:
            conn.executescript(schema_sql)

    # --- Service Lines ---

    def save_service_line(self, service_line: ServiceLine):
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO service_lines (id, name, description, keywords, case_studies, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    keywords = excluded.keywords,
                    case_studies = excluded.case_studies;
                """,
                (
                    service_line.id,
                    service_line.name,
                    service_line.description,
                    json.dumps(service_line.keywords),
                    json.dumps(service_line.case_studies),
                    service_line.created_at,
                ),
            )

    def get_service_lines(self) -> List[ServiceLine]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM service_lines ORDER BY name ASC;").fetchall()
            return [
                ServiceLine(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    keywords=json.loads(row["keywords"]) if row["keywords"] else [],
                    case_studies=json.loads(row["case_studies"]) if row["case_studies"] else [],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    # --- Clients ---

    def save_client(self, client: Client):
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO clients (id, name, jurisdiction, tier, sector, key_divisions, past_engagements, relationship_notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    jurisdiction = excluded.jurisdiction,
                    tier = excluded.tier,
                    sector = excluded.sector,
                    key_divisions = excluded.key_divisions,
                    past_engagements = excluded.past_engagements,
                    relationship_notes = excluded.relationship_notes,
                    updated_at = excluded.updated_at;
                """,
                (
                    client.id,
                    client.name,
                    client.jurisdiction,
                    client.tier,
                    client.sector,
                    json.dumps(client.key_divisions),
                    json.dumps(client.past_engagements),
                    client.relationship_notes or "",
                    client.created_at,
                    client.updated_at,
                ),
            )

    def get_clients(self, jurisdiction: Optional[str] = None) -> List[Client]:
        with self.get_connection() as conn:
            if jurisdiction and jurisdiction != "ALL":
                query = "SELECT * FROM clients WHERE jurisdiction = ? OR jurisdiction = 'ALL' ORDER BY name ASC;"
                rows = conn.execute(query, (jurisdiction,)).fetchall()
            else:
                query = "SELECT * FROM clients ORDER BY name ASC;"
                rows = conn.execute(query).fetchall()

            return [
                Client(
                    id=row["id"],
                    name=row["name"],
                    jurisdiction=row["jurisdiction"],
                    tier=row["tier"],
                    sector=row["sector"],
                    key_divisions=json.loads(row["key_divisions"]) if row["key_divisions"] else [],
                    past_engagements=json.loads(row["past_engagements"]) if row["past_engagements"] else [],
                    relationship_notes=row["relationship_notes"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    # --- Scans ---

    def has_content_hash(self, content_hash: str) -> bool:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM scans WHERE content_hash = ? LIMIT 1;",
                (content_hash,),
            ).fetchone()
            return row is not None

    def save_scan(self, scan: ScanRecord):
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO scans (id, content_hash, source_id, source_name, jurisdiction, title, url, published_date, summary, raw_content, ingested_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(content_hash) DO UPDATE SET
                    status = excluded.status;
                """,
                (
                    scan.id,
                    scan.content_hash,
                    scan.source_id,
                    scan.source_name,
                    scan.jurisdiction,
                    scan.title,
                    scan.url,
                    scan.published_date,
                    scan.summary,
                    scan.raw_content,
                    scan.ingested_at,
                    scan.status,
                ),
            )

    def get_scan_by_id(self, scan_id: str) -> Optional[ScanRecord]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM scans WHERE id = ?;", (scan_id,)).fetchone()
            if not row:
                return None
            return ScanRecord(
                id=row["id"],
                content_hash=row["content_hash"],
                source_id=row["source_id"],
                source_name=row["source_name"],
                jurisdiction=row["jurisdiction"],
                title=row["title"],
                url=row["url"],
                published_date=row["published_date"],
                summary=row["summary"],
                raw_content=row["raw_content"],
                ingested_at=row["ingested_at"],
                status=row["status"],
            )

    def get_scans(self, jurisdiction: Optional[str] = None, limit: int = 100) -> List[ScanRecord]:
        with self.get_connection() as conn:
            if jurisdiction and jurisdiction != "ALL":
                query = "SELECT * FROM scans WHERE jurisdiction = ? ORDER BY published_date DESC LIMIT ?;"
                rows = conn.execute(query, (jurisdiction, limit)).fetchall()
            else:
                query = "SELECT * FROM scans ORDER BY published_date DESC LIMIT ?;"
                rows = conn.execute(query, (limit,)).fetchall()

            return [
                ScanRecord(
                    id=row["id"],
                    content_hash=row["content_hash"],
                    source_id=row["source_id"],
                    source_name=row["source_name"],
                    jurisdiction=row["jurisdiction"],
                    title=row["title"],
                    url=row["url"],
                    published_date=row["published_date"],
                    summary=row["summary"],
                    raw_content=row["raw_content"],
                    ingested_at=row["ingested_at"],
                    status=row["status"],
                )
                for row in rows
            ]

    # --- Opportunities ---

    def save_opportunity(self, opp: OpportunityRecord):
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO opportunities (
                    id, scan_id, title, jurisdiction, target_client_id, primary_service_line_id,
                    verified_facts, strategic_interpretation, strategic_fit_score, urgency_score,
                    budget_score, total_score, conversation_starter, target_contact_persona,
                    status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    jurisdiction = excluded.jurisdiction,
                    target_client_id = excluded.target_client_id,
                    primary_service_line_id = excluded.primary_service_line_id,
                    verified_facts = excluded.verified_facts,
                    strategic_interpretation = excluded.strategic_interpretation,
                    strategic_fit_score = excluded.strategic_fit_score,
                    urgency_score = excluded.urgency_score,
                    budget_score = excluded.budget_score,
                    total_score = excluded.total_score,
                    conversation_starter = excluded.conversation_starter,
                    target_contact_persona = excluded.target_contact_persona,
                    status = excluded.status,
                    updated_at = excluded.updated_at;
                """,
                (
                    opp.id,
                    opp.scan_id,
                    opp.title,
                    opp.jurisdiction,
                    opp.target_client_id,
                    opp.primary_service_line_id,
                    opp.verified_facts,
                    opp.strategic_interpretation,
                    opp.strategic_fit_score,
                    opp.urgency_score,
                    opp.budget_score,
                    opp.total_score,
                    opp.conversation_starter,
                    opp.target_contact_persona,
                    opp.status,
                    opp.created_at,
                    opp.updated_at,
                ),
            )

    def get_opportunities(
        self,
        jurisdiction: Optional[str] = None,
        min_score: int = 0,
        limit: int = 50,
    ) -> List[OpportunityRecord]:
        with self.get_connection() as conn:
            params: List[Any] = [min_score]
            where_clauses = ["total_score >= ?"]
            if jurisdiction and jurisdiction != "ALL":
                where_clauses.append("jurisdiction = ?")
                params.append(jurisdiction)

            query = f"SELECT * FROM opportunities WHERE {' AND '.join(where_clauses)} ORDER BY total_score DESC LIMIT ?;"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [
                OpportunityRecord(
                    id=row["id"],
                    scan_id=row["scan_id"],
                    title=row["title"],
                    jurisdiction=row["jurisdiction"],
                    target_client_id=row["target_client_id"],
                    primary_service_line_id=row["primary_service_line_id"],
                    verified_facts=row["verified_facts"] or "",
                    strategic_interpretation=row["strategic_interpretation"] or "",
                    strategic_fit_score=row["strategic_fit_score"],
                    urgency_score=row["urgency_score"],
                    budget_score=row["budget_score"],
                    total_score=row["total_score"],
                    conversation_starter=row["conversation_starter"] or "",
                    target_contact_persona=row["target_contact_persona"] or "",
                    status=row["status"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]
