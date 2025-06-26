import pytest
import os
import sys
from unittest.mock import patch, MagicMock
import importlib

# Add parent directory to sys.path to allow importing 'app' module
# This handles cases where pytest might be run from different directories
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import the module under test. This import will execute the module-level 'settings = get_settings()'
# We will manipulate sys.modules and importlib.reload for testing this line's behavior.
try:
    from app.utils import config
except ImportError as e:
    pytest.fail(f"Could not import app.utils.config. Check sys.path or project structure. Error: {e}")

# --- Fixtures ---

@pytest.fixture(autouse=True)
def clear_config_module_cache_and_reload():
    """
    Fixture to clear the lru_cache for get_settings and delete the module
    from sys.modules before each test. This ensures a clean slate for tests
    that depend on module-level imports or lru_cache behavior.
    """
    # Clear the lru_cache of get_settings
    config.get_settings.cache_clear()

    # If the module is loaded, delete it to force a fresh import/reload
    # This is crucial for testing module-level variable initialization and its error cases
    if 'app.utils.config' in sys.modules:
        del sys.modules['app.utils.config']

    yield # Let the test run

    # After the test, clean up again for good measure, especially if a test failed mid-execution
    config.get_settings.cache_clear()
    if 'app.utils.config' in sys.modules:
        del sys.modules['app.utils.config']


@pytest.fixture
def mock_env_vars(monkeypatch, key_value, host_value, port_value, frontend_host_value, frontend_port_value, debug_value):
    """
    A generic fixture to set environment variables using monkeypatch.
    Designed to be used with parametrize for different test scenarios.
    """
    if key_value is not None:
        monkeypatch.setenv("GOOGLE_API_KEY", key_value)
    else:
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False) # Ensure it's not set

    monkeypatch.setenv("API_HOST", host_value)
    monkeypatch.setenv("API_PORT", str(port_value))
    monkeypatch.setenv("FRONTEND_HOST", frontend_host_value)
    monkeypatch.setenv("FRONTEND_PORT", str(frontend_port_value))
    monkeypatch.setenv("DEBUG", str(debug_value))

@pytest.fixture
def mock_logger_error():
    """Fixture to mock the logger's error method for asserting log calls."""
    # Ensure we mock the specific logger instance used in the config module
    with patch('app.utils.config.logger.error') as mock_log_error:
        yield mock_log_error

# --- Tests for Settings Class ---

# Parametrize common successful environment variables
@pytest.mark.parametrize(
    "key_value, host_value, port_value, frontend_host_value, frontend_port_value, debug_value",
    [
        ("valid_google_key", "test_host", 8080, "test_frontend", 3000, False),
        ("another_valid_key", "another_host", 9000, "another_frontend", 4000, True),
    ]
)
def test_settings_init_success(
    clear_config_module_cache_and_reload, # Ensure clean state for each test
    mock_env_vars,
    key_value,
    host_value,
    port_value,
    frontend_host_value,
    frontend_port_value,
    debug_value
):
    """
    Test successful initialization of Settings with various valid environment variables.
    Verifies that fields are correctly parsed and assigned.
    """
    # Import the module to ensure it's loaded with the patched environment variables
    reloaded_config = importlib.import_module('app.utils.config')
    settings = reloaded_config.Settings() # Explicitly instantiate Settings class

    assert settings.GOOGLE_API_KEY == key_value
    assert settings.API_HOST == host_value
    assert settings.API_PORT == port_value
    assert settings.FRONTEND_HOST == frontend_host_value
    assert settings.FRONTEND_PORT == frontend_port_value
    assert settings.DEBUG == debug_value

