"""
API endpoints for System Administration, Platform Overview, and User Management.
Strictly restricted to users with the 'admin' role.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import AuthenticatedUser, require_admin
from app.core.logging import get_logger
from app.schemas.recruiter import (
    AdminStatsResponse,
    AdminUserListItem,
    RecruiterProfile,
    UserRole,
    UserRoleUpdate,
    UserStatusUpdate,
)
from app.services.database.repositories.recruiter_repo import RecruiterRepository

logger = get_logger("api_admin")
router = APIRouter(prefix="/admin", tags=["System Administration"])

recruiter_repo = RecruiterRepository()


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="Get platform-wide operational statistics",
    description="Returns aggregate counts of users, active recruiters, candidates, jobs, runs, and evaluations.",
)
def get_system_stats(
    admin: AuthenticatedUser = Depends(require_admin),
) -> AdminStatsResponse:
    """Computes and returns system overview metrics."""
    logger.info("Admin %s requested system overview stats", admin.id)
    return recruiter_repo.get_admin_stats(token=admin.token)


@router.get(
    "/users",
    response_model=List[AdminUserListItem],
    summary="List registered users with status and entity counts",
    description="Lists users with optional search by name or email, role filtering, and pagination.",
)
def list_system_users(
    search: Optional[str] = Query(default=None, description="Search query for name or email"),
    role: Optional[str] = Query(default=None, description="Filter by role: admin, recruiter, viewer"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    admin: AuthenticatedUser = Depends(require_admin),
) -> List[AdminUserListItem]:
    """Lists platform users for admin management."""
    if role and role.lower() not in [r.value for r in UserRole]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role filter '{role}'. Valid roles: {[r.value for r in UserRole]}",
        )
    return recruiter_repo.list_all_users(
        search=search,
        role=role.lower() if role else None,
        limit=limit,
        offset=offset,
        token=admin.token,
    )


@router.patch(
    "/users/{user_id}/role",
    response_model=RecruiterProfile,
    summary="Assign or change user role",
    description="Modifies the authorization role (admin, recruiter, viewer) of a user.",
)
def update_user_role(
    user_id: UUID,
    payload: UserRoleUpdate,
    admin: AuthenticatedUser = Depends(require_admin),
) -> RecruiterProfile:
    """Updates user role."""
    target_role = payload.role.strip().lower()
    valid_roles = [r.value for r in UserRole]
    if target_role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{payload.role}'. Must be one of: {valid_roles}",
        )

    # Protect self-demotion if the admin is the only admin
    if user_id == admin.id and target_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote your own administrator account.",
        )

    updated = recruiter_repo.update_role(user_id, target_role, token=admin.token)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found.",
        )

    logger.info("Admin %s updated role of user %s to '%s'", admin.id, user_id, target_role)
    return updated


@router.patch(
    "/users/{user_id}/status",
    response_model=RecruiterProfile,
    summary="Activate or deactivate user account",
    description="Enables or disables user access to the recruitment platform.",
)
def update_user_status(
    user_id: UUID,
    payload: UserStatusUpdate,
    admin: AuthenticatedUser = Depends(require_admin),
) -> RecruiterProfile:
    """Toggles active/inactive status of a user."""
    # Prevent self-deactivation
    if user_id == admin.id and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own administrator account.",
        )

    updated = recruiter_repo.update_status(user_id, payload.is_active, token=admin.token)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found.",
        )

    logger.info(
        "Admin %s updated status of user %s to is_active=%s",
        admin.id,
        user_id,
        payload.is_active,
    )
    return updated
