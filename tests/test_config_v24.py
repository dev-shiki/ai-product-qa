import pytest
import os
import logging
from unittest.mock import patch

# Import the module under test
# Note: Importing app.utils.config will execute the module-level 'settings = get_settings()'
# The autouse fixture 'setup_and_teardown_env' ensures a valid GOOGLE_API_KEY is present
# during this initial import to prevent immediate ValueError.
from app.utils.config import Settings, get_settings, settings as module_level_settings

# --- Fixtures ---

@pytest.fixture(autouse=True)
def setup_and_teardown_env(monkeypatch):
    """
    Sets up default valid environment variables for tests and ensures the cache
    of get_settings is cleared before and after each test.

    This fixture is autouse:
    1. It runs before any test functions.
    2. It ensures GOOGLE_API_KEY is set for the initial import of app.utils.config,
       preventing a ValueError at module load time.
    3. It clears the lru_cache for get_settings before each test to guarantee isolation
       and allow tests to set specific environment conditions.
    """
    # Set default valid environment variables for module import and general tests
    monkeypatch.setenv("GOOGLE_API_KEY", "valid_google_api_key_123")
    monkeypatch.setenv("API_HOST", "test_api_host")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("FRONTEND_HOST", "test_frontend_host")
    monkeypatch.setenv("FRONTEND_PORT", "9500")
    monkeypatch.setenv("DEBUG", "False") # Test boolean parsing

    # Clear the lru_cache for get_settings before each test.
    # This ensures each test gets a fresh Settings instance,
    # reflecting any environment variable changes made within that test.
    get_settings.cache_clear()

    yield  # Run the test

    # Clean up: Clear the cache again after the test completes for good measure
    # and to prevent interference with other tests if autouse fixtures are
    # not completely isolated in all scenarios.
    get_settings.cache_clear()
    # monkeypatch automatically handles tearing down environment variable changes.


# --- Tests for Settings class ---

def test_settings_initialization_success_with_env_vars(setup_and_teardown_env):
    """
    Tests successful initialization of Settings.
    Verifies that all fields are correctly loaded from environment variables
    set by the autouse fixture.
    """
    settings_instance = Settings()

    assert settings_instance.GOOGLE_API_KEY == "valid_google_api_key_123"
    assert settings_instance.API_HOST == "test_api_host"
    assert settings_instance.API_PORT == 9000
    assert settings_instance.FRONTEND_HOST == "test_frontend_host"
    assert settings_instance.FRONTEND_PORT == 9500
    assert settings_instance.DEBUG is False

