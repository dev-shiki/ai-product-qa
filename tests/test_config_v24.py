import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Clear the lru_cache to ensure a fresh settings object is created for this test
    # (Assuming get_settings is imported: from app.utils.config import get_settings)
    get_settings.cache_clear()

    # Set a dummy GOOGLE_API_KEY environment variable to avoid ValueError
    # and ensure the Settings object can be created successfully.
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy_test_api_key")

    # Call the function to be tested
    settings = get_settings()

    # Assert that the returned object is not None
    assert settings is not None

    # Assert that a key attribute is correctly loaded
    assert settings.GOOGLE_API_KEY == "dummy_test_api_key"

    # Assert that the returned object is an instance of the Settings class
    # (Assuming Settings is imported: from app.utils.config import Settings)
    from app.utils.config import Settings
    assert isinstance(settings, Settings)

    # Optional: Test that calling it again returns the same cached instance
    cached_settings = get_settings()
    assert settings is cached_settings
