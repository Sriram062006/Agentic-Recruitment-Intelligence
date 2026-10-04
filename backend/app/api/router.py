"""
API router aggregator.
Includes health check and registers v1 routes (jobs, candidates, evaluations).
"""

from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.candidates import router as candidates_router
from app.api.v1.evaluations import router as evaluations_router
from app.api.v1.jobs import router as jobs_router
from app.schemas.common import HealthResponse

api_router = APIRouter()

# Health check endpoint
@api_router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
    description="Returns the operational status of the backend API service.",
    tags=["Health"],
)
async def health_check() -> HealthResponse:
    """Returns application health status."""
    return HealthResponse(status="healthy")


# V1 Route Groups
v1_router = APIRouter(prefix="/v1")
v1_router.include_router(auth_router)
v1_router.include_router(jobs_router)
v1_router.include_router(candidates_router)
v1_router.include_router(evaluations_router)

api_router.include_router(v1_router)
