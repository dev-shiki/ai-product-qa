import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Clear the lru_cache to ensure a fresh Settings object is created
    # This is important because get_settings is decorated with @lru_cache
    # and might have been called at module level upon app import.
    get_settings.cache_clear()

    # Set a dummy API key using monkeypatch, which is a pytest fixture.
    # This simulates setting the GOOGLE_API_KEY environment variable for the test duration.
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy_google_api_key_for_testing")

    # Call the function under test
    settings = get_settings()

    # Assertions to verify basic functionality
    # 1. Ensure the returned object is not None
    assert settings is not None

    # 2. Verify that the GOOGLE_API_KEY is correctly loaded from the mocked environment
    assert settings.GOOGLE_API_KEY == "dummy_google_api_key_for_testing"

    # 3. Verify some default values to confirm the Settings object is properly initialized
    assert settings.API_HOST == "localhost"
    assert settings.API_PORT == 8000
    assert settings.DEBUG is True
