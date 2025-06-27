import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Clear the lru_cache to ensure a clean state for this test.
    # This is important because get_settings() is called at the module level
    # in app/utils/config.py, which caches its result.
    get_settings.cache_clear()

    # Set a dummy GOOGLE_API_KEY environment variable.
    # This is crucial as Settings validation requires it.
    dummy_api_key = "test_google_api_key_for_unit_test"
    monkeypatch.setenv("GOOGLE_API_KEY", dummy_api_key)

    # Call the function under test for the first time.
    settings_instance_1 = get_settings()

    # Assert that a settings object is returned and has expected properties.
    assert settings_instance_1 is not None
    # Assuming the Settings class is available in the test scope for type checking.
    # from app.utils.config import Settings # (Not added as per instruction)
    # assert isinstance(settings_instance_1, Settings) # Can be added if Settings is explicitly imported in test file

    # Assert that the GOOGLE_API_KEY is correctly loaded from the environment variable.
    assert settings_instance_1.GOOGLE_API_KEY == dummy_api_key

    # Assert some default values to ensure the object is correctly populated.
    assert settings_instance_1.API_HOST == "localhost"
    assert settings_instance_1.API_PORT == 8000
    assert settings_instance_1.FRONTEND_HOST == "localhost"
    assert settings_instance_1.FRONTEND_PORT == 8501
    assert settings_instance_1.DEBUG is True

    # Test the lru_cache behavior:
    # A subsequent call to get_settings() should return the exact same instance
    # because of the @lru_cache decorator and no arguments.
    settings_instance_2 = get_settings()
    assert settings_instance_2 is settings_instance_1
