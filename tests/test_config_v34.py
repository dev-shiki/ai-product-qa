import pytest
from app.utils.config import get_settings

def test_get_settings_basic():
    # Get settings instance for the first time
    settings_instance_1 = get_settings()

    # Assert that a settings object is returned
    assert settings_instance_1 is not None

    # Assert that the returned object has expected attributes
    # This implicitly checks if it's a Settings-like object
    assert hasattr(settings_instance_1, "GOOGLE_API_KEY")
    assert hasattr(settings_instance_1, "API_HOST")
    assert hasattr(settings_instance_1, "API_PORT")
    assert hasattr(settings_instance_1, "DEBUG")

    # Assert some expected default values from the Settings class
    assert settings_instance_1.API_HOST == "localhost"
    assert settings_instance_1.API_PORT == 8000
    assert settings_instance_1.DEBUG is True

    # Test the lru_cache behavior: subsequent calls to get_settings() should return the same instance
    settings_instance_2 = get_settings()
    assert settings_instance_1 is settings_instance_2
