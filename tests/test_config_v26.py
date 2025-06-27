import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Clear the lru_cache to ensure a clean state for the test,
    # especially if get_settings was called during module import.
    get_settings.cache_clear()

    # Set a dummy GOOGLE_API_KEY using monkeypatch to prevent ValueError
    # and simulate a valid environment for the Settings instantiation.
    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key-123")

    # Optionally, set another environment variable to test overriding defaults
    monkeypatch.setenv("API_HOST", "test-host.example.com")

    # Get the settings instance for the first time
    settings_instance_1 = get_settings()

    # Assert that the returned object is an instance of Settings
    # (Assuming Settings class is available in the test scope,
    # as per 'import statements provided' instruction)
    assert isinstance(settings_instance_1, Settings)

    # Assert that the GOOGLE_API_KEY was loaded correctly
    assert settings_instance_1.GOOGLE_API_KEY == "test-api-key-123"

    # Assert that the overridden API_HOST was loaded correctly
    assert settings_instance_1.API_HOST == "test-host.example.com"

    # Assert that a default value is still present
    assert settings_instance_1.API_PORT == 8000

    # Get the settings instance again to test lru_cache behavior
    settings_instance_2 = get_settings()

    # Assert that the second call returns the exact same instance
    # due to the lru_cache decorator
    assert settings_instance_1 is settings_instance_2
