"""
Academic Research Evaluation and Matching Method Comparison Framework.
Calculates Precision@K, Recall@K, MRR, and NDCG@K.
Compares:
1. Method A: Pure Keyword / Rule-Based Matcher
2. Method B: Pure Semantic Similarity Matcher (FAISS)
3. Method C: Deterministic Hybrid Scorer (The Proposed Platform)
"""

import math
import time
from typing import Dict, List, Set, Tuple
from uuid import UUID, uuid4

from app.pipeline.scorer import (
    calculate_deterministic_fitment,
    compute_skill_overlap_score,
)
from app.schemas.candidate import CandidateProfile
from app.schemas.evaluation import FitmentWeightsConfig, HeuristicConfig
from app.schemas.job import JobProfile
from app.services.embeddings.sentence_transformer import SentenceTransformerService
from app.services.vector_store.faiss_store import FAISSVectorStore


def calculate_precision_at_k(recommended_ids: List[UUID], relevant_ids: Set[UUID], k: int) -> float:
    """Calculates Precision@K = (relevant in top K) / K."""
    if k <= 0:
        return 0.0
    top_k = recommended_ids[:k]
    hits = sum(1 for cid in top_k if cid in relevant_ids)
    return round(hits / k, 4)


def calculate_recall_at_k(recommended_ids: List[UUID], relevant_ids: Set[UUID], k: int) -> float:
    """Calculates Recall@K = (relevant in top K) / (total relevant)."""
    if len(relevant_ids) == 0:
        return 1.0
    top_k = recommended_ids[:k]
    hits = sum(1 for cid in top_k if cid in relevant_ids)
    return round(hits / len(relevant_ids), 4)


def calculate_mrr(recommended_ids: List[UUID], relevant_ids: Set[UUID]) -> float:
    """Calculates Mean Reciprocal Rank (MRR) = 1 / rank of first relevant candidate."""
    for idx, cid in enumerate(recommended_ids, start=1):
        if cid in relevant_ids:
            return round(1.0 / idx, 4)
    return 0.0


def calculate_ndcg_at_k(
    recommended_ids: List[UUID], relevance_grades: Dict[UUID, float], k: int
) -> float:
    """Calculates Normalized Discounted Cumulative Gain at K (NDCG@K)."""
    if k <= 0 or not relevance_grades:
        return 0.0

    top_k = recommended_ids[:k]
    dcg = 0.0
    for idx, cid in enumerate(top_k, start=1):
        rel = relevance_grades.get(cid, 0.0)
        dcg += (2.0**rel - 1.0) / math.log2(idx + 1)

    # Calculate Ideal DCG (IDCG)
    ideal_rels = sorted(relevance_grades.values(), reverse=True)[:k]
    idcg = 0.0
    for idx, rel in enumerate(ideal_rels, start=1):
        idcg += (2.0**rel - 1.0) / math.log2(idx + 1)

    if idcg == 0.0:
        return 0.0
    return round(dcg / idcg, 4)


class ResearchBenchmarkSuite:
    """Harness to run empirical comparison across Keyword, Semantic, and Hybrid matching."""

    def __init__(self):
        self.embedding_service = SentenceTransformerService()

    def run_method_comparison(
        self,
        candidates: List[Tuple[UUID, CandidateProfile]],
        job: JobProfile,
        ground_truth_relevance: Dict[UUID, float],  # 0.0 to 3.0 scale
        k: int = 5,
    ) -> Dict[str, Dict[str, float]]:
        """
        Runs Keyword, Semantic, and Hybrid ranking against the same job and candidate pool,
        evaluating Precision@K, Recall@K, MRR, and NDCG@K.
        """
        relevant_set = {cid for cid, grade in ground_truth_relevance.items() if grade >= 2.0}

        # ----------------- Method A: Keyword / Rule-Based -----------------
        start_kw = time.perf_counter()
        keyword_ranked = []
        for cid, profile in candidates:
            score, _, _, _, _ = compute_skill_overlap_score(
                candidate_skills=profile.skills,
                required_skills=job.required_skills,
                preferred_skills=job.preferred_skills,
                alpha=0.80,
            )
            keyword_ranked.append((cid, score))
        keyword_ranked.sort(key=lambda x: x[1], reverse=True)
        kw_ids = [x[0] for x in keyword_ranked]
        kw_latency = (time.perf_counter() - start_kw) * 1000

        # ----------------- Method B: Pure Semantic (FAISS / Vector) -----------------
        start_sem = time.perf_counter()
        job_text = f"{job.title}. {', '.join(job.required_skills)}. {job.summary}"
        job_vec = self.embedding_service.embed_text(job_text)

        semantic_ranked = []
        for cid, profile in candidates:
            cand_text = f"{profile.full_name}. {', '.join(profile.skills)}. {profile.summary or ''}"
            cand_vec = self.embedding_service.embed_text(cand_text)
            sim = float(np_dot := max(0.0, float(cand_vec.dot(job_vec))))
            semantic_ranked.append((cid, sim))
        semantic_ranked.sort(key=lambda x: x[1], reverse=True)
        sem_ids = [x[0] for x in semantic_ranked]
        sem_latency = (time.perf_counter() - start_sem) * 1000

        # ----------------- Method C: Proposed Hybrid Architecture -----------------
        start_hyb = time.perf_counter()
        weights = FitmentWeightsConfig(
            semantic_weight=0.35, skill_weight=0.35, experience_weight=0.20, qualification_weight=0.10
        )
        heuristics = HeuristicConfig()

        hybrid_ranked = []
        for (cid, profile), sem_tuple in zip(candidates, semantic_ranked):
            sim = sem_tuple[1]
            fitment = calculate_deterministic_fitment(
                candidate=profile,
                job=job,
                semantic_similarity=sim,
                weights=weights,
                heuristics=heuristics,
            )
            hybrid_ranked.append((cid, fitment["composite_score"]))
        hybrid_ranked.sort(key=lambda x: x[1], reverse=True)
        hyb_ids = [x[0] for x in hybrid_ranked]
        hyb_latency = (time.perf_counter() - start_hyb) * 1000

        # Compute Metrics
        return {
            "keyword": {
                "precision_at_k": calculate_precision_at_k(kw_ids, relevant_set, k),
                "recall_at_k": calculate_recall_at_k(kw_ids, relevant_set, k),
                "mrr": calculate_mrr(kw_ids, relevant_set),
                "ndcg_at_k": calculate_ndcg_at_k(kw_ids, ground_truth_relevance, k),
                "latency_ms": round(kw_latency, 2),
            },
            "semantic": {
                "precision_at_k": calculate_precision_at_k(sem_ids, relevant_set, k),
                "recall_at_k": calculate_recall_at_k(sem_ids, relevant_set, k),
                "mrr": calculate_mrr(sem_ids, relevant_set),
                "ndcg_at_k": calculate_ndcg_at_k(sem_ids, ground_truth_relevance, k),
                "latency_ms": round(sem_latency, 2),
            },
            "hybrid": {
                "precision_at_k": calculate_precision_at_k(hyb_ids, relevant_set, k),
                "recall_at_k": calculate_recall_at_k(hyb_ids, relevant_set, k),
                "mrr": calculate_mrr(hyb_ids, relevant_set),
                "ndcg_at_k": calculate_ndcg_at_k(hyb_ids, ground_truth_relevance, k),
                "latency_ms": round(hyb_latency, 2),
            },
        }
