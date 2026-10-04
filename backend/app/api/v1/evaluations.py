"""
API endpoints for Multi-Role Candidate Evaluation, Matrix Retrieval,
Role Leaderboards, and Grounded Explainability.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, status

from app.core.logging import get_logger
from app.core.orchestrator import PipelineOrchestrator
from app.schemas.evaluation import (
    EvaluationConfigRequest,
    EvaluationMatrixResponse,
    EvaluationResultItem,
    EvaluationRunResponse,
    ExplainabilityPayload,
    LeaderboardEntry,
)
from app.services.database.repositories.candidate_repo import CandidateRepository
from app.services.database.repositories.evaluation_repo import EvaluationRepository
from app.services.database.repositories.job_repo import JobRepository

logger = get_logger("api_evaluations")
router = APIRouter(prefix="/evaluations", tags=["Multi-Role Evaluations"])

evaluation_repo = EvaluationRepository()
job_repo = JobRepository()
candidate_repo = CandidateRepository()
orchestrator = PipelineOrchestrator(
    job_repo=job_repo,
    candidate_repo=candidate_repo,
    evaluation_repo=evaluation_repo,
)


@router.post(
    "/run",
    response_model=EvaluationRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create and execute a Multi-Role Candidate Evaluation run",
)
def create_evaluation_run(request: EvaluationConfigRequest) -> EvaluationRunResponse:
    """Executes N candidates x M jobs matrix evaluation with configurable weights."""
    try:
        run_record = orchestrator.execute_multi_role_evaluation(request)
        return run_record
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error("Multi-role evaluation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get(
    "/runs/{run_id}/status",
    response_model=EvaluationRunResponse,
    summary="Get status and counts for an evaluation run",
)
def get_run_status(run_id: UUID) -> EvaluationRunResponse:
    """Retrieves progress and completion state of an evaluation run."""
    run_record = evaluation_repo.get_run(run_id)
    if not run_record:
        raise HTTPException(status_code=404, detail=f"Evaluation run '{run_id}' not found")
    return run_record


@router.get(
    "/runs/{run_id}/matrix",
    response_model=EvaluationMatrixResponse,
    summary="Retrieve N x M Multi-Role Fitment Matrix",
)
def get_evaluation_matrix(run_id: UUID) -> EvaluationMatrixResponse:
    """Returns the complete N candidates x M jobs evaluation matrix grid."""
    run_record = evaluation_repo.get_run(run_id)
    if not run_record:
        raise HTTPException(status_code=404, detail=f"Evaluation run '{run_id}' not found")

    cells = evaluation_repo.get_matrix_cells(run_id)
    all_jobs = job_repo.list_all(limit=500)
    all_candidates = candidate_repo.list_all(limit=1000)

    # Filter to only jobs & candidates present in this run
    cand_ids = {c.candidate_id for c in cells}
    job_ids = {c.job_id for c in cells}

    cand_list = [{"id": str(c.id), "name": c.structured_profile.full_name} for c in all_candidates if c.id in cand_ids]
    job_list = [{"id": str(j.id), "title": j.title} for j in all_jobs if j.id in job_ids]

    return EvaluationMatrixResponse(
        run_id=run_id,
        candidates=cand_list,
        jobs=job_list,
        cells=cells,
        total_evaluations=len(cells),
    )


@router.get(
    "/runs/{run_id}/jobs/{job_id}/ranking",
    response_model=List[LeaderboardEntry],
    summary="Retrieve ranked candidate leaderboard for a specific role",
)
def get_role_leaderboard(
    run_id: UUID,
    job_id: UUID,
    limit: int = Query(default=50, ge=1, le=500),
) -> List[LeaderboardEntry]:
    """Returns candidates ranked by composite fitment score for a specific job description."""
    return evaluation_repo.get_leaderboard_for_job(run_id=run_id, job_id=job_id, limit=limit)


@router.get(
    "/runs/{run_id}/candidates/{candidate_id}/jobs/{job_id}/explainability",
    response_model=ExplainabilityPayload,
    summary="Retrieve grounded fitment explanation for a Candidate-Role pair",
)
def get_evaluation_explainability(
    run_id: UUID,
    candidate_id: UUID,
    job_id: UUID,
) -> ExplainabilityPayload:
    """Returns auditable evidence breakdown: matched/missing skills, experience delta, and rationale."""
    eval_item = evaluation_repo.get_candidate_evaluation_for_job(
        run_id=run_id, candidate_id=candidate_id, job_id=job_id
    )
    if not eval_item:
        raise HTTPException(
            status_code=404,
            detail=f"Evaluation result for candidate '{candidate_id}' and job '{job_id}' in run '{run_id}' not found",
        )
    return eval_item.explainability
