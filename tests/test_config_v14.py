import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Clear the lru_cache to ensure a fresh settings object is created
    # This is important because the cache persists across calls within a session.
    get_settings.cache_clear()

    # Set a dummy GOOGLE_API_KEY environment variable to pass validation
    monkeypatch.setenv("GOOGLE_API_KEY", "test_dummy_api_key_123")

    # Call the function to get settings
    settings = get_settings()

    # Assert that a settings object is returned and has expected attributes
    assert settings is not None
    assert hasattr(settings, "GOOGLE_API_KEY")
    assert hasattr(settings, "API_HOST")
    assert hasattr(settings, "API_PORT")
    assert hasattr(settings, "DEBUG")

    # Assert that the GOOGLE_API_KEY is the one we set
    assert settings.GOOGLE_API_KEY == "test_dummy_api_key_123"

    # Assert default values for other settings
    assert settings.API_HOST == "localhost"
    assert settings.API_PORT == 8000
    assert settings.DEBUG is True

    # Verify that calling get_settings again returns the same cached instance
    settings_cached = get_settings()
    assert settings is settings_cached
