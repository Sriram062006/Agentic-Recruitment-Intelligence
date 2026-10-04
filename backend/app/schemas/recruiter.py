"""
Pydantic schemas for Recruiter Profiles.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class RecruiterProfile(BaseModel):
    user_id: UUID
    full_name: str
    role: str = Field(default="recruiter")
    created_at: datetime
    updated_at: datetime


class RecruiterProfileUpdate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
