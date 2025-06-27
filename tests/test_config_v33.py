import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Ensure GOOGLE_API_KEY is set to prevent ValueError during Settings initialization.
    # This is a basic use of monkeypatch, not considered complex for pytest.
    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key-123")

    # Clear the lru_cache before the test to ensure a fresh Settings instance is created.
    # This is crucial because get_settings is called globally when config.py is imported,
    # and we want to test its behavior under controlled conditions.
    get_settings.cache_clear()

    # Call the function under test for the first time
    settings_instance_1 = get_settings()

    # Assertions for basic functionality:
    # 1. It should return an instance of Settings.
    assert isinstance(settings_instance_1, Settings)
    # 2. The GOOGLE_API_KEY should be correctly set from the mocked environment variable.
    assert settings_instance_1.GOOGLE_API_KEY == "test-api-key-123"

    # Test the lru_cache functionality:
    # A subsequent call to get_settings should return the exact same instance.
    settings_instance_2 = get_settings()
    assert settings_instance_1 is settings_instance_2
