# test_utils/config.py
import pytest
import os
from unittest.mock import patch
from functools import lru_cache

# IMPORTANT NOTE FOR RUNNING TESTS:
# The line 'settings = get_settings()' in app/utils/config.py means that the
# module attempts to load configuration upon import. If 'GOOGLE_API_KEY' is not
# set in the environment where pytest is run, the initial module import will fail.
# To run these tests successfully, ensure 'GOOGLE_API_KEY' is set to a valid string
# (e.g., via a shell environment variable like `export GOOGLE_API_KEY=test_initial_key`
# before running `pytest`, or through a `conftest.py` file using `pytest_configure` hook).
# Our tests will use `monkeypatch` to override this for specific test scenarios,
# but the initial module load requires a valid default.

# Fixture to clear the lru_cache for get_settings before and after each test.
# This ensures that tests are isolated and don't rely on cached state from previous tests.
@pytest.fixture(autouse=True)
def clear_settings_cache():
    """
    Clears the lru_cache of the get_settings function before and after each test.
    This ensures that each test starts with a clean slate regarding cached settings,
    allowing environment variables to be properly mocked for individual tests.
    """
    # Import the function inside the fixture to ensure it's loaded after
    # any potential environment setup by pytest itself, and to get a fresh
    # reference in case of complex reload scenarios (though not strictly necessary here).
    from app.utils.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear() # Clear again after the test completes for good measure

