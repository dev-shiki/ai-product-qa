import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    """
    Test basic functionality of get_settings, including environment variable loading
    and lru_cache behavior.
    """
    # To prevent ValueError from Settings.__init__ due to GOOGLE_API_KEY not being set,
    # and to test that settings are loaded from environment variables.
    monkeypatch.setenv("GOOGLE_API_KEY", "test_google_api_key")
    monkeypatch.setenv("API_HOST", "test_api_host")
    monkeypatch.setenv("API_PORT", "9001") # Note: environment variables are strings
    monkeypatch.setenv("FRONTEND_HOST", "test_frontend_host")
    monkeypatch.setenv("FRONTEND_PORT", "8502")
    monkeypatch.setenv("DEBUG", "False")

    # Clear the lru_cache for a clean test run, as get_settings is cached globally
    from app.utils.config import get_settings
    get_settings.cache_clear()

    # First call to get_settings
    settings_instance = get_settings()

    # Assert that an instance of Settings is returned
    from app.utils.config import Settings
    assert isinstance(settings_instance, Settings)

    # Assert that the settings fields are correctly loaded from environment variables
    assert settings_instance.GOOGLE_API_KEY == "test_google_api_key"
    assert settings_instance.API_HOST == "test_api_host"
    assert settings_instance.API_PORT == 9001
    assert settings_instance.FRONTEND_HOST == "test_frontend_host"
    assert settings_instance.FRONTEND_PORT == 8502
    assert settings_instance.DEBUG is False

    # Test lru_cache behavior: subsequent calls should return the same instance
    settings_instance_2 = get_settings()
    assert settings_instance is settings_instance_2
