"""
Pytest fixtures for backend tests.
Provides isolated test settings and authenticated client sessions.
"""

from typing import Dict
from uuid import UUID
import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.core.auth import AuthenticatedUser, get_current_user
from app.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing isolated test settings without external network dependencies."""
    return Settings(
        app_env="test",
        log_level="WARNING",
        cors_origins=["http://localhost:3000"],
        supabase_url=None,
        supabase_key=None,
    )


@pytest.fixture
def client(test_settings: Settings) -> TestClient:
    """Fixture providing FastAPI TestClient with standard test authorization override."""
    app = create_app(settings=test_settings)
    # Override auth to provide valid test user
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        email="recruiter.test@platform.ai",
        full_name="Dr. Elena Rostova",
        role="recruiter",
        token="test-local-token",
    )
    return TestClient(app)
