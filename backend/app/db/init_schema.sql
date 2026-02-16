-- ============================================================
-- Arthronyx — PostgreSQL Schema
-- ============================================================

-- Extension for full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ── Documents Table ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS documents (
    id              SERIAL PRIMARY KEY,
    doi             VARCHAR(255) UNIQUE NOT NULL,
    title           TEXT NOT NULL,
    authors         TEXT[] DEFAULT '{}',
    year            INTEGER NOT NULL,
    journal         VARCHAR(500) DEFAULT '',
    study_type      VARCHAR(100) NOT NULL DEFAULT 'Narrative Review',
    evidence_level  VARCHAR(10) NOT NULL DEFAULT 'V',
    sample_size     INTEGER,
    subdomain       VARCHAR(100) DEFAULT 'General Orthopedics',
    country         VARCHAR(100) DEFAULT '',
    trial_phase     VARCHAR(50),
    abstract        TEXT DEFAULT '',
    full_text_hash  VARCHAR(64),
    source          VARCHAR(100) NOT NULL DEFAULT 'PubMed',
    indexed_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_doi ON documents (doi);
CREATE INDEX IF NOT EXISTS idx_documents_year ON documents (year);
CREATE INDEX IF NOT EXISTS idx_documents_study_type ON documents (study_type);
CREATE INDEX IF NOT EXISTS idx_documents_evidence_level ON documents (evidence_level);
CREATE INDEX IF NOT EXISTS idx_documents_subdomain ON documents (subdomain);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents (source);

-- Full-text search index on title + abstract
CREATE INDEX IF NOT EXISTS idx_documents_title_trgm
    ON documents USING gin (title gin_trgm_ops);

-- ── Document Chunks Table ────────────────────────────────────
CREATE TABLE IF NOT EXISTS document_chunks (
    id              SERIAL PRIMARY KEY,
    chunk_id        VARCHAR(255) UNIQUE NOT NULL,
    document_doi    VARCHAR(255) NOT NULL REFERENCES documents(doi) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL DEFAULT 0,
    text            TEXT NOT NULL,
    token_count     INTEGER DEFAULT 0,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_doi ON document_chunks (document_doi);

-- ── Audit Log Table ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    id              SERIAL PRIMARY KEY,
    query_id        VARCHAR(100) UNIQUE NOT NULL,
    query_text      TEXT NOT NULL,
    query_filters   JSONB DEFAULT '{}',
    response_json   JSONB,
    retrieved_dois  TEXT[] DEFAULT '{}',
    cited_dois      TEXT[] DEFAULT '{}',
    validation_pass BOOLEAN DEFAULT TRUE,
    client_ip       VARCHAR(45) DEFAULT '',
    user_agent      TEXT DEFAULT '',
    processing_ms   INTEGER DEFAULT 0,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_query_id ON audit_logs (query_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs (created_at DESC);

-- ── Ingestion Log Table ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS ingestion_logs (
    id              SERIAL PRIMARY KEY,
    source          VARCHAR(100) NOT NULL,
    query_used      TEXT DEFAULT '',
    documents_found INTEGER DEFAULT 0,
    documents_added INTEGER DEFAULT 0,
    errors          TEXT DEFAULT '',
    started_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at    TIMESTAMP WITH TIME ZONE
);

-- ── Update Trigger ───────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE TRIGGER update_documents_modtime
    BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();
