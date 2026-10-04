"""
Tests for application configuration loading and baseline parameter defaults.
"""

from app.config import Settings, get_settings


def test_default_settings_instantiation() -> None:
    """Verifies that Settings loads properly with baseline parameter defaults."""
    settings = get_settings()

    assert settings.app_env in ["development", "test", "production"]
    assert settings.app_name == "Agentic AI Recruitment Intelligence Platform"
    assert settings.port == 8000

    # Verify baseline weights sum to 1.0 (baseline sanity check)
    total_weight = (
        settings.semantic_weight
        + settings.skill_weight
        + settings.experience_weight
        + settings.qualification_weight
    )
    assert round(total_weight, 4) == 1.0

    # Verify experimental heuristic parameters exist and are bounded
    assert 0.0 <= settings.alpha_skill_weight <= 1.0
    assert settings.beta_experience_penalty > 0.0
    assert settings.fitment_strong_threshold > settings.fitment_moderate_threshold


def test_custom_settings_override() -> None:
    """Verifies that configurable weights can be dynamically set for experiments."""
    custom = Settings(
        semantic_weight=0.50,
        skill_weight=0.30,
        experience_weight=0.10,
        qualification_weight=0.10,
        alpha_skill_weight=0.85,
        beta_experience_penalty=2.0,
    )
    assert custom.semantic_weight == 0.50
    assert custom.skill_weight == 0.30
    assert custom.alpha_skill_weight == 0.85
    assert custom.beta_experience_penalty == 2.0
