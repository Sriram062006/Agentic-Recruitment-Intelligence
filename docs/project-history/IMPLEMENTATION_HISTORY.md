# Implementation History: Agentic AI Recruitment Intelligence Platform

This document chronicles the step-by-step engineering milestones accomplished in building the platform.

---

## Milestone 1: Project Foundation & Architecture Freeze
- **Repository Structure:** Established clean multi-tiered structure (`backend/`, `frontend/`, `supabase/`, `docs/`).
- **Backend Architecture:** FastAPI application bootstrap with CORS, structured JSON logging, configuration parsing with Pydantic `BaseSettings`.
- **Frontend Architecture:** Vite + React + TypeScript with Tailwind CSS and Lucide React icons.
- **Architecture Freezing:** Clarified Single-Candidate Multi-Role model ($N$ candidates evaluated across $M$ jobs creates $N \times M$ matrix evaluations under `UNIQUE(run_id, candidate_id, job_id)`). Removed generic analytics dashboards in favor of direct recruiter workflows. Removed Cross-Encoder reranking from initial MVP in favor of Sentence Transformers + FAISS.

---

## Milestone 2: Document Ingestion, Parsing & Sanitization
- **PyMuPDF & python-docx Integration:** Implemented block-level layout-aware document parsers.
- **Robust Sanitization Engine:** Created `sanitizer.py` eliminating PostgreSQL-fatal NUL bytes (`\x00`), character replacements (`\ufffd`), while preserving international character sets and spaced section headings (`W O R K  E X P E R I E N C E`).
- **Deduplication:** Enforced SHA-256 content hashing at ingestion time to guarantee idempotent profile creation.

---

## Milestone 3: LLM Structured Extraction & Canonical Profiles
- **Gemini Structured Provider:** Integrated Google Gemini LLM API via JSON schema constraints.
- **Comprehensive Candidate Profile:** Expanded schema to capture:
  - Personal Information & Contact Details (email, phone, location, LinkedIn/GitHub)
  - Canonical Skills (technical, soft, tools, domain competencies)
  - Verified Career History (roles, companies, verified tenure, bullets)
  - Education Background (institution, degree, graduation year, GPA)
  - Certifications & Licenses
  - Projects, Open Source, and Publications
  - Extracurriculars & Honors
  - Executive Professional Summary

---

## Milestone 4: Semantic Embeddings & FAISS Vector Search
- **Embedding Generation:** Integrated `sentence-transformers` (`all-MiniLM-L6-v2`) generating 384-dimensional dense vectors with strict $L_2$ normalization.
- **Vector Indexing:** Built `FaissVectorStore` implementing `IndexFlatIP` with bidirectional integer ID to UUID mapping.
- **Persistence:** Local disk persistence with atomic index synchronization.

---

## Milestone 5: Deterministic Hybrid Scoring & Explainability
- **Scoring Engine:** Implemented pure mathematical scoring formula:
  $$S_{\text{total}}(C, J) = w_{\text{sem}} \cdot S_{\text{sem}} + w_{\text{skill}} \cdot S_{\text{skill}} + w_{\text{exp}} \cdot S_{\text{exp}} + w_{\text{qual}} \cdot S_{\text{qual}}$$
- **Baseline Heuristics:**
  - Skill balance ($\alpha = 0.80$ required vs preferred skill overlap).
  - Exponential experience penalty decay ($\beta = 1.50$ for tenure shortfalls).
  - Qualification hierarchy matching.
- **Evidence-Grounded Explainer:** Deterministic evidence generation outlining exact matched skills, missing skills, tenure comparison, and rationale.

---

## Milestone 6: Production Supabase Backend Integration
- **PostgreSQL Schemas & Constraints:** Provisioned tables for `recruiter_profiles`, `jobs`, `candidates`, `evaluation_runs`, `candidate_evaluations`.
- **Row Level Security (RLS):** Activated tenant isolation across all tables.
- **Automated Profile Sync:** Trigger `on_auth_user_created` syncing Auth signups to `recruiter_profiles`.
- **Private Storage Buckets:** Secured Supabase Storage buckets `resumes` and `job-descriptions` with per-user folder access policies.

---

## Milestone 7: Role-Based Access Control (Admin, Recruiter, Viewer)
- **Three User Roles:** Created `ADMIN`, `RECRUITER`, and `VIEWER` roles.
- **Database Schema Upgrades:**
  - Added `is_active BOOLEAN NOT NULL DEFAULT true` and `email TEXT` to `recruiter_profiles`.
  - Added security helper functions `is_admin()` and `can_mutate()`.
  - Updated PostgreSQL RLS policies to grant admins global visibility and restrict viewers to read-only operations.
- **Backend Authorization Dependencies:**
  - `require_role(allowed_roles)` dependency factory.
  - Dedicated role checks: `require_admin`, `require_recruiter_or_admin`, `require_any_authenticated`.
  - Account suspension checks blocking deactivated users with HTTP 403 Forbidden.

---

## Milestone 8: System Administration Panel & User Governance
- **Operational Metrics Endpoint:** Implemented `GET /api/v1/admin/stats` calculating live system metrics.
- **User Management Endpoints:** Implemented `GET /api/v1/admin/users`, `PATCH /api/v1/admin/users/{user_id}/role`, `PATCH /api/v1/admin/users/{user_id}/status`.
- **Safeguards:** Implemented validation preventing self-demotion and self-deactivation.
- **Frontend Admin Panel (`AdminView.tsx`):**
  - KPI overview metrics cards.
  - User management table with search, role filter, role switcher dropdown, and active/deactivate toggle.

---

## Milestone 9: Persistent Evaluation History
- **Run Directory & Frozen Snapshots:**
  - Implemented `GET /api/v1/evaluations/runs` and `GET /api/v1/evaluations/runs/{run_id}`.
  - Preserved weights snapshot in `evaluation_runs.config`.
- **Frontend History View (`EvaluationHistoryView.tsx`):**
  - Historical run directory table with search and status filtering.
  - Reopened run inspection displaying the frozen scoring snapshot, stored $N \times M$ matrix grid, role-wise leaderboards, and explainability modal without score recomputation.
