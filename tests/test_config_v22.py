import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    """
    Test the basic functionality of the get_settings function,
    including environment variable loading and lru_cache behavior.
    """
    # Clear the lru_cache to ensure a clean state for this test.
    # This is important as lru_cache retains its state across test runs.
    get_settings.cache_clear()

    # Set dummy environment variables using monkeypatch to avoid ValueError
    # from Settings validation and to test value loading.
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key-123")
    monkeypatch.setenv("API_HOST", "test.api.host")
    monkeypatch.setenv("API_PORT", "9090")
    monkeypatch.setenv("DEBUG", "False") # Test boolean conversion

    # Call get_settings for the first time
    settings1 = get_settings()

    # Assert that attributes are correctly loaded from environment variables or defaults
    assert settings1.GOOGLE_API_KEY == "test-google-api-key-123"
    assert settings1.API_HOST == "test.api.host"
    assert settings1.API_PORT == 9090
    assert settings1.DEBUG is False
    assert settings1.FRONTEND_HOST == "localhost" # Default value check
    assert settings1.FRONTEND_PORT == 8501 # Default value check

    # Call get_settings again to test lru_cache functionality
    settings2 = get_settings()

    # Assert that both calls return the exact same instance due to lru_cache
    assert settings1 is settings2

    # Clear the cache again to clean up for subsequent tests
    get_settings.cache_clear()
