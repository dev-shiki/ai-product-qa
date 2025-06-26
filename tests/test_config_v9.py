import pytest
import os
import logging
from unittest.mock import patch, MagicMock

# It's crucial to import the module under test only after ensuring
# the environment is somewhat prepared, or to handle the module-level
# variable initialization carefully.
# For simplicity in this case, we'll assume the pytest environment setup
# (e.g., via pytest.ini or command line) provides a default GOOGLE_API_KEY
# so that the module-level 'settings' variable doesn't cause a crash
# on the initial import.
# Our tests will then use monkeypatch to control the environment for *their*
# specific calls to get_settings() or Settings().
from app.utils.config import Settings, get_settings, logger as config_logger

# Fixture to clear the lru_cache for get_settings before each test.
# This ensures that each test gets a fresh Settings instance,
# allowing environment variable changes via monkeypatch to take effect.
@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clears the lru_cache for get_settings before each test."""
    get_settings.cache_clear()
    yield
    # Clear again after test as well, for subsequent test runs in the same session
    get_settings.cache_clear() 

@pytest.fixture
def mock_env_vars_valid(monkeypatch):
    """Fixture to set valid environment variables for Settings."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_api_key_123")
    monkeypatch.setenv("API_HOST", "test_api_host")
    monkeypatch.setenv("API_PORT", "1234")
    monkeypatch.setenv("FRONTEND_HOST", "test_frontend_host")
    monkeypatch.setenv("FRONTEND_PORT", "5678")
    monkeypatch.setenv("DEBUG", "False")

@pytest.fixture
def mock_env_vars_default_api_key(monkeypatch):
    """Fixture to set environment variables with the default placeholder GOOGLE_API_KEY."""
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")
    # Set other variables to prevent unexpected defaults and focus on the API key issue
    monkeypatch.setenv("API_HOST", "test_api_host")
    monkeypatch.setenv("API_PORT", "1234")
    monkeypatch.setenv("FRONTEND_HOST", "test_frontend_host")
    monkeypatch.setenv("FRONTEND_PORT", "5678")
    monkeypatch.setenv("DEBUG", "False")

@pytest.fixture
def mock_env_vars_missing_api_key(monkeypatch):
    """Fixture to ensure GOOGLE_API_KEY is not set in environment."""
    if "GOOGLE_API_KEY" in os.environ:
        monkeypatch.delenv("GOOGLE_API_KEY")
    # Set other variables to ensure they don't cause issues
    monkeypatch.setenv("API_HOST", "test_api_host")
    monkeypatch.setenv("API_PORT", "1234")
    monkeypatch.setenv("FRONTEND_HOST", "test_frontend_host")
    monkeypatch.setenv("FRONTEND_PORT", "5678")
    monkeypatch.setenv("DEBUG", "False")


class TestSettings:
    """Comprehensive tests for the Settings class."""

    def test_settings_loads_from_env_valid(self, mock_env_vars_valid):
        """
        Test that Settings initializes correctly with all valid environment variables.
        Verifies values are parsed as expected (e.g., int, bool).
        """
        settings = Settings()
        assert settings.GOOGLE_API_KEY == "test_api_key_123"
        assert settings.API_HOST == "test_api_host"
        assert settings.API_PORT == 1234
        assert settings.FRONTEND_HOST == "test_frontend_host"
        assert settings.FRONTEND_PORT == 5678
        assert settings.DEBUG is False

    def test_settings_uses_default_values_when_not_set(self, monkeypatch):
        """
        Test that Settings falls back to its defined default values
        for fields not explicitly provided in environment variables.
        """
        # Only set GOOGLE_API_KEY, ensuring others are not set
        monkeypatch.setenv("GOOGLE_API_KEY", "required_api_key")
        
        # Explicitly delete other variables to ensure default values are used
        for var in ["API_HOST", "API_PORT", "FRONTEND_HOST", "FRONTEND_PORT", "DEBUG"]:
            if var in os.environ:
                monkeypatch.delenv(var)

        settings = Settings()
        assert settings.GOOGLE_API_KEY == "required_api_key"
        assert settings.API_HOST == "localhost"
        assert settings.API_PORT == 8000
        assert settings.FRONTEND_HOST == "localhost"
        assert settings.FRONTEND_PORT == 8501
        assert settings.DEBUG is True # Default value for DEBUG is True

    def test_settings_raises_error_if_google_api_key_missing(self, mock_env_vars_missing_api_key, caplog):
        """
        Test that Settings raises a ValueError and logs an error
        when GOOGLE_API_KEY is completely missing from the environment.
        This covers the 'if not self.GOOGLE_API_KEY' branch.
        """
        caplog.set_level(logging.ERROR, logger=config_logger.name)

        with pytest.raises(ValueError) as excinfo:
            Settings()
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)

        # Verify the error log message
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.records[0].message

    def test_settings_raises_error_if_google_api_key_is_default_placeholder(self, mock_env_vars_default_api_key, caplog):
        """
        Test that Settings raises a ValueError and logs an error
        when GOOGLE_API_KEY is set to the default placeholder string.
        This covers the 'self.GOOGLE_API_KEY == "your-google-api-key-here"' branch.
        """
        caplog.set_level(logging.ERROR, logger=config_logger.name)

        with pytest.raises(ValueError) as excinfo:
            Settings()
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)

        # Verify the error log message
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.records[0].message

    def test_settings_config_env_file_attribute(self):
        """
        Test that the inner Config class specifies the correct environment file.
        This ensures pydantic_settings attempts to load from '.env'.
        """
        assert Settings.Config.env_file == ".env"

class TestGetSettings:
    """Comprehensive tests for the get_settings function."""

    def test_get_settings_returns_settings_instance(self, mock_env_vars_valid):
        """
        Test that get_settings successfully returns an instance of Settings.
        Verifies that the instance is correctly initialized.
        """
        settings_instance = get_settings()
        assert isinstance(settings_instance, Settings)
        assert settings_instance.GOOGLE_API_KEY == "test_api_key_123" # Verify initialization

    def test_get_settings_is_cached(self, mock_env_vars_valid):
        """
        Test that get_settings uses lru_cache and returns the exact same instance
        on subsequent calls within the same test scope.
        """
        # Due to `clear_settings_cache` fixture, this is a fresh call.
        first_call_settings = get_settings()
        second_call_settings = get_settings()

        # Both calls should return the exact same object due to lru_cache
        assert first_call_settings is second_call_settings

    def test_get_settings_calls_settings_init_only_once_due_to_cache(self, mock_env_vars_valid):
        """
        Test that the constructor of Settings (Settings.__init__) is called only once
        when get_settings is invoked multiple times, demonstrating lru_cache's effect.
        """
        # Patch Settings.__init__ to count calls
        # `autospec=True` ensures the mock has the same signature as the original
        with patch('app.utils.config.Settings.__init__', autospec=True) as mock_settings_init:
            # __init__ methods don't return anything, so set return_value to None
            mock_settings_init.return_value = None

            # First call to get_settings, should instantiate Settings
            get_settings()
            mock_settings_init.assert_called_once() # __init__ should have been called once

            # Second call to get_settings, should use the cache
            get_settings()
            mock_settings_init.assert_called_once() # __init__ should *still* only have been called once

            # Verify a third call also uses cache
            get_settings()
            mock_settings_init.assert_called_once() # Still only one call

    def test_get_settings_propagates_settings_initialization_error(self, mock_env_vars_missing_api_key):
        """
        Test that get_settings correctly propagates the ValueError raised
        during Settings initialization if required environment variables are missing.
        """
        with pytest.raises(ValueError) as excinfo:
            get_settings()
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)