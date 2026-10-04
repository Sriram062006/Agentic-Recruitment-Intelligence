"""
Pytest fixtures for backend tests.
"""

import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing isolated test settings."""
    return Settings(
        app_env="test",
        log_level="WARNING",
        cors_origins=["http://localhost:3000"],
    )


@pytest.fixture
def client(test_settings: Settings) -> TestClient:
    """Fixture providing FastAPI TestClient."""
    app = create_app(settings=test_settings)
    return TestClient(app)
