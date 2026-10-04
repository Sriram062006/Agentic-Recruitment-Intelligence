"""
Tests for Database Layer and Repositories.
Verifies entities, relationships, foreign keys, and the UNIQUE(run_id, candidate_id, job_id) constraint.
"""

from uuid import uuid4
import pytest

from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobProfile
from app.services.database.repositories.candidate_repo import CandidateRepository
from app.services.database.repositories.evaluation_repo import EvaluationRepository
from app.services.database.repositories.job_repo import JobRepository


def test_job_repository_crud():
    repo = JobRepository()
    profile = JobProfile(
        title="MLOps Engineer",
        department="Data Platform",
        summary="Build ML pipelines",
        required_skills=["Python", "Docker", "Kubernetes"],
        preferred_skills=["Terraform"],
        min_experience_years=4.0,
        required_qualification="Bachelor's",
    )

    created = repo.create(
        title=profile.title,
        department=profile.department,
        storage_path="jds/test_job.pdf",
        raw_content="MLOps Engineer job description",
        structured_profile=profile,
    )

    assert created.id is not None
    assert created.title == "MLOps Engineer"
    assert "Docker" in created.structured_profile.required_skills

    fetched = repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id

    # Cleanup
    assert repo.delete(created.id) is True
    assert repo.get_by_id(created.id) is None


def test_candidate_repository_deduplication():
    repo = CandidateRepository()
    profile = CandidateProfile(
        full_name="Alice Developer",
        total_experience_years=5.0,
        skills=["Python", "FastAPI", "PostgreSQL"],
        highest_qualification="Master's",
    )

    test_hash = f"test_hash_{uuid4().hex}"
    cand1 = repo.create(
        file_name="alice_resume.pdf",
        storage_path="resumes/alice.pdf",
        file_hash=test_hash,
        raw_text="Alice's resume text",
        structured_profile=profile,
    )

    assert cand1.id is not None
    assert cand1.structured_profile.full_name == "Alice Developer"

    # Fetch by hash
    fetched = repo.get_by_hash(test_hash)
    assert fetched is not None
    assert fetched.id == cand1.id

    # Cleanup
    repo.delete(cand1.id)


def test_evaluation_uniqueness_constraint():
    eval_repo = EvaluationRepository()
    job_repo = JobRepository()
    cand_repo = CandidateRepository()

    # Create dummy job and candidate
    job = job_repo.create(
        title="Backend Dev",
        department="Eng",
        storage_path="p",
        raw_content="c",
        structured_profile=JobProfile(title="Backend Dev", required_skills=["Go"]),
    )
    cand = cand_repo.create(
        file_name="c.pdf",
        storage_path="p",
        file_hash=uuid4().hex,
        raw_text="t",
        structured_profile=CandidateProfile(full_name="Bob", skills=["Go"]),
    )

    run = eval_repo.create_run(total_candidates=1, total_jobs=1, config={})

    # Save evaluation for (run.id, cand.id, job.id)
    eval_payload = {
        "id": uuid4(),
        "run_id": run.id,
        "candidate_id": cand.id,
        "job_id": job.id,
        "semantic_score": 0.85,
        "skill_score": 0.90,
        "experience_score": 0.80,
        "qualification_score": 1.0,
        "composite_score": 0.88,
        "rank_in_role": 1,
        "explainability": {
            "matched_skills": ["Go"],
            "missing_skills": [],
            "matched_preferred_skills": [],
            "missing_preferred_skills": [],
            "experience_comparison": {
                "required_years": 2.0,
                "candidate_years": 3.0,
                "delta_years": 1.0,
                "meets_requirement": True,
            },
            "qualification_comparison": {
                "required_degree": "Bachelor's",
                "candidate_degree": "Bachelor's",
                "status": "MEETS",
            },
            "strengths": ["Strong Go background"],
            "skill_gaps": [],
            "recommendation_rationale": "Strong fit",
        },
    }

    eval_repo.save_bulk_evaluations([eval_payload])

    # Re-saving same (run, candidate, job) updates rather than duplicates
    eval_payload_update = dict(eval_payload)
    eval_payload_update["composite_score"] = 0.95
    eval_repo.save_bulk_evaluations([eval_payload_update])

    cells = eval_repo.get_matrix_cells(run.id)
    assert len(cells) == 1
    assert cells[0].composite_score == 0.95

    # Cleanup
    job_repo.delete(job.id)
    cand_repo.delete(cand.id)
