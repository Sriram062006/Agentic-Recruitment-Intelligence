"""
Recruitment Intelligence Orchestrator.
Coordinates bulk document ingestion, canonical candidate profiling,
embedding generation, FAISS indexing, multi-role matrix matching,
deterministic hybrid scoring, role-wise ranking, and grounded explainability.

Core Research Invariant:
1 Candidate -> 1 Canonical Profile -> evaluated across M jobs -> M evaluations (N x M matrix).
"""

from typing import Dict, List, Optional
from uuid import UUID, uuid4

from app.config import get_settings
from app.core.logging import get_logger
from app.pipeline.explainer import generate_fitment_explanation
from app.pipeline.scorer import calculate_deterministic_fitment
from app.schemas.candidate import CandidateProfile, CandidateResponse
from app.schemas.common import RunStatus
from app.schemas.evaluation import (
    EvaluationConfigRequest,
    EvaluationRunResponse,
    FitmentWeightsConfig,
    HeuristicConfig,
)
from app.schemas.job import JobProfile, JobResponse
from app.services.database.repositories.candidate_repo import CandidateRepository
from app.services.database.repositories.evaluation_repo import EvaluationRepository
from app.services.database.repositories.job_repo import JobRepository
from app.services.embeddings.sentence_transformer import SentenceTransformerService
from app.services.llm.gemini_provider import GeminiLLMProvider
from app.services.vector_store.faiss_store import FAISSVectorStore, get_faiss_store

logger = get_logger("orchestrator")


def build_candidate_semantic_text(profile: CandidateProfile) -> str:
    """Builds a dense textual representation of candidate qualifications for embedding."""
    skills_str = ", ".join(profile.skills)
    exp_titles = [e.title for e in profile.experience_history if e.title]
    exp_str = ", ".join(exp_titles)
    return (
        f"Candidate: {profile.full_name}. "
        f"Verified Experience: {profile.total_experience_years} years. "
        f"Highest Qualification: {profile.highest_qualification}. "
        f"Roles: {exp_str}. "
        f"Key Skills: {skills_str}. "
        f"Summary: {profile.summary or ''}"
    ).strip()


def build_job_semantic_text(profile: JobProfile) -> str:
    """Builds a dense textual representation of job role requirements for embedding."""
    req_skills = ", ".join(profile.required_skills)
    pref_skills = ", ".join(profile.preferred_skills)
    resp = "; ".join(profile.key_responsibilities[:3])
    return (
        f"Job Title: {profile.title}. "
        f"Department: {profile.department or 'General'}. "
        f"Minimum Experience: {profile.min_experience_years} years. "
        f"Required Degree: {profile.required_qualification}. "
        f"Required Skills: {req_skills}. "
        f"Preferred Skills: {pref_skills}. "
        f"Responsibilities: {resp}. "
        f"Overview: {profile.summary}"
    ).strip()


