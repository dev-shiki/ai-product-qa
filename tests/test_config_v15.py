import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Set a valid GOOGLE_API_KEY for the duration of the test
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy_google_api_key_for_test")

    # Clear the lru_cache of get_settings to ensure a fresh instance is created.
    # This is important because get_settings() is called at module load time in app/utils/config.py,
    # and subsequent calls might return the cached instance, preventing a fresh run for the test.
    # get_settings is assumed to be in scope.
    get_settings.cache_clear()

    # Call the function to get settings
    settings_instance = get_settings()

    # Assert that the GOOGLE_API_KEY is correctly loaded from the mocked environment variable
    assert settings_instance.GOOGLE_API_KEY == "dummy_google_api_key_for_test"

    # Assert some default values to confirm the Settings object is properly initialized
    assert settings_instance.API_HOST == "localhost"
    assert settings_instance.API_PORT == 8000
    assert settings_instance.DEBUG is True

    # Assert that subsequent calls return the same cached instance due to lru_cache
    second_settings_instance = get_settings()
    assert second_settings_instance is settings_instance
