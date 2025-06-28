import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Set necessary environment variables for the test to ensure successful settings loading
    test_google_api_key = "test_google_api_key_123"
    test_api_host = "test.api.host"
    test_api_port = "9876"  # Pydantic will convert this string to an int
    test_debug_flag = "False" # Pydantic will convert this string to a boolean

    monkeypatch.setenv("GOOGLE_API_KEY", test_google_api_key)
    monkeypatch.setenv("API_HOST", test_api_host)
    monkeypatch.setenv("API_PORT", test_api_port)
    monkeypatch.setenv("DEBUG", test_debug_flag)

    # Clear the lru_cache to ensure that get_settings reloads configurations
    # from the environment variables set by monkeypatch, rather than using a
    # previously cached instance from initial module import.
    get_settings.cache_clear()

    # Call the function under test
    settings = get_settings()

    # Assertions to verify the basic functionality and correct loading of settings
    # 1. Assert that the returned object is an instance of the Settings class
    assert isinstance(settings, Settings)

    # 2. Assert that the GOOGLE_API_KEY is correctly loaded from the environment
    assert settings.GOOGLE_API_KEY == test_google_api_key

    # 3. Assert that other configured properties are correctly loaded or retain their defaults
    assert settings.API_HOST == test_api_host
    assert settings.API_PORT == int(test_api_port) # Verify type conversion
    assert settings.DEBUG is False # Verify boolean conversion
