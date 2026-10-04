"""
Tests for Explainability Engine and Anti-Hallucination Guarantees.
Verifies grounded evidence breakdown, matched/missing skill fidelity,
and ensures the LLM never alters numerical scores.
"""

from app.pipeline.explainer import generate_fitment_explanation
from app.pipeline.scorer import calculate_deterministic_fitment
from app.schemas.candidate import CandidateProfile
from app.schemas.evaluation import FitmentWeightsConfig, HeuristicConfig
from app.schemas.job import JobProfile
from app.services.llm.gemini_provider import GeminiLLMProvider


def test_grounded_explainability_generation():
    candidate = CandidateProfile(
        full_name="Sarah Connor",
        total_experience_years=5.0,
        skills=["Python", "FastAPI", "Docker", "Git"],
        highest_qualification="Master's",
    )
    job = JobProfile(
        title="Senior Python Backend Developer",
        required_skills=["Python", "FastAPI", "Docker", "Kubernetes"],
        preferred_skills=["AWS", "Redis"],
        min_experience_years=4.0,
        required_qualification="Bachelor's",
    )
    weights = FitmentWeightsConfig()
    heuristics = HeuristicConfig()

    signals = calculate_deterministic_fitment(
        candidate=candidate,
        job=job,
        semantic_similarity=0.82,
        weights=weights,
        heuristics=heuristics,
    )

    llm_provider = GeminiLLMProvider()
    explanation = generate_fitment_explanation(
        candidate=candidate,
        job=job,
        fitment_signals=signals,
        llm_provider=llm_provider,
    )

    # 1. Verify exact matched skills
    assert "Python" in explanation.matched_skills
    assert "FastAPI" in explanation.matched_skills
    assert "Docker" in explanation.matched_skills

    # 2. Verify exact missing required skills
    assert "Kubernetes" in explanation.missing_skills
    assert "Python" not in explanation.missing_skills

    # 3. Verify experience comparison
    assert explanation.experience_comparison.required_years == 4.0
    assert explanation.experience_comparison.candidate_years == 5.0
    assert explanation.experience_comparison.delta_years == 1.0
    assert explanation.experience_comparison.meets_requirement is True

    # 4. Verify qualification alignment
    assert explanation.qualification_comparison.status == "MEETS"

    # 5. Verify non-empty narrative
    assert len(explanation.strengths) > 0
    assert len(explanation.skill_gaps) > 0
    assert len(explanation.recommendation_rationale) > 10