def test_settings_uses_default_values_when_env_not_set(monkeypatch, setup_and_teardown_env):
    """
    Tests that Settings uses its defined default values when specific environment
    variables are not explicitly set (but GOOGLE_API_KEY must still be set for valid init).
    """
    # Remove non-essential env vars to check if defaults are picked up
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("FRONTEND_HOST", raising=False)
    monkeypatch.delenv("FRONTEND_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    settings_instance = Settings()

    # GOOGLE_API_KEY remains set by the autouse fixture
    assert settings_instance.GOOGLE_API_KEY == "valid_google_api_key_123"
    # Check that default values are used for unset variables
    assert settings_instance.API_HOST == "localhost"
    assert settings_instance.API_PORT == 8000
    assert settings_instance.FRONTEND_HOST == "localhost"
    assert settings_instance.FRONTEND_PORT == 8501
    assert settings_instance.DEBUG is True # Default value

@patch('app.utils.config.logger')  # Patch the logger object within the module under test
def test_settings_google_api_key_not_set_raises_error(mock_logger, monkeypatch, setup_and_teardown_env):
    """
    Tests that a ValueError is raised and an error is logged when GOOGLE_API_KEY is not set
    in the environment.
    """
    monkeypatch.delenv("GOOGLE_API_KEY") # Unset the environment variable

    with pytest.raises(ValueError) as excinfo:
        Settings()
    assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
    # Verify that the logger.error method was called with the expected message
    mock_logger.error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

@patch('app.utils.config.logger')
def test_settings_google_api_key_empty_raises_error(mock_logger, monkeypatch, setup_and_teardown_env):
    """
    Tests that a ValueError is raised and an error is logged when GOOGLE_API_KEY is an empty string.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "") # Set to an empty string

    with pytest.raises(ValueError) as excinfo:
        Settings()
    assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
    mock_logger.error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

@patch('app.utils.config.logger')
def test_settings_google_api_key_default_placeholder_raises_error(mock_logger, monkeypatch, setup_and_teardown_env):
    """
    Tests that a ValueError is raised and an error is logged when GOOGLE_API_KEY
    is set to the default placeholder string "your-google-api-key-here".
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here") # Set to the placeholder

    with pytest.raises(ValueError) as excinfo:
        Settings()
    assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
    mock_logger.error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")


# --- Tests for get_settings function ---

def test_get_settings_returns_settings_instance(setup_and_teardown_env):
    """
    Tests that the get_settings function returns a valid instance of the Settings class.
    """
    settings_instance = get_settings()
    assert isinstance(settings_instance, Settings)
    assert settings_instance.GOOGLE_API_KEY == "valid_google_api_key_123" # Value from autouse fixture

def test_get_settings_is_cached(setup_and_teardown_env):
    """
    Tests that get_settings uses lru_cache and returns the exact same instance on subsequent calls
    within the same test context (before cache clear).
    """
    first_call_settings = get_settings()
    second_call_settings = get_settings()

    # Assert that both calls return the identical object, confirming caching
    assert first_call_settings is second_call_settings
    assert id(first_call_settings) == id(second_call_settings)

def test_get_settings_reloads_after_cache_clear(monkeypatch, setup_and_teardown_env):
    """
    Tests that clearing the lru_cache makes get_settings return a new instance,
    which will then pick up any newly updated environment variables.
    """
    initial_settings = get_settings()

    # Change an environment variable value
    monkeypatch.setenv("GOOGLE_API_KEY", "new_google_api_key_456")

    # Explicitly clear the cache to force a reload on the next call
    get_settings.cache_clear()

    # Get settings again; this should create a new instance with the updated value
    new_settings = get_settings()

    # Assert that a new instance was created and it reflects the updated environment variable
    assert initial_settings is not new_settings
    assert id(initial_settings) != id(new_settings)
    assert new_settings.GOOGLE_API_KEY == "new_google_api_key_456"


# --- Tests for module-level 'settings' instance ---

def test_module_level_settings_instance_type_and_values(setup_and_teardown_env):
    """
    Tests that the module-level 'settings' variable is correctly initialized
    as a Settings instance and reflects the environment variables present
    during its initial import.
    """
    # The 'module_level_settings' variable is imported, meaning it was
    # initialized when app.utils.config was first loaded by pytest.
    # The 'autouse' fixture ensures GOOGLE_API_KEY was valid at that time.
    assert isinstance(module_level_settings, Settings)
    assert module_level_settings.GOOGLE_API_KEY == "valid_google_api_key_123"
    assert module_level_settings.API_HOST == "test_api_host"
    assert module_level_settings.DEBUG is False

def test_module_level_settings_is_cached_get_settings_result(setup_and_teardown_env):
    """
    Tests that the module-level 'settings' variable is the exact same instance
    that would be returned by calling get_settings() (as it's derived from it).
    """
    # Since module_level_settings is assigned directly from get_settings()
    # upon module import, and get_settings() is lru_cached, the module-level
    # instance should be the same as the one returned by a subsequent call
    # to get_settings() within the same cached context.
    # Our autouse fixture clears the cache before each test, so the first call
    # to get_settings() in a test will produce the instance that is effectively
    # the 'module_level_settings' for that test run.
    assert module_level_settings is get_settings()
    assert id(module_level_settings) == id(get_settings())