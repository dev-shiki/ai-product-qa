import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Ensure GOOGLE_API_KEY is set to avoid ValueError during Settings initialization
    # 'test_api_key' is just a placeholder, any non-empty string works.
    monkeypatch.setenv("GOOGLE_API_KEY", "test_google_api_key")

    # Clear the lru_cache to ensure a fresh instance is created for this test.
    # This is crucial because get_settings is a global variable and might have
    # been called and cached previously in the test session.
    from app.utils.config import get_settings, Settings
    get_settings.cache_clear()

    # Call get_settings for the first time
    settings_instance_1 = get_settings()

    # Assert that it returns an instance of the Settings class
    assert isinstance(settings_instance_1, Settings)

    # Verify that the GOOGLE_API_KEY is correctly loaded (from our monkeypatch)
    assert settings_instance_1.GOOGLE_API_KEY == "test_google_api_key"

    # Call get_settings again to test the lru_cache behavior
    settings_instance_2 = get_settings()

    # Assert that the second call returns the same instance as the first due to caching
    assert settings_instance_1 is settings_instance_2

    # Clean up the cache after the test (good practice for cached functions)
    get_settings.cache_clear()
