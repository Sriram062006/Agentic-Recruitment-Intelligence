# System Changelog

All notable changes and architectural advancements to the **Agentic AI Recruitment Intelligence Platform** are documented in this file.

---

## [1.3.0] - 2026-10-05
### Added
- **Multi-Role RBAC Authorization:**
  - Implemented 3 user roles: `admin`, `recruiter`, and `viewer`.
  - Added PostgreSQL security definer functions `is_admin()` and `can_mutate()`.
  - Applied non-destructive RLS policies on `recruiter_profiles`, `jobs`, `candidates`, `evaluation_runs`, and `candidate_evaluations`.
  - Added backend dependencies `require_role`, `require_admin`, `require_recruiter_or_admin`, and `require_any_authenticated`.
  - Created Admin Panel endpoints: `GET /api/v1/admin/stats`, `GET /api/v1/admin/users`, `PATCH /api/v1/admin/users/{user_id}/role`, and `PATCH /api/v1/admin/users/{user_id}/status`.
  - Implemented self-protection checks preventing admin self-demotion or self-deactivation.
  - Added `viewer` read-only role enforcement returning HTTP 403 on mutation attempts.
- **Frontend Admin Panel (`AdminView.tsx`):**
  - Displays real system telemetry cards (Total Users, Active Recruiters, Candidates, Job Descriptions, Evaluation Runs, Evaluation Status).
  - Recruiter management table with role selection dropdown, account status toggles, user search, and role filtering.
  - Role-gated access in `NavigationShell.tsx` and route guards in `App.tsx`.
- **Persistent Evaluation History (`EvaluationHistoryView.tsx`):**
  - Added run history browsing directory with live search, status filtering, and date sorting.
  - Interactive "View Evaluation" drawer opening historical runs without recalculating scores.
  - Displays frozen multi-role fitment matrix, role-specific candidate rankings, and explainable fitment breakdown using persisted database snapshots.
  - Added backend endpoint `GET /api/v1/evaluations/runs` to query user/admin evaluation runs.
- **Automated Verification Test Suite:**
  - Added `backend/tests/test_roles_and_admin_security.py` verifying RBAC access control, admin metrics, viewer 403 blocks, and deactivated user lockout.
  - Added `backend/tests/test_evaluation_history.py` validating run creation, historical querying, weight immutability, and stored matrix retrieval.
- **Project History Documentation:**
  - Generated comprehensive documentation in `docs/project-history/`: `PROJECT_STATE.md`, `IMPLEMENTATION_HISTORY.md`, `TEST_RESULTS.md`, `ARCHITECTURE.md`, and `CHANGELOG.md`.

### Fixed
- Fixed JWT header forwarding in `SupabaseClient` and `auth.py` to prevent `PGRST301: Expected 3 parts in JWT; got 1` when running local mock test suites.
- Fixed primary key resolution on `recruiter_profiles` from `id` to `user_id`.

---

## [1.2.0] - 2026-10-04
### Added
- **Deep Resume Content Extraction Pipeline:**
  - Overhauled candidate profile extraction to parse complete multi-page PDF/DOCX content rather than top-level summaries.
  - Integrated Gemini 2.5 Flash structured output schema for rich extraction of candidate career history, project contributions, education degrees, certifications, and canonical skills.
  - Implemented fallback heuristic parsers to safeguard against API token exhaustion or network interruptions.
- **Semantic Text Normalization & Clean Tokenization:**
  - Resolved concatenated skill strings (e.g., `AwsAzureCi/CdLlmAgileScrum`) into normalized canonical skill tokens.
  - Enhanced resume representation builder combining candidate headline, years of experience, canonical skills, and project summaries for dense vector generation.

---

## [1.1.0] - 2026-10-03
### Added
- **Supabase Cloud Backend Integration:**
  - Connected production Supabase instance (`xbalawmzdndhlmrekwvu.supabase.co`).
  - Created PostgreSQL database tables: `recruiter_profiles`, `jobs`, `candidates`, `evaluation_runs`, `candidate_evaluations`.
  - Configured Supabase Storage buckets `resumes` and `job-descs` with private access policies.
  - Enabled Row Level Security (RLS) on all production tables.
  - Integrated Supabase Authentication with frontend session management and token persistence.

---

## [1.0.0] - 2026-10-01
### Added
- **Core Platform Architecture (MVP):**
  - Initialized repository structure with `backend/` (FastAPI) and `frontend/` (React + TypeScript + Vite).
  - Sentence Transformers (`all-MiniLM-L6-v2`) dense vector embedding generation.
  - FAISS indexer for candidate vector storage and inner-product cosine similarity retrieval.
  - Deterministic multi-criteria scoring engine combining semantic similarity, required/preferred skill match, experience threshold, and academic qualification hierarchy.
  - Multi-Role evaluation matrix rendering candidate-role fitment with explainable scoring breakdown (matched skills, missing skills, strengths, skill gaps, recommendation rationale).
  - Frontend recruitment workspace covering Job Management, Candidate Pool, and Evaluation execution.
