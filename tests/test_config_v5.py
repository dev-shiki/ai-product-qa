import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Clear the cache to ensure a fresh instance is created with the mocked env vars
    # This is important for testing lru_cached functions.
    get_settings.cache_clear()

    # Set dummy environment variables required by Settings to pass validation and test overrides.
    # Pydantic-settings will pick these up.
    dummy_api_key = "dummy_google_api_key_for_test"
    dummy_api_host = "test.api.example.com"
    dummy_api_port = "1234" # Set as string, Pydantic should cast to int
    dummy_debug = "False" # Set as string, Pydantic should cast to bool

    monkeypatch.setenv("GOOGLE_API_KEY", dummy_api_key)
    monkeypatch.setenv("API_HOST", dummy_api_host)
    monkeypatch.setenv("API_PORT", dummy_api_port)
    monkeypatch.setenv("DEBUG", dummy_debug)

    # Call the function under test
    settings = get_settings()

    # Assert that the settings object has the expected values from the environment variables
    assert settings.GOOGLE_API_KEY == dummy_api_key
    assert settings.API_HOST == dummy_api_host
    assert settings.API_PORT == int(dummy_api_port) # Verify integer conversion
    assert settings.DEBUG is False # Verify boolean conversion

    # Assert that default values are also correctly set if not overridden
    # For example, FRONTEND_HOST and FRONTEND_PORT were not monkeypatched
    assert settings.FRONTEND_HOST == "localhost"
    assert settings.FRONTEND_PORT == 8501

    # Assert that the lru_cache behavior works (subsequent calls return the same instance)
    settings_cached = get_settings()
    assert settings is settings_cached
