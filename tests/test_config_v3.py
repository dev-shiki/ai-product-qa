import pytest
import os
import logging
from unittest.mock import patch, MagicMock

# Import the necessary components from the module under test.
# The global 'settings' variable (named 'global_settings_instance' here for clarity in tests)
# is initialized when app.utils.config is first imported by the test runner.
# Its state will depend on the environment variables present at that precise moment.
# For comprehensive testing, ensure GOOGLE_API_KEY is set in your test environment
# (e.g., via a conftest.py, pytest.ini, or system environment variable)
# when running pytest to ensure the module loads successfully and the global
# 'settings' instance is properly initialized.
from app.utils.config import Settings, get_settings, logger as config_logger, settings as global_settings_instance


@pytest.fixture(autouse=True)
def setup_and_teardown_env_and_cache(monkeypatch):
    """
    Fixture to clear the lru_cache for get_settings and ensure environment
    variables are cleaned before each test. This provides a consistent
    and isolated environment for each test function.
    """
    # Clear the lru_cache for get_settings to ensure fresh instances are created
    # for each test that calls get_settings().
    get_settings.cache_clear()

    # Clear all relevant environment variables to prevent leakage between tests
    # and ensure tests correctly handle missing/default values.
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("FRONTEND_HOST", raising=False)
    monkeypatch.delenv("FRONTEND_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    # Yield control to the test function. Code after yield runs as teardown.
    yield

    # Ensure cache is cleared again after the test, though autouse fixture should handle this.
    get_settings.cache_clear()


@pytest.fixture
def mock_config_logger():
    """
    Fixture to mock the logger instance used in app.utils.config.
    This allows us to assert that logging calls (e.g., logger.error) are made correctly.
    """
    # Patch the 'logger' object within the 'app.utils.config' module.
    # autospec=True ensures the mock has the same methods as the original logger,
    # preventing silent failures due to misspelled method calls.
    with patch("app.utils.config.logger", autospec=True) as mock_log:
        yield mock_log


# --- Test Cases for Settings Class ---

def test_settings_initialization_success_with_all_env_vars(monkeypatch):
    """
    Test that the Settings class initializes correctly when all expected
    environment variables are provided and have valid values.
    Verifies that attributes are set from environment variables.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "valid_key_123_abc")
    monkeypatch.setenv("API_HOST", "myapi.example.com")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("FRONTEND_HOST", "myfrontend.example.com")
    monkeypatch.setenv("FRONTEND_PORT", "9500")
    monkeypatch.setenv("DEBUG", "False")  # Pydantic converts "False" string to bool False

    settings = Settings()

    assert settings.GOOGLE_API_KEY == "valid_key_123_abc"
    assert settings.API_HOST == "myapi.example.com"
    assert settings.API_PORT == 9000
    assert settings.FRONTEND_HOST == "myfrontend.example.com"
    assert settings.FRONTEND_PORT == 9500
    assert settings.DEBUG is False

def test_settings_initialization_success_with_defaults(monkeypatch):
    """
    Test that the Settings class uses default values for optional settings
    when only the required GOOGLE_API_KEY is provided via environment variable.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "valid_key_for_defaults_xyz")

    settings = Settings()

    assert settings.GOOGLE_API_KEY == "valid_key_for_defaults_xyz"
    assert settings.API_HOST == "localhost"
    assert settings.API_PORT == 8000
    assert settings.FRONTEND_HOST == "localhost"
    assert settings.FRONTEND_PORT == 8501
    assert settings.DEBUG is True

def test_settings_initialization_missing_google_api_key_raises_error(mock_config_logger):
    """
    Test that Settings raises a ValueError and logs an error when the
    GOOGLE_API_KEY environment variable is not set.
    """
    # The autouse fixture 'setup_and_teardown_env_and_cache' ensures GOOGLE_API_KEY is absent.
    with pytest.raises(ValueError) as excinfo:
        Settings()

    assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
    mock_config_logger.error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

def test_settings_initialization_default_placeholder_google_api_key_raises_error(monkeypatch, mock_config_logger):
    """
    Test that Settings raises a ValueError and logs an error when the
    GOOGLE_API_KEY environment variable is set to its default placeholder string.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")

    with pytest.raises(ValueError) as excinfo:
        Settings()

    assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
    mock_config_logger.error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

def test_settings_config_env_file_attribute():
    """
    Test that the internal Config class of Settings has the correct
    env_file attribute, indicating the expected environment file name.
    """
    assert Settings.Config.env_file == ".env"


# --- Test Cases for get_settings Function ---

def test_get_settings_returns_settings_instance(monkeypatch):
    """
    Test that the get_settings function returns a valid instance of the Settings class.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "key_for_get_settings_test")
    settings_instance = get_settings()
    assert isinstance(settings_instance, Settings)
    assert settings_instance.GOOGLE_API_KEY == "key_for_get_settings_test"

def test_get_settings_lru_cache_behavior(monkeypatch):
    """
    Test that get_settings utilizes lru_cache correctly, returning the same
    instance on subsequent calls and creating a new one only after the cache is cleared.
    """
    # Ensure a fresh start (due to autouse fixture), then set key for the first call.
    monkeypatch.setenv("GOOGLE_API_KEY", "initial_cached_key_1")
    first_call_settings = get_settings()

    # Change the environment variable. Due to caching, this should not affect
    # the returned instance on the next call.
    monkeypatch.setenv("GOOGLE_API_KEY", "changed_key_after_cache_2")
    second_call_settings = get_settings()

    # Assert that the same instance is returned due to lru_cache.
    assert first_call_settings is second_call_settings
    # The attributes should reflect the environment variables when the *first*
    # instance was created (i.e., when the cache was populated).
    assert first_call_settings.GOOGLE_API_KEY == "initial_cached_key_1"
    assert second_call_settings.GOOGLE_API_KEY == "initial_cached_key_1"

    # Now, clear the lru_cache and verify that a new instance is created.
    get_settings.cache_clear()
    monkeypatch.setenv("GOOGLE_API_KEY", "key_after_cache_clear_3")
    third_call_settings = get_settings()

    # Assert that a new instance has been created.
    assert first_call_settings is not third_call_settings
    # The new instance should reflect the latest environment variable.
    assert third_call_settings.GOOGLE_API_KEY == "key_after_cache_clear_3"


# --- Test Cases for Global 'settings' Instance ---

def test_global_settings_instance_is_settings_object():
    """
    Test that the globally defined 'settings' instance (imported as
    'global_settings_instance' in this test file) is an instance of Settings.

    NOTE: The specific values/contents of this global instance depend on the
    environment variables present *when the 'app.utils.config' module was
    first imported by the pytest test runner*. To ensure full coverage and
    successful initialization of this global variable, GOOGLE_API_KEY must
    be set in the test environment (e.g., via `export GOOGLE_API_KEY=test_value`
    before running pytest, or in a `conftest.py` setup).
    This test primarily verifies its type. Dynamically changing its contents
    for individual test functions after its initial load is complex and generally
    not done in unit tests for global module-level variables.
    """
    # We use the already imported `global_settings_instance` from the top of this file.
    assert isinstance(global_settings_instance, Settings)