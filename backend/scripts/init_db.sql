-- ============================================================
-- JobIntel MVP — init_db.sql
-- Jalankan sekali di Supabase SQL Editor.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- ---------- ENUMs ----------
CREATE TYPE source_enum AS ENUM ('remoteok', 'wwr');
CREATE TYPE exp_level_enum AS ENUM ('junior', 'mid', 'senior', 'unknown');
CREATE TYPE emp_type_enum AS ENUM ('remote', 'onsite', 'hybrid', 'unknown');
CREATE TYPE skill_category_enum AS ENUM ('hard', 'soft', 'tool');
CREATE TYPE extraction_status_enum AS ENUM ('pending', 'done', 'failed');

-- ---------- job_postings: raw source of truth ----------
CREATE TABLE IF NOT EXISTS job_postings (
    id                 BIGSERIAL PRIMARY KEY,
    source             source_enum NOT NULL,
    source_id          TEXT        NOT NULL,
    title              TEXT        NOT NULL,
    company            TEXT,
    source_url         TEXT        NOT NULL,
    raw_description    TEXT,
    location           TEXT,
    posted_date        DATE,
    fetched_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    embedding          vector(384),
    is_duplicate_of    BIGINT REFERENCES job_postings(id),
    extraction_status  extraction_status_enum NOT NULL DEFAULT 'pending',
    extraction_version INT NOT NULL DEFAULT 1,
    retry_count        INT NOT NULL DEFAULT 0,
    UNIQUE (source, source_id)
);

-- ---------- extracted_requirements: hasil LLM, 1:1 ----------
CREATE TABLE IF NOT EXISTS extracted_requirements (
    job_posting_id       BIGINT PRIMARY KEY REFERENCES job_postings(id) ON DELETE CASCADE,
    hard_skills_raw      TEXT[],
    soft_skills_raw      TEXT[],
    tools_raw            TEXT[],
    experience_level     exp_level_enum,
    min_years_experience NUMERIC,
    employment_type      emp_type_enum,
    skill_ids            BIGINT[],
    extracted_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- skills: kamus normalisasi (ESCO + custom) ----------
CREATE TABLE IF NOT EXISTS skills (
    id             BIGSERIAL PRIMARY KEY,
    canonical_name TEXT NOT NULL UNIQUE,
    category       skill_category_enum NOT NULL,
    aliases        TEXT[] NOT NULL DEFAULT '{}',
    origin         TEXT  NOT NULL DEFAULT 'esco',
    esco_uri       TEXT,
    embedding      vector(384)
);

-- ---------- unmatched_skills: antrian review normalisasi ----------
CREATE TABLE IF NOT EXISTS unmatched_skills (
    id          BIGSERIAL PRIMARY KEY,
    raw_name    TEXT NOT NULL,
    first_seen  TIMESTAMPTZ NOT NULL DEFAULT now(),
    occurrences INT NOT NULL DEFAULT 1,
    resolved    BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (raw_name)
);

-- ---------- Indexes ----------
CREATE INDEX IF NOT EXISTS idx_postings_posted_date ON job_postings (posted_date DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_postings_status ON job_postings (extraction_status) WHERE extraction_status <> 'done';
CREATE INDEX IF NOT EXISTS idx_postings_dedup ON job_postings (is_duplicate_of) WHERE is_duplicate_of IS NULL;

CREATE INDEX IF NOT EXISTS idx_postings_embedding ON job_postings USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_skills_embedding ON skills USING hnsw (embedding vector_cosine_ops);

-- ---------- RPC: normalisasi skill ----------
-- Alias exact match: cari skill berdasarkan canonical_name atau aliases.
-- Seeder menyimpan canonical_name & aliases dalam lowercase.
CREATE OR REPLACE FUNCTION get_skill_id_by_alias(raw_name TEXT)
RETURNS BIGINT
LANGUAGE sql
STABLE
AS $$
    SELECT id FROM skills
    WHERE lower(canonical_name) = lower(raw_name)
       OR lower(raw_name) = ANY (aliases)
    LIMIT 1;
$$;

-- Closest skill by embedding (cosine similarity), threshold dari caller.
CREATE OR REPLACE FUNCTION find_closest_skill(qvec vector, threshold float)
RETURNS BIGINT
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    result_id BIGINT;
    best_sim  float;
BEGIN
    SELECT id, 1 - (embedding <=> qvec) INTO result_id, best_sim
    FROM skills
    ORDER BY embedding <=> qvec
    LIMIT 1;

    IF best_sim IS NULL OR best_sim < threshold THEN
        RETURN NULL;
    END IF;
    RETURN result_id;
END;
$$;

-- ---------- RPC: semantic search (FR-5) ----------
CREATE OR REPLACE FUNCTION search_jobs(
    qvec vector,
    search_threshold float,
    max_days int,
    src text,
    max_rows int
)
RETURNS TABLE (
    id BIGINT,
    title TEXT,
    company TEXT,
    source TEXT,
    source_url TEXT,
    posted_date DATE,
    location TEXT,
    similarity float
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        jp.id,
        jp.title,
        jp.company,
        jp.source::text AS source,
        jp.source_url,
        COALESCE(jp.posted_date, jp.fetched_at::date) AS posted_date,
        jp.location,
        1 - (jp.embedding <=> qvec) AS similarity
    FROM job_postings jp
    WHERE jp.embedding IS NOT NULL
      AND jp.is_duplicate_of IS NULL
      AND COALESCE(jp.posted_date, jp.fetched_at::date) >= current_date - max_days
      AND (src = 'all' OR jp.source::text = src)
      AND 1 - (jp.embedding <=> qvec) >= search_threshold
    ORDER BY jp.embedding <=> qvec
    LIMIT max_rows;
END;
$$;

-- ---------- RPC: top skills (FR-7/8/9) ----------
CREATE OR REPLACE FUNCTION top_skills(
    max_days int,
    role_vec vector,
    cat text,
    max_rows int
)
RETURNS TABLE (name TEXT, category TEXT, freq BIGINT)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
    WITH filtered AS (
        SELECT jp.id
        FROM job_postings jp
        WHERE jp.embedding IS NOT NULL
          AND jp.is_duplicate_of IS NULL
          AND COALESCE(jp.posted_date, jp.fetched_at::date) >= current_date - max_days
          AND (role_vec IS NULL OR 1 - (jp.embedding <=> role_vec) >= 0.25)
    )
    SELECT s.canonical_name AS name, s.category::text AS category, COUNT(*)::bigint AS freq
    FROM filtered f
    JOIN extracted_requirements er ON er.job_posting_id = f.id
    CROSS JOIN LATERAL unnest(er.skill_ids) AS sid
    JOIN skills s ON s.id = sid
    WHERE (cat IS NULL OR s.category::text = cat)
    GROUP BY s.id, s.canonical_name, s.category
    ORDER BY freq DESC
    LIMIT max_rows;
END;
$$;

-- ---------- RPC: count posting dalam rentang hari (konsisten COALESCE) ----------
CREATE OR REPLACE FUNCTION count_postings_in_days(max_days int, role_vec vector DEFAULT NULL)
RETURNS BIGINT
LANGUAGE sql
STABLE
AS $$
    SELECT COUNT(*)::bigint
    FROM job_postings
    WHERE is_duplicate_of IS NULL
      AND COALESCE(posted_date, fetched_at::date) >= current_date - max_days
      AND (role_vec IS NULL OR 1 - (embedding <=> role_vec) >= 0.25);
$$;
