-- Database schema for Allen + Clarke BD Opportunity Radar

CREATE TABLE IF NOT EXISTS service_lines (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    keywords TEXT, -- JSON array
    case_studies TEXT, -- JSON array
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    jurisdiction TEXT NOT NULL, -- NZ, AU, ALL
    tier TEXT NOT NULL, -- Commonwealth, Ministry, Crown Entity, State/Territory, Local
    sector TEXT NOT NULL,
    key_divisions TEXT, -- JSON array
    past_engagements TEXT, -- JSON array
    relationship_notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scans (
    id TEXT PRIMARY KEY,
    content_hash TEXT UNIQUE NOT NULL,
    source_id TEXT NOT NULL,
    source_name TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    published_date TEXT,
    summary TEXT,
    raw_content TEXT,
    ingested_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'raw'
);

CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    scan_id TEXT,
    title TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    target_client_id TEXT,
    primary_service_line_id TEXT,
    verified_facts TEXT,
    strategic_interpretation TEXT,
    strategic_fit_score INTEGER DEFAULT 0,
    urgency_score INTEGER DEFAULT 0,
    budget_score INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,
    conversation_starter TEXT,
    target_contact_persona TEXT,
    status TEXT NOT NULL DEFAULT 'identified',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (scan_id) REFERENCES scans(id),
    FOREIGN KEY (target_client_id) REFERENCES clients(id),
    FOREIGN KEY (primary_service_line_id) REFERENCES service_lines(id)
);

CREATE INDEX IF NOT EXISTS idx_scans_content_hash ON scans(content_hash);
CREATE INDEX IF NOT EXISTS idx_scans_jurisdiction ON scans(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_scans_published_date ON scans(published_date);
CREATE INDEX IF NOT EXISTS idx_clients_jurisdiction ON clients(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_opportunities_score ON opportunities(total_score DESC);
