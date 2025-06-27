import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Clear the lru_cache to ensure a fresh settings instance is created for the test.
    # This helps in isolating the test from previous calls or module-level initialization.
    get_settings.cache_clear()

    # Set a dummy GOOGLE_API_KEY to satisfy the Settings validation and prevent ValueError.
    monkeypatch.setenv("GOOGLE_API_KEY", "test_dummy_google_api_key")

    # Call the function under test.
    settings_instance = get_settings()

    # Assert that the function returns an object.
    assert settings_instance is not None

    # Assert that the returned object is an instance of the Settings class.
    # (Assumes 'Settings' class is imported and available in the test's scope,
    # as per instructions regarding pre-provided imports.)
    assert isinstance(settings_instance, Settings)

    # Assert that the GOOGLE_API_KEY was correctly set on the settings object.
    assert settings_instance.GOOGLE_API_KEY == "test_dummy_google_api_key"

    # Test that the lru_cache is working: subsequent calls return the exact same instance.
    settings_instance_cached = get_settings()
    assert settings_instance is settings_instance_cached
