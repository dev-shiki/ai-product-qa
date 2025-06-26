import pytest
import os
from unittest import mock
import logging
from pydantic import ValidationError

# Import the components from the module under test
# Assuming the test file is test_utils/config.py and the source is app/utils/config.py
from app.utils.config import Settings, get_settings, logger as config_logger

# Use a fixture to clear the lru_cache for get_settings before each test
@pytest.fixture(autouse=True)
def clear_settings_cache():
    """
    Fixture to clear the lru_cache for the `get_settings` function before each test
    to ensure test isolation and fresh configuration loading.
    """
    get_settings.cache_clear()
    yield
    get_settings.cache_clear() # Clear again after test to avoid interference with subsequent runs (if any)

# Fixture to temporarily set and unset environment variables for a test
@pytest.fixture
def mock_env_vars(monkeypatch):
    """
    Fixture to set and clean up environment variables using pytest's monkeypatch.
    Ensures a clean slate for environment-dependent tests.
    """
    # List of environment variables that `Settings` class might use
    env_vars_to_clear = [
        "GOOGLE_API_KEY",
        "API_HOST",
        "API_PORT",
        "FRONTEND_HOST",
        "FRONTEND_PORT",
        "DEBUG",
    ]
    
    # Store original values to restore them after the test
    original_env_values = {}
    for var in env_vars_to_clear:
        if var in os.environ:
            original_env_values[var] = os.environ[var]
            monkeypatch.delenv(var) # Remove the var for test's clean slate

    yield monkeypatch # Provide the monkeypatch object to the test

    # Restore original environment variables after the test completes
    for var, value in original_env_values.items():
        monkeypatch.setenv(var, value)

# --- Test Cases for Settings Class ---

def test_settings_initializes_with_valid_google_api_key_and_defaults(mock_env_vars):
    """
    Test that Settings initializes successfully when GOOGLE_API_KEY is valid
    and other optional fields take their default values.
    """
    mock_env_vars.setenv("GOOGLE_API_KEY", "my-valid-api-key-123")
    settings = Settings()

    assert settings.GOOGLE_API_KEY == "my-valid-api-key-123"
    assert settings.API_HOST == "localhost"
    assert settings.API_PORT == 8000
    assert settings.FRONTEND_HOST == "localhost"
    assert settings.FRONTEND_PORT == 8501
    assert settings.DEBUG is True

def test_settings_google_api_key_empty_string_raises_value_error(mock_env_vars, caplog):
    """
    Test that Settings' custom __init__ validation raises ValueError
    when GOOGLE_API_KEY is explicitly set as an empty string in the environment.
    Also checks for the corresponding error log message.
    """
    mock_env_vars.setenv("GOOGLE_API_KEY", "")
    
    with caplog.at_level(logging.ERROR, logger=config_logger):
        with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
            Settings()
    assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text

def test_settings_google_api_key_placeholder_raises_value_error(mock_env_vars, caplog):
    """
    Test that Settings' custom __init__ validation raises ValueError
    when GOOGLE_API_KEY is the placeholder "your-google-api-key-here" in the environment.
    Also checks for the corresponding error log message.
    """
    mock_env_vars.setenv("GOOGLE_API_KEY", "your-google-api-key-here")
    
    with caplog.at_level(logging.ERROR, logger=config_logger):
        with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
            Settings()
    assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text

def test_settings_missing_google_api_key_raises_pydantic_validation_error(mock_env_vars):
    """
    Test that Pydantic's BaseSettings raises a ValidationError if GOOGLE_API_KEY
    is not set at all in the environment, as it's a required field.
    This validation occurs before our custom __init__ method is called.
    """
    # Ensure GOOGLE_API_KEY is explicitly not set for this test
    if "GOOGLE_API_KEY" in os.environ:
        mock_env_vars.delenv("GOOGLE_API_KEY")

    with pytest.raises(ValidationError) as exc_info:
        Settings()
    # Optionally, check specific error details from Pydantic's ValidationError
    assert any("field required" in err["msg"] and err["loc"][0] == "GOOGLE_API_KEY" for err in exc_info.value.errors())

def test_settings_overrides_defaults_with_env_vars(mock_env_vars):
    """
    Test that environment variables successfully override default settings values
    for all configurable fields.
    """
    mock_env_vars.setenv("GOOGLE_API_KEY", "prod-api-key-789")
    mock_env_vars.setenv("API_HOST", "192.168.1.100")
    mock_env_vars.setenv("API_PORT", "9001")
    mock_env_vars.setenv("FRONTEND_HOST", "my-app.example.com")
    mock_env_vars.setenv("FRONTEND_PORT", "3000")
    mock_env_vars.setenv("DEBUG", "False") # Pydantic correctly converts "False" string to boolean False

    settings = Settings()

    assert settings.GOOGLE_API_KEY == "prod-api-key-789"
    assert settings.API_HOST == "192.168.1.100"
    assert settings.API_PORT == 9001
    assert settings.FRONTEND_HOST == "my-app.example.com"
    assert settings.FRONTEND_PORT == 3000
    assert settings.DEBUG is False

