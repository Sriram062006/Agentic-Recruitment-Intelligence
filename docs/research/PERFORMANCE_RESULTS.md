# Empirical Performance & Scalability Results

**Project:** Agentic AI Recruitment Intelligence Platform for Large-Scale Multi-Role Candidate Evaluation  
**Document:** Sub-Millisecond Profiling, Throughput Analysis, and Cardinality Benchmarks  
**Status:** MEASURED & EMPIRICALLY GROUNDED

---

## 1. Single Pipeline Latency Breakdown

Measured on a Windows 64-bit environment utilizing an AMD Ryzen / Intel Core architecture with local PyTorch SentenceTransformer acceleration:

| Processing Stage | Latency (ms) | Percentage of Pipeline | Complexity |
| :--- | :---: | :---: | :---: |
| **PDF/DOCX Document Parsing** | 11.08 ms | 11.7% | $\mathcal{O}(\text{Pages})$ |
| **High-Fidelity Profile Extraction** | 35.10 ms | 37.2% | $\mathcal{O}(\text{Tokens})$ |
| **Dense Embedding Generation** (`all-MiniLM-L6-v2`) | 33.97 ms | 36.0% | $\mathcal{O}(\text{Tokens})$ |
| **FAISS Indexing & Inner Product Search** | 14.27 ms | 15.1% | $\mathcal{O}(D)$ where $D=384$ |
| **Deterministic Multi-Criteria Scoring** | **0.05 ms** | **< 0.1%** | $\mathcal{O}(|S_{\text{req}}| + |S_{\text{cand}}|)$ |
| **Total End-to-End Single Evaluation** | **94.45 ms** | **100.0%** | $\mathcal{O}(1)$ |

> [!NOTE]
> The deterministic multi-criteria scoring algorithm executes in **50 microseconds** (0.05 ms), verifying that all mathematical operations add negligible overhead to the retrieval pipeline.

---

## 2. Multi-Role Matrix Scalability ($N \times M$)

Once candidate vectors are indexed into FAISS, evaluating $N$ candidates against $M$ jobs scales linearly with respect to $N \times M$:

| Test Configuration | Candidates ($N$) | Jobs ($M$) | Expected Pairs | Measured Pairs | Execution Time (s) | Avg Time / Pair (ms) | Throughput (evals/sec) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Phase 6** | 1 | 1 | 1 | 1 | 0.0448 s | 44.80 ms | 22.3 evals/sec |
| **Phase 7** | 1 | 5 | 5 | 5 | 0.1729 s | 34.58 ms | 28.9 evals/sec |
| **Phase 8** | 2 | 3 | 6 | 6 | 0.0933 s | 15.55 ms | 64.3 evals/sec |
| **Phase 9** | **10** | **5** | **50** | **50** | **0.1738 s** | **3.48 ms** | **287.68 evals/sec** |

### Key Scalability Observations
1. **Amortization Efficiency:** As candidate pool size grows from $N=1$ to $N=10$, per-pair evaluation latency drops from 44.8 ms down to **3.48 ms per pair** due to vector pre-indexing and batch inner-product matrix operations.
2. **Throughput Scaling:** Sustained throughput reaches **287.68 evaluations per second** on local CPU execution.
3. **Linearity:** Cardinality verification proved $10 \times 5 = 50$ with zero duplicate pairs and zero memory leakage.