def test_settings_init_with_defaults(monkeypatch, clear_config_module_cache_and_reload):
    """
    Test that Settings initializes with default values for optional fields when
    those environment variables are not set, while still requiring a valid GOOGLE_API_KEY.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "default_key_test")
    # Unset other environment variables to let defaults apply
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("FRONTEND_HOST", raising=False)
    monkeypatch.delenv("FRONTEND_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    # Re-import to ensure pydantic_settings re-reads env vars
    reloaded_config = importlib.import_module('app.utils.config')
    settings = reloaded_config.Settings()

    assert settings.GOOGLE_API_KEY == "default_key_test"
    assert settings.API_HOST == "localhost"
    assert settings.API_PORT == 8000
    assert settings.FRONTEND_HOST == "localhost"
    assert settings.FRONTEND_PORT == 8501
    assert settings.DEBUG is True

@pytest.mark.parametrize(
    "invalid_key, expected_log_message",
    [
        ("", "GOOGLE_API_KEY is not set or is using default value"),
        ("your-google-api-key-here", "GOOGLE_API_KEY is not set or is using default value")
    ]
)
def test_settings_init_invalid_key_raises_error_and_logs(
    invalid_key, expected_log_message, monkeypatch, mock_logger_error, clear_config_module_cache_and_reload
):
    """
    Test that Settings raises ValueError and logs an error when GOOGLE_API_KEY is invalid
    (empty string or default placeholder).
    """
    monkeypatch.setenv("GOOGLE_API_KEY", invalid_key)
    # Set other required environment variables to ensure the error is specifically for GOOGLE_API_KEY
    monkeypatch.setenv("API_HOST", "localhost")
    monkeypatch.setenv("API_PORT", "8000")
    monkeypatch.setenv("FRONTEND_HOST", "localhost")
    monkeypatch.setenv("FRONTEND_PORT", "8501")
    monkeypatch.setenv("DEBUG", "True")

    # Re-import the module, then explicitly instantiate Settings
    reloaded_config = importlib.import_module('app.utils.config')
    with pytest.raises(ValueError) as excinfo:
        reloaded_config.Settings()

    assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
    mock_logger_error.assert_called_once_with(expected_log_message)

def test_settings_init_no_key_set_raises_error_and_logs(
    monkeypatch, mock_logger_error, clear_config_module_cache_and_reload
):
    """
    Test that Settings raises ValueError and logs an error when GOOGLE_API_KEY is not set at all.
    """
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False) # Ensure it's not set
    monkeypatch.setenv("API_HOST", "localhost") # Set other required envs
    monkeypatch.setenv("API_PORT", "8000")
    monkeypatch.setenv("FRONTEND_HOST", "localhost")
    monkeypatch.setenv("FRONTEND_PORT", "8501")
    monkeypatch.setenv("DEBUG", "True")

    # Re-import the module, then explicitly instantiate Settings
    reloaded_config = importlib.import_module('app.utils.config')
    with pytest.raises(ValueError) as excinfo:
        reloaded_config.Settings()

    assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
    mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

def test_settings_config_env_file():
    """
    Test that the Config inner class correctly specifies the .env file.
    This ensures pydantic_settings knows where to look for environment variables.
    """
    assert config.Settings.Config.env_file == ".env"

# --- Tests for get_settings() function ---

def test_get_settings_returns_settings_instance(monkeypatch, clear_config_module_cache_and_reload):
    """
    Test that get_settings returns a valid instance of Settings.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_for_get")
    monkeypatch.setenv("API_HOST", "localhost")
    monkeypatch.setenv("API_PORT", "8000")
    monkeypatch.setenv("FRONTEND_HOST", "localhost")
    monkeypatch.setenv("FRONTEND_PORT", "8501")
    monkeypatch.setenv("DEBUG", "True")

    # Re-import to ensure get_settings is re-initialized with new cache and env
    reloaded_config = importlib.import_module('app.utils.config')
    settings_instance = reloaded_config.get_settings()
    assert isinstance(settings_instance, reloaded_config.Settings)
    assert settings_instance.GOOGLE_API_KEY == "test_key_for_get"

