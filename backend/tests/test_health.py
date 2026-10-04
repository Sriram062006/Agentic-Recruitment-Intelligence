"""
Tests for health check endpoint.
"""

from fastapi.testclient import TestClient


def test_health_check_returns_healthy(client: TestClient) -> None:
    """Verifies that GET /api/health responds with status 200 and healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "healthy"}
