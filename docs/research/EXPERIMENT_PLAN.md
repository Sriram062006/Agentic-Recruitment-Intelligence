# Academic Research Experimentation Plan

**Project:** Agentic AI Recruitment Intelligence Platform for Large-Scale Multi-Role Candidate Evaluation  
**Document:** Research Experimentation Plan & Protocol  
**Version:** 1.0.0  
**Status:** Approved & Executed

---

## 1. Research Objectives & Hypotheses

The primary research objective is to empirically evaluate a scalable, multi-role recruitment intelligence platform that evaluates a pool of $N$ candidate resumes against $M$ heterogeneous job specifications, producing an $N \times M$ evaluation matrix.

### Core Hypotheses
1. **Hypothesis 1 (Deterministic Integrity):** Decoupling LLM semantic extraction from multi-criteria fitment calculation ensures 100% deterministic reproducibility across multiple runs without prompt drift or score hallucination.
2. **Hypothesis 2 (Multi-Criteria Expressiveness):** A composite scoring model combining dense semantic similarity ($S_{\text{sem}}$), set-theoretic skill recall with penalty factors ($S_{\text{skill}}$), exponential tenure shortfall penalty ($S_{\text{exp}}$), and hierarchical qualification matching ($S_{\text{qual}}$) captures nuanced candidate suitability better than unimodal lexical matching or pure cosine similarity.
3. **Hypothesis 3 (Linear $N \times M$ Scalability):** Dense candidate vector pre-indexing combined with inner-product FAISS lookups allows evaluation latency to scale as $\mathcal{O}(N \cdot M)$ with sub-5ms per evaluation pair throughput.

---

## 2. Experimental Methodology & Validation Matrix

```
[Candidate Documents (PDF/DOCX)]      [Job Specifications (Text/PDF)]
               |                                      |
               v                                      v
   Document Text Sanitizer                Structured Profile Extractor
               |                                      |
               v                                      v
    Canonical Candidate Profile              Canonical Job Profile
               |                                      |
               v                                      v
  Dense Representation Builder            Dense Representation Builder
               |                                      |
               v                                      v
  SentenceTransformer (all-MiniLM-L6-v2)  SentenceTransformer (all-MiniLM-L6-v2)
               |                                      |
               v                                      |
     FAISS Index (Inner Product) <--------------------+
               |
               v (Cosine-Equivalent Similarity)
  +-------------------------------------------------------+
  |        Deterministic Multi-Criteria Scorer            |
  |  - S_sem (35%)                                        |
  |  - S_skill (35%, alpha=0.80)                          |
  |  - S_exp (20%, beta=1.50)                             |
  |  - S_qual (10%, ordinal tier map)                     |
  +-------------------------------------------------------+
               |
               v
  [N x M Matrix | Role Rankings | Auditable Explainability]
```

---

## 3. Evaluation Dimensions & Cardinalities

| Phase | Cardinality | Purpose | Status |
| :--- | :--- | :--- | :---: |
| **Phase 5** | $1 \times 1$ Pairs (3 pairs) | Exact mathematical scoring verification vs independent calculations | **MEASURED** |
| **Phase 6** | $1 \text{ candidate} \times 1 \text{ job}$ | Unit pipeline persistence and integrity verification | **MEASURED** |
| **Phase 7** | $1 \text{ candidate} \times 5 \text{ jobs}$ | Single-candidate multi-role evaluation; UUID reuse; score variance | **MEASURED** |
| **Phase 8** | $2 \text{ candidates} \times 3 \text{ jobs}$ | Small matrix verification; duplicate pair detection | **MEASURED** |
| **Phase 9** | $10 \text{ candidates} \times 5 \text{ jobs}$ | Enterprise benchmark; throughput, memory, latency at 50 pairs | **MEASURED** |
| **Phase 11**| Immutability Test | Configuration change isolation; historical score freeze verification | **MEASURED** |
| **Phase 15**| Performance Profiling | Sub-millisecond latency breakdown across all pipeline modules | **MEASURED** |
| **Phase 16**| Weight Sensitivity Ablation | Sensitivity analysis across 4 weight configurations | **MEASURED** |

---

## 4. Ground Truth Labeling Protocol (Required for Future IR Benchmark)

Quantitative Information Retrieval metrics (Precision@K, Recall@K, MRR, NDCG@K) require independent human relevance judgments. The formal protocol requires:
- **Judges:** At least 2 independent technical recruitment specialists.
- **Scale:** 4-point graded relevance:
  - `3` (Highly Relevant): Exceeds all mandatory technical and tenure requirements.
  - `2` (Viable / Relevant): Meets core mandatory skills with minor non-critical gaps.
  - `1` (Marginal / Low): Transferable background but significant tenure or skill deficits.
  - `0` (Irrelevant): No meaningful overlap with role requirements.
- **Inter-Annotator Agreement:** Measured via Cohen's Kappa ($\kappa \ge 0.70$) prior to calculating ranking accuracy.
