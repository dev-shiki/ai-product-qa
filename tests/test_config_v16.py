import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Ensure the lru_cache for get_settings is cleared before the test.
    # This is critical because `get_settings()` is called at the module level in `config.py`
    # (`settings = get_settings()`), which populates the cache. Clearing it allows
    # our `monkeypatch` to effectively change the environment variables for the test.
    get_settings.cache_clear()

    # Set a dummy GOOGLE_API_KEY environment variable for the test duration.
    # This prevents the `ValueError` that `Settings` class would raise if the key
    # is not set or is the default placeholder.
    test_api_key = "test-api-key-12345"
    monkeypatch.setenv("GOOGLE_API_KEY", test_api_key)

    # Call the function under test.
    settings = get_settings()

    # Assert that the GOOGLE_API_KEY in the returned settings object matches our dummy key.
    assert settings.GOOGLE_API_KEY == test_api_key

    # Assert some other default values to confirm the Settings object was correctly loaded.
    assert settings.API_HOST == "localhost"
    assert settings.API_PORT == 8000
    assert settings.DEBUG is True

    # Verify that subsequent calls to get_settings return the same cached instance.
    cached_settings = get_settings()
    assert settings is cached_settings
