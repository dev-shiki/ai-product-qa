import pytest
import os
import logging
from unittest.mock import MagicMock
from functools import lru_cache

# Fixture to clear the lru_cache for get_settings() before and after each test.
# This ensures test isolation by preventing cached values from previous tests
# from affecting the current test.
@pytest.fixture(autouse=True)
def clear_settings_cache(monkeypatch):
    # To safely import `get_settings` (which involves `Settings` instantiation
    # at module level), we temporarily ensure `GOOGLE_API_KEY` is set.
    original_api_key = os.environ.get("GOOGLE_API_KEY")
    if original_api_key is None:
        monkeypatch.setenv("GOOGLE_API_KEY", "temp_key_for_fixture_import")

    # Import the function after potentially setting the temporary key
    from app.utils.config import get_settings

    # Clear the cache
    get_settings.cache_clear()

    # Restore the original environment variable state after clearing cache
    if original_api_key is None:
        monkeypatch.delenv("GOOGLE_API_KEY")
    else:
        monkeypatch.setenv("GOOGLE_API_KEY", original_api_key)

    yield  # Yield control to the test
    
    # Clear the cache again after the test completes
    get_settings.cache_clear()


# Fixture to set valid environment variables for successful Settings initialization.
@pytest.fixture
def set_valid_env_vars(monkeypatch):
    """
    Sets a comprehensive set of valid environment variables for testing
    successful configuration loading.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "test_google_api_key_123")
    monkeypatch.setenv("API_HOST", "test_api_host.com")
    monkeypatch.setenv("API_PORT", "9001")
    monkeypatch.setenv("FRONTEND_HOST", "test_frontend_host.com")
    monkeypatch.setenv("FRONTEND_PORT", "9502")
    monkeypatch.setenv("DEBUG", "False")  # Test boolean conversion from string
    yield


# Fixture to mock the `logger.error` method used in the Settings class.
@pytest.fixture
def mock_logger_error(mocker):
    """
    Mocks the logger.error method to assert if error messages are logged.
    """
    # Patch the logger.error method in the config module's specific logger instance
    mock = mocker.patch("app.utils.config.logger.error")
    yield mock


# --- Test Cases for Settings Class Initialization ---

def test_settings_init_with_valid_env_vars(set_valid_env_vars):
    """
    Tests that the Settings class correctly initializes by loading values
    from environment variables, overriding default values.
    """
    # Import Settings here to ensure it uses the environment set by the fixture
    from app.utils.config import Settings
    settings_instance = Settings()

    assert settings_instance.GOOGLE_API_KEY == "test_google_api_key_123"
    assert settings_instance.API_HOST == "test_api_host.com"
    assert settings_instance.API_PORT == 9001
    assert settings_instance.FRONTEND_HOST == "test_frontend_host.com"
    assert settings_instance.FRONTEND_PORT == 9502
    assert settings_instance.DEBUG is False


def test_settings_init_with_kwargs_override_env_vars(set_valid_env_vars):
    """
    Tests that Settings can be initialized with direct keyword arguments,
    and these arguments correctly override values provided by environment variables.
    """
    from app.utils.config import Settings
    # Override some values that are also set by environment variables
    settings_instance = Settings(
        GOOGLE_API_KEY="kwarg_google_key",
        API_PORT=1234,
        DEBUG=True
    )
    assert settings_instance.GOOGLE_API_KEY == "kwarg_google_key"  # Overridden
    assert settings_instance.API_HOST == "test_api_host.com"  # From env
    assert settings_instance.API_PORT == 1234  # Overridden
    assert settings_instance.DEBUG is True  # Overridden


def test_settings_init_with_default_values_when_env_not_set(monkeypatch):
    """
    Tests that optional settings fields correctly use their predefined default values
    if they are not provided via environment variables or kwargs.
    Requires a valid GOOGLE_API_KEY to pass initial validation.
    """
    # Ensure GOOGLE_API_KEY is set to allow successful instantiation
    monkeypatch.setenv("GOOGLE_API_KEY", "valid_key_for_default_test")
    
    # Unset other environment variables to ensure defaults are used
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("FRONTEND_HOST", raising=False)
    monkeypatch.delenv("FRONTEND_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    from app.utils.config import Settings
    settings_instance = Settings()

    assert settings_instance.GOOGLE_API_KEY == "valid_key_for_default_test"
    assert settings_instance.API_HOST == "localhost"  # Default value
    assert settings_instance.API_PORT == 8000  # Default value
    assert settings_instance.FRONTEND_HOST == "localhost"  # Default value
    assert settings_instance.FRONTEND_PORT == 8501  # Default value
    assert settings_instance.DEBUG is True  # Default value


def test_settings_init_missing_google_api_key_raises_error(monkeypatch, mock_logger_error):
    """
    Tests that initializing Settings raises a ValueError and logs an error
    when the GOOGLE_API_KEY environment variable is not set.
    """
    # Ensure GOOGLE_API_KEY is definitely not set for this test
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    # Also unset other optional variables to ensure no interference
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("FRONTEND_HOST", raising=False)
    monkeypatch.delenv("FRONTEND_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    # Import Settings class directly to test its __init__ in isolation
    from app.utils.config import Settings

    with pytest.raises(ValueError) as excinfo:
        Settings()
    assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
    mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")


def test_settings_init_default_google_api_key_raises_error(monkeypatch, mock_logger_error):
    """
    Tests that initializing Settings raises a ValueError and logs an error
    when GOOGLE_API_KEY is set to its default placeholder string.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")
    # Unset other optional variables to ensure no interference
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("FRONTEND_HOST", raising=False)
    monkeypatch.delenv("FRONTEND_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    from app.utils.config import Settings

    with pytest.raises(ValueError) as excinfo:
        Settings()
    assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
    mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")


# --- Test Cases for get_settings Function ---

def test_get_settings_returns_settings_instance(set_valid_env_vars):
    """
    Tests that the get_settings function correctly returns an instance of Settings.
    """
    from app.utils.config import get_settings, Settings
    settings_instance = get_settings()
    assert isinstance(settings_instance, Settings)
    assert settings_instance.GOOGLE_API_KEY == "test_google_api_key_123"


def test_get_settings_caches_instance(set_valid_env_vars):
    """
    Tests that get_settings uses lru_cache and returns the exact same
    instance on subsequent calls, demonstrating caching behavior.
    """
    from app.utils.config import get_settings
    first_call_instance = get_settings()
    second_call_instance = get_settings()
    assert first_call_instance is second_call_instance  # Verify same object reference


# --- Test Cases for Module-Level 'settings' Variable ---

def test_module_level_settings_variable_is_cached_instance(set_valid_env_vars):
    """
    Tests that the module-level 'settings' variable is correctly initialized
    as an instance of Settings and is the same cached instance as returned by
    get_settings(). This verifies the execution of `settings = get_settings()`
    at module import time.
    """
    # Import the module-level 'settings' variable and the 'get_settings' function.
    # The `set_valid_env_vars` fixture ensures GOOGLE_API_KEY is available when
    # `app.utils.config` is first imported for this test.
    from app.utils.config import settings, get_settings
    
    # 'settings' is automatically initialized via `get_settings()` when `app.utils.config`
    # is first imported into the test session for this specific test case.
    # Due to the `clear_settings_cache` autouse fixture, `get_settings()` will
    # produce a fresh instance for this test.
    
    assert isinstance(settings, type(get_settings()))
    assert settings is get_settings()  # Should be the same cached instance
    assert settings.GOOGLE_API_KEY == "test_google_api_key_123"