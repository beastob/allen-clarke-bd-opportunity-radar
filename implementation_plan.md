# Implementation Plan: Knowledge Base & Government Feed Ingestion Engine (Issue #2)

## Overview
This implementation establishes the data foundation and ingestion layer for the Allen + Clarke Business Development Opportunity Radar. It initializes an embedded SQLite relational database, seeds authentic Allen + Clarke consulting service lines and New Zealand & Australian public sector client registries (enriched with authentic case studies from the Allen + Clarke website and resource hub), and implements a robust government feed ingestion engine with SHA-256 deduplication, jurisdiction filtering, and offline fallback fixtures.

---

## User Review Required

> [!IMPORTANT]
> **Proposed Architectural Seams**:
> 1. **Database & Knowledge Base Seam (`src/radar/db/`)**: Schema initialization and idempotent seeding of A+C practice lines and NZ/AU client directory.
> 2. **Content Hashing & Normalization Seam (`src/radar/ingestion/hasher.py`, `src/radar/ingestion/parser.py`)**: Deterministic SHA-256 hashing and HTML/RSS normalization.
> 3. **Feed Fetcher & Fixture Seam (`src/radar/ingestion/fetcher.py`)**: RSS/Atom retrieval with automatic offline fallback to curated XML fixtures.
> 4. **Ingestion Engine & Deduplication Seam (`src/radar/ingestion/engine.py`)**: Full orchestration saving to SQLite with duplicate suppression.

---

## Proposed Changes

### 1. Data Models & SQLite Knowledge Base (`src/radar/db/`)

#### [NEW] [models.py](file:///C:/Projects/allen-clarke-bd-opportunity-radar-worktrees/2-kb-and-gov-feed-ingestion/src/radar/models.py)
- Pydantic models: `ServiceLine`, `Client`, `FeedItem`, `ScanRecord`, `OpportunityRecord`, `IngestionResult`.

#### [NEW] [schema.sql](file:///C:/Projects/allen-clarke-bd-opportunity-radar-worktrees/2-kb-and-gov-feed-ingestion/src/radar/db/schema.sql)
- SQLite schema for `service_lines`, `clients`, `scans`, and `opportunities`.
- Appropriate indexes on `scans(content_hash)`, `scans(jurisdiction)`, `scans(published_date)`, `clients(jurisdiction)`, `opportunities(total_score)`.

#### [NEW] [database.py](file:///C:/Projects/allen-clarke-bd-opportunity-radar-worktrees/2-kb-and-gov-feed-ingestion/src/radar/db/database.py)
- `DatabaseManager`: Connection handling, migration/schema application, queries for service lines, clients, scans, and opportunities.

#### [NEW] [seed.py](file:///C:/Projects/allen-clarke-bd-opportunity-radar-worktrees/2-kb-and-gov-feed-ingestion/src/radar/db/seed.py)
- `seed_database(db: DatabaseManager, force: bool = False)`: Reads JSON seed data and idempotently populates SQLite.

---

### 2. Knowledge Base Seed Data & Fallback Fixtures (`src/radar/data/`)

