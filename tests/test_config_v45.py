import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Ensure a valid GOOGLE_API_KEY is set to bypass the validation error
    monkeypatch.setenv("GOOGLE_API_KEY", "test_google_api_key_123")

    # Call the function under test
    settings = get_settings()

    # Assert that the returned object is not None
    assert settings is not None

    # Assert that the GOOGLE_API_KEY is correctly loaded
    assert settings.GOOGLE_API_KEY == "test_google_api_key_123"

    # Assert that default values are also loaded correctly
    assert settings.API_HOST == "localhost"
    assert settings.API_PORT == 8000
    assert settings.DEBUG is True
