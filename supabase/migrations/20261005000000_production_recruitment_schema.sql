-- Production Supabase Migration: 20261005000000_production_recruitment_schema.sql
-- Agentic AI Recruitment Intelligence Platform for Large-Scale Multi-Role Candidate Evaluation
-- Clean, Non-Destructive Schema Creation for Remote Supabase PostgreSQL

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 1. Recruiter Profiles Table
-- ============================================================
CREATE TABLE IF NOT EXISTS public.recruiter_profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'recruiter',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 2. Jobs Table
-- ============================================================
CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    storage_path TEXT NOT NULL,
    raw_content TEXT NOT NULL,
    structured_profile JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 3. Candidates Table (Canonical: One record per resume per recruiter)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    raw_text TEXT NOT NULL,
    structured_profile JSONB NOT NULL,
    faiss_index_id BIGINT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT unique_recruiter_file_hash UNIQUE (recruiter_id, file_hash)
);

-- ============================================================
-- 4. Evaluation Runs Table (Multi-Role batch evaluations)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.evaluation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    total_candidates INT NOT NULL DEFAULT 0,
    total_jobs INT NOT NULL DEFAULT 0,
    total_evaluations INT NOT NULL DEFAULT 0,
    config JSONB NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    error_message TEXT
);

-- ============================================================
-- 5. Candidate Evaluations Table (N candidates x M jobs matrix)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.candidate_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES public.evaluation_runs(id) ON DELETE CASCADE,
    recruiter_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES public.candidates(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
    semantic_score NUMERIC(5, 4) NOT NULL,
    skill_score NUMERIC(5, 4) NOT NULL,
    experience_score NUMERIC(5, 4) NOT NULL,
    qualification_score NUMERIC(5, 4) NOT NULL,
    composite_score NUMERIC(5, 4) NOT NULL,
    rank_in_role INT NOT NULL,
    explainability JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT unique_run_candidate_job UNIQUE (run_id, candidate_id, job_id)
);

