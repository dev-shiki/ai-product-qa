import pytest
from unittest.mock import patch, MagicMock
import os
import logging
import importlib

# Import the module under test
# It's crucial to import it this way for reload() to work consistently
import app.utils.config

# --- Fixtures ---

@pytest.fixture(autouse=True)
def clear_lru_cache_and_reset_os_env():
    """
    Clears the lru_cache for get_settings and manages OS environment variables.
    This fixture is autoused to ensure a clean state for most tests, especially
    regarding environment variables and the cached settings instance.
    """
    # Store original environment variables to restore them later
    original_environ = dict(os.environ)

    # Clear the cache for get_settings
    app.utils.config.get_settings.cache_clear()

    # Yield control to the test function
    yield

    # Restore original environment variables after the test completes
    os.environ.clear()
    os.environ.update(original_environ)

    # Clear cache again in case a test itself re-populated it (though less common)
    app.utils.config.get_settings.cache_clear()

@pytest.fixture
def mock_logger():
    """Mocks the logger used in config.py to capture log messages."""
    with patch('app.utils.config.logger', spec=True) as mock_log:
        yield mock_log

# --- Test Cases for Settings Class ---

def test_settings_initialization_success_from_env(clear_lru_cache_and_reset_os_env):
    """
    Test that Settings initializes successfully when GOOGLE_API_KEY is provided via environment
    variables and other settings take default values or are overridden from env.
    """
    with patch.dict(os.environ, {
        "GOOGLE_API_KEY": "env-test-api-key-123",
        "API_HOST": "env-host.com",
        "API_PORT": "9000", # pydantic-settings will convert "9000" to 9000
        "DEBUG": "False" # pydantic-settings will convert "False" to False
    }):
        settings_instance = app.utils.config.Settings()
        assert settings_instance.GOOGLE_API_KEY == "env-test-api-key-123"
        assert settings_instance.API_HOST == "env-host.com"
        assert settings_instance.API_PORT == 9000
        assert settings_instance.FRONTEND_HOST == "localhost" # Default value
        assert settings_instance.FRONTEND_PORT == 8501 # Default value
        assert settings_instance.DEBUG is False

def test_settings_initialization_success_with_kwargs(clear_lru_cache_and_reset_os_env):
    """
    Test that Settings initializes successfully when GOOGLE_API_KEY is provided via kwargs.
    Kwargs should override environment variables if both are present.
    """
    # Set some environment variables that will be overridden by kwargs
    with patch.dict(os.environ, {
        "GOOGLE_API_KEY": "env-should-be-overridden",
        "API_HOST": "env-host",
        "FRONTEND_PORT": "9999"
    }):
        settings_instance = app.utils.config.Settings(
            GOOGLE_API_KEY="kwargs-api-key",
            API_HOST="kwargs-host",
            API_PORT=9001,
            DEBUG=False
        )
        assert settings_instance.GOOGLE_API_KEY == "kwargs-api-key"
        assert settings_instance.API_HOST == "kwargs-host"
        assert settings_instance.API_PORT == 9001
        assert settings_instance.FRONTEND_HOST == "localhost" # Default
        assert settings_instance.FRONTEND_PORT == 8501 # Default (not overridden by kwargs here)
        assert settings_instance.DEBUG is False

def test_settings_initialization_missing_api_key(mock_logger, clear_lru_cache_and_reset_os_env):
    """
    Test that Settings raises ValueError and logs an error when GOOGLE_API_KEY is missing
    (neither in environment nor kwargs).
    """
    # Ensure GOOGLE_API_KEY is not in the environment
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError) as excinfo:
            app.utils.config.Settings()
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        mock_logger.error.assert_called_once_with(
            "GOOGLE_API_KEY is not set or is using default value"
        )

def test_settings_initialization_empty_api_key(mock_logger, clear_lru_cache_and_reset_os_env):
    """
    Test that Settings raises ValueError and logs an error when GOOGLE_API_KEY is an empty string.
    """
    with patch.dict(os.environ, {"GOOGLE_API_KEY": ""}):
        with pytest.raises(ValueError) as excinfo:
            app.utils.config.Settings()
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        mock_logger.error.assert_called_once_with(
            "GOOGLE_API_KEY is not set or is using default value"
        )