class PipelineOrchestrator:
    def __init__(
        self,
        job_repo: Optional[JobRepository] = None,
        candidate_repo: Optional[CandidateRepository] = None,
        evaluation_repo: Optional[EvaluationRepository] = None,
        embedding_service: Optional[SentenceTransformerService] = None,
        faiss_store: Optional[FAISSVectorStore] = None,
        llm_provider: Optional[GeminiLLMProvider] = None,
    ):
        self.job_repo = job_repo or JobRepository()
        self.candidate_repo = candidate_repo or CandidateRepository()
        self.evaluation_repo = evaluation_repo or EvaluationRepository()
        self.embedding_service = embedding_service or SentenceTransformerService()
        self.faiss_store = faiss_store or get_faiss_store()
        self.llm_provider = llm_provider or GeminiLLMProvider()

    def index_candidate(self, candidate_response: CandidateResponse) -> int:
        """Embeds and indexes a single canonical candidate profile into FAISS."""
        text_rep = build_candidate_semantic_text(candidate_response.structured_profile)
        embedding = self.embedding_service.embed_text(text_rep)
        faiss_id = self.faiss_store.add_candidate(candidate_response.id, embedding)
        self.candidate_repo.update_faiss_id(candidate_response.id, faiss_id)
        return faiss_id

    def execute_multi_role_evaluation(
        self,
        request: EvaluationConfigRequest,
        run_id: Optional[UUID] = None,
    ) -> EvaluationRunResponse:
        """
        Executes N candidates x M jobs matrix evaluation.
        Produces exactly N x M role-wise candidate evaluations.
        """
        settings = get_settings()
        rid = run_id or uuid4()

        # 1. Resolve Target Jobs
        all_jobs = self.job_repo.list_all(limit=500)
        if request.job_ids:
            target_jobs = [j for j in all_jobs if j.id in request.job_ids]
        else:
            target_jobs = all_jobs

        if not target_jobs:
            raise ValueError("No active job descriptions found for evaluation run")

        # 2. Resolve Target Candidates (Canonical Profiles)
        all_candidates = self.candidate_repo.list_all(limit=1000)
        if request.candidate_ids:
            target_candidates = [c for c in all_candidates if c.id in request.candidate_ids]
        else:
            target_candidates = all_candidates

        if not target_candidates:
            raise ValueError("No candidates found in pool for evaluation run")

        # 3. Resolve Configurable Weights & Heuristics
        weights = request.weights or FitmentWeightsConfig(
            semantic_weight=settings.semantic_weight,
            skill_weight=settings.skill_weight,
            experience_weight=settings.experience_weight,
            qualification_weight=settings.qualification_weight,
        )
        heuristics = request.heuristics or HeuristicConfig(
            alpha_skill_weight=settings.alpha_skill_weight,
            beta_experience_penalty=settings.beta_experience_penalty,
            fitment_strong_threshold=settings.fitment_strong_threshold,
            fitment_moderate_threshold=settings.fitment_moderate_threshold,
        )

        config_snapshot = {
            "weights": weights.model_dump(),
            "heuristics": heuristics.model_dump(),
        }

        # 4. Create Evaluation Run Record
        run_record = self.evaluation_repo.create_run(
            total_candidates=len(target_candidates),
            total_jobs=len(target_jobs),
            config=config_snapshot,
            run_id=rid,
        )
        self.evaluation_repo.update_run_status(rid, RunStatus.PROCESSING)

        try:
            # 5. Ensure All Target Candidates are Indexed in FAISS
            for cand in target_candidates:
                if cand.faiss_index_id is None or cand.id not in self.faiss_store._uuid_to_id:
                    self.index_candidate(cand)

            all_evaluations: List[Dict] = []

            # 6. Evaluate Each Job independently across all Candidates
            for job in target_jobs:
                job_semantic_text = build_job_semantic_text(job.structured_profile)
                job_vector = self.embedding_service.embed_text(job_semantic_text)

                job_eval_candidates = []

                for cand in target_candidates:
                    # Semantic Cosine Similarity via FAISS Inner Product
                    sim = self.faiss_store.compute_similarity(cand.id, job_vector)

                    # Deterministic Fitment Scoring
                    fitment_signals = calculate_deterministic_fitment(
                        candidate=cand.structured_profile,
                        job=job.structured_profile,
                        semantic_similarity=sim,
                        weights=weights,
                        heuristics=heuristics,
                    )

                    # Grounded Explainability Synthesis
                    explainability = generate_fitment_explanation(
                        candidate=cand.structured_profile,
                        job=job.structured_profile,
                        fitment_signals=fitment_signals,
                        llm_provider=self.llm_provider,
                    )

                    job_eval_candidates.append(
                        {
                            "id": uuid4(),
                            "run_id": rid,
                            "candidate_id": cand.id,
                            "job_id": job.id,
                            "composite_score": fitment_signals["composite_score"],
                            "semantic_score": fitment_signals["semantic_score"],
                            "skill_score": fitment_signals["skill_score"],
                            "experience_score": fitment_signals["experience_score"],
                            "qualification_score": fitment_signals["qualification_score"],
                            "explainability": explainability.model_dump(),
                        }
                    )

                # 7. Role-Wise Ranking: Sort candidates by composite_score DESC
                job_eval_candidates.sort(key=lambda x: x["composite_score"], reverse=True)
                for rank_idx, eval_item in enumerate(job_eval_candidates, start=1):
                    eval_item["rank_in_role"] = rank_idx
                    all_evaluations.append(eval_item)

            # 8. Save All N x M Evaluation Records
            self.evaluation_repo.save_bulk_evaluations(all_evaluations)
            self.evaluation_repo.update_run_status(rid, RunStatus.COMPLETED)
            logger.info(
                "Evaluation run %s completed: %d candidates x %d jobs = %d evaluations",
                rid,
                len(target_candidates),
                len(target_jobs),
                len(all_evaluations),
            )
            return self.evaluation_repo.get_run(rid)  # type: ignore

        except Exception as e:
            logger.error("Evaluation run %s failed: %s", rid, e, exc_info=True)
            self.evaluation_repo.update_run_status(rid, RunStatus.FAILED, error_message=str(e))
            raise
