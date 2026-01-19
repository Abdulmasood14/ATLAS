-- ============================================================================
-- CHATBOT UI - DATABASE MIGRATIONS
-- ============================================================================
-- Purpose: Create tables for chat sessions, messages, feedback (RLHF), and exports
-- Database: financial_rag (existing)
-- Date: 2025-12-18
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLE 1: chat_sessions
-- ============================================================================
-- Purpose: Track user chat sessions with company context
-- ============================================================================

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255),  -- Optional user identification (for future auth)
    company_id VARCHAR(100),  -- Active company for this session
    company_name VARCHAR(255),  -- Company name for display
    created_at TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP DEFAULT NOW(),
    session_metadata JSONB DEFAULT '{}',  -- Browser info, IP, etc.
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for chat_sessions
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_chat_sessions_company_id ON chat_sessions(company_id);
CREATE INDEX idx_chat_sessions_created_at ON chat_sessions(created_at DESC);
CREATE INDEX idx_chat_sessions_is_active ON chat_sessions(is_active) WHERE is_active = TRUE;

-- ============================================================================
-- TABLE 2: chat_messages
-- ============================================================================
-- Purpose: Store all chat messages (user queries and assistant responses)
-- ============================================================================

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    query_metadata JSONB DEFAULT '{}',  -- Sources, chunks, retrieval info
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for chat_messages
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at DESC);
CREATE INDEX idx_chat_messages_role ON chat_messages(role);

-- ============================================================================
-- TABLE 3: feedback_responses (RLHF Data Collection)
-- ============================================================================
-- Purpose: Store user feedback on assistant responses for RLHF
-- This is the core table for Reinforcement Learning from Human Feedback
-- ============================================================================

