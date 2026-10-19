-- Migration: 20261005010000_admin_roles_and_viewer_access.sql
-- Agentic AI Recruitment Intelligence Platform
-- Multi-Role Support: ADMIN, RECRUITER, VIEWER and User Management

ALTER TABLE public.recruiter_profiles 
  ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true,
  ADD COLUMN IF NOT EXISTS email TEXT;

-- Backfill emails from auth.users
UPDATE public.recruiter_profiles rp
SET email = u.email
FROM auth.users u
WHERE rp.user_id = u.id AND (rp.email IS NULL OR rp.email = '');

-- Update trigger function to also store email and default is_active
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.recruiter_profiles (user_id, full_name, role, email, is_active)
  VALUES (
    new.id,
    COALESCE(new.raw_user_meta_data->>'full_name', 'Recruiter'),
    COALESCE(new.raw_user_meta_data->>'role', 'recruiter'),
    new.email,
    true
  )
  ON CONFLICT (user_id) DO UPDATE
  SET full_name = EXCLUDED.full_name,
      email = EXCLUDED.email,
      updated_at = now();
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Security helper functions
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS boolean AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM public.recruiter_profiles
    WHERE user_id = auth.uid() AND role = 'admin' AND is_active = true
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.can_mutate()
RETURNS boolean AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM public.recruiter_profiles
    WHERE user_id = auth.uid() AND role IN ('admin', 'recruiter') AND is_active = true
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Update RLS on recruiter_profiles
ALTER POLICY "Recruiter read own profile" ON public.recruiter_profiles 
  USING (auth.uid() = user_id OR public.is_admin());

ALTER POLICY "Recruiter update own profile" ON public.recruiter_profiles 
  USING (auth.uid() = user_id OR public.is_admin()) 
  WITH CHECK (auth.uid() = user_id OR public.is_admin());

-- Update RLS on jobs
ALTER POLICY "Recruiter read own jobs" ON public.jobs 
  USING (auth.uid() = recruiter_id OR public.is_admin());

ALTER POLICY "Recruiter insert own jobs" ON public.jobs 
  WITH CHECK (auth.uid() = recruiter_id AND public.can_mutate());

ALTER POLICY "Recruiter update own jobs" ON public.jobs 
  USING (auth.uid() = recruiter_id AND public.can_mutate()) 
  WITH CHECK (auth.uid() = recruiter_id AND public.can_mutate());

ALTER POLICY "Recruiter delete own jobs" ON public.jobs 
  USING (auth.uid() = recruiter_id AND public.can_mutate());

-- Update RLS on candidates
ALTER POLICY "Recruiter read own candidates" ON public.candidates 
  USING (auth.uid() = recruiter_id OR public.is_admin());

ALTER POLICY "Recruiter insert own candidates" ON public.candidates 
  WITH CHECK (auth.uid() = recruiter_id AND public.can_mutate());

ALTER POLICY "Recruiter update own candidates" ON public.candidates 
  USING (auth.uid() = recruiter_id AND public.can_mutate()) 
  WITH CHECK (auth.uid() = recruiter_id AND public.can_mutate());

ALTER POLICY "Recruiter delete own candidates" ON public.candidates 
  USING (auth.uid() = recruiter_id AND public.can_mutate());

-- Update RLS on evaluation_runs
ALTER POLICY "Recruiter read own runs" ON public.evaluation_runs 
  USING (auth.uid() = recruiter_id OR public.is_admin());

ALTER POLICY "Recruiter insert own runs" ON public.evaluation_runs 
  WITH CHECK (auth.uid() = recruiter_id AND public.can_mutate());

ALTER POLICY "Recruiter update own runs" ON public.evaluation_runs 
  USING (auth.uid() = recruiter_id AND public.can_mutate()) 
  WITH CHECK (auth.uid() = recruiter_id AND public.can_mutate());

ALTER POLICY "Recruiter delete own runs" ON public.evaluation_runs 
  USING (auth.uid() = recruiter_id AND public.can_mutate());

-- Update RLS on candidate_evaluations
ALTER POLICY "Recruiter read own evaluations" ON public.candidate_evaluations 
  USING (auth.uid() = recruiter_id OR public.is_admin());

ALTER POLICY "Recruiter insert own evaluations" ON public.candidate_evaluations 
  WITH CHECK (auth.uid() = recruiter_id AND public.can_mutate());

ALTER POLICY "Recruiter update own evaluations" ON public.candidate_evaluations 
  USING (auth.uid() = recruiter_id AND public.can_mutate()) 
  WITH CHECK (auth.uid() = recruiter_id AND public.can_mutate());

ALTER POLICY "Recruiter delete own evaluations" ON public.candidate_evaluations 
  USING (auth.uid() = recruiter_id AND public.can_mutate());
