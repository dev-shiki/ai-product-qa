import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Ensure a valid GOOGLE_API_KEY is set in the environment for the test
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key-123")

    # Clear the lru_cache of get_settings to ensure a fresh Settings object is created
    # This is crucial because settings = get_settings() is called at module level,
    # and the cache might hold an instance from a previous import or test run.
    get_settings.cache_clear()

    # Call the function under test
    settings_obj = get_settings()

    # Assert that the function returns an object
    assert settings_obj is not None

    # Assert that the returned object has expected attributes (basic check for Settings type behavior)
    assert hasattr(settings_obj, "GOOGLE_API_KEY")
    assert hasattr(settings_obj, "API_HOST")
    assert hasattr(settings_obj, "API_PORT")
    assert hasattr(settings_obj, "DEBUG")

    # Assert that the GOOGLE_API_KEY from the mocked environment variable is used
    assert settings_obj.GOOGLE_API_KEY == "test-google-api-key-123"

    # Assert that default values are correctly loaded
    assert settings_obj.API_HOST == "localhost"
    assert settings_obj.API_PORT == 8000
    assert settings_obj.DEBUG is True
