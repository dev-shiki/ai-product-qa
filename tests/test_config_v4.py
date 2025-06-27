import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Set a dummy GOOGLE_API_KEY to satisfy the validation
    monkeypatch.setenv("GOOGLE_API_KEY", "test_google_api_key_123")

    # Clear the lru_cache for get_settings to ensure a fresh call
    # This is important if get_settings was called in another test or module import.
    from app.utils.config import get_settings
    get_settings.cache_clear()

    # Call the function under test
    settings_instance = get_settings()

    # Assert that it returns an instance of Settings
    # Assuming Settings class is available in the test scope (e.g., via import)
    from app.utils.config import Settings
    assert isinstance(settings_instance, Settings)

    # Assert that the GOOGLE_API_KEY is correctly loaded
    assert settings_instance.GOOGLE_API_KEY == "test_google_api_key_123"

    # Assert that default values are also present
    assert settings_instance.API_HOST == "localhost"
    assert settings_instance.API_PORT == 8000
    assert settings_instance.DEBUG is True

    # Test lru_cache behavior: calling it again should return the exact same instance
    settings_instance_2 = get_settings()
    assert settings_instance is settings_instance_2
