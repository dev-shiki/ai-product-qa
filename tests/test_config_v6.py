import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Clear the lru_cache to ensure a fresh Settings instance is created for this test.
    # This is crucial because `settings = get_settings()` is called at module import time,
    # and `lru_cache` would return that initial instance unless cleared.
    get_settings.cache_clear()

    # Set a valid GOOGLE_API_KEY environment variable.
    # This prevents the ValueError from being raised by Settings.__init__.
    test_api_key = "test_google_api_key_12345"
    monkeypatch.setenv("GOOGLE_API_KEY", test_api_key)

    # Call the function under test for the first time.
    settings_instance_1 = get_settings()

    # Assert that the returned object is not None and has expected properties.
    assert settings_instance_1 is not None
    assert settings_instance_1.GOOGLE_API_KEY == test_api_key
    assert settings_instance_1.API_HOST == "localhost"
    assert settings_instance_1.API_PORT == 8000
    assert settings_instance_1.DEBUG is True

    # Test the lru_cache behavior: subsequent calls should return the exact same instance.
    settings_instance_2 = get_settings()
    assert settings_instance_1 is settings_instance_2
