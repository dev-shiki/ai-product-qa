import pytest
import os
import sys
import importlib
import logging
from functools import lru_cache

# --- Path setup for importing the module under test ---
# This block ensures that the 'app' directory is in the Python path
# so that `app.utils.config` can be imported correctly, regardless
# of where pytest is run from.
# Get the directory of the current test file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate up to the project root (assuming test_utils/config.py -> app/utils/config.py)
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
# Add the project root to sys.path
sys.path.insert(0, project_root)

# Import the module under test.
# We import it as 'config_module' to avoid conflicts with common variable names
# and to be able to reload it for specific tests if necessary.
import app.utils.config as config_module

# Remove the added path to avoid impacting other tests or system behavior
sys.path.pop(0)
# --- End of path setup ---


@pytest.fixture(autouse=True)
def mock_env_vars_and_clear_cache(monkeypatch):
    """
    Fixture to set up mock environment variables for tests and clear the
    lru_cache for get_settings.
    Uses autouse=True to ensure it's applied to all tests, providing a consistent
    environment. This is crucial for the module-level 'settings' instance which
    is initialized on module import.
    """
    # Set valid default values for all settings.
    # Pydantic's BaseSettings will pick these up.
    monkeypatch.setenv("GOOGLE_API_KEY", "test-valid-api-key-123")
    monkeypatch.setenv("API_HOST", "test_api_host")
    monkeypatch.setenv("API_PORT", "9001")
    monkeypatch.setenv("FRONTEND_HOST", "test_frontend_host")
    monkeypatch.setenv("FRONTEND_PORT", "8502")
    monkeypatch.setenv("DEBUG", "False") # Set as string for env var parsing

    # Clear the lru_cache for get_settings before each test
    # This ensures that get_settings starts clean for tests focusing on caching behavior
    # or for tests where a fresh Settings instance is desired.
    config_module.get_settings.cache_clear()
    yield
    # No explicit cleanup needed for monkeypatch, it handles unsetting env vars
    # when the fixture scope ends.
    # Clearing cache again after the test ensures isolation for any subsequent tests
    # that might run in the same session.
    config_module.get_settings.cache_clear()


def test_settings_init_success():
    """
    Test successful initialization of the Settings class with valid environment variables.
    Verifies that fields are correctly parsed and assigned.
    """
    settings = config_module.Settings()

    assert settings.GOOGLE_API_KEY == "test-valid-api-key-123"
    assert settings.API_HOST == "test_api_host"
    assert settings.API_PORT == 9001
    assert settings.FRONTEND_HOST == "test_frontend_host"
    assert settings.FRONTEND_PORT == 8502
    assert settings.DEBUG is False


def test_settings_init_defaults_when_not_overridden(monkeypatch):
    """
    Test that default values are used for settings when their corresponding
    environment variables are not explicitly set (except for GOOGLE_API_KEY).
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "another-valid-key") # Keep valid for init
    # Unset other environment variables to ensure defaults are used
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("FRONTEND_HOST", raising=False)
    monkeypatch.delenv("FRONTEND_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    settings = config_module.Settings()

    assert settings.GOOGLE_API_KEY == "another-valid-key"
    assert settings.API_HOST == "localhost"       # Default from class definition
    assert settings.API_PORT == 8000             # Default from class definition
    assert settings.FRONTEND_HOST == "localhost" # Default from class definition
    assert settings.FRONTEND_PORT == 8501        # Default from class definition
    assert settings.DEBUG is True               # Default from class definition


@pytest.mark.parametrize(
    "api_key_value",
    [
        "",                               # Empty string
        "your-google-api-key-here",       # The default placeholder value
        pytest.param(None, id="missing_env_var") # Simulate missing env var
    ],
    ids=["empty_string", "default_placeholder"]
)
def test_settings_init_google_api_key_validation_raises_value_error_and_logs(
    monkeypatch, caplog, api_key_value
):
    """
    Test that Settings initialization raises a ValueError and logs an error
    when GOOGLE_API_KEY is missing, empty, or set to the default placeholder.
    """
    # Capture logs at ERROR level for precise assertion
    with caplog.at_level(logging.ERROR):
        if api_key_value is None:
            # Simulate a missing environment variable
            monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        else:
            # Set the environment variable to the parameterized invalid value
            monkeypatch.setenv("GOOGLE_API_KEY", api_key_value)

        # Expect a ValueError to be raised
        with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
            config_module.Settings()

        # Assert that the specific error message was logged
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text
        assert len(caplog.records) == 1 # Ensure only one log message for this scenario


def test_get_settings_returns_settings_instance():
    """
    Test that the get_settings function successfully returns an instance of the Settings class.
    """
    settings_instance = config_module.get_settings()
    assert isinstance(settings_instance, config_module.Settings)
    # Verify a property to ensure it's a validly initialized instance
    assert settings_instance.GOOGLE_API_KEY == "test-valid-api-key-123"


def test_get_settings_is_cached():
    """
    Test that get_settings utilizes functools.lru_cache and returns the same
    Settings instance on subsequent calls without re-initialization.
    """
    # First call will create and cache the settings instance
    settings_1 = config_module.get_settings()

    # Second call should return the exact same cached instance
    settings_2 = config_module.get_settings()

    assert settings_1 is settings_2 # Verify object identity (same instance)


def test_get_settings_cache_clear_creates_new_instance():
    """
    Test that explicitly calling get_settings.cache_clear() causes a new
    Settings instance to be created on the next call to get_settings.
    """
    settings_1 = config_module.get_settings()

    # Clear the lru_cache
    config_module.get_settings.cache_clear()

    # A subsequent call to get_settings should now create a new instance
    settings_2 = config_module.get_settings()

    assert settings_1 is not settings_2 # Verify different object identity
    assert isinstance(settings_2, config_module.Settings) # Ensure it's still a valid instance


def test_module_level_settings_instance_is_valid():
    """
    Test that the 'settings' variable, which is initialized at the module level
    upon import, is a valid Settings instance. This implicitly confirms the
    initial call to get_settings() during module loading succeeded.
    This test relies on the `mock_env_vars_and_clear_cache` fixture ensuring
    a valid environment for the module's initial load.
    """
    assert isinstance(config_module.settings, config_module.Settings)
    assert config_module.settings.GOOGLE_API_KEY == "test-valid-api-key-123"
    assert config_module.settings.API_HOST == "test_api_host"
    assert config_module.settings.DEBUG is False # Value from mock_env_vars fixture


def test_lru_cache_decorator_is_applied():
    """
    Verify that the get_settings function has been correctly decorated
    with functools.lru_cache, by checking for the presence of 'cache_info' method.
    """
    assert hasattr(config_module.get_settings, 'cache_info')
    assert callable(config_module.get_settings.cache_info)
    # Optionally, check initial cache state
    cache_info = config_module.get_settings.cache_info()
    assert cache_info.hits == 0
    assert cache_info.misses == 0