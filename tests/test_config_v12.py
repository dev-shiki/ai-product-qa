import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Clear the lru_cache to ensure a fresh Settings object is created for this test.
    # This is crucial for test isolation, as get_settings uses lru_cache.
    get_settings.cache_clear()

    # Set necessary environment variables to pass validation and test custom values.
    test_api_key = "test_api_key_12345"
    test_api_host = "test.api.host"
    test_api_port = "9000"
    test_debug_mode = "False" # Test boolean conversion

    monkeypatch.setenv("GOOGLE_API_KEY", test_api_key)
    monkeypatch.setenv("API_HOST", test_api_host)
    monkeypatch.setenv("API_PORT", test_api_port)
    monkeypatch.setenv("DEBUG", test_debug_mode)

    # Call the function under test
    settings = get_settings()

    # Assertions to check if settings are loaded correctly
    assert settings is not None
    assert settings.GOOGLE_API_KEY == test_api_key
    assert settings.API_HOST == test_api_host
    assert settings.API_PORT == int(test_api_port)
    assert settings.DEBUG is False

    # Verify that get_settings is cached and returns the same instance on subsequent calls
    cached_settings = get_settings()
    assert cached_settings is settings
