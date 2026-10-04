"""
Pydantic schemas for Multi-Role Evaluation, Configurable Weights, Heuristics,
Evaluation Matrix, Role-wise Leaderboards, and Grounded Explainability.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator

from app.schemas.common import RunStatus


class FitmentWeightsConfig(BaseModel):
    """Configurable weights for the multi-role composite fitment score."""
    semantic_weight: float = Field(default=0.35, ge=0.0, le=1.0)
    skill_weight: float = Field(default=0.35, ge=0.0, le=1.0)
    experience_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    qualification_weight: float = Field(default=0.10, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_sum_equals_one(self) -> "FitmentWeightsConfig":
        total = round(
            self.semantic_weight
            + self.skill_weight
            + self.experience_weight
            + self.qualification_weight,
            4,
        )
        if abs(total - 1.0) > 1e-3:
            raise ValueError(f"Sum of fitment weights must equal 1.0, got {total}")
        return self


class HeuristicConfig(BaseModel):
    """Configurable experimental heuristic parameters."""
    alpha_skill_weight: float = Field(default=0.80, ge=0.0, le=1.0, description="Required vs preferred balance")
    beta_experience_penalty: float = Field(default=1.50, ge=0.0, description="Shortfall exponential penalty factor")
    fitment_strong_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    fitment_moderate_threshold: float = Field(default=0.50, ge=0.0, le=1.0)


class EvaluationConfigRequest(BaseModel):
    """Request payload to create a new multi-role evaluation run."""
    job_ids: Optional[List[UUID]] = Field(default=None, description="Selected job IDs (all active if omitted)")
    candidate_ids: Optional[List[UUID]] = Field(default=None, description="Selected candidate IDs (all active if omitted)")
    weights: Optional[FitmentWeightsConfig] = Field(default=None, description="Configurable weights (defaults to baseline)")
    heuristics: Optional[HeuristicConfig] = Field(default=None, description="Configurable heuristics")


class ExperienceComparison(BaseModel):
    required_years: float
    candidate_years: float
    delta_years: float
    meets_requirement: bool


class QualificationComparison(BaseModel):
    required_degree: str
    candidate_degree: str
    status: str  # MEETS, EQUIVALENT, SHORTFALL


class ExplainabilityPayload(BaseModel):
    """Auditable evidence-grounded fitment explanation."""
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    matched_preferred_skills: List[str] = Field(default_factory=list)
    missing_preferred_skills: List[str] = Field(default_factory=list)
    experience_comparison: ExperienceComparison
    qualification_comparison: QualificationComparison
    strengths: List[str] = Field(default_factory=list)
    skill_gaps: List[str] = Field(default_factory=list)
    recommendation_rationale: str


class EvaluationResultItem(BaseModel):
    """Evaluation result for one Candidate evaluated against one Job."""
    id: UUID
    run_id: UUID
    candidate_id: UUID
    job_id: UUID
    candidate_name: str
    job_title: str
    semantic_score: float
    skill_score: float
    experience_score: float
    qualification_score: float
    composite_score: float
    rank_in_role: int
    explainability: ExplainabilityPayload
    created_at: datetime


class EvaluationRunResponse(BaseModel):
    """Status and metadata of an Evaluation Run."""
    id: UUID
    status: RunStatus
    total_candidates: int
    total_jobs: int
    total_evaluations: int
    config: Dict
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class MatrixCell(BaseModel):
    candidate_id: UUID
    job_id: UUID
    composite_score: float
    rank_in_role: int
    fitment_tier: str  # Strong, Moderate, Low


class EvaluationMatrixResponse(BaseModel):
    """N candidates x M jobs evaluation matrix view."""
    run_id: UUID
    candidates: List[Dict[str, str]]  # list of {id, name}
    jobs: List[Dict[str, str]]        # list of {id, title}
    cells: List[MatrixCell]
    total_evaluations: int


class LeaderboardEntry(BaseModel):
    """Ranked candidate entry for a single role leaderboard."""
    rank: int
    candidate_id: UUID
    candidate_name: str
    total_experience_years: float
    highest_qualification: str
    composite_score: float
    semantic_score: float
    skill_score: float
    experience_score: float
    qualification_score: float
    matched_skills_count: int
    missing_skills_count: int
