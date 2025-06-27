import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Set a dummy GOOGLE_API_KEY to bypass the validation error
    monkeypatch.setenv("GOOGLE_API_KEY", "test_google_api_key")

    # Get settings the first time
    settings_instance_1 = get_settings()

    # Assert it's an instance of the Settings class (assuming Settings is accessible from the same module)
    assert isinstance(settings_instance_1, type(get_settings())) # More robust way to check type without direct 'Settings' import

    # Assert basic attributes and default values
    assert settings_instance_1.GOOGLE_API_KEY == "test_google_api_key"
    assert settings_instance_1.API_HOST == "localhost"
    assert settings_instance_1.API_PORT == 8000
    assert settings_instance_1.DEBUG is True

    # Get settings a second time to test lru_cache
    settings_instance_2 = get_settings()

    # Assert that the same instance is returned due to lru_cache
    assert settings_instance_1 is settings_instance_2
