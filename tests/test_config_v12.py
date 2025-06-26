import pytest
import os
import logging
from unittest.mock import MagicMock
import sys
import importlib

# Define the module path for dynamic import and reload
CONFIG_MODULE_PATH = "app.utils.config"

# --- Fixtures ---

@pytest.fixture(autouse=True)
def clear_settings_cache():
    """
    Clears the lru_cache for get_settings before and after each test.
    This ensures that each test starts with a clean cache for the singleton.
    """
    # Ensure the module is imported before trying to access get_settings,
    # as it might not be imported yet if this is the very first test.
    if CONFIG_MODULE_PATH in sys.modules:
        current_get_settings = sys.modules[CONFIG_MODULE_PATH].get_settings
        current_get_settings.cache_clear()
    yield
    # Clear again after the test, just in case, for the next test's clean slate.
    if CONFIG_MODULE_PATH in sys.modules:
        current_get_settings = sys.modules[CONFIG_MODULE_PATH].get_settings
        current_get_settings.cache_clear()


@pytest.fixture
def mock_env_vars_success(monkeypatch):
    """Sets up valid environment variables for Settings."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_google_api_key_123")
    monkeypatch.setenv("API_HOST", "test_host")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("FRONTEND_HOST", "test_frontend_host")
    monkeypatch.setenv("FRONTEND_PORT", "9500")
    monkeypatch.setenv("DEBUG", "False") # Test boolean parsing


@pytest.fixture
def mock_env_vars_default_only_key(monkeypatch):
    """
    Sets only GOOGLE_API_KEY and ensures other optional variables are unset
    to test default values.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "valid_key_for_defaults")
    # Ensure these are not set by previous tests or system environment
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("FRONTEND_HOST", raising=False)
    monkeypatch.delenv("FRONTEND_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)


@pytest.fixture
def mock_env_vars_error_empty(monkeypatch):
    """Sets GOOGLE_API_KEY to an empty string to trigger ValueError."""
    monkeypatch.setenv("GOOGLE_API_KEY", "")


@pytest.fixture
def mock_env_vars_error_default(monkeypatch):
    """Sets GOOGLE_API_KEY to the default placeholder string to trigger ValueError."""
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")


@pytest.fixture
def mock_logger():
    """
    Provides a MagicMock for the logger.error method.
    The actual patching of the module's logger is handled by `reload_config_module`
    or directly in tests using `Settings()`.
    """
    return MagicMock()


@pytest.fixture
def reload_config_module(monkeypatch):
    """
    Fixture to handle reloading the config module.
    It removes the module from sys.modules and re-imports it,
    allowing for fresh initialization of module-level variables like 'settings'.
    It also allows applying a logger mock to the reloaded module's logger.
    """
    def _reload(apply_mock_logger=None):
        # Remove the module from sys.modules to ensure a fresh import
        if CONFIG_MODULE_PATH in sys.modules:
            del sys.modules[CONFIG_MODULE_PATH]

        # Re-import the module
        # This will execute module-level code, including `settings = get_settings()`
        # We need to import the actual module path, not from the top-level test file.
        from app.utils import config
        importlib.reload(config) # Reload ensures global state is re-evaluated

        # Apply logger mock to the reloaded module's logger if provided
        if apply_mock_logger:
            monkeypatch.setattr(config.logger, 'error', apply_mock_logger)
        return config # Return the reloaded module object

    return _reload


# --- Test Cases for Settings Class ---

def test_settings_loads_env_vars_successfully(mock_env_vars_success):
    """
    Test that Settings loads all environment variables correctly when valid environment
    variables are set.
    """
    # Import Settings dynamically to ensure it uses the mocked environment
    from app.utils.config import Settings
    settings_instance = Settings()
    assert settings_instance.GOOGLE_API_KEY == "test_google_api_key_123"
    assert settings_instance.API_HOST == "test_host"
    assert settings_instance.API_PORT == 9000
    assert settings_instance.FRONTEND_HOST == "test_frontend_host"
    assert settings_instance.FRONTEND_PORT == 9500
    assert settings_instance.DEBUG is False


def test_settings_uses_default_values_when_env_not_set(mock_env_vars_default_only_key):
    """
    Test that Settings uses its default values for fields when corresponding
    environment variables are not provided (but GOOGLE_API_KEY is valid).
    """
    from app.utils.config import Settings
    settings_instance = Settings()
    assert settings_instance.GOOGLE_API_KEY == "valid_key_for_defaults"
    assert settings_instance.API_HOST == "localhost" # Default
    assert settings_instance.API_PORT == 8000 # Default
    assert settings_instance.FRONTEND_HOST == "localhost" # Default
    assert settings_instance.FRONTEND_PORT == 8501 # Default
    assert settings_instance.DEBUG is True # Default


def test_settings_raises_value_error_on_empty_google_api_key(mock_env_vars_error_empty, mock_logger, monkeypatch):
    """
    Test that Settings raises ValueError and logs an error when GOOGLE_API_KEY is an empty string.
    """
    # Patch the logger explicitly for the initial import of Settings if it hasn't happened yet
    # or to ensure the mock is active for this specific test.
    # We need to patch the logger from the module we are importing.
    from app.utils import config
    monkeypatch.setattr(config.logger, 'error', mock_logger)

    with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
        config.Settings() # Use config.Settings to ensure it's from the patched module
    mock_logger.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")


def test_settings_raises_value_error_on_default_google_api_key(mock_env_vars_error_default, mock_logger, monkeypatch):
    """
    Test that Settings raises ValueError and logs an error when GOOGLE_API_KEY is the default placeholder.
    """
    from app.utils import config
    monkeypatch.setattr(config.logger, 'error', mock_logger)

    with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
        config.Settings()
    mock_logger.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")


def test_settings_init_with_kwargs_overrides_env_and_validates(monkeypatch):
    """
    Test that Settings can be initialized with kwargs, overriding environment variables,
    and still performs the GOOGLE_API_KEY validation correctly.
    """
    # Set an invalid env var for GOOGLE_API_KEY to ensure kwargs take precedence
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")
    # Also set some other env vars to confirm kwargs override them too
    monkeypatch.setenv("API_PORT", "9999")

    from app.utils.config import Settings
    settings_instance = Settings(GOOGLE_API_KEY="key_from_kwargs", API_PORT=1234)
    assert settings_instance.GOOGLE_API_KEY == "key_from_kwargs"
    assert settings_instance.API_PORT == 1234
    assert settings_instance.API_HOST == "localhost" # Default as not provided in kwargs/env


def test_settings_init_with_invalid_kwargs_still_raises_error(mock_logger, monkeypatch):
    """
    Test that Settings initialized with invalid GOOGLE_API_KEY via kwargs
    still raises ValueError and logs the error.
    """
    from app.utils import config
    monkeypatch.setattr(config.logger, 'error', mock_logger)

    # Test with empty string provided via kwargs
    with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
        config.Settings(GOOGLE_API_KEY="")
    mock_logger.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")
    mock_logger.reset_mock() # Reset mock for the next assertion

    # Test with default placeholder provided via kwargs
    with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
        config.Settings(GOOGLE_API_KEY="your-google-api-key-here")
    mock_logger.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")


# --- Test get_settings() Function ---

def test_get_settings_returns_settings_instance(mock_env_vars_success):
    """
    Test that get_settings returns an instance of Settings with correct values.
    """
    from app.utils.config import get_settings, Settings
    settings_instance = get_settings()
    assert isinstance(settings_instance, Settings)
    assert settings_instance.GOOGLE_API_KEY == "test_google_api_key_123"


def test_get_settings_is_cached(mock_env_vars_success):
    """
    Test that get_settings caches the Settings instance using lru_cache,
    meaning subsequent calls return the exact same object.
    """
    from app.utils.config import get_settings
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2 # Should be the exact same object due to caching

    # Verify cache behavior
    cache_info = get_settings.cache_info()
    assert cache_info.hits >= 1 # At least one hit from the second call
    assert cache_info.misses == 1 # Only one miss from the first call


# --- Test module-level 'settings' variable ---

def test_module_level_settings_initialized_successfully(mock_env_vars_success, reload_config_module):
    """
    Test that the module-level 'settings' variable is initialized correctly
    when the environment is valid upon module import.
    This covers the `settings = get_settings()` line in a success scenario.
    """
    # Reload the module to ensure 'settings' is initialized with the mocked environment
    config_module = reload_config_module()
    # Access the 'settings' variable from the reloaded module
    module_settings = config_module.settings

    assert isinstance(module_settings, config_module.Settings)
    assert module_settings.GOOGLE_API_KEY == "test_google_api_key_123"
    assert module_settings.API_HOST == "test_host"


def test_module_level_settings_initialization_fails_on_invalid_env(mock_env_vars_error_default, reload_config_module, mock_logger):
    """
    Test that the module-level 'settings' variable initialization raises ValueError
    when the environment is invalid upon module import.
    This covers the `settings = get_settings()` line in an error scenario,
    and ensures the logger is called.
    """
    with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
        # Reload the module. The error will be raised during this import.
        # Pass mock_logger to ensure it's applied to the newly loaded module's logger.
        config_module = reload_config_module(apply_mock_logger=mock_logger)

    mock_logger.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")


# --- Test Logger Configuration ---

def test_logger_is_configured_correctly():
    """Test that the logger is a proper logging.Logger instance and its name is correct."""
    from app.utils.config import logger as original_config_logger
    assert isinstance(original_config_logger, logging.Logger)
    assert original_config_logger.name == "app.utils.config"