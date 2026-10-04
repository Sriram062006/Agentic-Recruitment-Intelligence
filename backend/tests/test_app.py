"""
Tests for application startup, CORS headers, and OpenAPI route registration.
"""

from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app


def test_app_startup_and_docs_available() -> None:
    """Verifies that FastAPI initializes cleanly and exposes OpenAPI documentation."""
    app = create_app(Settings(app_env="test"))
    client = TestClient(app)

    docs_response = client.get("/docs")
    assert docs_response.status_code == 200

    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200
    openapi_data = openapi_response.json()
    assert "/api/health" in openapi_data["paths"]


def test_cors_preflight_headers() -> None:
    """Verifies that CORS headers respond as configured for allowed origins."""
    app = create_app(Settings(cors_origins=["http://localhost:5173"]))
    client = TestClient(app)

    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