-- ============================================================
-- 6. Indexes for Performance & Search Optimization
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_recruiter_profiles_user ON public.recruiter_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_recruiter ON public.jobs(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_candidates_recruiter ON public.candidates(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_candidates_file_hash ON public.candidates(recruiter_id, file_hash);
CREATE INDEX IF NOT EXISTS idx_eval_runs_recruiter ON public.evaluation_runs(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_eval_runs_status ON public.evaluation_runs(status);
CREATE INDEX IF NOT EXISTS idx_candidate_evals_recruiter ON public.candidate_evaluations(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_candidate_evals_run_job ON public.candidate_evaluations(run_id, job_id, composite_score DESC);
CREATE INDEX IF NOT EXISTS idx_candidate_evals_cand ON public.candidate_evaluations(run_id, candidate_id);

-- ============================================================
-- 7. Automated Recruiter Profile Sync on Auth Signup
-- ============================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.recruiter_profiles (user_id, full_name, role)
  VALUES (
    new.id,
    COALESCE(new.raw_user_meta_data->>'full_name', 'Recruiter'),
    COALESCE(new.raw_user_meta_data->>'role', 'recruiter')
  )
  ON CONFLICT (user_id) DO UPDATE
  SET full_name = EXCLUDED.full_name,
      updated_at = now();
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- 8. Row Level Security (RLS) Activation
-- ============================================================
ALTER TABLE public.recruiter_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evaluation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.candidate_evaluations ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- 9. Row Level Security Policies (Strict Ownership Isolation)
-- ============================================================

-- 9.1 recruiter_profiles policies
CREATE POLICY "Recruiter read own profile"
    ON public.recruiter_profiles FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Recruiter insert own profile"
    ON public.recruiter_profiles FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Recruiter update own profile"
    ON public.recruiter_profiles FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 9.2 jobs policies
CREATE POLICY "Recruiter read own jobs"
    ON public.jobs FOR SELECT
    TO authenticated
    USING (auth.uid() = recruiter_id);

CREATE POLICY "Recruiter insert own jobs"
    ON public.jobs FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = recruiter_id);

CREATE POLICY "Recruiter update own jobs"
    ON public.jobs FOR UPDATE
    TO authenticated
    USING (auth.uid() = recruiter_id)
    WITH CHECK (auth.uid() = recruiter_id);

CREATE POLICY "Recruiter delete own jobs"
    ON public.jobs FOR DELETE
    TO authenticated
    USING (auth.uid() = recruiter_id);

-- 9.3 candidates policies
CREATE POLICY "Recruiter read own candidates"
    ON public.candidates FOR SELECT
    TO authenticated
    USING (auth.uid() = recruiter_id);

CREATE POLICY "Recruiter insert own candidates"
    ON public.candidates FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = recruiter_id);

CREATE POLICY "Recruiter update own candidates"
    ON public.candidates FOR UPDATE
    TO authenticated
    USING (auth.uid() = recruiter_id)
    WITH CHECK (auth.uid() = recruiter_id);

CREATE POLICY "Recruiter delete own candidates"
    ON public.candidates FOR DELETE
    TO authenticated
    USING (auth.uid() = recruiter_id);

-- 9.4 evaluation_runs policies
CREATE POLICY "Recruiter read own runs"
    ON public.evaluation_runs FOR SELECT
    TO authenticated
    USING (auth.uid() = recruiter_id);

CREATE POLICY "Recruiter insert own runs"
    ON public.evaluation_runs FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = recruiter_id);

CREATE POLICY "Recruiter update own runs"
    ON public.evaluation_runs FOR UPDATE
    TO authenticated
    USING (auth.uid() = recruiter_id)
    WITH CHECK (auth.uid() = recruiter_id);

CREATE POLICY "Recruiter delete own runs"
    ON public.evaluation_runs FOR DELETE
    TO authenticated
    USING (auth.uid() = recruiter_id);

-- 9.5 candidate_evaluations policies
CREATE POLICY "Recruiter read own evaluations"
    ON public.candidate_evaluations FOR SELECT
    TO authenticated
    USING (auth.uid() = recruiter_id);

CREATE POLICY "Recruiter insert own evaluations"
    ON public.candidate_evaluations FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = recruiter_id);

CREATE POLICY "Recruiter update own evaluations"
    ON public.candidate_evaluations FOR UPDATE
    TO authenticated
    USING (auth.uid() = recruiter_id)
    WITH CHECK (auth.uid() = recruiter_id);

CREATE POLICY "Recruiter delete own evaluations"
    ON public.candidate_evaluations FOR DELETE
    TO authenticated
    USING (auth.uid() = recruiter_id);

-- ============================================================
-- 10. Private Supabase Storage Buckets
-- ============================================================
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES 
    (
        'resumes',
        'resumes',
        false,
        10485760,
        ARRAY['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']::text[]
    ),
    (
        'job-descriptions',
        'job-descriptions',
        false,
        10485760,
        ARRAY['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword', 'text/plain']::text[]
    )
ON CONFLICT (id) DO UPDATE
SET public = false,
    file_size_limit = 10485760;

-- ============================================================
-- 11. Storage Row Level Security Policies
-- ============================================================

CREATE POLICY "Recruiter upload own resume"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'resumes' 
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

CREATE POLICY "Recruiter read own resume"
    ON storage.objects FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'resumes' 
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

CREATE POLICY "Recruiter delete own resume"
    ON storage.objects FOR DELETE
    TO authenticated
    USING (
        bucket_id = 'resumes' 
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

CREATE POLICY "Recruiter upload own jd"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'job-descriptions' 
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

CREATE POLICY "Recruiter read own jd"
    ON storage.objects FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'job-descriptions' 
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

CREATE POLICY "Recruiter delete own jd"
    ON storage.objects FOR DELETE
    TO authenticated
    USING (
        bucket_id = 'job-descriptions' 
        AND (storage.foldername(name))[1] = auth.uid()::text
    );