#### [NEW] [seed_service_lines.json](file:///C:/Projects/allen-clarke-bd-opportunity-radar-worktrees/2-kb-and-gov-feed-ingestion/src/radar/data/seed_service_lines.json)
- Sourced directly from Allen + Clarke website (`/how-we-can-help` and `/resource-hub`):
  - **Policy + Regulation**: Regulatory design, legislative reform, bill submissions analysis (e.g. Therapeutics Products Bill, Fast-Track Approvals Bill).
  - **Evaluation + Review**: Program evaluation, realist evaluation, M&E frameworks (e.g. Victorian Disability Liaison Officer Program, Australia's Cancer Plan).
  - **Strategy + Planning**: Operating model design, strategic planning, whole-of-system design.
  - **Business Change & Public Sector Governance / Transformation + Change**: Public sector reform, change management.
  - **Kaupapa Māori & Pacific Policy**: Te Tiriti / Treaty analysis (e.g. 292k submissions on Treaty Principles Bill), Pacific development cooperation (Tuvalu Program, Te Pātuitanga fisheries review).
  - **Performance + Optimisation**: Efficiency reviews, service design.
  - **Risk Management**: Regulatory risk frameworks.
  - **Secretariat + Service Delivery**: Independent reviews, stakeholder panels.

#### [NEW] [seed_clients.json](file:///C:/Projects/allen-clarke-bd-opportunity-radar-worktrees/2-kb-and-gov-feed-ingestion/src/radar/data/seed_clients.json)
- Structured profiles for major NZ and AU government departments:
  - **NZ**: Ministry of Health (Manatū Hauora), Ministry of Justice, Ministry for Primary Industries (MPI), Ministry for the Environment (MfE), Ministry of Foreign Affairs and Trade (MFAT), Te Puni Kōkiri, Oranga Tamariki, ACC, Te Whatu Ora (Health NZ), Treasury NZ.
  - **AU Commonwealth**: Department of Health and Aged Care, Department of Social Services (DSS), Attorney-General's Department, Department of the Prime Minister and Cabinet (PM&C), NDIS Quality and Safeguards Commission, Cancer Australia, DCCEEW.
  - **AU State**: Victorian Department of Health, NSW Health, Queensland Health, Victorian Department of Premier and Cabinet.

#### [NEW] [fixtures/](file:///C:/Projects/allen-clarke-bd-opportunity-radar-worktrees/2-kb-and-gov-feed-ingestion/src/radar/data/fixtures/)
- Curated RSS/Atom XML fixtures for offline demo verification:
  - `nz_beehive_fixture.xml`
  - `nz_parliament_fixture.xml`
  - `au_ministers_fixture.xml`
  - `au_legislation_fixture.xml`

---

### 3. Government Feed Ingestion Engine (`src/radar/ingestion/`)

#### [NEW] [registry.py](file:///C:/Projects/allen-clarke-bd-opportunity-radar-worktrees/2-kb-and-gov-feed-ingestion/src/radar/ingestion/registry.py)
- Configuration of official NZ and AU government RSS/Atom endpoints.

#### [NEW] [hasher.py](file:///C:/Projects/allen-clarke-bd-opportunity-radar-worktrees/2-kb-and-gov-feed-ingestion/src/radar/ingestion/hasher.py)
- Canonical text normalization and SHA-256 content hashing.

#### [NEW] [parser.py](file:///C:/Projects/allen-clarke-bd-opportunity-radar-worktrees/2-kb-and-gov-feed-ingestion/src/radar/ingestion/parser.py)
- RSS/Atom XML parser using `feedparser` and `beautifulsoup4` for HTML tag sanitization.

#### [NEW] [fetcher.py](file:///C:/Projects/allen-clarke-bd-opportunity-radar-worktrees/2-kb-and-gov-feed-ingestion/src/radar/ingestion/fetcher.py)
- HTTP fetcher with timeout and automated fallback to curated fixtures when offline or in fixture mode.

#### [NEW] [engine.py](file:///C:/Projects/allen-clarke-bd-opportunity-radar-worktrees/2-kb-and-gov-feed-ingestion/src/radar/ingestion/engine.py)
- `IngestionEngine`: Coordinates fetch $\rightarrow$ parse $\rightarrow$ hash $\rightarrow$ deduplicate against SQLite $\rightarrow$ insert into `scans`.

---

## Verification Plan

### Automated Tests
Run via pytest in the worktree virtual environment:
- `pytest tests/test_db.py` (Seam 1: Schema creation, CRUD operations, seeding idempotency)
- `pytest tests/test_hasher.py` (Seam 2: SHA-256 deterministic hashing, normalization)
- `pytest tests/test_fetcher.py` (Seam 3: RSS parsing, jurisdiction filtering, offline fixture fallback)
- `pytest tests/test_ingestion_engine.py` (Seam 4: End-to-end ingestion and deduplication idempotency)
- `pytest --cov=src` (Full suite verification with coverage)

### Manual Verification
- Execute a test script initializing `radar.db`, seeding the database, running a scan against curated fixtures and live feeds, verifying deduplication by running consecutive scans, and inspecting SQLite table contents.
