import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Clear the lru_cache to ensure a fresh Settings object is created
    # This is important because get_settings() is called at module level in config.py,
    # potentially caching an invalid state if .env is not properly set up for testing.
    get_settings.cache_clear()

    # Set a valid GOOGLE_API_KEY environment variable for the test
    test_api_key = "test_valid_api_key_123"
    monkeypatch.setenv("GOOGLE_API_KEY", test_api_key)

    # Call the get_settings function
    settings = get_settings()

    # Assert that the returned object is an instance of Settings
    assert isinstance(settings, Settings)

    # Assert that GOOGLE_API_KEY is correctly loaded from the mocked environment
    assert settings.GOOGLE_API_KEY == test_api_key

    # Assert some default values from the Settings class
    assert settings.API_HOST == "localhost"
    assert settings.API_PORT == 8000
    assert settings.DEBUG is True
