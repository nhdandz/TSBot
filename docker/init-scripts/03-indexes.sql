-- =============================================================================
-- Performance Indexes for TSBot
-- Optimized for 50-100 concurrent users
-- =============================================================================

-- ── chat_history indexes ──────────────────────────────────────────────────

-- Hot path: fetch last 5 messages per session (called on EVERY chat request)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chat_history_session_time_desc
    ON chat_history(session_id, created_at DESC);

-- Feedback query: find messages by session + role + id (chat.py feedback endpoint)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chat_history_session_role_id
    ON chat_history(session_id, role, id DESC);

-- get_sessions window function: first user message per session
-- Partial index (role='user' only) → much smaller, faster
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chat_history_user_session_time
    ON chat_history(session_id, created_at ASC)
    WHERE role = 'user';

-- ── diem_chuan index ──────────────────────────────────────────────────────

-- SQL Agent filters: nam, gioi_tinh, khu_vuc — covering index includes join keys
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diem_chuan_filter_covering
    ON diem_chuan(nam, gioi_tinh, khu_vuc)
    INCLUDE (diem_chuan, chi_tieu, nganh_id, khoi_thi_id);

-- ── feedback index ────────────────────────────────────────────────────────

-- Lookup feedback by session
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_feedback_session
    ON feedback(session_id);

-- ── flagged_conversation ──────────────────────────────────────────────────

-- Admin review queue
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_flagged_status
    ON flagged_conversation(status, created_at DESC);