def test_get_settings_lru_cache_efficiency(monkeypatch, mocker, clear_config_module_cache_and_reload):
    """
    Test that get_settings uses lru_cache, ensuring the Settings() constructor
    is called only once even on multiple calls to get_settings.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "cached_key")
    monkeypatch.setenv("API_HOST", "localhost")
    monkeypatch.setenv("API_PORT", "8000")
    monkeypatch.setenv("FRONTEND_HOST", "localhost")
    monkeypatch.setenv("FRONTEND_PORT", "8501")
    monkeypatch.setenv("DEBUG", "True")

    # Re-import to get a fresh get_settings with cleared cache
    reloaded_config = importlib.import_module('app.utils.config')

    # Spy on the Settings constructor to count calls
    mock_settings_constructor = mocker.spy(reloaded_config, 'Settings')

    first_call = reloaded_config.get_settings()
    second_call = reloaded_config.get_settings() # This should use the cache

    mock_settings_constructor.assert_called_once()
    assert first_call is second_call # Verify that the exact same object is returned

def test_get_settings_cache_clear(monkeypatch, mocker, clear_config_module_cache_and_reload):
    """
    Test that calling get_settings.cache_clear() properly invalidates the cache,
    allowing a fresh initialization of Settings on subsequent calls.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "first_key")
    monkeypatch.setenv("API_HOST", "localhost")
    monkeypatch.setenv("API_PORT", "8000")
    monkeypatch.setenv("FRONTEND_HOST", "localhost")
    monkeypatch.setenv("FRONTEND_PORT", "8501")
    monkeypatch.setenv("DEBUG", "True")

    reloaded_config = importlib.import_module('app.utils.config')
    mock_settings_constructor = mocker.spy(reloaded_config, 'Settings')

    # First call to get_settings
    first_settings = reloaded_config.get_settings()
    mock_settings_constructor.assert_called_once()

    # Change environment variable - this change should only be reflected after cache clear
    monkeypatch.setenv("GOOGLE_API_KEY", "second_key")

    # Clear the cache explicitly
    reloaded_config.get_settings.cache_clear()

    # Second call to get_settings, should re-initialize
    second_settings = reloaded_config.get_settings()

    assert mock_settings_constructor.call_count == 2 # Settings constructor should be called twice
    assert first_settings is not second_settings # Objects should be different instances
    assert first_settings.GOOGLE_API_KEY == "first_key"
    assert second_settings.GOOGLE_API_KEY == "second_key"

# --- Tests for module-level 'settings' variable ---

def test_module_level_settings_init_success_on_import(monkeypatch, clear_config_module_cache_and_reload):
    """
    Test that the module-level 'settings' object is correctly initialized on module import
    when valid environment variables are present. This tests the line `settings = get_settings()`.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "module_import_key")
    monkeypatch.setenv("API_HOST", "imported_host")
    monkeypatch.setenv("API_PORT", "8100")
    monkeypatch.setenv("FRONTEND_HOST", "imported_frontend")
    monkeypatch.setenv("FRONTEND_PORT", "8600")
    monkeypatch.setenv("DEBUG", "False")

    # Re-import the module to trigger the global 'settings = get_settings()' line
    reloaded_config = importlib.import_module('app.utils.config')

    assert isinstance(reloaded_config.settings, reloaded_config.Settings)
    assert reloaded_config.settings.GOOGLE_API_KEY == "module_import_key"
    assert reloaded_config.settings.API_HOST == "imported_host"
    assert reloaded_config.settings.API_PORT == 8100
    assert reloaded_config.settings.FRONTEND_HOST == "imported_frontend"
    assert reloaded_config.settings.FRONTEND_PORT == 8600
    assert reloaded_config.settings.DEBUG is False

@pytest.mark.parametrize("invalid_key_value", ["", "your-google-api-key-here", None])
def test_module_level_settings_init_invalid_key_raises_error_on_import(
    invalid_key_value, monkeypatch, mock_logger_error, clear_config_module_cache_and_reload
):
    """
    Test that importing the config module raises ValueError and logs an error
    when GOOGLE_API_KEY is invalid at module import time. This targets the
    error path of the `settings = get_settings()` line.
    """
    if invalid_key_value is not None:
        monkeypatch.setenv("GOOGLE_API_KEY", invalid_key_value)
    else:
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False) # Ensure it's not set at all

    # Set other required environment variables to ensure it's specifically the GOOGLE_API_KEY error
    monkeypatch.setenv("API_HOST", "localhost")
    monkeypatch.setenv("API_PORT", "8000")
    monkeypatch.setenv("FRONTEND_HOST", "localhost")
    monkeypatch.setenv("FRONTEND_PORT", "8501")
    monkeypatch.setenv("DEBUG", "True")

    with pytest.raises(ValueError) as excinfo:
        # Attempt to re-import the module, which will trigger the global 'settings = get_settings()'
        # and raise the expected ValueError.
        importlib.import_module('app.utils.config')

    assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
    mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")