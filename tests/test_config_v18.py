import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # It's crucial to clear the lru_cache to ensure a fresh Settings instance
    # is created with our test environment variables.
    # Assumes 'get_settings' is available via top-level import in the test file.
    get_settings.cache_clear()

    # Set a dummy GOOGLE_API_KEY environment variable to satisfy validation
    test_api_key = "test_google_api_key_123_abc"
    monkeypatch.setenv("GOOGLE_API_KEY", test_api_key)

    # Call the function under test
    settings_instance = get_settings()

    # Assertions
    # Assumes 'Settings' class is available via top-level import in the test file.
    assert isinstance(settings_instance, Settings)
    assert settings_instance.GOOGLE_API_KEY == test_api_key
    assert settings_instance.API_HOST == "localhost"
    assert settings_instance.API_PORT == 8000
    assert settings_instance.FRONTEND_HOST == "localhost"
    assert settings_instance.FRONTEND_PORT == 8501
    assert settings_instance.DEBUG is True
