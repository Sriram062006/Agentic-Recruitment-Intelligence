"""
Pydantic schemas for Candidate Resumes and Canonical Structured Candidate Profiles.
Preserves the single-candidate multi-role paradigm.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class WorkExperienceEntry(BaseModel):
    """Structured work history tenure entry."""
    title: str = Field(description="Role or job title held")
    organization: Optional[str] = Field(default=None, description="Company or institution")
    duration_years: float = Field(default=0.0, description="Duration in years")
    summary: Optional[str] = Field(default=None, description="Key duties and achievements")


class EducationEntry(BaseModel):
    """Structured educational credential entry."""
    degree: str = Field(description="Degree level: Doctorate, Master's, Bachelor's, Associate, High School")
    field: Optional[str] = Field(default=None, description="Field of study or major")
    institution: Optional[str] = Field(default=None, description="School, college or university")
    graduation_year: Optional[int] = Field(default=None, description="Year degree was conferred")


class CandidateProfile(BaseModel):
    """Canonical structured profile extracted from unstructured candidate resume text."""
    full_name: str = Field(default="Candidate", description="Detected candidate full name")
    email: Optional[str] = Field(default=None, description="Contact email address")
    phone: Optional[str] = Field(default=None, description="Contact phone number")
    location: Optional[str] = Field(default=None, description="Geographic location or city")
    total_experience_years: float = Field(default=0.0, description="Total computed years of verified experience")
    skills: List[str] = Field(default_factory=list, description="Canonical extracted skill keywords")
    experience_history: List[WorkExperienceEntry] = Field(default_factory=list, description="Chronological work history")
    highest_qualification: str = Field(default="Bachelor's", description="Highest verified degree tier")
    education: List[EducationEntry] = Field(default_factory=list, description="All verified educational degrees")
    summary: Optional[str] = Field(default=None, description="Professional executive summary")


class CandidateResponse(BaseModel):
    """API response model for an ingested candidate."""
    id: UUID
    recruiter_id: Optional[UUID] = None
    file_name: str
    storage_path: str
    file_hash: str
    raw_text: str
    structured_profile: CandidateProfile
    faiss_index_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class CandidateSummary(BaseModel):
    """Brief candidate representation for pool directories and selection lists."""
    id: UUID
    full_name: str
    file_name: str
    total_experience_years: float
    highest_qualification: str
    skills_count: int
    faiss_indexed: bool
    created_at: datetime