def test_settings_env_var_integer_conversion_error_raises_pydantic_validation_error(mock_env_vars):
    """
    Test that Pydantic raises a ValidationError if an environment variable
    expected to be an integer is provided with a non-integer string.
    """
    mock_env_vars.setenv("GOOGLE_API_KEY", "valid-key") # Required by custom init
    mock_env_vars.setenv("API_PORT", "not-an-integer-string")

    with pytest.raises(ValidationError) as exc_info:
        Settings()
    assert any("value is not a valid integer" in err["msg"] and err["loc"][0] == "API_PORT" for err in exc_info.value.errors())

def test_settings_env_var_boolean_conversion_error_raises_pydantic_validation_error(mock_env_vars):
    """
    Test that Pydantic raises a ValidationError if a boolean environment variable
    is provided with an invalid string (e.g., "invalid_bool").
    """
    mock_env_vars.setenv("GOOGLE_API_KEY", "valid-key")
    mock_env_vars.setenv("DEBUG", "invalid_bool")

    with pytest.raises(ValidationError) as exc_info:
        Settings()
    assert any("value could not be parsed to a boolean" in err["msg"] and err["loc"][0] == "DEBUG" for err in exc_info.value.errors())


# --- Test Cases for get_settings function and lru_cache ---

def test_get_settings_returns_settings_instance(mock_env_vars):
    """
    Test that the `get_settings` function correctly returns an instance of the Settings class.
    """
    mock_env_vars.setenv("GOOGLE_API_KEY", "get-settings-test-key")
    settings_instance = get_settings()
    assert isinstance(settings_instance, Settings)
    assert settings_instance.GOOGLE_API_KEY == "get-settings-test-key"

def test_get_settings_uses_lru_cache(mock_env_vars):
    """
    Test that `get_settings` utilizes `lru_cache`, ensuring that subsequent calls
    return the exact same Settings instance without re-initialization.
    """
    mock_env_vars.setenv("GOOGLE_API_KEY", "cached-api-key")

    instance1 = get_settings()
    instance2 = get_settings()

    # Assert that both calls return the identical object, demonstrating cache hit
    assert instance1 is instance2

    # Verify attributes are as expected from initial load
    assert instance1.GOOGLE_API_KEY == "cached-api-key"
    assert instance2.GOOGLE_API_KEY == "cached-api-key"

def test_get_settings_reflects_env_changes_after_cache_clear(mock_env_vars):
    """
    Test that `get_settings` creates a new Settings instance with updated
    environment variables after its cache is explicitly cleared.
    """
    # First call to get_settings: "initial-key"
    mock_env_vars.setenv("GOOGLE_API_KEY", "initial-key-from-env")
    settings1 = get_settings()
    assert settings1.GOOGLE_API_KEY == "initial-key-from-env"

    # Modify environment variable
    mock_env_vars.setenv("GOOGLE_API_KEY", "updated-key-from-env")

    # Clear the cache (the autouse fixture does this, but explicitly calling here
    # demonstrates its effect within the test flow)
    get_settings.cache_clear()

    # Second call to get_settings: Should create a new instance reflecting the update
    settings2 = get_settings()
    assert settings2.GOOGLE_API_KEY == "updated-key-from-env"
    assert settings1 is not settings2 # Ensure it's a new instance

    # Verify that the first instance retains its original value (immutability)
    assert settings1.GOOGLE_API_KEY == "initial-key-from-env"


# --- Test Cases for Global Settings Object (`settings`) ---

def test_global_settings_object_is_instance_of_settings(mock_env_vars):
    """
    Test that the globally exposed 'settings' object (initialized at module load time)
    is an instance of the Settings class. This implicitly covers the execution
    of the line `settings = get_settings()`.
    """
    # Ensure a valid GOOGLE_API_KEY is set, as the global `settings` object
    # would have been initialized based on the environment at the first import
    # of the app.utils.config module by the test runner.
    mock_env_vars.setenv("GOOGLE_API_KEY", "global-test-key")

    # Re-import to ensure we're getting the 'settings' object as initialized
    # by the test environment. In a real pytest run, the module might be imported once.
    # This explicit import is for clarity and to ensure the line `settings = get_settings()`
    # is definitely covered by *a* test if not already.
    from app.utils.config import settings

    assert isinstance(settings, Settings)
    # Further assertions on its values depend on the exact state of the environment
    # during the very first import of the module, which is hard to control per-test
    # for a global variable. The functionality is covered by other tests.