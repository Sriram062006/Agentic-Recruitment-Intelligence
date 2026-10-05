"""
Pydantic schemas for Candidate Resumes and Canonical Structured Candidate Profiles.
Preserves the single-candidate multi-role paradigm and provides complete, auditable CV representations.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PersonalInformation(BaseModel):
    """Personal contact and identity details."""
    full_name: str = Field(default="Candidate", description="Full name")
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    location: Optional[str] = Field(default=None, description="Location or city/country")
    linkedin: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    github: Optional[str] = Field(default=None, description="GitHub profile URL")
    portfolio: Optional[str] = Field(default=None, description="Portfolio or personal website")


class WorkExperienceEntry(BaseModel):
    """Structured work history tenure entry."""
    title: str = Field(description="Role or job title held")
    organization: Optional[str] = Field(default=None, description="Company or institution")
    location: Optional[str] = Field(default=None, description="Geographic location")
    start_date: Optional[str] = Field(default=None, description="Start date (e.g., 2022, Sept 2021)")
    end_date: Optional[str] = Field(default=None, description="End date (e.g., 2025, Present)")
    duration_years: float = Field(default=0.0, description="Duration in years")
    responsibilities: List[str] = Field(default_factory=list, description="Core responsibilities and duties")
    achievements: List[str] = Field(default_factory=list, description="Quantified achievements and outcomes")
    technologies: List[str] = Field(default_factory=list, description="Technologies and tools used")
    domain: Optional[str] = Field(default=None, description="Industry domain or functional area")
    summary: Optional[str] = Field(default=None, description="Concise role overview")


class EducationEntry(BaseModel):
    """Structured educational credential entry."""
    degree: str = Field(description="Degree title (e.g., Master's in Computer Science, Bachelor of Science)")
    field: Optional[str] = Field(default=None, description="Field of study or major")
    institution: Optional[str] = Field(default=None, description="School, college or university")
    graduation_year: Optional[int] = Field(default=None, description="Year degree was conferred")


class CertificationEntry(BaseModel):
    """Professional licenses, certifications, and accreditations."""
    name: str = Field(description="Certification title")
    issuing_organization: Optional[str] = Field(default=None, description="Issuing body or authority")
    year: Optional[int] = Field(default=None, description="Year earned or valid through")


class ProjectEntry(BaseModel):
    """Notable academic, research, open-source, or commercial project."""
    name: str = Field(description="Project title")
    description: Optional[str] = Field(default=None, description="Project scope and goals")
    technologies: List[str] = Field(default_factory=list, description="Tech stack and tools")
    responsibilities: List[str] = Field(default_factory=list, description="Key contributions")
    outcomes: Optional[str] = Field(default=None, description="Quantified results or impact")


class CandidateProfile(BaseModel):
    """Canonical structured profile extracted from unstructured candidate resume text."""
    full_name: str = Field(default="Candidate", description="Detected candidate full name")
    email: Optional[str] = Field(default=None, description="Contact email address")
    phone: Optional[str] = Field(default=None, description="Contact phone number")
    location: Optional[str] = Field(default=None, description="Geographic location or city")
    personal_information: Optional[PersonalInformation] = Field(default=None, description="Nested personal info")
    professional_summary: Optional[str] = Field(default=None, description="Grounded executive summary")
    summary: Optional[str] = Field(default=None, description="Executive summary (sync with professional_summary)")
    total_experience_years: float = Field(default=0.0, description="Total computed years of verified experience")
    skills: List[str] = Field(default_factory=list, description="Canonical extracted skill keywords (clean individual strings)")
    skills_by_category: Dict[str, List[str]] = Field(default_factory=dict, description="Categorized skills")
    experience_history: List[WorkExperienceEntry] = Field(default_factory=list, description="Chronological work history")
    work_experience: List[WorkExperienceEntry] = Field(default_factory=list, description="Alias for experience_history")
    highest_qualification: str = Field(default="Bachelor's", description="Highest verified degree tier")
    education: List[EducationEntry] = Field(default_factory=list, description="All verified educational degrees")
    certifications: List[CertificationEntry] = Field(default_factory=list, description="Verified professional certifications")
    projects: List[ProjectEntry] = Field(default_factory=list, description="Projects and research works")
    languages: List[str] = Field(default_factory=list, description="Natural spoken/written languages")
    achievements: List[str] = Field(default_factory=list, description="Key professional milestones")
    domains: List[str] = Field(default_factory=list, description="Industry domains")
    tools_and_technologies: List[str] = Field(default_factory=list, description="Software tools, platforms, and suites")
    source_text: Optional[str] = Field(default=None, description="Cleaned document source snippet")


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
