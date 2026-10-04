# Agentic AI Recruitment Intelligence Platform for Large-Scale Multi-Role Candidate Evaluation

## Project Objective
An academic research prototype investigating the automated, explainable, and multi-role evaluation of large-scale candidate resume pools against diverse job descriptions.

The platform implements a unified pipeline where **one candidate resume produces one canonical structured profile**, which is evaluated independently across multiple job descriptions ($N \times M$ evaluation matrix) to generate role-wise rankings, structured fitment scores, and auditable evidence-grounded explanations.

---

## Approved Technology Stack

### Backend
- **Framework:** FastAPI with Python 3.10+ (tested on Python 3.13)
- **Document Ingestion:** PyMuPDF (`fitz`) for PDF and `python-docx` for DOCX
- **Structured Extraction & Explanations:** Google Gemini via modular provider interface
- **Embeddings:** Sentence Transformers (`all-MiniLM-L6-v2`, 384-dimensional dense vectors, $L_2$ normalized)
- **Vector Search:** FAISS (`IndexFlatIP` with bidirectional integer-to-UUID ID mapping)
- **Database:** Supabase PostgreSQL with local SQLite persistence fallback
- **Storage:** Supabase Storage with local persistent file storage fallback
- **Scoring & Ranking:** Purely deterministic hybrid formula with configurable weights and baseline heuristics

### Frontend
- **Framework & Language:** React 18+ with TypeScript
- **Bundler:** Vite
- **Styling:** Tailwind CSS & PostCSS
- **Component UI:** shadcn/ui design conventions with Lucide React icons

---

## Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                          # FastAPI application factory & CORS configuration
│   │   ├── config.py                        # Pydantic BaseSettings & configurable baseline weights
│   │   ├── api/
│   │   │   ├── router.py                    # Root API router
│   │   │   └── v1/
│   │   │       ├── jobs.py                  # Job description ingestion & management
│   │   │       ├── candidates.py            # Resume upload, candidate pool management
│   │   │       └── evaluations.py           # Multi-role evaluation matrix, leaderboards, explainability
│   │   ├── core/
│   │   │   ├── logging.py                   # Structured logging with request tracing
│   │   │   └── orchestrator.py              # Multi-role pipeline coordinator
│   │   ├── parsers/
│   │   │   ├── base.py                      # BaseDocumentParser interface
│   │   │   ├── pdf_parser.py                # PyMuPDF layout-aware block extractor
│   │   │   ├── docx_parser.py               # python-docx paragraph & table extractor
│   │   │   └── factory.py                   # Document routing and validation
│   │   ├── services/
│   │   │   ├── database/                    # Supabase PostgREST client & SQLite fallback
│   │   │   │   └── repositories/            # JobRepository, CandidateRepository, EvaluationRepository
│   │   │   ├── storage/                     # Supabase Storage & local persistent storage
│   │   │   ├── embeddings/                  # Sentence Transformers all-MiniLM-L6-v2 wrapper
│   │   │   ├── vector_store/                # FAISS IndexFlatIP + ID mapping manager
│   │   │   └── llm/                         # Gemini provider with structured JSON output
│   │   ├── pipeline/
│   │   │   ├── scorer.py                    # Deterministic hybrid scoring engine
│   │   │   ├── explainer.py                 # Grounded evidence synthesizer
│   │   │   └── benchmark.py                 # Precision@K, Recall@K, MRR, NDCG@K research evaluation
│   │   └── schemas/                         # Pydantic models (Job, Candidate, Evaluation, Matrix)
│   ├── scripts/
│   │   ├── run_benchmarks.py                # Automated performance benchmark measurement
│   │   └── run_e2e_demonstration.py         # 10 candidates x 5 jobs E2E demonstration script
│   ├── tests/                               # Comprehensive pytest suite (28 tests)
│   ├── requirements.txt                     # Backend dependencies
│   ├── pyproject.toml                       # Package configuration and pytest settings
│   └── .env.example                         # Environment credentials template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/                      # Header, NavigationShell
│   │   │   └── explainability/              # FitmentModal with matched/missing skills
│   │   ├── views/
│   │   │   ├── WorkspaceView.tsx            # Foundation & health connectivity check
│   │   │   ├── JobManagementView.tsx        # Upload and inspect Job Descriptions
│   │   │   ├── CandidatePoolView.tsx        # Bulk resume upload, search, career drawer
│   │   │   └── EvaluationView.tsx           # Multi-role matrix, sliders, role leaderboards
│   │   ├── lib/
│   │   │   └── api-client.ts                # Typed API client for FastAPI backend
│   │   ├── types/                           # TypeScript definitions
│   │   ├── App.tsx                          # Root application component
│   │   └── main.tsx                         # Entry point
│   ├── package.json                         # Frontend dependencies
│   ├── vite.config.ts                       # Vite bundler & backend proxy config
│   └── tailwind.config.js                   # Tailwind CSS configuration
├── supabase/
│   └── migrations/                          # PostgreSQL DDL migration scripts
└── README.md
```

---

## The Canonical Candidate Multi-Role Model

```
One Resume Document
       │
       ▼
