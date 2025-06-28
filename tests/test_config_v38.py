import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Import `get_settings` and `Settings` is assumed to be handled by the test file's imports.
    from app.utils.config import get_settings, Settings

    # Clear the lru_cache to ensure a fresh evaluation during the test.
    # This is important because get_settings() is called at module load time,
    # and lru_cache caches exceptions, which could prevent the test from running correctly.
    get_settings.cache_clear()

    # Use monkeypatch to temporarily set the GOOGLE_API_KEY environment variable.
    # This prevents the ValueError from being raised by the Settings class during instantiation.
    monkeypatch.setenv("GOOGLE_API_KEY", "test_google_api_key_123")

    # Call the get_settings function for the first time.
    settings_instance_1 = get_settings()

    # Assert that the returned object is an instance of the Settings class.
    assert isinstance(settings_instance_1, Settings)

    # Call the get_settings function again.
    # Due to @lru_cache(), it should return the exact same instance.
    settings_instance_2 = get_settings()

    # Assert that the two instances are indeed the same object, verifying lru_cache behavior.
    assert settings_instance_1 is settings_instance_2

    # Assert some default values to confirm the Settings object is correctly loaded.
    assert settings_instance_1.API_HOST == "localhost"
    assert settings_instance_1.API_PORT == 8000
    assert settings_instance_1.DEBUG is True
