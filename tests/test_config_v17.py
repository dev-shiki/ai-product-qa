import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Ensure the lru_cache is cleared before the test to get fresh settings
    # (assuming get_settings is accessible in the test scope)
    get_settings.cache_clear()

    # Set necessary environment variables for the test using monkeypatch
    monkeypatch.setenv("GOOGLE_API_KEY", "mock_google_api_key_123")
    monkeypatch.setenv("API_HOST", "test_api_host")
    monkeypatch.setenv("API_PORT", "9999")
    monkeypatch.setenv("DEBUG", "False")

    # Call the function under test
    settings = get_settings()

    # Assertions for basic functionality and configured values
    assert settings is not None
    assert settings.GOOGLE_API_KEY == "mock_google_api_key_123"
    assert settings.API_HOST == "test_api_host"
    assert settings.API_PORT == 9999
    assert settings.DEBUG is False

    # Assertions for default values that were not overridden
    assert settings.FRONTEND_HOST == "localhost"
    assert settings.FRONTEND_PORT == 8501
