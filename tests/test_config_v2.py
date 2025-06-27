import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Clear the lru_cache to ensure a fresh instance is created
    # This is important if get_settings was called before the test setup.
    get_settings.cache_clear()

    # Set a valid GOOGLE_API_KEY environment variable for the test duration.
    # This prevents the ValueError raised by Settings.__init__.
    test_api_key = "test-api-key-123abc"
    monkeypatch.setenv("GOOGLE_API_KEY", test_api_key)

    # Call the function under test
    settings_instance = get_settings()

    # Assertions for basic functionality:
    # 1. Check that the returned object is not None.
    assert settings_instance is not None

    # 2. Check that the GOOGLE_API_KEY from environment is correctly picked up.
    assert settings_instance.GOOGLE_API_KEY == test_api_key

    # 3. Check some default values to ensure a valid Settings object is returned.
    assert settings_instance.API_HOST == "localhost"
    assert settings_instance.API_PORT == 8000
    assert settings_instance.DEBUG is True

    # 4. Verify the lru_cache functionality: subsequent calls should return the same instance.
    settings_cached_instance = get_settings()
    assert settings_instance is settings_cached_instance
