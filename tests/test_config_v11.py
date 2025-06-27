import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Ensure a clean slate for the cached settings by clearing the lru_cache
    # This is crucial for tests that modify environment variables
    # as get_settings is called at module import level.
    get_settings.cache_clear()

    # Set necessary environment variables for the Settings model to initialize successfully
    # and to test overrides.
    test_google_api_key = "test-api-key-123abc"
    test_api_host = "test-api.example.com"
    test_api_port = "9090"
    test_debug = "False" # Test boolean conversion

    monkeypatch.setenv("GOOGLE_API_KEY", test_google_api_key)
    monkeypatch.setenv("API_HOST", test_api_host)
    monkeypatch.setenv("API_PORT", test_api_port)
    monkeypatch.setenv("DEBUG", test_debug)

    # Call the function under test
    settings = get_settings()

    # Assertions to verify the settings object and its properties
    assert settings is not None
    assert hasattr(settings, "GOOGLE_API_KEY")
    assert settings.GOOGLE_API_KEY == test_google_api_key
    assert hasattr(settings, "API_HOST")
    assert settings.API_HOST == test_api_host
    assert hasattr(settings, "API_PORT")
    assert settings.API_PORT == int(test_api_port)
    assert hasattr(settings, "DEBUG")
    assert settings.DEBUG is False # Verify boolean conversion from string "False"

    # Verify that the lru_cache is working by calling it again
    # and ensuring it returns the exact same instance.
    cached_settings = get_settings()
    assert settings is cached_settings
