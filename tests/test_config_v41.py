import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Temporarily set GOOGLE_API_KEY to avoid ValueError during Settings initialization
    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key-123")

    # Call the function under test
    settings = get_settings()

    # Assert that an object is returned and is not None
    assert settings is not None

    # Assert some basic attributes and their expected values
    assert hasattr(settings, "GOOGLE_API_KEY")
    assert settings.GOOGLE_API_KEY == "test-api-key-123"
    assert hasattr(settings, "API_HOST")
    assert settings.API_HOST == "localhost"
    assert hasattr(settings, "DEBUG")
    assert settings.DEBUG is True

    # Test the lru_cache functionality: calling it again should return the same instance
    settings_cached = get_settings()
    assert settings is settings_cached
