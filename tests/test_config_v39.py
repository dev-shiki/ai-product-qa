import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Set a dummy GOOGLE_API_KEY to ensure validation passes and specific value is loaded.
    test_api_key = "test-api-key-for-unit-test"
    monkeypatch.setenv("GOOGLE_API_KEY", test_api_key)

    # Clear the lru_cache of get_settings. This is crucial because get_settings() is called
    # at the module level in app/utils/config.py, and its result is cached.
    # To ensure our monkeypatched environment is used for the test, we must clear the cache.
    get_settings.cache_clear()

    # Call the function under test
    settings_instance = get_settings()

    # Assertions:
    # 1. Verify that the returned object is an instance of the Settings class.
    #    We assume 'Settings' class is also available in the test scope (e.g., imported globally).
    assert isinstance(settings_instance, Settings)

    # 2. Verify that the GOOGLE_API_KEY is correctly loaded from our mocked environment variable.
    assert settings_instance.GOOGLE_API_KEY == test_api_key

    # 3. Verify that lru_cache is working as expected by checking if subsequent calls
    #    return the exact same instance.
    another_settings_instance = get_settings()
    assert settings_instance is another_settings_instance

    # 4. Optionally, verify some default values to ensure settings are loaded correctly.
    assert settings_instance.API_HOST == "localhost"
    assert settings_instance.API_PORT == 8000
    assert settings_instance.DEBUG is True
