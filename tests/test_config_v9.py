import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Clear the lru_cache to ensure a fresh instance is created for this test.
    # This is crucial for cached functions that rely on external state like
    # environment variables that might change between tests.
    get_settings.cache_clear()

    # Set dummy environment variables required by Settings to avoid ValueError
    # and to test that they are correctly loaded.
    monkeypatch.setenv("GOOGLE_API_KEY", "test_api_key_123")
    monkeypatch.setenv("API_HOST", "test_api_host")
    monkeypatch.setenv("API_PORT", "9999")
    monkeypatch.setenv("DEBUG", "False") # Test boolean conversion

    # Call the function under test
    settings = get_settings()

    # Assert that the returned object is an instance of the Settings class.
    assert isinstance(settings, Settings)

    # Assert that the settings object contains the values we set via environment variables.
    assert settings.GOOGLE_API_KEY == "test_api_key_123"
    assert settings.API_HOST == "test_api_host"
    assert settings.API_PORT == 9999
    assert settings.DEBUG is False

    # Also test some default values that were not overridden by environment variables.
    assert settings.FRONTEND_HOST == "localhost" # Default from class definition
    assert settings.FRONTEND_PORT == 8501 # Default from class definition
