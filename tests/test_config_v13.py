import pytest
import os
import logging
import sys
from unittest.mock import MagicMock, patch

# Import the module under test.
# This import path assumes the test file is located at tests/utils/test_config.py
# and the source file is at app/utils/config.py, with 'app' and 'tests' being siblings
# in the project root.
from app.utils.config import Settings, get_settings, logger

# --- Fixtures ---

@pytest.fixture(autouse=True)
def clear_settings_cache_and_reload_module():
    """
    Clears the lru_cache for get_settings before and after each test.
    Also ensures the app.utils.config module is reloaded to reset global 'settings' variable,
    allowing environment variables to take effect for module-level initialization.
    """
    # Clear lru_cache for get_settings
    get_settings.cache_clear()

    # Before the test, remove the module from sys.modules if it's already loaded
    # This forces a fresh import and re-execution of module-level code (like global 'settings')
    # in the context of the current test's monkeypatch environment.
    if 'app.utils.config' in sys.modules:
        del sys.modules['app.utils.config']
    
    yield  # Run the test

    # Clear lru_cache again after the test to ensure clean state for subsequent tests
    get_settings.cache_clear()
    # Clean up sys.modules again to prevent state leakage
    if 'app.utils.config' in sys.modules:
        del sys.modules['app.utils.config']


@pytest.fixture
def mock_valid_google_api_key(monkeypatch):
    """Sets a valid GOOGLE_API_KEY environment variable for tests."""
    monkeypatch.setenv("GOOGLE_API_KEY", "valid_test_api_key_123")


@pytest.fixture
def caplog_at_error(caplog):
    """
    Fixture to capture log messages at ERROR level specifically for the logger
    used in config.py.
    """
    caplog.set_level(logging.ERROR, logger=logger.name)
    return caplog


# --- Tests for Settings Class ---

