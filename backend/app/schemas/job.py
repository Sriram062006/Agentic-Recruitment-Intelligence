"""
Pydantic schemas for Job Descriptions and structured Job Profiles.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class JobProfile(BaseModel):
    """Normalized structured profile extracted from unstructured Job Description text."""
    title: str = Field(description="Standardized job title")
    department: Optional[str] = Field(default=None, description="Department or functional division")
    summary: str = Field(default="", description="Executive summary of the role")
    required_skills: List[str] = Field(default_factory=list, description="Must-have required skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Nice-to-have or preferred skills")
    min_experience_years: float = Field(default=0.0, description="Minimum required experience in years")
    preferred_experience_years: Optional[float] = Field(default=None, description="Preferred experience in years")
    required_qualification: str = Field(default="Bachelor's", description="Standardized minimum degree tier")
    key_responsibilities: List[str] = Field(default_factory=list, description="Core responsibilities")


class JobResponse(BaseModel):
    """API response model for an ingested Job."""
    id: UUID
    title: str
    department: Optional[str] = None
    storage_path: str
    raw_content: str
    structured_profile: JobProfile
    created_at: datetime
    updated_at: datetime


class JobSummary(BaseModel):
    """Brief summary of a Job for listing tables."""
    id: UUID
    title: str
    department: Optional[str] = None
    min_experience_years: float
    required_skills_count: int
    created_at: datetime
