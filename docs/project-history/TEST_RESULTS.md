# Test Results & Verification: Agentic AI Recruitment Intelligence Platform

**Date of Execution:** October 5, 2026  
**Total Tests Executed:** 54  
**Total Tests Passed:** 54 (100% Pass Rate)  
**Total Tests Failed:** 0  
**Environment:** Python 3.13.11 / Windows 11 / Supabase PostgreSQL / Pytest 8.4.2  

---

## 1. Test Suite Summary Table

| Test Module | Tests | Status | Scope & Objective |
| :--- | :---: | :---: | :--- |
| `tests/test_api_v1.py` | 1 | **PASSED** | End-to-end HTTP contract workflow (Jobs, Resumes, Evaluation, Matrix, Leaderboard, Explainability) |
| `tests/test_app.py` | 2 | **PASSED** | Application startup, OpenAPI docs availability, CORS preflight headers |
| `tests/test_config.py` | 2 | **PASSED** | Pydantic BaseSettings, default weights, environment overrides |
| `tests/test_database.py` | 3 | **PASSED** | Repository CRUD, SHA-256 deduplication, unique run-candidate-job constraint |
| `tests/test_embeddings_faiss.py` | 2 | **PASSED** | Sentence Transformers 384-d normalization, FAISS IndexFlatIP indexing and removal |
| `tests/test_evaluation_history.py` | 1 | **PASSED** | Evaluation run history lifecycle, frozen snapshot weights verification, stored matrix retrieval |
| `tests/test_explainability.py` | 1 | **PASSED** | Evidence-grounded explainability generation, matched/missing skill accuracy |
| `tests/test_extraction_complete.py` | 15 | **PASSED** | Full CV parsing, Unicode preservation, NUL byte sanitization, no skills concatenation |
| `tests/test_health.py` | 1 | **PASSED** | Backend health endpoint operational status |
| `tests/test_multi_role_evaluation.py` | 1 | **PASSED** | Controlled 10 candidates $\times$ 5 jobs ($50$ evaluations) batch execution |
| `tests/test_parsers.py` | 5 | **PASSED** | PyMuPDF and python-docx parsing, empty file, corrupted file, unsupported format checks |
| `tests/test_research_evaluation.py` | 2 | **PASSED** | Precision@K, Recall@K, MRR, NDCG@K calculation, semantic vs hybrid comparison |
| `tests/test_roles_and_admin_security.py` | 4 | **PASSED** | Admin stats, user management, recruiter admin denial, viewer read-only enforcement, deactivated lockout |
| `tests/test_scoring_deterministic.py` | 4 | **PASSED** | Pure mathematical determinism, $\alpha$ skill balance, $\beta$ tenure penalty, degree hierarchy |
| `tests/test_security.py` | 4 | **PASSED** | File extension validation, prompt injection resistance, SQL injection defense, zero secrets in code |
| `tests/test_supabase_live.py` | 6 | **PASSED** | Live Supabase user signup, RLS job/candidate isolation, private storage isolation, real multi-role run |
| **Total** | **54** | **100% PASSED** | Complete system verified |

---

## 2. Key Verification Findings

### A. Role-Based Access Control (RBAC) Verification
- **Admin Privileges:** Validated that users with role `'admin'` can read system statistics (`GET /api/v1/admin/stats`), list users with active counts (`GET /api/v1/admin/users`), update user roles, and toggle user active states.
- **Admin Safeguards:** Confirmed that attempting self-demotion or self-deactivation returns HTTP 400 Bad Request with an explicit safeguard message.
- **Recruiter Isolation:** Confirmed that users with role `'recruiter'` receive HTTP 403 Forbidden when attempting to access `/api/v1/admin/*` endpoints.
- **Viewer Restrictions:** Confirmed that users with role `'viewer'` are rejected with HTTP 403 Forbidden on all mutating endpoints (`POST /jobs/upload`, `DELETE /jobs/{id}`, `POST /candidates/upload`, `DELETE /candidates/{id}`, `POST /evaluations/run`), while permitted to execute all read queries (`GET /jobs`, `GET /candidates`, `GET /evaluations/runs`, `GET /evaluations/runs/{id}/matrix`).
- **Account Suspension:** Confirmed that users with `is_active = false` are blocked with HTTP 403 Forbidden on all platform routes.

