import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Set a dummy GOOGLE_API_KEY to satisfy the validation in Settings.__init__
    # without relying on an actual .env file or system environment variable.
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key-123")

    # Clear the cache to ensure that a fresh Settings instance is created
    # for this specific test run. This is crucial because get_settings is lru_cached
    # and might have been called previously (e.g., during module import).
    get_settings.cache_clear()

    # Call get_settings for the first time in this test
    settings_instance_1 = get_settings()

    # Assert that the returned object is an instance of the Settings class
    # (Assuming Settings class is accessible in the test scope)
    assert isinstance(settings_instance_1, Settings)

    # Assert that the GOOGLE_API_KEY is correctly loaded from the monkeypatched environment
    assert settings_instance_1.GOOGLE_API_KEY == "test-google-api-key-123"

    # Assert some default values to ensure basic configuration is loaded
    assert settings_instance_1.API_HOST == "localhost"
    assert settings_instance_1.API_PORT == 8000
    assert settings_instance_1.DEBUG is True

    # Test the lru_cache functionality: subsequent calls should return the same instance
    settings_instance_2 = get_settings()
    assert settings_instance_1 is settings_instance_2
