import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Assuming get_settings and Settings are imported in the test file context
    from app.utils.config import get_settings, Settings

    # Set a dummy GOOGLE_API_KEY to satisfy the Settings class's validation
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy_test_api_key")

    # Clear the lru_cache to ensure a fresh state for testing cache behavior
    get_settings.cache_clear()

    # First call to get_settings
    settings_instance_1 = get_settings()

    # Assert that it returns an instance of Settings
    assert isinstance(settings_instance_1, Settings)

    # Assert some default values or expected behaviors
    assert settings_instance_1.API_HOST == "localhost"
    assert settings_instance_1.DEBUG is True
    assert settings_instance_1.GOOGLE_API_KEY == "dummy_test_api_key"

    # Second call to get_settings to test lru_cache functionality
    settings_instance_2 = get_settings()

    # Assert that both calls return the exact same instance (due to lru_cache)
    assert settings_instance_1 is settings_instance_2
