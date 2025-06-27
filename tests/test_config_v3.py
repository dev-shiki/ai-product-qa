import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # It's crucial to clear the lru_cache for get_settings before testing.
    # This ensures that our monkeypatching of environment variables takes effect
    # on the first call to get_settings within the test, rather than returning
    # an instance potentially cached from module import.
    get_settings.cache_clear()

    # Use monkeypatch to set a dummy GOOGLE_API_KEY environment variable.
    # This is necessary because the Settings class validates this key and
    # raises a ValueError if it's not set or has the default placeholder value.
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy_test_api_key_123")

    # Call the function under test.
    settings_instance = get_settings()

    # Assert that the returned object is an instance of the Settings class.
    assert isinstance(settings_instance, Settings)

    # Assert that the GOOGLE_API_KEY was correctly loaded from the monkeypatched environment.
    assert settings_instance.GOOGLE_API_KEY == "dummy_test_api_key_123"

    # Assert some other default values to ensure the settings object is correctly initialized.
    assert settings_instance.API_HOST == "localhost"
    assert settings_instance.DEBUG is True

    # Verify lru_cache behavior: subsequent calls to get_settings should return the same instance.
    settings_instance_2 = get_settings()
    assert settings_instance is settings_instance_2

    # Clean up the cache after the test to ensure isolation for other tests.
    get_settings.cache_clear()
