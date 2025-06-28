import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Clear the lru_cache to ensure a fresh state for the test
    # This is important when environment variables influence the cached result
    get_settings.cache_clear()

    # Temporarily set the GOOGLE_API_KEY environment variable
    # This is required because Settings.__init__ validates its presence
    dummy_api_key = "test-google-api-key-123"
    monkeypatch.setenv("GOOGLE_API_KEY", dummy_api_key)

    # Call the function under test
    settings_instance = get_settings()

    # Assert that an instance of Settings is returned
    assert isinstance(settings_instance, Settings)

    # Assert that the GOOGLE_API_KEY was correctly loaded from the environment
    assert settings_instance.GOOGLE_API_KEY == dummy_api_key

    # Assert that some default values are as expected
    assert settings_instance.API_HOST == "localhost"
    assert settings_instance.DEBUG is True