One Canonical Candidate Profile (Stored ONCE in Database)
       │
       ├─────────────────┬─────────────────┬─────────────────┐
       ▼                 ▼                 ▼                 ▼
  Job Role A        Job Role B        Job Role C        Job Role D
       │                 │                 │                 │
       ▼                 ▼                 ▼                 ▼
Fitment Score A   Fitment Score B   Fitment Score C   Fitment Score D
(Rank in Role A)  (Rank in Role B)  (Rank in Role C)  (Rank in Role D)
```

**Cardinality Guarantee:** $N$ candidates evaluated across $M$ jobs creates exactly $N \times M$ evaluations in `candidate_evaluations` under constraint `UNIQUE(run_id, candidate_id, job_id)`, without duplicating candidate entities.

---

## Deterministic Hybrid Scoring Formula

The final numerical score is calculated strictly mathematically:

$$S_{\text{total}}(C, J) = w_{\text{sem}} \cdot S_{\text{sem}} + w_{\text{skill}} \cdot S_{\text{skill}} + w_{\text{exp}} \cdot S_{\text{exp}} + w_{\text{qual}} \cdot S_{\text{qual}}$$

- **Baseline Weights (Configurable):**
  $$w_{\text{sem}} = 0.35, \quad w_{\text{skill}} = 0.35, \quad w_{\text{exp}} = 0.20, \quad w_{\text{qual}} = 0.10$$
- **Skill Overlap ($\alpha = 0.80$ baseline):**
  $$S_{\text{skill}} = \alpha \cdot \text{Recall}(S_C, R_J) + (1 - \alpha) \cdot \text{Recall}(S_C, P_J)$$
- **Experience Match ($\beta = 1.50$ baseline shortfall penalty):**
  $$S_{\text{exp}} = \begin{cases} 1.0 & \text{if } Y_C \ge Y_J^{\min} \\ \exp\left(-\beta \cdot \frac{Y_J^{\min} - Y_C}{Y_J^{\min}}\right) & \text{if } Y_C < Y_J^{\min} \end{cases}$$
- **Anti-Hallucination Mandate:** The LLM does NOT calculate or modify numerical scores. It acts exclusively as a synthesizer summarizing deterministic evidence (matched/missing skills, experience delta, qualification match) into human-readable rationales.

---

## How to Run the Platform

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Node.js 18+ and npm

---

### 2. Start Backend

```bash
cd backend

# Create & activate virtual environment (if not already done)
py -3.13 -m venv .venv
.\.venv\Scripts\activate   # Windows
# source .venv/bin/activate # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base: `http://127.0.0.1:8000`
- Health Endpoint: `http://127.0.0.1:8000/api/health`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

---

### 3. Start Frontend

```bash
cd frontend

# Install dependencies (if not already done)
npm install

# Start Vite development server
npm run dev
```
- Open browser at `http://localhost:5173`.
- The application will automatically connect to the FastAPI backend.

---

### 4. Run Automated Test Suite

```bash
# In backend directory
pytest tests -v
```
All 28 unit, integration, and E2E tests will execute and pass.

---

### 5. Run Performance Benchmark

```bash
python backend/scripts/run_benchmarks.py
```

### 6. Run End-to-End Demonstration Script

```bash
python backend/scripts/run_e2e_demonstration.py
```
Outputs role-wise candidate rankings across a 10 candidate $\times$ 5 job matrix ($50$ evaluations).
