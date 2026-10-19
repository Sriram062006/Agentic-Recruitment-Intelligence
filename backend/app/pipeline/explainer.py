"""
Explainability Engine.
Generates structured, auditable evidence packages and calls the LLM synthesizer.
Enforces the anti-hallucination mandate: all explanations are strictly grounded in deterministic signals.
The LLM is strictly prohibited from modifying numerical scores.
"""

from typing import Any, Dict
from app.schemas.candidate import CandidateProfile
from app.schemas.evaluation import (
    ExperienceComparison,
    ExplainabilityPayload,
    QualificationComparison,
)
from app.schemas.job import JobProfile
from app.services.llm.base import BaseLLMProvider


def generate_fitment_explanation(
    candidate: CandidateProfile,
    job: JobProfile,
    fitment_signals: Dict[str, Any],
    llm_provider: BaseLLMProvider,
    candidate_raw_text: str = "",
) -> ExplainabilityPayload:
    """
    Transforms deterministic fitment signals into a grounded ExplainabilityPayload,
    including requirement-by-requirement audit and grounded evidence citations.
    """
    exp_delta = fitment_signals["experience_delta"]
    meets_exp = candidate.total_experience_years >= job.min_experience_years

    exp_comp = ExperienceComparison(
        required_years=job.min_experience_years,
        candidate_years=candidate.total_experience_years,
        delta_years=exp_delta,
        meets_requirement=meets_exp,
    )

    qual_comp = QualificationComparison(
        required_degree=job.required_qualification,
        candidate_degree=candidate.highest_qualification,
        status=fitment_signals["qualification_status"],
    )

    exp_summary = (
        f"{candidate.total_experience_years} years verified vs {job.min_experience_years} years required "
        f"({'+' if exp_delta >= 0 else ''}{exp_delta} yrs delta)"
    )
    qual_summary = f"{candidate.highest_qualification} (Status: {fitment_signals['qualification_status']})"

    # Synthesize grounded narrative via LLM provider
    narrative = llm_provider.synthesize_fitment_explanation(
        candidate_name=candidate.full_name,
        job_title=job.title,
        matched_skills=fitment_signals["matched_required_skills"],
        missing_skills=fitment_signals["missing_required_skills"],
        experience_summary=exp_summary,
        qualification_summary=qual_summary,
    )

    # Perform requirement-by-requirement evidence extraction
    requirement_analysis = llm_provider.analyze_requirements(
        candidate=candidate,
        job=job,
        candidate_raw_text=candidate_raw_text,
    )

    # Calculate Recruiter Recommendation based on composite score & requirement gaps
    composite_score = fitment_signals.get("composite_score", 0.0)
    missing_must_haves = [r for r in requirement_analysis if r.get("type") == "MUST_HAVE" and r.get("status") == "MISSING"]

    if composite_score >= 0.75 and len(missing_must_haves) <= 1:
        recruiter_rec = "STRONG FIT"
    elif composite_score >= 0.65 and len(missing_must_haves) <= 3:
        recruiter_rec = "GOOD FIT"
    elif composite_score >= 0.50:
        recruiter_rec = "PARTIAL FIT"
    elif composite_score >= 0.35:
        recruiter_rec = "WEAK FIT"
    else:
        recruiter_rec = "NOT RECOMMENDED"

    return ExplainabilityPayload(
        matched_skills=fitment_signals["matched_required_skills"],
        missing_skills=fitment_signals["missing_required_skills"],
        matched_preferred_skills=fitment_signals["matched_preferred_skills"],
        missing_preferred_skills=fitment_signals["missing_preferred_skills"],
        experience_comparison=exp_comp,
        qualification_comparison=qual_comp,
        strengths=narrative.get("strengths", []),
        skill_gaps=narrative.get("skill_gaps", []),
        recommendation_rationale=narrative.get("recommendation_rationale", "Fitment evaluation completed."),
        requirement_analysis=requirement_analysis,
        recruiter_recommendation=recruiter_rec,
    )

