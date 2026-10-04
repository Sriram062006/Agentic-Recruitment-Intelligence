"""
Tests for Academic Research Evaluation Metrics and Matching Method Comparison.
Verifies Precision@K, Recall@K, MRR, NDCG@K, and empirical comparisons.
"""

from uuid import uuid4
import pytest

from app.pipeline.benchmark import (
    ResearchBenchmarkSuite,
    calculate_mrr,
    calculate_ndcg_at_k,
    calculate_precision_at_k,
    calculate_recall_at_k,
)
from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobProfile


def test_information_retrieval_metrics():
    doc1 = uuid4()
    doc2 = uuid4()
    doc3 = uuid4()
    doc4 = uuid4()
    doc5 = uuid4()

    recommended = [doc1, doc2, doc3, doc4, doc5]
    relevant = {doc1, doc3, doc5}  # 3 relevant documents

    # Precision@3 = 2 / 3 (doc1, doc3)
    p3 = calculate_precision_at_k(recommended, relevant, k=3)
    assert p3 == round(2 / 3, 4)

    # Recall@3 = 2 / 3
    r3 = calculate_recall_at_k(recommended, relevant, k=3)
    assert r3 == round(2 / 3, 4)

    # MRR = 1 / 1 = 1.0 (doc1 is relevant)
    mrr = calculate_mrr(recommended, relevant)
    assert mrr == 1.0

    # NDCG@3 with relevance grades
    grades = {doc1: 3.0, doc2: 0.0, doc3: 2.0, doc4: 0.0, doc5: 1.0}
    ndcg3 = calculate_ndcg_at_k(recommended, grades, k=3)
    assert 0.0 <= ndcg3 <= 1.0


def test_matching_method_comparison_experiment():
    suite = ResearchBenchmarkSuite()

    job = JobProfile(
        title="Full Stack Python Engineer",
        required_skills=["Python", "FastAPI", "React", "TypeScript"],
        min_experience_years=3.0,
        required_qualification="Bachelor's",
    )

    c1 = (uuid4(), CandidateProfile(full_name="High Hybrid Match", total_experience_years=4.0, skills=["Python", "FastAPI", "React", "TypeScript", "PostgreSQL"]))
    c2 = (uuid4(), CandidateProfile(full_name="Keyword Match Only Low Exp", total_experience_years=0.5, skills=["Python", "FastAPI", "React", "TypeScript"]))
    c3 = (uuid4(), CandidateProfile(full_name="Semantic Match Low Keywords", total_experience_years=5.0, skills=["Django", "Vue", "JavaScript", "SQL"]))
    c4 = (uuid4(), CandidateProfile(full_name="Unrelated Profile", total_experience_years=2.0, skills=["C++", "Embedded", "Firmware"]))

    candidates = [c1, c2, c3, c4]
    ground_truth = {
        c1[0]: 3.0,  # Highly relevant
        c2[0]: 1.0,  # Underqualified tenure
        c3[0]: 2.0,  # Transferable skills
        c4[0]: 0.0,  # Irrelevant
    }

    results = suite.run_method_comparison(candidates, job, ground_truth, k=2)

    assert "keyword" in results
    assert "semantic" in results
    assert "hybrid" in results

    # Verify that all metrics are computed and bounded
    for method, metrics in results.items():
        assert 0.0 <= metrics["precision_at_k"] <= 1.0
        assert 0.0 <= metrics["recall_at_k"] <= 1.0
        assert 0.0 <= metrics["mrr"] <= 1.0
        assert 0.0 <= metrics["ndcg_at_k"] <= 1.0
        assert metrics["latency_ms"] >= 0.0
