# Agentic AI Recruitment Intelligence Platform for Large-Scale Multi-Role Candidate Evaluation

## Project Objective
An academic research prototype investigating the automated, explainable, and multi-role evaluation of large-scale candidate resume pools against diverse job descriptions. 

The system implements a unified pipeline where **one candidate resume produces one canonical structured profile**, which is evaluated independently across multiple job descriptions ($N \times M$ evaluation matrix) to generate role-wise rankings, structured fitment scores, and auditable evidence-grounded explanations.

---

## Technology Stack

### Backend
- **Language & Runtime:** Python 3.10+ (tested on Python 3.13)
- **Framework:** FastAPI
- **Configuration & Validation:** Pydantic v2 & Pydantic Settings
- **ASGI Server:** Uvicorn
- **Testing:** Pytest, HTTPX, Pytest-AsyncIO

### Planned AI & Data Stack (Future Phases)
- **Document Ingestion:** PyMuPDF (`fitz`), `python-docx`
- **Structured Extraction & Explanations:** Google Gemini via modular provider interface
- **Embeddings:** Sentence Transformers (`all-MiniLM-L6-v2`, 384-d dense vectors)
- **Vector Index:** FAISS (`IndexFlatIP` with bidirectional integer-to-UUID IDMap)
- **Database:** Supabase PostgreSQL
- **Storage:** Supabase Storage

### Frontend
- **Framework & Language:** React 18+ with TypeScript
- **Bundler & Tooling:** Vite
- **Styling:** Tailwind CSS & PostCSS
- **Component Primitives:** shadcn/ui design conventions with Lucide React icons

---

## Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app factory, CORS, and router registration
│   │   ├── config.py            # Pydantic BaseSettings & configurable baseline parameters
│   │   ├── api/                 # API router and endpoints (/api/health)
│   │   ├── core/                # Core utilities & structured logging
│   │   ├── parsers/             # Document parsers (PyMuPDF, docx - future phase)
│   │   ├── services/            # LLM, embeddings, FAISS, Supabase wrappers (future phases)
│   │   ├── pipeline/            # Matcher, scorer, explainer engines (future phases)
│   │   └── schemas/             # Pydantic data schemas
│   ├── tests/                   # Pytest test suite (health, config, app startup)
│   ├── requirements.txt         # Phase 1 minimal dependencies
│   ├── pyproject.toml           # Project metadata and test configuration
│   └── .env.example             # Configuration and credentials template
├── frontend/
│   ├── src/
│   │   ├── components/common/   # Header, NavigationShell, Status components
│   │   ├── lib/                 # api-client.ts, utils.ts
│   │   ├── views/               # WorkspaceView application shell
│   │   ├── App.tsx              # Root application component
│   │   ├── main.tsx             # DOM entrypoint
│   │   └── index.css            # Tailwind directives and tokens
│   ├── package.json             # Frontend dependencies & scripts
│   ├── vite.config.ts           # Vite bundler configuration & backend API proxy
│   ├── tsconfig.json            # TypeScript project references
│   └── tailwind.config.js       # Tailwind CSS configuration
├── supabase/
│   └── migrations/              # Database schema migrations (future phases)
├── .github/
│   └── workflows/               # CI/CD pipelines
├── .gitignore                   # Excludes .venv, node_modules, .env, FAISS binaries
└── README.md                    # Project documentation
```

---

## Current Implementation Status

> **Phase 1 completed.**

- **Repository Scaffold:** Full directory structure, `.gitignore`, and package trees initialized.
- **Backend Foundation:** FastAPI application factory, Pydantic `BaseSettings` configuration, structured Python logging, and `/api/health` endpoint established.
- **Frontend Foundation:** React + TypeScript + Vite + Tailwind CSS shell initialized with navigation frame and live API health check verification.
- **Test Suite:** Automated tests covering FastAPI startup, CORS policies, configuration loading, and health checks pass with 100% success.

*Notice: In accordance with the development plan, AI matching, document parsing, embeddings, FAISS indexing, Supabase persistence, and multi-role evaluation logic belong to subsequent phases and are not yet implemented.*

---

## Setup and Execution Guide

### 1. Prerequisites
- Python 3.10 or higher
- Node.js 18+ and npm

---

### 2. Backend Setup & Run

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows
   py -3.13 -m venv .venv
   .\.venv\Scripts\activate

   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Phase 1 minimal dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Prepare environment variables:**
   ```bash
   cp .env.example .env
   ```

5. **Run backend automated tests:**
   ```bash
   pytest tests -v
   ```

6. **Start the FastAPI backend server:**
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

7. **Verify health endpoint:**
   - URL: `http://127.0.0.1:8000/api/health`
   - Response: `{"status": "healthy"}`
   - Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

---

### 3. Frontend Setup & Run

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Verify TypeScript compilation and production build:**
   ```bash
   npm run build
   ```

4. **Start Vite development server:**
   ```bash
   npm run dev
   ```

5. **Access Application:**
   Open `http://localhost:5173` in your browser. The application workspace shell will display `Backend Status: Connected` confirming live end-to-end communication with the FastAPI service.

---

## Environment Configuration Parameters

The backend configuration in `app/config.py` defines configurable parameters for experimental evaluation:

| Parameter | Type | Default (Baseline) | Description |
|---|---|---|---|
| `SEMANTIC_WEIGHT` | `float` | `0.35` | Initial baseline weight for vector embedding similarity |
| `SKILL_WEIGHT` | `float` | `0.35` | Initial baseline weight for structured skill match |
| `EXPERIENCE_WEIGHT` | `float` | `0.20` | Initial baseline weight for candidate tenure alignment |
| `QUALIFICATION_WEIGHT`| `float` | `0.10` | Initial baseline weight for degree tier match |
| `ALPHA_SKILL_WEIGHT` | `float` | `0.80` | Experimental factor weighting required vs. preferred skills |
| `BETA_EXPERIENCE_PENALTY` | `float` | `1.50` | Experimental exponential decay factor for tenure deficit |
| `FITMENT_STRONG_THRESHOLD` | `float` | `0.75` | Experimental cutoff for strong role fitment classification |
| `FITMENT_MODERATE_THRESHOLD` | `float` | `0.50` | Experimental cutoff for moderate role fitment classification |

---

## Development Phases Sequence

1. **Phase 1: Project Foundation (Completed)**
2. Phase 2: Supabase Database + Storage
3. Phase 3: Document Parsing
4. Phase 4: LLM Structured Extraction
5. Phase 5: Sentence Transformer Embeddings
6. Phase 6: FAISS Vector Index
7. Phase 7: Multi-Role Fitment Engine
8. Phase 8: Explainability Engine
9. Phase 9: Bulk Processing
10. Phase 10: Recruiter Frontend
11. Phase 11: Search, Filtering and Ranking
12. Phase 12: Research Evaluation
13. Phase 13: Matching Method Comparison
14. Phase 14: Testing
15. Phase 15: Security
16. Phase 16: Performance Benchmarking
17. Phase 17: Final Integration and Polish
