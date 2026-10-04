"""
Common schemas used across API endpoints.
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(default="healthy", description="Application service status")
