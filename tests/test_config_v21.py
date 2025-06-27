import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Set a valid GOOGLE_API_KEY environment variable to prevent ValueError
    # during the initialization of the Settings class.
    monkeypatch.setenv("GOOGLE_API_KEY", "test_api_key_123")

    # Call get_settings for the first time.
    # This should instantiate the Settings object and cache it.
    settings_instance_1 = get_settings()

    # Assert that an object was returned and is not None.
    assert settings_instance_1 is not None

    # Assert that a key property (GOOGLE_API_KEY) is correctly set based on the environment variable.
    assert settings_instance_1.GOOGLE_API_KEY == "test_api_key_123"

    # Assert a default property from the Settings class.
    assert settings_instance_1.API_PORT == 8000

    # Call get_settings a second time.
    # Due to @lru_cache, this should return the same cached instance as the first call.
    settings_instance_2 = get_settings()

    # Assert that both calls returned the exact same object, confirming caching behavior.
    assert settings_instance_1 is settings_instance_2
