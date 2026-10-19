"""
API endpoints for Multi-Role Candidate Evaluation, Evaluation History,
Matrix Retrieval, Role Leaderboards, and Grounded Explainability.
Secured with Supabase Authentication, RBAC, and PostgreSQL Row Level Security.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import (
    AuthenticatedUser,
    require_any_authenticated,
    require_recruiter_or_admin,
)
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
def create_evaluation_run(
    request: EvaluationConfigRequest,
    user: AuthenticatedUser = Depends(require_recruiter_or_admin),
) -> EvaluationRunResponse:
    """Executes N candidates x M jobs matrix evaluation with configurable weights under recruiter ownership."""
    try:
        run_record = orchestrator.execute_multi_role_evaluation(
            request, recruiter_id=user.id, token=user.token
        )
        return run_record
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error("Multi-role evaluation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get(
    "/runs",
    response_model=List[EvaluationRunResponse],
    summary="List historical Multi-Role evaluation runs",
    description="Retrieves a list of all historical evaluation runs with their frozen configuration snapshots.",
)
def list_evaluation_runs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None, description="Filter by status: PENDING, RUNNING, COMPLETED, FAILED"),
    user: AuthenticatedUser = Depends(require_any_authenticated),
) -> List[EvaluationRunResponse]:
    """Lists historical evaluation runs for the authenticated user or all runs for admin."""
    # If admin, list all runs; otherwise scope to recruiter
    scoped_recruiter_id = None if user.role == "admin" else user.id
    return evaluation_repo.list_runs(
        limit=limit,
        offset=offset,
        recruiter_id=scoped_recruiter_id,
        status=status,
        token=user.token,
    )


@router.get(
    "/runs/{run_id}",
    response_model=EvaluationRunResponse,
    summary="Get details of a specific evaluation run",
)
def get_evaluation_run(
    run_id: UUID,
    user: AuthenticatedUser = Depends(require_any_authenticated),
) -> EvaluationRunResponse:
    """Retrieves full run record including status, counts, and frozen configuration snapshot."""
    run_record = evaluation_repo.get_run(run_id, token=user.token)
    if not run_record:
        raise HTTPException(status_code=404, detail=f"Evaluation run '{run_id}' not found")
    return run_record


@router.get(
    "/runs/{run_id}/status",
    response_model=EvaluationRunResponse,
    summary="Get status and counts for an evaluation run",
)
def get_run_status(
    run_id: UUID,
    user: AuthenticatedUser = Depends(require_any_authenticated),
) -> EvaluationRunResponse:
    """Retrieves progress and completion state of an evaluation run."""
    run_record = evaluation_repo.get_run(run_id, token=user.token)
    if not run_record:
        raise HTTPException(status_code=404, detail=f"Evaluation run '{run_id}' not found")
    return run_record


@router.get(
    "/runs/{run_id}/matrix",
    response_model=EvaluationMatrixResponse,
    summary="Retrieve N x M Multi-Role Fitment Matrix",
)
def get_evaluation_matrix(
    run_id: UUID,
    user: AuthenticatedUser = Depends(require_any_authenticated),
) -> EvaluationMatrixResponse:
    """Returns the complete N candidates x M jobs evaluation matrix grid from stored evaluations."""
    run_record = evaluation_repo.get_run(run_id, token=user.token)
    if not run_record:
        raise HTTPException(status_code=404, detail=f"Evaluation run '{run_id}' not found")

    cells = evaluation_repo.get_matrix_cells(run_id, token=user.token)
    
    # In live database, fetch jobs and candidates for this run
    scoped_recruiter_id = None if user.role == "admin" else user.id
    all_jobs = job_repo.list_all(limit=500, recruiter_id=scoped_recruiter_id, token=user.token)
    all_candidates = candidate_repo.list_all(limit=1000, recruiter_id=scoped_recruiter_id, token=user.token)

    cand_ids = {c.candidate_id for c in cells}
    job_ids = {c.job_id for c in cells}

    cand_list = [
        {"id": str(c.id), "name": c.structured_profile.full_name}
        for c in all_candidates
        if c.id in cand_ids
    ]
    job_list = [
        {"id": str(j.id), "title": j.title}
        for j in all_jobs
        if j.id in job_ids
    ]

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
    user: AuthenticatedUser = Depends(require_any_authenticated),
) -> List[LeaderboardEntry]:
    """Returns candidates ranked by composite fitment score for a specific job description."""
    return evaluation_repo.get_leaderboard_for_job(
        run_id=run_id, job_id=job_id, limit=limit, token=user.token
    )


@router.get(
    "/runs/{run_id}/candidates/{candidate_id}/jobs/{job_id}/explainability",
    response_model=ExplainabilityPayload,
    summary="Retrieve grounded fitment explanation for a Candidate-Role pair",
)
def get_evaluation_explainability(
    run_id: UUID,
    candidate_id: UUID,
    job_id: UUID,
    user: AuthenticatedUser = Depends(require_any_authenticated),
) -> ExplainabilityPayload:
    """Returns auditable evidence breakdown: matched/missing skills, experience delta, and rationale."""
    eval_item = evaluation_repo.get_candidate_evaluation_for_job(
        run_id=run_id, candidate_id=candidate_id, job_id=job_id, token=user.token
    )
    if not eval_item:
        raise HTTPException(
            status_code=404,
            detail=f"Evaluation result for candidate '{candidate_id}' and job '{job_id}' in run '{run_id}' not found",
        )
    return eval_item.explainability