def test_settings_initialization_default_api_key(mock_logger, clear_lru_cache_and_reset_os_env):
    """
    Test that Settings raises ValueError and logs an error when GOOGLE_API_KEY is the default
    placeholder string "your-google-api-key-here".
    """
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "your-google-api-key-here"}):
        with pytest.raises(ValueError) as excinfo:
            app.utils.config.Settings()
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        mock_logger.error.assert_called_once_with(
            "GOOGLE_API_KEY is not set or is using default value"
        )

# --- Test Cases for get_settings() function ---

def test_get_settings_returns_settings_instance(clear_lru_cache_and_reset_os_env):
    """
    Test that get_settings returns a valid instance of Settings.
    """
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key-for-get_settings"}):
        settings_instance = app.utils.config.get_settings()
        assert isinstance(settings_instance, app.utils.config.Settings)
        assert settings_instance.GOOGLE_API_KEY == "test-key-for-get_settings"

def test_get_settings_uses_lru_cache(clear_lru_cache_and_reset_os_env):
    """
    Test that get_settings uses lru_cache, returning the exact same instance on subsequent calls
    without re-instantiating Settings.
    """
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key-for-cache"}):
        # Patch the Settings constructor to verify it's called only once
        with patch('app.utils.config.Settings', wraps=app.utils.config.Settings) as MockSettings:
            first_call_settings = app.utils.config.get_settings()
            second_call_settings = app.utils.config.get_settings()

            # The Settings constructor should only be called once
            MockSettings.assert_called_once()
            # The returned instances must be the same object
            assert first_call_settings is second_call_settings
            assert first_call_settings.GOOGLE_API_KEY == "test-key-for-cache"

def test_get_settings_raises_value_error_if_api_key_invalid(clear_lru_cache_and_reset_os_env):
    """
    Test that get_settings propagates ValueError from Settings initialization
    if the GOOGLE_API_KEY is invalid.
    """
    with patch.dict(os.environ, {"GOOGLE_API_KEY": ""}): # Invalid API key
        with pytest.raises(ValueError) as excinfo:
            app.utils.config.get_settings()
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)

# --- Test Cases for Global Settings Instance ---

def test_global_settings_is_settings_instance(clear_lru_cache_and_reset_os_env):
    """
    Test that the globally exposed 'settings' object (app.utils.config.settings)
    is an instance of Settings and is correctly initialized.
    This test implicitly reloads the module due to the autouse fixture and the
    patching of os.environ.
    """
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "global-settings-key"}):
        # Reload the module to ensure global `settings` variable is re-initialized
        # with the patched environment.
        importlib.reload(app.utils.config)

        # Access the reloaded global settings
        reloaded_settings = app.utils.config.settings

        assert isinstance(reloaded_settings, app.utils.config.Settings)
        assert reloaded_settings.GOOGLE_API_KEY == "global-settings-key"

def test_global_settings_is_same_as_get_settings_instance(clear_lru_cache_and_reset_os_env):
    """
    Test that the globally exposed 'settings' object is the same instance
    as returned by get_settings() because get_settings() is cached.
    """
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "global-and-get-settings-key"}):
        # Reload the module to re-initialize global_settings with mocked env
        importlib.reload(app.utils.config)

        reloaded_settings = app.utils.config.settings
        # Call get_settings which will retrieve the cached instance that was
        # created during the module reload (by `settings = get_settings()`).
        retrieved_settings = app.utils.config.get_settings()

        assert reloaded_settings is retrieved_settings
        assert reloaded_settings.GOOGLE_API_KEY == "global-and-get-settings-key"


def test_global_settings_initialization_failure(mock_logger, clear_lru_cache_and_reset_os_env):
    """
    Test that the global 'settings' object causes a ValueError when the module is imported
    if the GOOGLE_API_KEY is invalid, and logs an error.
    This covers the `settings = get_settings()` line and its error propagation.
    """
    # Ensure GOOGLE_API_KEY is an invalid value to trigger the error
    with patch.dict(os.environ, {"GOOGLE_API_KEY": ""}, clear=True):
        # Attempt to reload the module, which will trigger the global initialization
        # and should raise a ValueError.
        with pytest.raises(ValueError) as excinfo:
            importlib.reload(app.utils.config)

        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        mock_logger.error.assert_called_once_with(
            "GOOGLE_API_KEY is not set or is using default value"
        )