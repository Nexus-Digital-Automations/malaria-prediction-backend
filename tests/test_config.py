"""Test configuration module."""

from malaria_predictor.config import Settings


def test_settings_creation() -> None:
    """Test that settings can be created with defaults."""
    settings = Settings()
    assert settings.app_name == "Malaria Prediction API"
    assert settings.version == "0.1.0"
    assert settings.api_port == 8000


def test_settings_with_env_override() -> None:
    """Test that settings can be overridden via environment."""
    import os

    # Temporarily set environment variable
    os.environ["API_PORT"] = "9000"
    try:
        settings = Settings()
        assert settings.api_port == 9000
    finally:
        # Clean up
        del os.environ["API_PORT"]
