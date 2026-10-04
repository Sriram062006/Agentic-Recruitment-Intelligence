"""
API router aggregator.
Includes health check and prepares route groups for future phases.
"""

from fastapi import APIRouter
from app.schemas.common import HealthResponse

api_router = APIRouter()


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
