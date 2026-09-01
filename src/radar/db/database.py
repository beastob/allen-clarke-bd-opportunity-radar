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

    # --- Helper row converters ---

    @staticmethod
    def _row_to_service_line(row: sqlite3.Row) -> ServiceLine:
        return ServiceLine(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            keywords=json.loads(row["keywords"]) if row["keywords"] else [],
            case_studies=json.loads(row["case_studies"]) if row["case_studies"] else [],
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_client(row: sqlite3.Row) -> Client:
        return Client(
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

    @staticmethod
    def _row_to_scan(row: sqlite3.Row) -> ScanRecord:
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

    @staticmethod
    def _row_to_opportunity(row: sqlite3.Row) -> OpportunityRecord:
        return OpportunityRecord(
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
            return [self._row_to_service_line(row) for row in rows]

    def get_service_line_by_id(self, service_line_id: str) -> Optional[ServiceLine]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM service_lines WHERE id = ?;", (service_line_id,)).fetchone()
            return self._row_to_service_line(row) if row else None

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

            return [self._row_to_client(row) for row in rows]

    def get_client_by_id(self, client_id: str) -> Optional[Client]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM clients WHERE id = ?;", (client_id,)).fetchone()
            return self._row_to_client(row) if row else None

    def get_client_by_name(self, client_name: str) -> Optional[Client]:
        with self.get_connection() as conn:
            cleaned = client_name.strip()
            # 1. Try exact id match
            row = conn.execute("SELECT * FROM clients WHERE LOWER(id) = LOWER(?);", (cleaned,)).fetchone()
            if not row:
                # 2. Try exact name match (case-insensitive)
                row = conn.execute("SELECT * FROM clients WHERE LOWER(name) = LOWER(?);", (cleaned,)).fetchone()
            if not row:
                # 3. Try substring name or id match
                search_pattern = f"%{cleaned}%"
                row = conn.execute(
                    "SELECT * FROM clients WHERE name LIKE ? OR id LIKE ? ORDER BY LENGTH(name) ASC LIMIT 1;",
                    (search_pattern, search_pattern),
                ).fetchone()
            if not row:
                # 4. Try multi-token match (all words match name or id)
                tokens = [t.strip() for t in cleaned.split() if t.strip()]
                if len(tokens) > 1:
                    conditions = []
                    token_params = []
                    for t in tokens:
                        conditions.append("(name LIKE ? OR id LIKE ?)")
                        token_params.extend([f"%{t}%", f"%{t}%"])
                    query = f"SELECT * FROM clients WHERE {' AND '.join(conditions)} ORDER BY LENGTH(name) ASC LIMIT 1;"
                    row = conn.execute(query, token_params).fetchone()

            return self._row_to_client(row) if row else None

    def update_client_relationship_notes(
        self,
        client_id: str,
        relationship_notes: str,
        append: bool = True,
    ) -> Optional[Client]:
        client = self.get_client_by_id(client_id) or self.get_client_by_name(client_id)
        if not client:
            return None

        from datetime import datetime, timezone
        now_str = datetime.now(timezone.utc).isoformat()

        if append and client.relationship_notes:
            updated_notes = f"{client.relationship_notes}\n[{now_str}] {relationship_notes}"
        else:
            updated_notes = relationship_notes

        client.relationship_notes = updated_notes
        client.updated_at = now_str

        self.save_client(client)
        return client

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
            return self._row_to_scan(row) if row else None

    def get_scans(self, jurisdiction: Optional[str] = None, limit: int = 100) -> List[ScanRecord]:
        with self.get_connection() as conn:
            if jurisdiction and jurisdiction != "ALL":
                query = "SELECT * FROM scans WHERE jurisdiction = ? ORDER BY published_date DESC LIMIT ?;"
                rows = conn.execute(query, (jurisdiction, limit)).fetchall()
            else:
                query = "SELECT * FROM scans ORDER BY published_date DESC LIMIT ?;"
                rows = conn.execute(query, (limit,)).fetchall()

            return [self._row_to_scan(row) for row in rows]

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

    def get_opportunity_by_id(self, opportunity_id: str) -> Optional[OpportunityRecord]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM opportunities WHERE id = ?;", (opportunity_id,)).fetchone()
            return self._row_to_opportunity(row) if row else None

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
            return [self._row_to_opportunity(row) for row in rows]

    def query_opportunities(
        self,
        client: Optional[str] = None,
        sector: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        min_score: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Queries opportunities with multi-field filtering and joins client & service line metadata."""
        with self.get_connection() as conn:
            params: List[Any] = [min_score]
            where_clauses = ["o.total_score >= ?"]

            if jurisdiction and jurisdiction != "ALL":
                where_clauses.append("o.jurisdiction = ?")
                params.append(jurisdiction)

            if client:
                where_clauses.append("(c.id = ? OR c.name LIKE ?)")
                params.extend([client, f"%{client}%"])

            if sector:
                where_clauses.append("c.sector LIKE ?")
                params.append(f"%{sector}%")

            query = f"""
                SELECT
                    o.id,
                    o.scan_id,
                    o.title,
                    o.jurisdiction,
                    o.target_client_id,
                    c.name AS client_name,
                    c.sector AS client_sector,
                    c.tier AS client_tier,
                    o.primary_service_line_id,
                    sl.name AS service_line_name,
                    o.verified_facts,
                    o.strategic_interpretation,
                    o.strategic_fit_score,
                    o.urgency_score,
                    o.budget_score,
                    o.total_score,
                    o.conversation_starter,
                    o.target_contact_persona,
                    o.status,
                    o.created_at,
                    o.updated_at
                FROM opportunities o
                LEFT JOIN clients c ON o.target_client_id = c.id
                LEFT JOIN service_lines sl ON o.primary_service_line_id = sl.id
                WHERE {' AND '.join(where_clauses)}
                ORDER BY o.total_score DESC
                LIMIT ?;
            """
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [
                {
                    "id": row["id"],
                    "scan_id": row["scan_id"],
                    "title": row["title"],
                    "jurisdiction": row["jurisdiction"],
                    "target_client_id": row["target_client_id"],
                    "client_name": row["client_name"] or "Unknown Client",
                    "client_sector": row["client_sector"] or "General Public Sector",
                    "client_tier": row["client_tier"] or "Other",
                    "primary_service_line_id": row["primary_service_line_id"],
                    "service_line_name": row["service_line_name"] or "Policy & Strategy Advisory",
                    "verified_facts": row["verified_facts"] or "",
                    "strategic_interpretation": row["strategic_interpretation"] or "",
                    "strategic_fit_score": row["strategic_fit_score"],
                    "urgency_score": row["urgency_score"],
                    "budget_score": row["budget_score"],
                    "total_score": row["total_score"],
                    "conversation_starter": row["conversation_starter"] or "",
                    "target_contact_persona": row["target_contact_persona"] or "",
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
                for row in rows
            ]