CREATE TABLE IF NOT EXISTS feedback_responses (
    feedback_id SERIAL PRIMARY KEY,
    message_id INT NOT NULL REFERENCES chat_messages(message_id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,

    -- Core Query/Response Data
    user_query TEXT NOT NULL,
    assistant_response TEXT NOT NULL,

    -- Feedback Score (RLHF)
    feedback_score DECIMAL(2,1) NOT NULL CHECK (feedback_score IN (0.0, 0.5, 1.0)),
    -- 1.0 = Good (thumbs up)
    -- 0.5 = Medium (neutral)
    -- 0.0 = Bad (thumbs down)

    -- Context Information (for analysis)
    retrieved_chunks JSONB DEFAULT '[]',  -- Array of chunks used for this response
    model_used VARCHAR(100),  -- e.g., 'phi4:14b', 'gpt-oss:20b'
    retrieval_tier VARCHAR(50),  -- 'vector', 'keyword', 'hybrid'
    company_id VARCHAR(100),  -- Company being queried
    query_type VARCHAR(20),  -- 'objective', 'subjective', 'mixed'
    statement_type VARCHAR(50),  -- 'consolidated', 'standalone', NULL

    -- Metadata
    feedback_timestamp TIMESTAMP DEFAULT NOW(),
    review_status VARCHAR(20) DEFAULT 'pending' CHECK (review_status IN ('pending', 'reviewed', 'resolved', 'ignored')),
    reviewer_notes TEXT,
    reviewed_at TIMESTAMP,
    reviewed_by VARCHAR(255)
);

-- Indexes for feedback_responses
CREATE INDEX idx_feedback_session_id ON feedback_responses(session_id);
CREATE INDEX idx_feedback_message_id ON feedback_responses(message_id);
CREATE INDEX idx_feedback_score ON feedback_responses(feedback_score);
CREATE INDEX idx_feedback_review_status ON feedback_responses(review_status);
CREATE INDEX idx_feedback_timestamp ON feedback_responses(feedback_timestamp DESC);
CREATE INDEX idx_feedback_model_used ON feedback_responses(model_used);
CREATE INDEX idx_feedback_company_id ON feedback_responses(company_id);

-- Composite index for RLHF analysis (find bad/medium responses)
CREATE INDEX idx_feedback_score_review ON feedback_responses(feedback_score, review_status)
    WHERE feedback_score < 1.0;

-- ============================================================================
-- TABLE 4: query_exports
-- ============================================================================
-- Purpose: Track exported query history (JSON/CSV/Excel downloads)
-- ============================================================================

CREATE TABLE IF NOT EXISTS query_exports (
    export_id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(session_id) ON DELETE SET NULL,
    export_format VARCHAR(20) NOT NULL CHECK (export_format IN ('json', 'csv', 'xlsx')),
    file_path TEXT,  -- Path to generated export file
    file_size_bytes BIGINT,
    message_count INT,  -- Number of messages exported
    created_at TIMESTAMP DEFAULT NOW(),
    downloaded_at TIMESTAMP,
    export_metadata JSONB DEFAULT '{}'
);

-- Indexes for query_exports
CREATE INDEX idx_exports_session_id ON query_exports(session_id);
CREATE INDEX idx_exports_created_at ON query_exports(created_at DESC);
CREATE INDEX idx_exports_format ON query_exports(export_format);

-- ============================================================================
-- TABLE 5: company_uploads (Track PDF uploads)
-- ============================================================================
-- Purpose: Track PDF uploads and ingestion status
-- ============================================================================

CREATE TABLE IF NOT EXISTS company_uploads (
    upload_id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(session_id) ON DELETE SET NULL,
    company_id VARCHAR(100) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    fiscal_year VARCHAR(20),

    -- File info
    original_filename VARCHAR(500),
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT,

    -- Ingestion status
    upload_status VARCHAR(50) DEFAULT 'pending' CHECK (upload_status IN ('pending', 'processing', 'completed', 'failed')),
    ingestion_started_at TIMESTAMP,
    ingestion_completed_at TIMESTAMP,
    chunks_created INT,
    chunks_stored INT,
    error_message TEXT,

    -- Metadata
    uploaded_at TIMESTAMP DEFAULT NOW(),
    uploaded_by VARCHAR(255)
);

-- Indexes for company_uploads
CREATE INDEX idx_uploads_company_id ON company_uploads(company_id);
CREATE INDEX idx_uploads_session_id ON company_uploads(session_id);
CREATE INDEX idx_uploads_status ON company_uploads(upload_status);
CREATE INDEX idx_uploads_timestamp ON company_uploads(uploaded_at DESC);

-- ============================================================================
-- VIEWS FOR ANALYTICS
-- ============================================================================

-- View: Feedback summary by company
CREATE OR REPLACE VIEW v_feedback_summary_by_company AS
SELECT
    company_id,
    COUNT(*) as total_responses,
    SUM(CASE WHEN feedback_score = 1.0 THEN 1 ELSE 0 END) as good_count,
    SUM(CASE WHEN feedback_score = 0.5 THEN 1 ELSE 0 END) as medium_count,
    SUM(CASE WHEN feedback_score = 0.0 THEN 1 ELSE 0 END) as bad_count,
    ROUND(AVG(feedback_score), 2) as avg_score,
    COUNT(DISTINCT session_id) as unique_sessions
FROM feedback_responses
GROUP BY company_id
ORDER BY total_responses DESC;

-- View: Feedback summary by model
CREATE OR REPLACE VIEW v_feedback_summary_by_model AS
SELECT
    model_used,
    COUNT(*) as total_responses,
    SUM(CASE WHEN feedback_score = 1.0 THEN 1 ELSE 0 END) as good_count,
    SUM(CASE WHEN feedback_score = 0.5 THEN 1 ELSE 0 END) as medium_count,
    SUM(CASE WHEN feedback_score = 0.0 THEN 1 ELSE 0 END) as bad_count,
    ROUND(AVG(feedback_score), 2) as avg_score
FROM feedback_responses
GROUP BY model_used
ORDER BY total_responses DESC;

-- View: Recent bad/medium feedback (for review)
CREATE OR REPLACE VIEW v_feedback_needs_review AS
SELECT
    f.feedback_id,
    f.feedback_score,
    f.user_query,
    f.assistant_response,
    f.model_used,
    f.company_id,
    f.feedback_timestamp,
    f.review_status,
    cs.company_name
FROM feedback_responses f
JOIN chat_sessions cs ON f.session_id = cs.session_id
WHERE f.feedback_score < 1.0
  AND f.review_status = 'pending'
ORDER BY f.feedback_timestamp DESC;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function: Update session last_activity on message insert
CREATE OR REPLACE FUNCTION update_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE chat_sessions
    SET last_activity = NOW()
    WHERE session_id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update session activity
DROP TRIGGER IF EXISTS trg_update_session_activity ON chat_messages;
CREATE TRIGGER trg_update_session_activity
AFTER INSERT ON chat_messages
FOR EACH ROW
EXECUTE FUNCTION update_session_activity();

-- Function: Get session message count
CREATE OR REPLACE FUNCTION get_session_message_count(p_session_id UUID)
RETURNS INT AS $$
BEGIN
    RETURN (SELECT COUNT(*) FROM chat_messages WHERE session_id = p_session_id);
END;
$$ LANGUAGE plpgsql;

-- Function: Get session feedback summary
CREATE OR REPLACE FUNCTION get_session_feedback_summary(p_session_id UUID)
RETURNS TABLE(
    good_count BIGINT,
    medium_count BIGINT,
    bad_count BIGINT,
    avg_score NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        SUM(CASE WHEN feedback_score = 1.0 THEN 1 ELSE 0 END) as good_count,
        SUM(CASE WHEN feedback_score = 0.5 THEN 1 ELSE 0 END) as medium_count,
        SUM(CASE WHEN feedback_score = 0.0 THEN 1 ELSE 0 END) as bad_count,
        ROUND(AVG(feedback_score), 2) as avg_score
    FROM feedback_responses
    WHERE session_id = p_session_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================================================

-- Uncomment to insert sample data
-- INSERT INTO chat_sessions (user_id, company_id, company_name)
-- VALUES ('test_user', 'PHX_FXD', 'Phoenix Mills');

-- ============================================================================
-- GRANTS (Optional - adjust based on your PostgreSQL user setup)
-- ============================================================================

-- Grant permissions to postgres user (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify tables were created
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name IN ('chat_sessions', 'chat_messages', 'feedback_responses', 'query_exports', 'company_uploads')
ORDER BY table_name;

-- ============================================================================
-- END OF MIGRATIONS
-- ============================================================================
