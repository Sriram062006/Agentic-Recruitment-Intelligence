"""
Pydantic schemas for Recruiter Profiles, Roles, and Admin Management.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    VIEWER = "viewer"


class RecruiterProfile(BaseModel):
    user_id: UUID
    full_name: str
    email: Optional[str] = None
    role: str = Field(default="recruiter")
    is_active: bool = Field(default=True)
    created_at: datetime
    updated_at: datetime


class RecruiterProfileUpdate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)


class UserRoleUpdate(BaseModel):
    role: str = Field(..., description="Role to assign: admin, recruiter, or viewer")


class UserStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Active status for user account")


class AdminUserListItem(BaseModel):
    user_id: UUID
    full_name: str
    email: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    candidates_count: Optional[int] = 0
    jobs_count: Optional[int] = 0
    runs_count: Optional[int] = 0


class AdminStatsResponse(BaseModel):
    total_users: int
    active_recruiters: int
    total_candidates: int
    total_jobs: int
    total_runs: int
    total_evaluations: int
