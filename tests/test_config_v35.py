import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Clear the cache to ensure a fresh settings instance is created
    get_settings.cache_clear()

    # Set a dummy GOOGLE_API_KEY environment variable for the test
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy_test_api_key")

    # Call the get_settings function
    settings = get_settings()

    # Assert that the returned object is an instance of Settings
    assert isinstance(settings, Settings)

    # Assert that the GOOGLE_API_KEY is correctly loaded
    assert settings.GOOGLE_API_KEY == "dummy_test_api_key"

    # Assert that a default value is correctly loaded
    assert settings.API_HOST == "localhost"
    assert settings.API_PORT == 8000
    assert settings.DEBUG is True
