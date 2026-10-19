"""
Integration and Persistence Tests for Evaluation Runs History.
Verifies that historical runs preserve frozen configuration snapshots,
can be listed, reopened, and inspected without recalculation.
"""

from uuid import UUID
import pytest
from fastapi.testclient import TestClient

from app.core.auth import AuthenticatedUser, get_current_user
from app.main import create_app
from tests.test_parsers import create_sample_pdf_bytes


@pytest.fixture
def test_client():
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        email="recruiter@platform.test",
        full_name="History Tester",
        role="recruiter",
        is_active=True,
        token=None,
    )
    return TestClient(app)


def test_evaluation_history_lifecycle(test_client):
    # 1. Ingest Job Description
    jd_bytes = create_sample_pdf_bytes("Job Title: Lead Architect\nRequirements: Python, Cloud. 8 years exp.")
    jd_resp = test_client.post(
        "/api/v1/jobs/upload",
        files=[("files", ("arch_jd.pdf", jd_bytes, "application/pdf"))],
    )
    assert jd_resp.status_code == 201
    job_id = jd_resp.json()[0]["id"]

    # 2. Ingest Candidate Resume
    cand_bytes = create_sample_pdf_bytes("Full Name: Sarah Chen\nSkills: Python, Cloud, Kubernetes.\nExperience: 9 years.")
    cand_resp = test_client.post(
        "/api/v1/candidates/upload",
        files=[("files", ("sarah_resume.pdf", cand_bytes, "application/pdf"))],
    )
    assert cand_resp.status_code == 201
    candidate_id = cand_resp.json()[0]["id"]

    # 3. Trigger Evaluation Run with Custom Weights
    custom_weights = {
        "semantic_weight": 0.40,
        "skill_weight": 0.30,
        "experience_weight": 0.20,
        "qualification_weight": 0.10,
    }
    custom_heuristics = {
        "alpha_skill_weight": 0.85,
        "beta_experience_penalty": 1.75,
        "fitment_strong_threshold": 0.75,
        "fitment_moderate_threshold": 0.50,
    }
    eval_resp = test_client.post(
        "/api/v1/evaluations/run",
        json={
            "job_ids": [job_id],
            "candidate_ids": [candidate_id],
            "weights": custom_weights,
            "heuristics": custom_heuristics,
        },
    )
    assert eval_resp.status_code == 202
    run_id = eval_resp.json()["id"]

    # 4. List Historical Runs
    runs_resp = test_client.get("/api/v1/evaluations/runs")
    assert runs_resp.status_code == 200
    runs = runs_resp.json()
    assert len(runs) >= 1
    found_run = next((r for r in runs if r["id"] == run_id), None)
    assert found_run is not None
    assert found_run["status"] == "COMPLETED"
    assert found_run["total_candidates"] == 1
    assert found_run["total_jobs"] == 1
    assert found_run["total_evaluations"] == 1

    # 5. Verify Frozen Scoring Snapshot
    run_detail_resp = test_client.get(f"/api/v1/evaluations/runs/{run_id}")
    assert run_detail_resp.status_code == 200
    run_detail = run_detail_resp.json()
    snapshot_weights = run_detail["config"]["weights"]
    assert snapshot_weights["semantic_weight"] == 0.40
    assert snapshot_weights["skill_weight"] == 0.30
    assert snapshot_weights["experience_weight"] == 0.20
    assert snapshot_weights["qualification_weight"] == 0.10

    # 6. Reopen Stored Matrix & Verify Cells
    matrix_resp = test_client.get(f"/api/v1/evaluations/runs/{run_id}/matrix")
    assert matrix_resp.status_code == 200
    matrix = matrix_resp.json()
    assert len(matrix["cells"]) == 1
    assert matrix["cells"][0]["candidate_id"] == candidate_id
    assert matrix["cells"][0]["job_id"] == job_id
    assert matrix["cells"][0]["composite_score"] > 0

    # Clean up test artifacts
    test_client.delete(f"/api/v1/jobs/{job_id}")
    test_client.delete(f"/api/v1/candidates/{candidate_id}")
