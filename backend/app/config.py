"""
Application configuration module.
Uses Pydantic BaseSettings to parse environment variables and enforce type safety.
Baseline fitment weights and heuristic parameters are explicitly configurable.
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", "backend/.env"],
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application settings
    app_env: str = Field(default="development", description="Environment: development, test, production")
    app_name: str = Field(
        default="Agentic AI Recruitment Intelligence Platform",
        description="Public platform name",
    )
    host: str = Field(default="127.0.0.1", description="Server host binding")
    port: int = Field(default=8000, description="Server port")
    log_level: str = Field(default="INFO", description="Standard logging level")
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins for frontend client",
    )

    # External Provider Credentials (configured in future phases)
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Google Gemini API key for structured extraction",
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Google Gemini model name for structured extraction (e.g. gemini-2.5-flash, gemini-2.5-flash-lite)",
    )
    gemini_fitment_model: str = Field(
        default="gemini-3.1-pro-preview",
        description="Google Gemini model for deep reasoning fitment evaluation (fallback: gemini-2.5-pro, gemini-2.5-flash)",
    )
    gemini_preprocessing_model: str = Field(
        default="gemini-2.5-flash",
        description="Google Gemini model for fast preprocessing and parsing",
    )
    supabase_url: Optional[str] = Field(
        default=None,
        description="Supabase PostgreSQL project URL",
    )
    supabase_key: Optional[str] = Field(
        default=None,
        description="Supabase anonymous or service role key",
    )

    # Vector Index Configuration
    faiss_index_path: str = Field(
        default="data/faiss/candidates.index",
        description="Local path for FAISS index persistence",
    )

    # Configurable Initial Baseline Fitment Weights (Experimental Baseline)
    semantic_weight: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Baseline weight for semantic embedding similarity",
    )
    skill_weight: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Baseline weight for structured skill overlap",
    )
    experience_weight: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description="Baseline weight for verified tenure fit",
    )
    qualification_weight: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Baseline weight for qualification tier match",
    )

    # Experimental Heuristic Parameters (Subject to validation)
    alpha_skill_weight: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        description="Heuristic weight balancing required vs preferred skills",
    )
    beta_experience_penalty: float = Field(
        default=1.50,
        ge=0.0,
        description="Exponential decay factor penalizing underqualification",
    )
    fitment_strong_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Heuristic threshold for strong fitment classification",
    )
    fitment_moderate_threshold: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="Heuristic threshold for moderate fitment classification",
    )


def get_settings() -> Settings:
    """Returns application settings instance."""
    return Settings()
