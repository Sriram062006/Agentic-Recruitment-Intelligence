"""
Deterministic Hybrid Fitment Scoring Engine.
Calculates multi-role candidate fitment mathematically without non-deterministic LLM interference.
Enforces the approved baseline formulas, configurable weights, and experimental heuristics.
"""

import math
from typing import Any, Dict, List, Set, Tuple
from app.schemas.candidate import CandidateProfile
from app.schemas.evaluation import FitmentWeightsConfig, HeuristicConfig
from app.schemas.job import JobProfile

DEGREE_TIER_MAP: Dict[str, int] = {
    "doctorate": 4,
    "phd": 4,
    "master's": 3,
    "masters": 3,
    "master": 3,
    "bachelor's": 2,
    "bachelors": 2,
    "bachelor": 2,
    "associate": 1,
    "high school": 0,
}


def compute_skill_overlap_score(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: List[str],
    alpha: float = 0.80,
) -> Tuple[float, List[str], List[str], List[str], List[str]]:
    """
    Computes S_skill = alpha * recall(required) + (1 - alpha) * recall(preferred).
    Returns (skill_score, matched_required, missing_required, matched_preferred, missing_preferred).
    """
    cand_set: Set[str] = {s.lower().strip() for s in candidate_skills}
    req_set: Set[str] = {s.lower().strip() for s in required_skills}
    pref_set: Set[str] = {s.lower().strip() for s in preferred_skills}

    matched_req = [s for s in required_skills if s.lower().strip() in cand_set]
    missing_req = [s for s in required_skills if s.lower().strip() not in cand_set]

    matched_pref = [s for s in preferred_skills if s.lower().strip() in cand_set]
    missing_pref = [s for s in preferred_skills if s.lower().strip() not in cand_set]

    req_recall = (len(matched_req) / len(req_set)) if len(req_set) > 0 else 1.0
    pref_recall = (len(matched_pref) / len(pref_set)) if len(pref_set) > 0 else 1.0

    skill_score = alpha * req_recall + (1.0 - alpha) * pref_recall
    clamped_score = max(0.0, min(1.0, float(skill_score)))

    return clamped_score, matched_req, missing_req, matched_pref, missing_pref


def compute_experience_fit_score(
    candidate_years: float,
    required_years: float,
    beta: float = 1.50,
) -> float:
    """
    Computes experience score with exponential decay penalty for shortfalls.
    If cand_years >= req_years: 1.0
    Else: exp(-beta * shortfall / req_years)
    """
    if required_years <= 0.0 or candidate_years >= required_years:
        return 1.0

    shortfall = required_years - candidate_years
    penalty_ratio = shortfall / required_years
    score = math.exp(-beta * penalty_ratio)
    return max(0.0, min(1.0, float(score)))


def compute_qualification_score(
    candidate_degree: str,
    required_degree: str,
) -> Tuple[float, str]:
    """
    Computes qualification alignment based on ordinal degree hierarchy.
    Returns (score, status_label).
    """
    cand_tier = DEGREE_TIER_MAP.get(candidate_degree.lower().strip(), 2)
    req_tier = DEGREE_TIER_MAP.get(required_degree.lower().strip(), 2)

    if cand_tier >= req_tier:
        return 1.0, "MEETS"
    elif cand_tier == req_tier - 1:
        return 0.70, "EQUIVALENT"
    else:
        return 0.30, "SHORTFALL"


def calculate_deterministic_fitment(
    candidate: CandidateProfile,
    job: JobProfile,
    semantic_similarity: float,
    weights: FitmentWeightsConfig,
    heuristics: HeuristicConfig,
) -> Dict[str, Any]:
    """
    Calculates composite fitment score S_total and all intermediate deterministic signals.
    S_total = w_sem * S_sem + w_skill * S_skill + w_exp * S_exp + w_qual * S_qual
    """
    # 1. Semantic Score
    s_sem = max(0.0, min(1.0, float(semantic_similarity)))

    # 2. Skill Score
    s_skill, matched_req, missing_req, matched_pref, missing_pref = compute_skill_overlap_score(
        candidate_skills=candidate.skills,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
        alpha=heuristics.alpha_skill_weight,
    )

    # 3. Experience Score
    s_exp = compute_experience_fit_score(
        candidate_years=candidate.total_experience_years,
        required_years=job.min_experience_years,
        beta=heuristics.beta_experience_penalty,
    )

    # 4. Qualification Score
    s_qual, qual_status = compute_qualification_score(
        candidate_degree=candidate.highest_qualification,
        required_degree=job.required_qualification,
    )

    # Composite Fitment Score
    s_total = (
        weights.semantic_weight * s_sem
        + weights.skill_weight * s_skill
        + weights.experience_weight * s_exp
        + weights.qualification_weight * s_qual
    )
    s_total_clamped = round(max(0.0, min(1.0, float(s_total))), 4)

    return {
        "composite_score": s_total_clamped,
        "semantic_score": round(s_sem, 4),
        "skill_score": round(s_skill, 4),
        "experience_score": round(s_exp, 4),
        "qualification_score": round(s_qual, 4),
        "matched_required_skills": matched_req,
        "missing_required_skills": missing_req,
        "matched_preferred_skills": matched_pref,
        "missing_preferred_skills": missing_pref,
        "experience_delta": round(candidate.total_experience_years - job.min_experience_years, 2),
        "qualification_status": qual_status,
    }
