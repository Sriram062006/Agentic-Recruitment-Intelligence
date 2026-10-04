"""
API endpoints for Recruiter Authentication and Profile Management.
Integrates with Supabase Auth identities and enforces Row Level Security.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import AuthenticatedUser, get_current_user
from app.core.logging import get_logger
from app.schemas.recruiter import RecruiterProfile, RecruiterProfileUpdate
from app.services.database.repositories.recruiter_repo import RecruiterRepository

logger = get_logger("api_auth")
router = APIRouter(prefix="/auth", tags=["Recruiter Authentication"])

recruiter_repo = RecruiterRepository()


@router.get(
    "/me",
    response_model=RecruiterProfile,
    summary="Get currently authenticated recruiter profile",
)
def get_current_recruiter_profile(
    user: AuthenticatedUser = Depends(get_current_user),
) -> RecruiterProfile:
    """Returns the authenticated recruiter profile associated with the Supabase Auth session."""
    profile = recruiter_repo.get_by_user_id(user.id, token=user.token)
    if not profile:
        # Fallback profile representation if not yet queried
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return RecruiterProfile(
            user_id=user.id,
            full_name=user.full_name,
            role=user.role,
            created_at=now,
            updated_at=now,
        )
    return profile


@router.put(
    "/profile",
    response_model=RecruiterProfile,
    summary="Update recruiter full name and profile metadata",
)
def update_profile(
    payload: RecruiterProfileUpdate,
    user: AuthenticatedUser = Depends(get_current_user),
) -> RecruiterProfile:
    """Updates the recruiter profile in PostgreSQL under RLS."""
    updated = recruiter_repo.update_profile(user.id, payload.full_name, token=user.token)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recruiter profile not found or could not be updated",
        )
    return updated


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Acknowledge recruiter logout",
)
def logout(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Signals backend that the recruiter session is closed."""
    logger.info("Recruiter %s logged out", user.id)
    return {"status": "logged_out", "user_id": str(user.id)}
