import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Prepare a test value for GOOGLE_API_KEY
    test_key = "test_google_api_key_for_unit_test_123"

    # Set the environment variable using monkeypatch.
    # This ensures the Settings object can be initialized without raising ValueError.
    monkeypatch.setenv("GOOGLE_API_KEY", test_key)

    # Clear the lru_cache for get_settings.
    # This is crucial because `settings = get_settings()` is called at the module level
    # when `app/utils/config.py` is imported. Clearing the cache ensures that
    # our test call to `get_settings()` results in a fresh Settings object
    # initialized with our `monkeypatch`'d environment variable.
    try:
        if hasattr(get_settings, 'cache_clear'):
            get_settings.cache_clear()
    except Exception:
        # Handle cases where cache_clear might not be available for some reason,
        # though for lru_cache it should be.
        pass

    # Call the function under test
    settings_obj = get_settings()

    # Assert that the returned object has the expected attributes and values
    assert hasattr(settings_obj, "GOOGLE_API_KEY")
    assert settings_obj.GOOGLE_API_KEY == test_key

    # Assert some default values to ensure the Settings object is correctly initialized
    assert hasattr(settings_obj, "API_HOST")
    assert settings_obj.API_HOST == "localhost"

    assert hasattr(settings_obj, "API_PORT")
    assert settings_obj.API_PORT == 8000

    assert hasattr(settings_obj, "DEBUG")
    assert settings_obj.DEBUG is True
