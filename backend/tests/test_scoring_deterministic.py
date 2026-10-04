"""
Tests for Deterministic Multi-Role Scoring Engine.
Verifies mathematical repeatability, configurable weights, skill overlap,
exponential experience penalty, and qualification tiers.
"""

from app.pipeline.scorer import (
    calculate_deterministic_fitment,
    compute_experience_fit_score,
    compute_qualification_score,
    compute_skill_overlap_score,
)
from app.schemas.candidate import CandidateProfile
from app.schemas.evaluation import FitmentWeightsConfig, HeuristicConfig
from app.schemas.job import JobProfile


def test_scoring_determinism():
    candidate = CandidateProfile(
        full_name="Jane Doe",
        total_experience_years=4.0,
        skills=["Python", "FastAPI", "Docker", "PostgreSQL"],
        highest_qualification="Master's",
    )
    job = JobProfile(
        title="Backend Engineer",
        required_skills=["Python", "FastAPI", "Docker"],
        preferred_skills=["Kubernetes", "AWS"],
        min_experience_years=3.0,
        required_qualification="Bachelor's",
    )
    weights = FitmentWeightsConfig(
        semantic_weight=0.35,
        skill_weight=0.35,
        experience_weight=0.20,
        qualification_weight=0.10,
    )
    heuristics = HeuristicConfig(alpha_skill_weight=0.80, beta_experience_penalty=1.50)

    # Calling twice must produce identical values
    res1 = calculate_deterministic_fitment(candidate, job, 0.88, weights, heuristics)
    res2 = calculate_deterministic_fitment(candidate, job, 0.88, weights, heuristics)

    assert res1 == res2
    assert 0.0 <= res1["composite_score"] <= 1.0


def test_skill_overlap_alpha_balance():
    # Candidate matches all required, zero preferred
    cand_skills = ["Python", "FastAPI"]
    req_skills = ["Python", "FastAPI"]
    pref_skills = ["Docker", "Kubernetes"]

    score, matched_req, missing_req, matched_pref, missing_pref = compute_skill_overlap_score(
        candidate_skills=cand_skills,
        required_skills=req_skills,
        preferred_skills=pref_skills,
        alpha=0.80,
    )

    # req recall = 1.0, pref recall = 0.0 -> score = 0.80 * 1.0 + 0.20 * 0.0 = 0.80
    assert round(score, 2) == 0.80
    assert len(matched_req) == 2
    assert len(missing_pref) == 2


def test_experience_penalty_exponential_decay():
    # Meets or exceeds: score must be 1.0
    assert compute_experience_fit_score(candidate_years=5.0, required_years=3.0) == 1.0
    assert compute_experience_fit_score(candidate_years=3.0, required_years=3.0) == 1.0

    # Shortfall: 2 years actual vs 4 years required (shortfall = 2, ratio = 0.5)
    # exp(-1.5 * 0.5) = exp(-0.75) ≈ 0.472
    score = compute_experience_fit_score(candidate_years=2.0, required_years=4.0, beta=1.50)
    assert 0.45 < score < 0.50

    # Zero required experience
    assert compute_experience_fit_score(candidate_years=1.0, required_years=0.0) == 1.0


def test_qualification_hierarchy():
    # Doctorate candidate for Bachelor role -> 1.0
    s1, status1 = compute_qualification_score("Doctorate", "Bachelor's")
    assert s1 == 1.0 and status1 == "MEETS"

    # Bachelor candidate for Master role -> 0.70 (Tier diff = 1)
    s2, status2 = compute_qualification_score("Bachelor's", "Master's")
    assert s2 == 0.70 and status2 == "EQUIVALENT"

    # High School for Master role -> 0.30 (Tier diff >= 2)
    s3, status3 = compute_qualification_score("High School", "Master's")
    assert s3 == 0.30 and status3 == "SHORTFALL"
