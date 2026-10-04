"""
Automated Performance Benchmarking Script.
Measures cold-start vs warm inference, parsing latency, embedding time, FAISS search,
scoring throughput, database persistence, and end-to-end runtime.
"""

import os
import sys
import time
from pathlib import Path
from uuid import uuid4

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.orchestrator import PipelineOrchestrator
from app.parsers.factory import parse_document
from app.pipeline.scorer import calculate_deterministic_fitment
from app.schemas.candidate import CandidateProfile
from app.schemas.evaluation import EvaluationConfigRequest, FitmentWeightsConfig, HeuristicConfig
from app.schemas.job import JobProfile
from app.services.database.repositories.candidate_repo import CandidateRepository
from app.services.database.repositories.evaluation_repo import EvaluationRepository
from app.services.database.repositories.job_repo import JobRepository
from app.services.embeddings.sentence_transformer import SentenceTransformerService
from app.services.llm.gemini_provider import GeminiLLMProvider
from app.services.vector_store.faiss_store import FAISSVectorStore
from tests.test_parsers import create_sample_docx_bytes, create_sample_pdf_bytes


def run_comprehensive_benchmark():
    print("=" * 70)
    print("STARTING RECRUITMENT INTELLIGENCE PERFORMANCE BENCHMARK")
    print("=" * 70)

    results = {}

    # 1. Parsing Benchmark
    pdf_bytes = create_sample_pdf_bytes("Staff AI Engineer with Python, PyTorch, FAISS, Docker, and Kubernetes. 6 years experience.")
    docx_bytes = create_sample_docx_bytes(["Cloud Architect with AWS, Kubernetes, Terraform, and Go. 8 years experience."])

    t0 = time.perf_counter()
    for _ in range(10):
        parse_document(pdf_bytes, "sample.pdf")
    pdf_parse_time = (time.perf_counter() - t0) / 10 * 1000  # ms
    results["pdf_parse_ms"] = round(pdf_parse_time, 2)

    t0 = time.perf_counter()
    for _ in range(10):
        parse_document(docx_bytes, "sample.docx")
    docx_parse_time = (time.perf_counter() - t0) / 10 * 1000  # ms
    results["docx_parse_ms"] = round(docx_parse_time, 2)

    # 2. LLM Extraction Benchmark (Fallback / Provider)
    llm = GeminiLLMProvider()
    sample_raw = "Alex Johnson. Email: alex@example.com. Phone: 555-0199. Senior Engineer with 5 years in Python, FastAPI, Docker. Bachelor's in CS."
    t0 = time.perf_counter()
    for _ in range(10):
        llm.extract_candidate_profile(sample_raw)
    llm_cand_time = (time.perf_counter() - t0) / 10 * 1000
    results["llm_cand_extract_ms"] = round(llm_cand_time, 2)

    # 3. Embedding Model Benchmark (Cold-start vs Warm)
    t0 = time.perf_counter()
    embed_service = SentenceTransformerService()
    cold_start_time = embed_service.initialization_time_seconds
    results["embedding_cold_start_sec"] = round(cold_start_time, 3)

    # Warm single inference
    t0 = time.perf_counter()
    for _ in range(10):
        embed_service.embed_text("Senior Full Stack Developer specializing in React and Node.js with 5 years experience.")
    warm_single_ms = (time.perf_counter() - t0) / 10 * 1000
    results["embedding_warm_single_ms"] = round(warm_single_ms, 2)

    # Warm batch inference (10 items)
    batch_texts = [f"Candidate {i} with skill set {i}" for i in range(10)]
    t0 = time.perf_counter()
    embed_service.embed_batch(batch_texts)
    batch_10_ms = (time.perf_counter() - t0) * 1000
    results["embedding_batch_10_ms"] = round(batch_10_ms, 2)

    # 4. FAISS Indexing & Search Benchmark
    test_faiss_path = "data/faiss/benchmark.index"
    faiss_store = FAISSVectorStore(dimension=384, index_file_path=test_faiss_path)

    cand_uuids = [uuid4() for _ in range(50)]
    cand_vecs = embed_service.embed_batch([f"Profile {i} in Software Development" for i in range(50)])

    t0 = time.perf_counter()
    faiss_store.batch_add(cand_uuids, cand_vecs)
    indexing_50_ms = (time.perf_counter() - t0) * 1000
    results["faiss_index_50_ms"] = round(indexing_50_ms, 2)

    # Search top-K
    query_vec = embed_service.embed_text("Lead Python Developer")
    t0 = time.perf_counter()
    for _ in range(50):
        faiss_store.search_top_k(query_vec, k=10)
    search_k10_ms = (time.perf_counter() - t0) / 50 * 1000
    results["faiss_search_k10_ms"] = round(search_k10_ms, 3)

    # 5. Deterministic Scoring Latency
    c_prof = CandidateProfile(full_name="Bench Cand", total_experience_years=4.0, skills=["Python", "FastAPI", "Docker"])
    j_prof = JobProfile(title="Bench Job", required_skills=["Python", "Docker"], min_experience_years=3.0)
    weights = FitmentWeightsConfig()
    heuristics = HeuristicConfig()

    t0 = time.perf_counter()
    for _ in range(100):
        calculate_deterministic_fitment(c_prof, j_prof, 0.85, weights, heuristics)
    scoring_100_ms = (time.perf_counter() - t0) / 100 * 1000
    results["scoring_single_ms"] = round(scoring_100_ms, 4)

    # 6. Database Persistence Latency with valid foreign keys
    job_repo = JobRepository()
    cand_repo = CandidateRepository()
    eval_repo = EvaluationRepository()

    test_job = job_repo.create(
        title="DB Test Job", department="Eng", storage_path="p", raw_content="c",
        structured_profile=JobProfile(title="DB Test Job", required_skills=["Python"])
    )
    test_cands = [
        cand_repo.create(
            file_name=f"db_cand_{i}.pdf", storage_path="p", file_hash=uuid4().hex, raw_text="t",
            structured_profile=CandidateProfile(full_name=f"DB Cand {i}", skills=["Python"])
        )
        for i in range(50)
    ]
    test_run = eval_repo.create_run(total_candidates=50, total_jobs=1, config={})

    dummy_evals = [
        {
            "id": uuid4(),
            "run_id": test_run.id,
            "candidate_id": tc.id,
            "job_id": test_job.id,
            "composite_score": 0.82,
            "semantic_score": 0.80,
            "skill_score": 0.85,
            "experience_score": 0.90,
            "qualification_score": 1.0,
            "rank_in_role": idx + 1,
            "explainability": {"matched_skills": ["Python"], "missing_skills": []},
        }
        for idx, tc in enumerate(test_cands)
    ]
    t0 = time.perf_counter()
    eval_repo.save_bulk_evaluations(dummy_evals)
    db_save_50_ms = (time.perf_counter() - t0) * 1000
    results["db_save_50_evals_ms"] = round(db_save_50_ms, 2)

    # Cleanup persistence test
    job_repo.delete(test_job.id)
    for tc in test_cands:
        cand_repo.delete(tc.id)

    # 7. End-to-End Orchestrator Throughput (10 candidates x 5 jobs = 50 evaluations)
    orch = PipelineOrchestrator(
        job_repo=job_repo,
        candidate_repo=cand_repo,
        evaluation_repo=eval_repo,
        embedding_service=embed_service,
        faiss_store=faiss_store,
        llm_provider=llm,
    )

    bench_jobs = [
        job_repo.create(
            title=f"Benchmark Role {j}",
            department="Eng",
            storage_path="p",
            raw_content="c",
            structured_profile=JobProfile(title=f"Role {j}", required_skills=["Python", "SQL"], min_experience_years=2.0),
        )
        for j in range(5)
    ]
    bench_cands = [
        cand_repo.create(
            file_name=f"cand_{c}.pdf",
            storage_path="p",
            file_hash=uuid4().hex,
            raw_text="t",
            structured_profile=CandidateProfile(full_name=f"Cand {c}", skills=["Python", "SQL"], total_experience_years=3.0),
        )
        for c in range(10)
    ]

    t0 = time.perf_counter()
    run_res = orch.execute_multi_role_evaluation(
        EvaluationConfigRequest(
            job_ids=[j.id for j in bench_jobs],
            candidate_ids=[c.id for c in bench_cands],
        )
    )
    e2e_total_sec = time.perf_counter() - t0
    results["e2e_50_evals_sec"] = round(e2e_total_sec, 3)
    results["evaluations_per_second"] = round(50.0 / e2e_total_sec, 2)

    print("\nBENCHMARK RESULTS SUMMARY:")
    for k, v in results.items():
        print(f"  {k}: {v}")

    # Cleanup benchmark artifacts
    for j in bench_jobs:
        job_repo.delete(j.id)
    for c in bench_cands:
        cand_repo.delete(c.id)

    return results


if __name__ == "__main__":
    run_comprehensive_benchmark()
