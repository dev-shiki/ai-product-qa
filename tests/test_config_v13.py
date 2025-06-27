import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Set a valid GOOGLE_API_KEY environment variable for the test duration
    # This is necessary because Settings validation requires it.
    monkeypatch.setenv("GOOGLE_API_KEY", "test_api_key_123")

    # Call the function under test
    settings_instance = get_settings()

    # Assert that the returned object is an instance of the Settings class
    # (Assuming 'Settings' class is imported in the test file scope)
    assert isinstance(settings_instance, Settings)

    # Assert that the GOOGLE_API_KEY is correctly loaded
    assert settings_instance.GOOGLE_API_KEY == "test_api_key_123"

    # Assert that default values are correctly applied
    assert settings_instance.API_HOST == "localhost"
    assert settings_instance.API_PORT == 8000

    # Test lru_cache behavior: subsequent calls should return the same instance
    cached_settings_instance = get_settings()
    assert settings_instance is cached_settings_instance
