import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Set a dummy GOOGLE_API_KEY to satisfy the Settings validation
    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key-123")

    # Clear the cache before the test to ensure a fresh instance,
    # important for isolated testing of lru_cache functions.
    # Assuming get_settings is imported at the module level.
    get_settings.cache_clear()

    # First call to get_settings
    settings_instance_1 = get_settings()

    # Assert that it's an instance of the Settings class
    # Assuming Settings is also imported and available.
    assert isinstance(settings_instance_1, Settings)

    # Assert that the GOOGLE_API_KEY is correctly loaded
    assert settings_instance_1.GOOGLE_API_KEY == "test-api-key-123"

    # Assert a default value
    assert settings_instance_1.API_HOST == "localhost"
    assert settings_instance_1.API_PORT == 8000
    assert settings_instance_1.DEBUG is True

    # Second call to get_settings to test the lru_cache
    settings_instance_2 = get_settings()

    # Assert that the same instance is returned due to lru_cache
    assert settings_instance_1 is settings_instance_2

    # Clear the cache after the test (good practice for test isolation)
    get_settings.cache_clear()
