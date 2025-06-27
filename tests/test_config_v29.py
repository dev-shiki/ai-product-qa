import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Clear the cache before running the test to ensure a clean state
    # This is crucial because get_settings is decorated with lru_cache
    get_settings.cache_clear()

    # Set a dummy API key to satisfy the validation requirement
    monkeypatch.setenv("GOOGLE_API_KEY", "test_google_api_key_123")

    # Call get_settings for the first time
    settings_instance_1 = get_settings()

    # Assert basic attributes and the set environment variable
    assert settings_instance_1.GOOGLE_API_KEY == "test_google_api_key_123"
    assert settings_instance_1.API_HOST == "localhost"  # Check a default value

    # Call get_settings again to test lru_cache functionality
    settings_instance_2 = get_settings()

    # Assert that both calls return the same instance due to lru_cache
    assert settings_instance_1 is settings_instance_2

    # Verify that the value from the cached instance is still correct
    assert settings_instance_2.GOOGLE_API_KEY == "test_google_api_key_123"

    # Clear the cache after the test to prevent side effects on other tests
    get_settings.cache_clear()
