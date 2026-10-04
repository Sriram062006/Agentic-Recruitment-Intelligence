"""
Controlled Multi-Role Evaluation Benchmark Test (10 candidates x 5 jobs = 50 evaluations).
Verifies the Single-Candidate Multi-Role Model:
- Exactly 10 unique candidate profiles
- Exactly 5 unique job profiles
- Exactly 50 candidate-role evaluations
- Deterministic role ranking (1 to 10 per role)
- No duplicate candidates, no orphaned evaluations.
"""

from uuid import uuid4
import pytest

from app.core.orchestrator import PipelineOrchestrator
from app.schemas.candidate import CandidateProfile
from app.schemas.common import RunStatus
from app.schemas.evaluation import EvaluationConfigRequest
from app.schemas.job import JobProfile
from app.services.database.repositories.candidate_repo import CandidateRepository
from app.services.database.repositories.evaluation_repo import EvaluationRepository
from app.services.database.repositories.job_repo import JobRepository


def test_controlled_10_candidates_by_5_jobs_evaluation():
    job_repo = JobRepository()
    cand_repo = CandidateRepository()
    eval_repo = EvaluationRepository()
    orchestrator = PipelineOrchestrator(
        job_repo=job_repo,
        candidate_repo=cand_repo,
        evaluation_repo=eval_repo,
    )

    # 1. Create 5 Distinct Job Roles
    jobs_data = [
        JobProfile(title="Backend Python Engineer", department="Backend", required_skills=["Python", "FastAPI", "SQL"], min_experience_years=3.0),
        JobProfile(title="Frontend React Developer", department="Frontend", required_skills=["React", "TypeScript", "Tailwind CSS"], min_experience_years=2.0),
        JobProfile(title="DevOps Cloud Engineer", department="Infrastructure", required_skills=["Docker", "Kubernetes", "AWS", "Linux"], min_experience_years=4.0),
        JobProfile(title="Machine Learning Scientist", department="AI Research", required_skills=["Python", "PyTorch", "Machine Learning", "NLP"], min_experience_years=3.5, required_qualification="Master's"),
        JobProfile(title="Full Stack Lead", department="Engineering", required_skills=["Python", "React", "TypeScript", "PostgreSQL", "Docker"], min_experience_years=5.0),
    ]

    created_job_ids = []
    for jd in jobs_data:
        j = job_repo.create(
            title=jd.title,
            department=jd.department,
            storage_path=f"jds/{jd.title.replace(' ', '_')}.pdf",
            raw_content=f"JD for {jd.title}",
            structured_profile=jd,
        )
        created_job_ids.append(j.id)

    # 2. Create 10 Distinct Canonical Candidate Profiles
    candidates_data = [
        CandidateProfile(full_name="Candidate 01 - Python Specialist", total_experience_years=4.5, skills=["Python", "FastAPI", "SQL", "Docker"], highest_qualification="Bachelor's"),
        CandidateProfile(full_name="Candidate 02 - React Specialist", total_experience_years=3.0, skills=["React", "TypeScript", "Tailwind CSS", "HTML", "CSS"], highest_qualification="Bachelor's"),
        CandidateProfile(full_name="Candidate 03 - DevOps Specialist", total_experience_years=6.0, skills=["Docker", "Kubernetes", "AWS", "Linux", "CI/CD"], highest_qualification="Bachelor's"),
        CandidateProfile(full_name="Candidate 04 - AI Researcher", total_experience_years=4.0, skills=["Python", "PyTorch", "Machine Learning", "NLP", "Deep Learning"], highest_qualification="Master's"),
        CandidateProfile(full_name="Candidate 05 - Senior Full Stack", total_experience_years=7.0, skills=["Python", "React", "TypeScript", "PostgreSQL", "Docker", "FastAPI"], highest_qualification="Master's"),
        CandidateProfile(full_name="Candidate 06 - Junior Python Dev", total_experience_years=1.5, skills=["Python", "SQL"], highest_qualification="Bachelor's"),
        CandidateProfile(full_name="Candidate 07 - Frontend Junior", total_experience_years=1.0, skills=["React", "JavaScript", "HTML"], highest_qualification="Associate"),
        CandidateProfile(full_name="Candidate 08 - Cloud Infrastructure", total_experience_years=3.5, skills=["AWS", "Linux", "Docker"], highest_qualification="Bachelor's"),
        CandidateProfile(full_name="Candidate 09 - ML Engineer Junior", total_experience_years=2.0, skills=["Python", "Scikit-Learn", "Pandas"], highest_qualification="Bachelor's"),
        CandidateProfile(full_name="Candidate 10 - Polyglot Architect", total_experience_years=8.0, skills=["Python", "Go", "Kubernetes", "PostgreSQL", "React", "AWS"], highest_qualification="Doctorate"),
    ]

    created_cand_ids = []
    for cd in candidates_data:
        c = cand_repo.create(
            file_name=f"{cd.full_name.replace(' ', '_')}.pdf",
            storage_path=f"resumes/{cd.full_name.replace(' ', '_')}.pdf",
            file_hash=f"hash_{uuid4().hex}",
            raw_text=f"Resume of {cd.full_name}",
            structured_profile=cd,
        )
        created_cand_ids.append(c.id)

    # Verify input cardinalities
    assert len(created_job_ids) == 5
    assert len(created_cand_ids) == 10

    # 3. Execute Multi-Role Evaluation
    request = EvaluationConfigRequest(
        job_ids=created_job_ids,
        candidate_ids=created_cand_ids,
    )
    run_result = orchestrator.execute_multi_role_evaluation(request)

    assert run_result.status == RunStatus.COMPLETED
    assert run_result.total_candidates == 10
    assert run_result.total_jobs == 5
    assert run_result.total_evaluations == 50  # 10 x 5 = 50

    # 4. Verify Matrix Dimensions
    cells = eval_repo.get_matrix_cells(run_result.id)
    assert len(cells) == 50

    # Verify every candidate evaluated against every job exactly once
    pair_set = set()
    for cell in cells:
        pair = (cell.candidate_id, cell.job_id)
        assert pair not in pair_set, f"Duplicate evaluation found for pair {pair}"
        pair_set.add(pair)
        assert 0.0 <= cell.composite_score <= 1.0

    assert len(pair_set) == 50

    # 5. Verify Role-Wise Leaderboards and Rankings
    for job_id in created_job_ids:
        leaderboard = eval_repo.get_leaderboard_for_job(run_result.id, job_id, limit=20)
        assert len(leaderboard) == 10  # All 10 candidates ranked for this role
        ranks = [entry.rank for entry in leaderboard]
        assert ranks == list(range(1, 11))  # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        # Verify monotonicity of scores in leaderboard
        scores = [entry.composite_score for entry in leaderboard]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]

    # 6. Verify Domain Alignment (e.g. Python Specialist ranks higher for Backend Python than React Specialist)
    python_job_id = created_job_ids[0]
    python_leaderboard = eval_repo.get_leaderboard_for_job(run_result.id, python_job_id)
    cand_scores_dict = {entry.candidate_name: entry.composite_score for entry in python_leaderboard}

    assert cand_scores_dict["Candidate 01 - Python Specialist"] > cand_scores_dict["Candidate 02 - React Specialist"]

    # Clean up test entities
    for jid in created_job_ids:
        job_repo.delete(jid)
    for cid in created_cand_ids:
        cand_repo.delete(cid)
