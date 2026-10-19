"""
Pydantic schemas for Job Descriptions and structured Job Profiles.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class JobProfile(BaseModel):
    """Normalized structured profile extracted from unstructured Job Description text."""
    title: str = Field(description="Standardized job title")
    department: Optional[str] = Field(default=None, description="Department or functional division")
    company_or_client: Optional[str] = Field(default=None, description="Hiring organization, company, or client")
    location: Optional[str] = Field(default=None, description="Job location or site")
    remote_work: Optional[str] = Field(default=None, description="Remote work policy (e.g. Yes, Hybrid, On-site)")
    start_date: Optional[str] = Field(default=None, description="Target start date or timeframe")
    end_date: Optional[str] = Field(default=None, description="Expected project end date or duration")
    work_regime: Optional[str] = Field(default=None, description="Full-time, Part-time, Days/week")
    summary: str = Field(default="", description="Executive summary of the role")
    context_or_project_background: Optional[str] = Field(default=None, description="Business context or project background")
    required_skills: List[str] = Field(default_factory=list, description="Must-have required skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Nice-to-have or preferred skills")
    must_have_requirements: List[str] = Field(default_factory=list, description="Exhaustive list of mandatory criteria/must-haves")
    should_have_requirements: List[str] = Field(default_factory=list, description="Exhaustive list of desired criteria/should-haves")
    min_experience_years: float = Field(default=0.0, description="Minimum required experience in years")
    max_experience_years: Optional[float] = Field(default=None, description="Maximum required experience in years")
    preferred_experience_years: Optional[float] = Field(default=None, description="Preferred experience in years")
    required_qualification: Optional[str] = Field(default="Bachelor's", description="Standardized minimum degree tier")

    @field_validator("required_qualification", mode="before")
    @classmethod
    def default_req_qual(cls, v):
        if v is None or not str(v).strip():
            return "Bachelor's"
        return str(v)
    preferred_qualifications: List[str] = Field(default_factory=list, description="Preferred degrees or educational levels")
    certifications: List[str] = Field(default_factory=list, description="Listed certifications")
    required_certifications: List[str] = Field(default_factory=list, description="Mandatory certifications")
    languages: List[str] = Field(default_factory=list, description="Required natural languages (e.g. Dutch C2, English)")
    key_responsibilities: List[str] = Field(default_factory=list, description="Core responsibilities")
    seniority: Optional[str] = Field(default=None, description="Seniority level (Senior, Lead, Principal, Mid, Junior)")
    technical_environment: List[str] = Field(default_factory=list, description="Technical environment details")
    tools: List[str] = Field(default_factory=list, description="Specific software tools")
    technologies: List[str] = Field(default_factory=list, description="Core technologies mentioned")
    frameworks: List[str] = Field(default_factory=list, description="Frameworks mentioned")
    platforms: List[str] = Field(default_factory=list, description="Platforms and cloud ecosystems")
    methodologies: List[str] = Field(default_factory=list, description="Delivery and organizational methodologies")
    domain: Optional[str] = Field(default=None, description="Industry or functional domain")
    stakeholder_requirements: List[str] = Field(default_factory=list, description="Stakeholder coordination requirements")
    management_requirements: List[str] = Field(default_factory=list, description="Budget, team, vendor, or project management requirements")
    compliance_requirements: List[str] = Field(default_factory=list, description="Regulatory, security, or compliance requirements")
    other_requirements: List[str] = Field(default_factory=list, description="Miscellaneous requirements")
    extraction_status: str = Field(default="VERIFIED", description="Extraction verification status (VERIFIED/PARTIAL)")
    extraction_confidence: float = Field(default=1.0, description="Extraction confidence score (0.0 - 1.0)")
    source_text: Optional[str] = Field(default=None, description="Source raw text or excerpt")


class JobResponse(BaseModel):
    """API response model for an ingested Job."""
    id: UUID
    recruiter_id: Optional[UUID] = None
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
