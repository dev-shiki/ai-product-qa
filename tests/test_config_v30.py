import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Clear the lru_cache to ensure a fresh settings object is created for the test.
    # This is crucial for isolated testing when get_settings is cached.
    get_settings.cache_clear()

    # Set a dummy Google API Key environment variable for the test duration.
    # This allows the Settings object to initialize without raising a ValueError.
    monkeypatch.setenv("GOOGLE_API_KEY", "test_google_api_key_123")

    # Call the get_settings function.
    settings_instance = get_settings()

    # Assert that an object was returned and is not None.
    assert settings_instance is not None

    # Assert that the GOOGLE_API_KEY was correctly set from the environment variable.
    assert settings_instance.GOOGLE_API_KEY == "test_google_api_key_123"

    # Assert that default values for other settings are correctly applied.
    assert settings_instance.API_HOST == "localhost"
    assert settings_instance.API_PORT == 8000
    assert settings_instance.DEBUG is True