### B. Evaluation History & Snapshot Immutability Verification
- Confirmed that every evaluation run saves a complete snapshot of configuration weights ($w_{\text{sem}}, w_{\text{skill}}, w_{\text{exp}}, w_{\text{qual}}$) and heuristics ($\alpha, \beta$, thresholds) into `evaluation_runs.config`.
- Confirmed that reopening a historical run retrieves the stored matrix cells and role leaderboards without re-triggering evaluation calculations.

### C. Live Supabase PostgreSQL Verification
- Authenticated and verified against remote instance: `https://xbalawmzdndhlmrekwvu.supabase.co`.
- Verified that Row Level Security policies enforce multi-tenant isolation so Recruiters cannot view each other's candidate resumes or job descriptions.
- Verified that private storage buckets (`resumes` and `job-descriptions`) block cross-tenant downloads.

---

## 3. Frontend Build Verification
- Command: `npm run build`
- Output: `dist/index.html` (0.45 kB), `dist/assets/index.css` (30.13 kB), `dist/assets/index.js` (563.40 kB).
- Status: **0 Errors / Clean Production Build**.

---

## 4. Academic Validation & Multi-Role Experimentation Results (Phases 2-17)

**Execution Script:** `backend/scripts/run_academic_validation.py`  
**Data Artifact:** `backend/data/academic_validation_results.json`

### A. Mathematical Scoring Equivalence (Phase 5)
Tested 3 real candidate $\times$ JD pairs:
1. Jeremy Scheppers $\times$ Senior IT PM: App = `0.8504`, Independent = `0.8504`, Absolute Difference = **`0.000000`** (Match: True)
2. Hugues Crepin $\times$ IAM Architect: App = `0.8173`, Independent = `0.8173`, Absolute Difference = **`0.000000`** (Match: True)
3. Jeremy Scheppers $\times$ DevOps Lead: App = `0.6430`, Independent = `0.6430`, Absolute Difference = **`0.000000`** (Match: True)

### B. Cardinality & Multi-Role Scalability Benchmarks (Phases 6-9)
- **$1 \times 1$ Evaluation:** 1 Candidate $\times$ 1 Job = **1 Evaluation** in 0.0448 s (Status: COMPLETED)
- **$1 \times 5$ Multi-Role Evaluation:** 1 Candidate $\times$ 5 Jobs = **5 Evaluations** in 0.1729 s (1 candidate UUID reused across all 5 evaluations; 5 distinct scores)
- **$2 \times 3$ Evaluation:** 2 Candidates $\times$ 3 Jobs = **6 Evaluations** in 0.0933 s (0 duplicate pairs)
- **$10 \times 5$ Scalability Test:** 10 Real Candidates $\times$ 5 Jobs = **50 Evaluations** in 0.1738 s (Throughput: **287.68 evals/sec**, Average: **3.48 ms/pair**, 0 failures, 0 duplicates)

### C. Historical Immutability (Phase 11)
- Run 1 original score (`0.8504`) verified against reopened score (`0.8504`) after Run 2 was executed with modified weights (`w_sem = 0.60`). Reopened evaluation strictly preserved frozen historical snapshot.

### D. Sub-Millisecond Latency Profiling (Phase 15)
- Document Parsing: 11.08 ms
- Profile Extraction: 35.10 ms
- Dense Vector Embedding (`all-MiniLM-L6-v2`): 33.97 ms
- FAISS Indexing & Inner Product Search: 14.27 ms
- Deterministic Multi-Criteria Scoring: **0.05 ms** (50 $\mu$s)
- Total Single Candidate Pipeline: **94.45 ms**

