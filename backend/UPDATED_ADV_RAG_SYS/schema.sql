-- Financial RAG V2 - PostgreSQL Schema
-- Optimized for hybrid retrieval (Vector + Keyword + Classification)

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS financial_metrics_v2 CASCADE;
DROP TABLE IF EXISTS document_chunks_v2 CASCADE;

-- Main document chunks table
CREATE TABLE document_chunks_v2 (
    -- Primary key
    chunk_id TEXT PRIMARY KEY,

    -- Company metadata
    company_id TEXT NOT NULL,
    company_name TEXT,
    fiscal_year TEXT,

    -- Chunk content
    chunk_text TEXT NOT NULL,
    chunk_type TEXT NOT NULL, -- 'table', 'paragraph', 'list', 'heading'

    -- Multi-label classification
    section_types TEXT[], -- ['balance_sheet', 'fair_value', 'notes']
    note_number TEXT, -- 'Note 12', 'Note 5.3', etc.
    statement_type TEXT, -- 'standalone', 'consolidated', 'both'

    -- Source tracking
    page_numbers INTEGER[],
    source_pdf TEXT,

    -- Additional metadata (JSONB for flexibility)
    metadata JSONB,

    -- Embeddings (BGE-M3: 1024 dimensions)
    embedding vector(1024),

    -- Full-text search vector (for GIN index)
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english',
            coalesce(chunk_text, '') || ' ' ||
            coalesce(company_name, '') || ' ' ||
            coalesce(note_number, '')
        )
    ) STORED,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Financial metrics extracted from chunks
CREATE TABLE financial_metrics_v2 (
    metric_id SERIAL PRIMARY KEY,

    -- Company identification
    company_id TEXT NOT NULL,
    company_name TEXT,

    -- Metric details
    metric_name TEXT NOT NULL, -- 'investment_property', 'revenue', etc.
    metric_value NUMERIC,
    unit TEXT, -- 'crores', 'lakhs', 'millions', etc.
    fiscal_year TEXT,
    period TEXT, -- 'March 31, 2025'
    statement_type TEXT, -- 'standalone', 'consolidated'

    -- Source tracking
    source_chunk_id TEXT REFERENCES document_chunks_v2(chunk_id) ON DELETE CASCADE,
    source_section TEXT,
    note_reference TEXT,
    page_number INTEGER,

    -- Context for LLM extraction
    context_text TEXT,

    -- Additional metadata
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- 1. HNSW INDEX for fast vector similarity search (BGE-M3 embeddings)
CREATE INDEX idx_chunks_embedding_hnsw
ON document_chunks_v2
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 2. GIN INDEX for fast full-text keyword search (FALLBACK)
CREATE INDEX idx_chunks_search_vector_gin
ON document_chunks_v2
USING gin(search_vector);

-- 3. B-TREE INDEXES for filtering
CREATE INDEX idx_chunks_company ON document_chunks_v2(company_id);
CREATE INDEX idx_chunks_chunk_type ON document_chunks_v2(chunk_type);
CREATE INDEX idx_chunks_statement_type ON document_chunks_v2(statement_type);
CREATE INDEX idx_chunks_note_number ON document_chunks_v2(note_number);

-- 4. GIN INDEX for array column (section_types)
CREATE INDEX idx_chunks_section_types_gin
ON document_chunks_v2
USING gin(section_types);

-- 5. INDEXES for financial_metrics_v2
CREATE INDEX idx_metrics_company_metric ON financial_metrics_v2(company_id, metric_name);
CREATE INDEX idx_metrics_source_chunk ON financial_metrics_v2(source_chunk_id);
CREATE INDEX idx_metrics_fiscal_year ON financial_metrics_v2(fiscal_year);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER update_document_chunks_updated_at
BEFORE UPDATE ON document_chunks_v2
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Chunks with Fair Value + Investment Property
CREATE OR REPLACE VIEW fair_value_chunks AS
SELECT
    chunk_id,
    company_id,
    company_name,
    chunk_text,
    chunk_type,
    page_numbers,
    note_number
FROM document_chunks_v2
WHERE
    'fair_value' = ANY(section_types) OR
    'investment_property' = ANY(section_types);

-- View: All Notes sections
CREATE OR REPLACE VIEW notes_chunks AS
SELECT
    chunk_id,
    company_id,
    company_name,
    chunk_text,
    chunk_type,
    note_number,
    page_numbers
FROM document_chunks_v2
WHERE
    'notes' = ANY(section_types) OR
    note_number IS NOT NULL
ORDER BY
    company_id,
    note_number;

-- ============================================================================
-- SAMPLE QUERIES (Documentation)
-- ============================================================================

-- Query 1: Vector similarity search with filters
-- SELECT chunk_id, chunk_text, 1 - (embedding <=> '[0.1, 0.2, ...]'::vector) AS similarity
-- FROM document_chunks_v2
-- WHERE company_id = 'PHX_FXD'
--   AND 'fair_value' = ANY(section_types)
-- ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
-- LIMIT 10;

-- Query 2: Keyword search (FALLBACK)
-- SELECT chunk_id, chunk_text, ts_rank(search_vector, query) AS rank
-- FROM document_chunks_v2, to_tsquery('english', 'fair & value & investment & property') query
-- WHERE company_id = 'PHX_FXD'
--   AND search_vector @@ query
-- ORDER BY rank DESC
-- LIMIT 10;

-- Query 3: Get all chunks from a specific Note
-- SELECT chunk_id, chunk_text, page_numbers
-- FROM document_chunks_v2
-- WHERE company_id = 'PHX_FXD'
--   AND note_number = 'Note 12'
-- ORDER BY page_numbers[1];

-- ============================================================================
-- STATISTICS
-- ============================================================================

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON document_chunks_v2 TO your_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON financial_metrics_v2 TO your_user;

-- Analyze tables for query planner
ANALYZE document_chunks_v2;
ANALYZE financial_metrics_v2;

-- Show table sizes
-- SELECT
--     schemaname,
--     tablename,
--     pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
-- FROM pg_tables
-- WHERE tablename IN ('document_chunks_v2', 'financial_metrics_v2');
