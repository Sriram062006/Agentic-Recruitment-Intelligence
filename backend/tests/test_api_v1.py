"""
API Integration Tests for v1 endpoints.
Verifies HTTP contract for Jobs, Candidates, and Evaluations.
"""

import io
from fastapi.testclient import TestClient
from app.main import create_app
from tests.test_parsers import create_sample_pdf_bytes


from uuid import UUID
from app.core.auth import AuthenticatedUser, get_current_user


def test_api_v1_full_workflow():
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        email="developer@test.local",
        full_name="Local Developer",
        role="recruiter",
        token=None,
    )
    client = TestClient(app)

    # 1. Upload Job Description
    jd_content = create_sample_pdf_bytes("Job Title: Backend Developer\nRequirements: Python, FastAPI, Docker. 3 years exp.")
    job_resp = client.post(
        "/api/v1/jobs/upload",
        files=[("files", ("backend_dev.pdf", jd_content, "application/pdf"))],
    )
    assert job_resp.status_code == 201
    jobs = job_resp.json()
    assert len(jobs) == 1
    job_id = jobs[0]["id"]

    # 2. Upload Candidate Resume
    resume_content = create_sample_pdf_bytes("Full Name: John Engineer\nSkills: Python, FastAPI, Docker, SQL.\nExperience: 4 years.")
    cand_resp = client.post(
        "/api/v1/candidates/upload",
        files=[("files", ("john_resume.pdf", resume_content, "application/pdf"))],
    )
    assert cand_resp.status_code == 201
    candidates = cand_resp.json()
    assert len(candidates) == 1
    candidate_id = candidates[0]["id"]

    # 3. Trigger Evaluation Run
    eval_resp = client.post(
        "/api/v1/evaluations/run",
        json={
            "job_ids": [job_id],
            "candidate_ids": [candidate_id],
        },
    )
    assert eval_resp.status_code == 202
    eval_run = eval_resp.json()
    run_id = eval_run["id"]
    assert eval_run["status"] == "COMPLETED"
    assert eval_run["total_evaluations"] == 1

    # 4. Fetch Matrix
    matrix_resp = client.get(f"/api/v1/evaluations/runs/{run_id}/matrix")
    assert matrix_resp.status_code == 200
    matrix = matrix_resp.json()
    assert len(matrix["cells"]) == 1
    assert matrix["cells"][0]["candidate_id"] == candidate_id
    assert matrix["cells"][0]["job_id"] == job_id

    # 5. Fetch Role Leaderboard
    leaderboard_resp = client.get(f"/api/v1/evaluations/runs/{run_id}/jobs/{job_id}/ranking")
    assert leaderboard_resp.status_code == 200
    leaderboard = leaderboard_resp.json()
    assert len(leaderboard) == 1
    assert leaderboard[0]["rank"] == 1
    assert leaderboard[0]["candidate_id"] == candidate_id

    # 6. Fetch Explainability
    expl_resp = client.get(
        f"/api/v1/evaluations/runs/{run_id}/candidates/{candidate_id}/jobs/{job_id}/explainability"
    )
    assert expl_resp.status_code == 200
    expl = expl_resp.json()
    assert "Python" in expl["matched_skills"]
    assert len(expl["strengths"]) > 0

    # 7. Verify Candidate and Job File Retrieval
    cand_file_resp = client.get(f"/api/v1/candidates/{candidate_id}/file")
    assert cand_file_resp.status_code == 200
    assert cand_file_resp.headers["content-type"] == "application/pdf"
    assert "john_resume.pdf" in cand_file_resp.headers["content-disposition"]
    assert len(cand_file_resp.content) > 0

    job_file_resp = client.get(f"/api/v1/jobs/{job_id}/file")
    assert job_file_resp.status_code == 200
    assert job_file_resp.headers["content-type"] == "application/pdf"
    assert len(job_file_resp.content) > 0

    # Cleanup
    client.delete(f"/api/v1/jobs/{job_id}")
    client.delete(f"/api/v1/candidates/{candidate_id}")