class TestSettings:
    """Comprehensive tests for the Settings class."""

    def test_settings_initialization_success(self, mock_valid_google_api_key):
        """
        GIVEN a valid GOOGLE_API_KEY is set in the environment
        WHEN a Settings instance is created
        THEN it should initialize with the provided API key and default values,
             and no ValueError should be raised.
        """
        settings = Settings()
        assert settings.GOOGLE_API_KEY == "valid_test_api_key_123"
        assert settings.API_HOST == "localhost"
        assert settings.API_PORT == 8000
        assert settings.FRONTEND_HOST == "localhost"
        assert settings.FRONTEND_PORT == 8501
        assert settings.DEBUG is True

    @pytest.mark.parametrize(
        "api_key_value",
        [
            "",  # Empty string for GOOGLE_API_KEY
            "your-google-api-key-here",  # Default placeholder value
        ],
        ids=["empty_string_key", "default_placeholder_key"]
    )
    def test_settings_initialization_invalid_api_key_raises_value_error(
        self, monkeypatch, caplog_at_error, api_key_value
    ):
        """
        GIVEN an invalid GOOGLE_API_KEY (empty or default placeholder) is set
        WHEN a Settings instance is created
        THEN it should raise a ValueError and log an error message.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", api_key_value)

        with pytest.raises(ValueError) as excinfo:
            Settings()

        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)

        # Check that the error was logged
        assert len(caplog_at_error.records) == 1
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog_at_error.records[0].message
        assert caplog_at_error.records[0].levelno == logging.ERROR

    def test_settings_initialization_missing_required_api_key_raises_validation_error(
        self, monkeypatch
    ):
        """
        GIVEN GOOGLE_API_KEY is not set in the environment (missing)
        WHEN a Settings instance is created
        THEN pydantic.ValidationError should be raised (before custom __init__ logic).
        """
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)  # Ensure it's not set

        from pydantic import ValidationError  # ValidationError comes from pydantic

        with pytest.raises(ValidationError) as excinfo:
            Settings()

        # Check for specific error message related to missing field
        assert "GOOGLE_API_KEY" in str(excinfo.value)
        assert "field required" in str(excinfo.value)

    def test_settings_with_environment_overrides(self, monkeypatch, mock_valid_google_api_key):
        """
        GIVEN a valid GOOGLE_API_KEY and other environment variables are set
        WHEN a Settings instance is created
        THEN it should correctly load overridden values from environment variables.
        """
        monkeypatch.setenv("API_HOST", "test-host.com")
        monkeypatch.setenv("API_PORT", "9000")
        monkeypatch.setenv("FRONTEND_HOST", "test-frontend.com")
        monkeypatch.setenv("FRONTEND_PORT", "9500")
        monkeypatch.setenv("DEBUG", "False")  # Pydantic converts "False" string to boolean False

        settings = Settings()

        assert settings.GOOGLE_API_KEY == "valid_test_api_key_123"  # From fixture
        assert settings.API_HOST == "test-host.com"
        assert settings.API_PORT == 9000
        assert settings.FRONTEND_HOST == "test-frontend.com"
        assert settings.FRONTEND_PORT == 9500
        assert settings.DEBUG is False


# --- Tests for get_settings function ---

class TestGetSettings:
    """Comprehensive tests for the get_settings function."""

    def test_get_settings_returns_settings_instance(self, mock_valid_google_api_key):
        """
        GIVEN a valid GOOGLE_API_KEY is set
        WHEN get_settings() is called
        THEN it should return an instance of Settings.
        """
        settings_instance = get_settings()
        assert isinstance(settings_instance, Settings)
        assert settings_instance.GOOGLE_API_KEY == "valid_test_api_key_123"

    def test_get_settings_lru_cache_efficiency(self, monkeypatch, mock_valid_google_api_key):
        """
        GIVEN a valid GOOGLE_API_KEY is set
        WHEN get_settings() is called multiple times
        THEN it should use lru_cache, ensuring Settings.__init__ is called only once
             for subsequent calls until the cache is cleared.
        """
        # Patch the Settings.__init__ method to track calls
        # We need to import the module inside the test function AFTER monkeypatch setup
        # if we are testing module-level variables (like global `settings`)
        # However, for `get_settings` and `Settings` class, direct import is fine
        # as `clear_settings_cache_and_reload_module` fixture handles fresh state.
        from app.utils.config import Settings, get_settings
        
        # Preserve original __init__ to allow the mock to call it
        original_settings_init = Settings.__init__
        mock_settings_init = MagicMock(side_effect=original_settings_init)
        monkeypatch.setattr(Settings, '__init__', mock_settings_init)

        # First call to get_settings
        settings1 = get_settings()
        assert mock_settings_init.call_count == 1  # __init__ should be called once

        # Second call to get_settings - should use cache
        settings2 = get_settings()
        assert mock_settings_init.call_count == 1  # __init__ should NOT be called again
        assert settings1 is settings2             # Should be the exact same object

        # Clear the cache
        get_settings.cache_clear()

        # Third call to get_settings after clearing cache - should re-initialize
        settings3 = get_settings()
        assert mock_settings_init.call_count == 2  # __init__ should be called again
        assert settings1 is not settings3          # Should be a new object

    def test_get_settings_propagates_settings_error(self, monkeypatch, caplog_at_error):
        """
        GIVEN an invalid GOOGLE_API_KEY that causes Settings initialization to fail
        WHEN get_settings() is called
        THEN it should propagate the ValueError from Settings initialization and log the error.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")  # Invalid key

        with pytest.raises(ValueError) as excinfo:
            get_settings()

        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        assert len(caplog_at_error.records) == 1
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog_at_error.records[0].message
        assert caplog_at_error.records[0].levelno == logging.ERROR


# --- Test for Global 'settings' variable ---

def test_global_settings_instance_initialization(monkeypatch, mock_valid_google_api_key):
    """
    GIVEN a valid GOOGLE_API_KEY is set in the environment
    WHEN the app.utils.config module is imported (reloaded)
    THEN the global 'settings' variable should be an initialized Settings instance.
    This test leverages the `clear_settings_cache_and_reload_module` fixture
    to ensure a fresh module import.
    """
    # Import the module here. Due to `clear_settings_cache_and_reload_module` fixture,
    # sys.modules['app.utils.config'] will have been cleared, so this is a fresh import,
    # re-executing `settings = get_settings()`.
    from app.utils.config import settings as global_settings_var

    assert isinstance(global_settings_var, Settings)
    assert global_settings_var.GOOGLE_API_KEY == "valid_test_api_key_123"
    assert global_settings_var.API_HOST == "localhost" # Ensure defaults are loaded too


def test_global_settings_instance_initialization_fails_on_invalid_key(
    monkeypatch, caplog_at_error
):
    """
    GIVEN an invalid GOOGLE_API_KEY set in the environment
    WHEN the app.utils.config module is imported (reloaded)
    THEN the import should raise a ValueError due to the invalid key.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")

    # The import itself will cause the error
    with pytest.raises(ValueError) as excinfo:
        from app.utils import config as _  # Import with alias to avoid unused import warning

    assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
    assert len(caplog_at_error.records) == 1
    assert "GOOGLE_API_KEY is not set or is using default value" in caplog_at_error.records[0].message
    assert caplog_at_error.records[0].levelno == logging.ERROR