# Fixture to provide a set of standard mocked environment variables for tests.
@pytest.fixture
def mock_env_vars(monkeypatch):
    """
    Fixture to set standard mocked environment variables using pytest's monkeypatch.
    This provides a consistent test environment for successful configuration loading.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "test-mock-api-key")
    monkeypatch.setenv("API_HOST", "mock-api-host.com")
    monkeypatch.setenv("API_PORT", "9001")
    monkeypatch.setenv("FRONTEND_HOST", "mock-frontend-host.com")
    monkeypatch.setenv("FRONTEND_PORT", "9502")
    monkeypatch.setenv("DEBUG", "False") # Test boolean parsing

# --- Test Cases for Settings Class ---

def test_settings_initialization_success_all_fields(mock_env_vars):
    """
    Test successful initialization of the Settings class when all fields
    (including required and optional) are provided via environment variables.
    """
    from app.utils.config import Settings
    settings_instance = Settings()

    assert settings_instance.GOOGLE_API_KEY == "test-mock-api-key"
    assert settings_instance.API_HOST == "mock-api-host.com"
    assert settings_instance.API_PORT == 9001
    assert settings_instance.FRONTEND_HOST == "mock-frontend-host.com"
    assert settings_instance.FRONTEND_PORT == 9502
    assert settings_instance.DEBUG is False

def test_settings_initialization_defaults_only_required(monkeypatch):
    """
    Test successful initialization of Settings when only the required
    GOOGLE_API_KEY is set. Other fields should fall back to their default values.
    """
    from app.utils.config import Settings

    monkeypatch.setenv("GOOGLE_API_KEY", "required-key-only")
    # Ensure other optional variables are not set, so defaults are used
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("FRONTEND_HOST", raising=False)
    monkeypatch.delenv("FRONTEND_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    settings_instance = Settings()

    assert settings_instance.GOOGLE_API_KEY == "required-key-only"
    assert settings_instance.API_HOST == "localhost"
    assert settings_instance.API_PORT == 8000
    assert settings_instance.FRONTEND_HOST == "localhost"
    assert settings_instance.FRONTEND_PORT == 8501
    assert settings_instance.DEBUG is True

def test_settings_google_api_key_empty_raises_error_and_logs(monkeypatch):
    """
    Test that Settings raises a ValueError and logs an error message
    when GOOGLE_API_KEY is an empty string.
    """
    from app.utils.config import Settings
    from app.utils.config import logger as config_logger # Import logger to patch it

    monkeypatch.setenv("GOOGLE_API_KEY", "")
    # Clear other env vars to ensure a clean test environment
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("FRONTEND_HOST", raising=False)
    monkeypatch.delenv("FRONTEND_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    with patch.object(config_logger, 'error') as mock_logger_error:
        with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
            Settings()
        mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

def test_settings_google_api_key_default_string_raises_error_and_logs(monkeypatch):
    """
    Test that Settings raises a ValueError and logs an error message
    when GOOGLE_API_KEY is set to the default placeholder string.
    """
    from app.utils.config import Settings
    from app.utils.config import logger as config_logger

    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")
    # Clear other env vars to ensure a clean test environment
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("FRONTEND_HOST", raising=False)
    monkeypatch.delenv("FRONTEND_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    with patch.object(config_logger, 'error') as mock_logger_error:
        with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
            Settings()
        mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

def test_settings_debug_boolean_parsing(monkeypatch):
    """
    Test that the 'DEBUG' field correctly parses various boolean-like
    values from environment variables into Python booleans.
    """
    from app.utils.config import Settings

    monkeypatch.setenv("GOOGLE_API_KEY", "valid-key-for-debug-test")

    # Test "True" and similar values
    monkeypatch.setenv("DEBUG", "True")
    assert Settings().DEBUG is True
    monkeypatch.setenv("DEBUG", "true")
    assert Settings().DEBUG is True
    monkeypatch.setenv("DEBUG", "1")
    assert Settings().DEBUG is True

    # Test "False" and similar values
    monkeypatch.setenv("DEBUG", "False")
    assert Settings().DEBUG is False
    monkeypatch.setenv("DEBUG", "false")
    assert Settings().DEBUG is False
    monkeypatch.setenv("DEBUG", "0")
    assert Settings().DEBUG is False

    # Test default value when DEBUG is not set
    monkeypatch.delenv("DEBUG", raising=False)
    assert Settings().DEBUG is True

def test_settings_unknown_env_var_ignored(monkeypatch):
    """
    Test that pydantic-settings correctly ignores environment variables
    that are not explicitly defined in the Settings model.
    """
    from app.utils.config import Settings
    monkeypatch.setenv("GOOGLE_API_KEY", "valid-key-for-unknown")
    monkeypatch.setenv("UNKNOWN_FIELD", "this_should_be_ignored")

    settings_instance = Settings()
    assert not hasattr(settings_instance, "UNKNOWN_FIELD")
    assert settings_instance.GOOGLE_API_KEY == "valid-key-for-unknown" # Ensure known field is still correct

# --- Test Cases for get_settings Function ---

def test_get_settings_caches_instance(monkeypatch):
    """
    Test that get_settings uses lru_cache and returns the same instance on
    subsequent calls, and that cache_clear allows a new instance to be created.
    """
    from app.utils.config import get_settings

    # 1. First call initializes and caches an instance based on current env
    monkeypatch.setenv("GOOGLE_API_KEY", "key-for-first-cache")
    first_settings_instance = get_settings()
    assert first_settings_instance.GOOGLE_API_KEY == "key-for-first-cache"

    # 2. Second call should return the cached instance, even if env var changes
    monkeypatch.setenv("GOOGLE_API_KEY", "key-for-second-call-should-be-ignored")
    second_settings_instance = get_settings()
    assert second_settings_instance is first_settings_instance
    # The value should still be from the *first* call due to caching
    assert second_settings_instance.GOOGLE_API_KEY == "key-for-first-cache"

    # 3. Clear cache and make a third call; this should create a new instance
    get_settings.cache_clear()
    monkeypatch.setenv("GOOGLE_API_KEY", "key-for-third-call-new-instance")
    third_settings_instance = get_settings()
    assert third_settings_instance is not first_settings_instance # Should be a different object
    assert third_settings_instance.GOOGLE_API_KEY == "key-for-third-call-new-instance" # Should reflect new env

def test_get_settings_loads_correct_values_after_cache_clear(mock_env_vars):
    """
    Test that get_settings correctly loads values from environment variables
    when the cache is clear (e.g., on first call or after cache_clear()).
    This implicitly tests the underlying Settings instantiation via get_settings.
    """
    from app.utils.config import get_settings

    # The mock_env_vars fixture sets specific environment variables,
    # and clear_settings_cache (autouse) ensures the cache is clean.
    settings_instance = get_settings()

    assert settings_instance.GOOGLE_API_KEY == "test-mock-api-key"
    assert settings_instance.API_HOST == "mock-api-host.com"
    assert settings_instance.API_PORT == 9001
    assert settings_instance.FRONTEND_HOST == "mock-frontend-host.com"
    assert settings_instance.FRONTEND_PORT == 9502
    assert settings_instance.DEBUG is False

# --- Test Case for Global Settings Variable ---

def test_global_settings_variable_is_settings_instance(monkeypatch):
    """
    Test that the module-level 'settings' variable (defined as `settings = get_settings()`
    in the source file) is indeed an instance of the Settings class.
    This line executes only once when the module is first imported by Python.
    Its specific values depend on the environment at that time.
    """
    # Set a valid key for the initial module load if it hasn't been done externally.
    # This monkeypatch tries to influence the very first import if pytest hasn't
    # loaded the module yet for test discovery, or ensures it's set for any
    # subsequent re-imports if that were to happen.
    monkeypatch.setenv("GOOGLE_API_KEY", "global-initial-load-key")

    # Import the global `settings` variable and the `Settings` class definition.
    from app.utils.config import settings, Settings

    # Assert that the global 'settings' variable is an instance of the 'Settings' class.
    assert isinstance(settings, Settings)
    # The actual values within `settings` at this point will depend on the
    # environment when `app.utils.config` was first imported by the test runner.
    # This test primarily verifies the type and that the line `settings = get_settings()`
    # successfully executed and assigned a Settings object.
    # Comprehensive value testing is handled by `test_get_settings_loads_correct_values`.