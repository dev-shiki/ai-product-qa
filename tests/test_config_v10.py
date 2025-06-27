import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Ensure a fresh Settings object is created by clearing the cache,
    # as get_settings uses lru_cache and might have been called globally
    # (e.g., by `settings = get_settings()` at module level).
    get_settings.cache_clear()

    # Set necessary environment variables using monkeypatch fixture.
    # This prevents the ValueError from GOOGLE_API_KEY not being set or being default,
    # and allows verifying that settings are picked up correctly.
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key-123")
    monkeypatch.setenv("API_HOST", "test.api.host")
    monkeypatch.setenv("API_PORT", "9999")
    monkeypatch.setenv("DEBUG", "False") # Test boolean parsing

    # Call the function under test.
    settings = get_settings()

    # Assert that the returned object has the expected attributes
    # and their values match the environment variables set.
    assert hasattr(settings, "GOOGLE_API_KEY")
    assert settings.GOOGLE_API_KEY == "test-google-api-key-123"

    assert hasattr(settings, "API_HOST")
    assert settings.API_HOST == "test.api.host"

    assert hasattr(settings, "API_PORT")
    assert settings.API_PORT == 9999 # Pydantic parses string to int

    assert hasattr(settings, "DEBUG")
    assert settings.DEBUG is False # Pydantic parses string to boolean
