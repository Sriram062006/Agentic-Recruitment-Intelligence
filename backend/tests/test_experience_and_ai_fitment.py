"""
Unit and integration tests for Experience Interval Merging, Manual Override,
Missing Skills Classification, and Score Consistency Review.
"""

from datetime import datetime
import pytest
from app.pipeline.ai_fitment import (
    AIFitmentEvaluator,
    audit_score_consistency,
    classify_missing_skills,
    generate_recruiter_verification_questions,
    map_score_to_category,
)
from app.schemas.candidate import (
    CandidateContactUpdate,
    CandidateProfile,
    EducationEntry,
    PersonalInformation,
    WorkExperienceEntry,
)
from app.schemas.evaluation import FitmentCategory, RecommendationVerdict
from app.schemas.job import JobProfile
from app.services.llm.extractor import StructuredCandidateExtractor


def test_experience_overlapping_interval_merging():
    """
    Verifies that overlapping employment intervals are merged:
    Role A: 2020 - 2023 (3 years)
    Role B: 2021 - 2024 (3 years)
    Total experience must be 4.0 years (2020 to 2024), NOT 3 + 3 = 6 years.
    """
    experiences = [
        WorkExperienceEntry(
            title="Software Engineer",
            organization="Company A",
            start_date="2020",
            end_date="2023",
            duration_years=3.0,
        ),
        WorkExperienceEntry(
            title="Senior Engineer",
            organization="Company B",
            start_date="2021",
            end_date="2024",
            duration_years=3.0,
        ),
    ]

    total = StructuredCandidateExtractor._calculate_total_experience("Sample resume text", experiences)
    assert total == 4.0, f"Expected 4.0 merged years, got {total}"


def test_experience_excludes_education_and_projects():
    """
    Verifies that education and external dates do not count towards total employment experience.
    """
    experiences = [
        WorkExperienceEntry(
            title="DevOps Engineer",
            organization="Cloud Corp",
            start_date="2022",
            end_date="2024",
            duration_years=2.0,
        )
    ]
    total = StructuredCandidateExtractor._calculate_total_experience("Graduated in 2018 with MS degree", experiences)
    assert total == 2.0, f"Expected 2.0 employment years, got {total}"


def test_experience_present_date_handling():
    """
    Verifies that 'Present' or 'Current' calculates through current year.
    """
    current_year = datetime.now().year
    s_float = StructuredCandidateExtractor._parse_date_to_year_float("2020", is_end=False)
    e_float = StructuredCandidateExtractor._parse_date_to_year_float("Present", is_end=True)

    assert s_float == 2020.0
    assert e_float is not None and e_float >= current_year


def test_missing_skills_classification():
    """
    Verifies that missing skills are categorized into:
    - Equivalent Skill
    - Not Evidenced
    - Partially Evidenced
    - Clearly Missing
    """
    candidate = CandidateProfile(
        full_name="Alex River",
        skills=["Docker", "PostgreSQL", "FastAPI"],
        tools_and_technologies=["Git", "Linux"],
        professional_summary="Enthusiastic developer with interest in Kubernetes architecture.",
        total_experience_years=5.0,
    )

    # Kubernetes -> Equivalent to Docker in EQUIVALENTS_MAP, or in summary -> checks
    # AWS -> Clearly Missing
    # MySQL -> Equivalent to PostgreSQL
    missing_analysis = classify_missing_skills(["MySQL", "AWS"], candidate, candidate_raw_text="")

    classifications = {item["skill"]: item["classification"] for item in missing_analysis}
    assert classifications["MySQL"] == "Equivalent Skill"
    assert classifications["AWS"] == "Clearly Missing"


def test_score_consistency_audit_high_match_low_score():
    """
    Detects High-Match / Low-Score contradiction and applies review adjustment.
    """
    audit = audit_score_consistency(
        fitment_score=55.0,  # inappropriately low
        req_coverage=0.95,   # meets 95% requirements
        exp_ratio=1.2,       # meets experience requirement
        must_have_count=5,
        matched_must_have_count=5,
    )
    assert audit["status"] == "WARNING_FLAGGED"
    assert audit["adjusted_score"] >= 78.0
    assert any("SCORE_CONSISTENCY_WARNING: High match" in f for f in audit["flags"])


def test_score_consistency_audit_low_match_high_score():
    """
    Detects Low-Match / High-Score contradiction and applies review adjustment.
    """
    audit = audit_score_consistency(
        fitment_score=92.0,  # inappropriately high
        req_coverage=0.35,   # only 35% requirements met
        exp_ratio=0.4,       # severe experience shortfall
        must_have_count=6,
        matched_must_have_count=2,
    )
    assert audit["status"] == "WARNING_FLAGGED"
    assert audit["adjusted_score"] <= 68.0
    assert any("SCORE_CONSISTENCY_WARNING: Low match" in f for f in audit["flags"])


def test_score_calibration_category_tiers():
    """
    Verifies exact score category calibration:
    >= 90: EXCELLENT_FIT
    >= 80: STRONG_FIT
    >= 70: GOOD_FIT
    >= 60: PARTIAL_FIT
    >= 40: WEAK_FIT
    < 40: POOR_FIT
    """
    cat, rec = map_score_to_category(94.0)
    assert cat == FitmentCategory.EXCELLENT_FIT.value
    assert rec == RecommendationVerdict.STRONGLY_RECOMMEND.value

    cat, rec = map_score_to_category(82.5)
    assert cat == FitmentCategory.STRONG_FIT.value
    assert rec == RecommendationVerdict.RECOMMEND.value

    cat, rec = map_score_to_category(74.0)
    assert cat == FitmentCategory.GOOD_FIT.value
    assert rec == RecommendationVerdict.RECOMMEND.value

    cat, rec = map_score_to_category(63.0)
    assert cat == FitmentCategory.PARTIAL_FIT.value
    assert rec == RecommendationVerdict.CONSIDER.value

    cat, rec = map_score_to_category(48.0)
    assert cat == FitmentCategory.WEAK_FIT.value
    assert rec == RecommendationVerdict.DO_NOT_RECOMMEND.value

    cat, rec = map_score_to_category(28.0)
    assert cat == FitmentCategory.POOR_FIT.value
    assert rec == RecommendationVerdict.DO_NOT_RECOMMEND.value
