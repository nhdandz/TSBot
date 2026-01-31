-- =============================================================================
-- PostgreSQL Extensions for TSBot
-- =============================================================================

-- Vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Full-text search improvements
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Vietnamese text normalization (remove diacritics)
CREATE EXTENSION IF NOT EXISTS unaccent;

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
