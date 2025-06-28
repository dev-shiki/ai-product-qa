import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Set a dummy API key to satisfy the validation
    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key-123")

    # Clear the cache of get_settings to ensure a fresh instance for this test
    # This is important for `@lru_cache` decorated functions in unit tests
    get_settings.cache_clear()

    # Call the function
    settings = get_settings()

    # Assert basic functionality: it returns an object with expected attributes
    assert settings.GOOGLE_API_KEY == "test-api-key-123"
    assert settings.API_HOST == "localhost" # Check a default value
    assert settings.DEBUG is True # Check another default boolean value

    # Test that subsequent calls return the same cached instance
    settings_2 = get_settings()
    assert settings is settings_2 # Verify lru_cache behavior
