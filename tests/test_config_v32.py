import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Ensure the cache is cleared before testing to get a fresh instance
    # This is crucial because get_settings is decorated with @lru_cache
    # and might have been called at module import time (settings = get_settings()).
    get_settings.cache_clear()

    # Set a specific GOOGLE_API_KEY environment variable for this test
    # This prevents the ValueError from Settings' __init__ and allows testing with a known value.
    test_api_key = "dummy-api-key-for-testing-123"
    monkeypatch.setenv("GOOGLE_API_KEY", test_api_key)

    # Call the get_settings function
    settings_instance_1 = get_settings()

    # Assertions for basic properties
    # (Assuming Settings class is available for isinstance check in the test environment)
    # assert isinstance(settings_instance_1, Settings) # Cannot use without importing Settings explicitly
    assert settings_instance_1.GOOGLE_API_KEY == test_api_key
    assert settings_instance_1.API_HOST == "localhost"  # Check a default value
    assert settings_instance_1.API_PORT == 8000
    assert settings_instance_1.DEBUG is True

    # Test that subsequent calls return the same cached instance
    settings_instance_2 = get_settings()
    assert settings_instance_1 is settings_instance_2
