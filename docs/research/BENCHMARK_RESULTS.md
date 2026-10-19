# Empirical Benchmark Results & IR Analysis

**Project:** Agentic AI Recruitment Intelligence Platform for Large-Scale Multi-Role Candidate Evaluation  
**Document:** Method Comparison, Information Retrieval Framework, and Empirical Findings  
**Status:** MEASURED & ACADEMICALLY AUDITED

---

## 1. Classification of Experimental Metrics

In accordance with strict academic guidelines, all reported metrics are partitioned into verified categories:

- **MEASURED:** Directly captured from automated execution on real candidate CVs and real JDs.
- **DERIVED:** Mathematically computed from measured values using formal definitions.
- **NOT AVAILABLE:** Requires external human consensus labels that have not yet been produced.

| Metric / Dimension | Value / Status | Academic Category | Evidence Source |
| :--- | :--- | :---: | :--- |
| **Candidate Parsing Latency** | 11.08 ms | **MEASURED** | Phase 15 automated test |
| **Candidate Extraction Latency** | 35.10 ms | **MEASURED** | Phase 15 automated test |
| **Embedding Generation Latency** | 33.97 ms | **MEASURED** | Phase 15 automated test |
| **FAISS Query Latency** | 14.27 ms | **MEASURED** | Phase 15 automated test |
| **Deterministic Scoring Latency** | 0.05 ms | **MEASURED** | Phase 15 automated test |
| **$10 \times 5$ Batch Evaluation Time** | 0.174 s (50 pairs) | **MEASURED** | Phase 9 automated test |
| **System Evaluation Throughput** | 287.68 evals / sec | **DERIVED** | $\frac{50 \text{ evaluations}}{0.1738 \text{ s}}$ |
| **Average Evaluation Time** | 3.48 ms / pair | **DERIVED** | $\frac{173.8 \text{ ms}}{50 \text{ pairs}}$ |
| **Mathematical Difference** | 0.000000 | **MEASURED** | Phase 5 independent calculation |
| **Duplicate Evaluations** | 0 | **MEASURED** | Phase 9 set cardinality verification |
| **Precision@K / Recall@K** | *Pending Human Labels* | **NOT AVAILABLE** | Requires Double-Blind Annotators |
| **NDCG@K / MRR** | *Pending Human Labels* | **NOT AVAILABLE** | Requires Graded Relevance Consensus |

---

## 2. Comparison of Matching Paradigms

The platform architecture enables three distinct retrieval and ranking paradigms:

1. **Method A — Keyword / Lexical Baseline:**
   - Evaluates set-theoretic recall between candidate canonical skills and job requirements ($S_{\text{skill}}$).
   - *Limitation:* Ignores tenure shortfalls, semantic context, and degree discrepancies. Treats a 1-year junior with a listed skill identically to a 10-year senior.
2. **Method B — Dense Semantic Vector Matching:**
   - Computes cosine similarity of dense 384-dimensional embeddings generated via `sentence-transformers/all-MiniLM-L6-v2`.
   - *Limitation:* Can exhibit semantic drift; may reward general narrative similarity while overlooking missing mandatory certifications or specific technical requirements.
3. **Method C — Deterministic Hybrid Scorer (The Proposed Platform):**
   - Synthesizes dense semantic alignment ($w_{\text{sem}} = 0.35$), structured skill overlap ($w_{\text{skill}} = 0.35$), exponential tenure penalty ($w_{\text{exp}} = 0.20$), and qualification hierarchy ($w_{\text{qual}} = 0.10$).
   - *Advantage:* Produces highly distinct role differentiation, penalizes critical experience gaps deterministically, and provides auditable evidence explanations.

---

## 3. Official Research Statement on Relevance Accuracy

> [!CAUTION]
> **Academic Benchmark Notice:**
> **Quantitative relevance accuracy (Precision, Recall, MRR, NDCG) cannot yet be claimed because validated human ground truth is unavailable.**  
> While the IR evaluation mathematical framework (`calculate_precision_at_k`, `calculate_recall_at_k`, `calculate_mrr`, `calculate_ndcg_at_k`) has been fully implemented and verified in [`app/pipeline/benchmark.py`](file:///c:/Users/srira/Downloads/Agentic-Recruitment-Intelligence/backend/app/pipeline/benchmark.py), actual relevance scores will only be published once the formal annotation protocol specified in [`DATASET.md`](file:///c:/Users/srira/Downloads/Agentic-Recruitment-Intelligence/docs/research/DATASET.md) is executed with human recruiters.
