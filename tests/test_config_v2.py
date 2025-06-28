import pytest
from app.utils.config import Settings
import os

@pytest.fixture
def clean_settings_env(monkeypatch):
    """
    Fixture to ensure Settings doesn't load from a real .env file
    and provides a clean slate for GOOGLE_API_KEY environment variable.
    """
    # Prevent BaseSettings from loading from a real .env file
    monkeypatch.setattr(Settings.Config, 'env_file', os.devnull)
    # Ensure GOOGLE_API_KEY is unset at the start of each test using this fixture
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

def test_settings_valid_configuration_and_defaults(monkeypatch, clean_settings_env):
    """
    Test that Settings can be instantiated with a valid GOOGLE_API_KEY
    and that default values are correctly loaded.
    """
    expected_api_key = "test_valid_api_key_123"
    monkeypatch.setenv("GOOGLE_API_KEY", expected_api_key)

    settings = Settings()

    assert settings.GOOGLE_API_KEY == expected_api_key
    assert settings.API_HOST == "localhost"
    assert settings.API_PORT == 8000
    assert settings.FRONTEND_HOST == "localhost"
    assert settings.FRONTEND_PORT == 8501
    assert settings.DEBUG is True

def test_settings_google_api_key_missing(clean_settings_env):
    """
    Test that Settings raises ValueError when GOOGLE_API_KEY is missing from environment.
    """
    # GOOGLE_API_KEY is ensured to be unset by clean_settings_env fixture

    with pytest.raises(ValueError) as excinfo:
        Settings()

    assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)

def test_settings_google_api_key_default_placeholder(monkeypatch, clean_settings_env):
    """
    Test that Settings raises ValueError when GOOGLE_API_KEY is set to its default placeholder.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")

    with pytest.raises(ValueError) as excinfo:
        Settings()

    assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)

# Optional: A test to ensure get_settings() returns a Settings instance
# This is more an integration test for lru_cache, but simple enough to include.
def test_get_settings_returns_settings_instance(monkeypatch, clean_settings_env):
    """
    Test that get_settings() function returns an instance of Settings.
    Note: This test implicitly relies on the caching mechanism,
    so ensure environment setup is consistent if calling multiple times.
    """
    from app.utils.config import get_settings # Import get_settings here to avoid circular dependencies if get_settings uses settings directly at module level
    
    expected_api_key = "another_valid_key_456"
    monkeypatch.setenv("GOOGLE_API_KEY", expected_api_key)

    settings_instance = get_settings()
    assert isinstance(settings_instance, Settings)
    assert settings_instance.GOOGLE_API_KEY == expected_api_key