# Project State: Agentic AI Recruitment Intelligence Platform

**Last Updated:** October 5, 2026  
**System Status:** Fully Operational & Production Verified  
**Active Backend Environment:** Python 3.13 FastAPI + Supabase PostgreSQL  
**Active Frontend Environment:** React 18 + TypeScript + Vite + Tailwind CSS  
**Database Project URL:** `https://xbalawmzdndhlmrekwvu.supabase.co` (Verified & Integrated)  

---

## 1. Executive Summary

The **Agentic AI Recruitment Intelligence Platform for Large-Scale Multi-Role Candidate Evaluation** is an academic research prototype and enterprise recruitment system. The platform evaluates large pools of unstructured candidate resumes (PDF/DOCX) across multiple distinct job descriptions simultaneously ($N \times M$ evaluation matrix) without duplicating candidate profiles, using deterministic hybrid fitment algorithms, Sentence Transformers semantic embeddings, FAISS vector search, and grounded LLM explainability.

All user roles (`ADMIN`, `RECRUITER`, `VIEWER`), the System Administration Panel, persistent Evaluation Runs History, and multi-tenant Row Level Security (RLS) are fully implemented, verified, and active.

---

## 2. Implemented Capabilities & Current State

### A. Core Recruitment Engine
1. **Layout-Aware Document Parsing:**
   - Multi-column and block-level text extraction with PyMuPDF (`fitz`) and `python-docx`.
   - Comprehensive sanitization removing control sequences (`\x00` NUL bytes) while preserving Unicode accents (`é`, `ü`), mathematical symbols, and formatting.
2. **Canonical Candidate Representation (Single-Candidate Principle):**
   - 10+ resume sections extracted into canonical structured profiles (`CandidateProfile`).
   - SHA-256 deduplication preventing redundant processing.
   - 1 canonical candidate record evaluated across $M$ job descriptions under `UNIQUE(run_id, candidate_id, job_id)`.
3. **Semantic Embeddings & Vector Indexing:**
   - Sentence Transformers (`all-MiniLM-L6-v2`) generating 384-dimensional $L_2$-normalized dense embeddings.
   - FAISS `IndexFlatIP` vector index providing sub-millisecond cosine-equivalent candidate retrieval.
4. **Deterministic Hybrid Scoring:**
   - Strict mathematical scoring formula balancing semantic similarity ($w_{\text{sem}}$), skill overlap ($w_{\text{skill}}$), experience tenure ($w_{\text{exp}}$), and qualification tiers ($w_{\text{qual}}$).
   - Configurable baseline weights and heuristic parameters ($\alpha, \beta$, thresholds).
   - Grounded, auditable explainability breakdown (matched/missing skills, tenure delta, qualification status, and evidence rationale).

### B. Role-Based Access Control (RBAC) & Security
1. **Three Defined Roles:**
   - **`ADMIN`:** Full system governance, real operational telemetry, user management (list, search, filter, role modification, account suspension/reactivation).
   - **`RECRUITER`:** Full operational access to Candidate Pool, Job Management, Create Evaluation, Evaluation Matrix, Rankings, Explainable Fitment, and Evaluation History.
   - **`VIEWER`:** Strictly read-only access across all candidate, job, matrix, and evaluation views. Ingestion and deletion actions are disabled in the UI and blocked at FastAPI and Supabase RLS levels with HTTP 403 Forbidden.
2. **Account Activation Governance:**
   - Deactivated accounts (`is_active = false`) are immediately locked out of both backend endpoints and frontend views with dedicated suspension notices.
3. **Multi-Tenant Row Level Security (RLS):**
   - Active RLS policies across PostgreSQL tables (`recruiter_profiles`, `jobs`, `candidates`, `evaluation_runs`, `candidate_evaluations`) enforcing strict tenant ownership isolation with admin visibility.

### C. Persistent Evaluation History
1. **Immutable Scoring Snapshots:**
   - Every evaluation run preserves the complete configuration snapshot ($w_{\text{sem}}, w_{\text{skill}}, w_{\text{exp}}, w_{\text{qual}}, \alpha, \beta$, thresholds) immutably in `evaluation_runs.config`.
2. **Historical Matrix & Leaderboard Reopening:**
   - Historical runs can be browsed, searched, filtered, and reopened directly from the website.
   - Reopening retrieves persisted matrix cells from Supabase without recalculation, ensuring reproducible academic evaluations.
   - Drill-down into grounded Candidate $\times$ Role explainability reports works seamlessly on historical records.

### D. System Administration Panel
1. **Real Operational Telemetry:**
   - Total registered users, active authorized recruiters, ingested candidate resumes, benchmark jobs, evaluation runs executed, and total evaluation pairs ($N \times M$).
2. **User Management Interface:**
   - Search by name or email, role filtering, role assignment dropdown (`admin`, `recruiter`, `viewer`), and account active/deactivated toggles with safeguards against self-demotion and self-deactivation.

---

## 3. Database Schema Status

| Table Name | Primary Key | Key Foreign Keys | Key Constraints | RLS Status |
| :--- | :--- | :--- | :--- | :--- |
| `public.recruiter_profiles` | `user_id` (UUID) | `auth.users(id)` | User metadata, `is_active` | **Active** |
| `public.jobs` | `id` (UUID) | `auth.users(id)` | Title, department, profile | **Active** |
| `public.candidates` | `id` (UUID) | `auth.users(id)` | `UNIQUE(recruiter_id, file_hash)` | **Active** |
| `public.evaluation_runs` | `id` (UUID) | `auth.users(id)` | Frozen `config` JSONB, status | **Active** |
| `public.candidate_evaluations` | `id` (UUID) | `runs(id)`, `candidates(id)`, `jobs(id)` | `UNIQUE(run_id, candidate_id, job_id)` | **Active** |

---

## 4. Test Verification Status
- **Backend Test Suite:** 54/54 tests passing (100% pass rate).
- **Live Supabase Tests:** Verified against `xbalawmzdndhlmrekwvu.supabase.co`.
- **Frontend Build:** Verified with Vite production bundling (0 TypeScript / build errors).
