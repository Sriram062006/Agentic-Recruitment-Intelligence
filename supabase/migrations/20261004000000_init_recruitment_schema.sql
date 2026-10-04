-- Supabase Migration: 20261004000000_init_recruitment_schema.sql
-- Agentic AI Recruitment Intelligence Platform for Large-Scale Multi-Role Candidate Evaluation

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Jobs Table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    storage_path TEXT NOT NULL,
    raw_content TEXT NOT NULL,
    structured_profile JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Candidates Table (Canonical Model: Exactly 1 record per unique resume file)
CREATE TABLE IF NOT EXISTS candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    raw_text TEXT NOT NULL,
    structured_profile JSONB NOT NULL,
    faiss_index_id BIGINT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Evaluation Runs Table
CREATE TABLE IF NOT EXISTS evaluation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    total_candidates INT NOT NULL DEFAULT 0,
    total_jobs INT NOT NULL DEFAULT 0,
    total_evaluations INT NOT NULL DEFAULT 0,
    config JSONB NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT
);

-- 4. Candidate Evaluations Table (N candidates x M jobs evaluations)
CREATE TABLE IF NOT EXISTS candidate_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES evaluation_runs(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    semantic_score NUMERIC(5, 4) NOT NULL,
    skill_score NUMERIC(5, 4) NOT NULL,
    experience_score NUMERIC(5, 4) NOT NULL,
    qualification_score NUMERIC(5, 4) NOT NULL,
    composite_score NUMERIC(5, 4) NOT NULL,
    rank_in_role INT NOT NULL,
    explainability JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_run_candidate_job UNIQUE (run_id, candidate_id, job_id)
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_eval_job_composite ON candidate_evaluations(run_id, job_id, composite_score DESC);
CREATE INDEX IF NOT EXISTS idx_eval_candidate ON candidate_evaluations(run_id, candidate_id);
CREATE INDEX IF NOT EXISTS idx_eval_run_status ON evaluation_runs(status);
CREATE INDEX IF NOT EXISTS idx_candidates_file_hash ON candidates(file_hash);
