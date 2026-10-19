"""
Comprehensive Tests for Role-Based Access Control (RBAC), Admin Endpoints,
Viewer Read-Only Restrictions, and Account Deactivation Enforcement.
"""

from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient

from app.core.auth import AuthenticatedUser, get_current_user
from app.main import create_app
from tests.test_parsers import create_sample_pdf_bytes


@pytest.fixture
def base_app():
    return create_app()


def get_mock_user(role: str = "recruiter", is_active: bool = True, user_id: UUID = None) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=user_id or UUID("00000000-0000-0000-0000-000000000001"),
        email=f"{role}@platform.test",
        full_name=f"Test {role.capitalize()}",
        role=role,
        is_active=is_active,
        token=None,
    )


def test_admin_stats_and_user_management(base_app):
    admin_id = UUID("00000000-0000-0000-0000-000000000001")
    target_user_id = UUID("00000000-0000-0000-0000-000000000002")

    base_app.dependency_overrides[get_current_user] = lambda: get_mock_user(role="admin", user_id=admin_id)
    client = TestClient(base_app)

    # 1. Admin can access stats
    stats_resp = client.get("/api/v1/admin/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "total_users" in stats
    assert "active_recruiters" in stats
    assert "total_candidates" in stats
    assert "total_jobs" in stats
    assert "total_runs" in stats
    assert "total_evaluations" in stats

    # 2. Admin can list users
    users_resp = client.get("/api/v1/admin/users")
    assert users_resp.status_code == 200
    assert isinstance(users_resp.json(), list)

    # 3. Admin self-demotion is rejected
    self_demote_resp = client.patch(
        f"/api/v1/admin/users/{admin_id}/role",
        json={"role": "recruiter"},
    )
    assert self_demote_resp.status_code == 400
    assert "demote your own" in self_demote_resp.json()["detail"].lower()

    # 4. Admin self-deactivation is rejected
    self_deact_resp = client.patch(
        f"/api/v1/admin/users/{admin_id}/status",
        json={"is_active": False},
    )
    assert self_deact_resp.status_code == 400
    assert "deactivate your own" in self_deact_resp.json()["detail"].lower()


def test_recruiter_blocked_from_admin_endpoints(base_app):
    recruiter_id = UUID("00000000-0000-0000-0000-000000000003")
    base_app.dependency_overrides[get_current_user] = lambda: get_mock_user(role="recruiter", user_id=recruiter_id)
    client = TestClient(base_app)

    # Recruiter cannot view admin stats
    resp = client.get("/api/v1/admin/stats")
    assert resp.status_code == 403
    assert "forbidden" in resp.json()["detail"].lower()

    # Recruiter cannot list users
    resp_users = client.get("/api/v1/admin/users")
    assert resp_users.status_code == 403

    # Recruiter cannot change roles
    resp_role = client.patch(
        f"/api/v1/admin/users/{recruiter_id}/role",
        json={"role": "admin"},
    )
    assert resp_role.status_code == 403


def test_viewer_role_read_only_enforcement(base_app):
    viewer_id = UUID("00000000-0000-0000-0000-000000000004")
    base_app.dependency_overrides[get_current_user] = lambda: get_mock_user(role="viewer", user_id=viewer_id)
    client = TestClient(base_app)

    # 1. Viewer blocked from uploading jobs
    sample_pdf = create_sample_pdf_bytes("Job Title: Test Role\nRequirements: Python")
    resp_jd = client.post(
        "/api/v1/jobs/upload",
        files=[("files", ("test.pdf", sample_pdf, "application/pdf"))],
    )
    assert resp_jd.status_code == 403
    assert "forbidden" in resp_jd.json()["detail"].lower()

    # 2. Viewer blocked from deleting jobs
    resp_del_jd = client.delete(f"/api/v1/jobs/{uuid4()}")
    assert resp_del_jd.status_code == 403

    # 3. Viewer blocked from uploading resumes
    resp_cand = client.post(
        "/api/v1/candidates/upload",
        files=[("files", ("test_cand.pdf", sample_pdf, "application/pdf"))],
    )
    assert resp_cand.status_code == 403

    # 4. Viewer blocked from deleting candidates
    resp_del_cand = client.delete(f"/api/v1/candidates/{uuid4()}")
    assert resp_del_cand.status_code == 403

    # 5. Viewer blocked from creating evaluation run
    resp_run = client.post(
        "/api/v1/evaluations/run",
        json={"job_ids": [str(uuid4())], "candidate_ids": [str(uuid4())]},
    )
    assert resp_run.status_code == 403

    # 6. Viewer CAN read jobs, candidates, and runs
    assert client.get("/api/v1/jobs").status_code == 200
    assert client.get("/api/v1/candidates").status_code == 200
    assert client.get("/api/v1/evaluations/runs").status_code == 200


def test_deactivated_account_blocked(base_app):
    user_id = UUID("00000000-0000-0000-0000-000000000005")
    base_app.dependency_overrides[get_current_user] = lambda: get_mock_user(role="recruiter", is_active=False, user_id=user_id)
    client = TestClient(base_app)

    # Even read endpoints reject deactivated accounts with 403
    resp_jobs = client.get("/api/v1/jobs")
    assert resp_jobs.status_code == 403
    assert "deactivated" in resp_jobs.json()["detail"].lower()
