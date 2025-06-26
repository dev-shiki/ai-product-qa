import pytest
import os
import sys
import importlib
from unittest.mock import MagicMock

# Define the module path for dynamic imports and patching
CONFIG_MODULE_PATH = 'app.utils.config'

# --- Fixtures ---

@pytest.fixture(autouse=True)
def setup_env_and_cleanup(monkeypatch):
    """
    Fixture to ensure environment variables are clean for each test
    and to clear the lru_cache of get_settings.
    This runs automatically for every test.
    """
    # Define common environment variables that might be set by tests
    env_vars_to_clear = [
        "GOOGLE_API_KEY", "API_HOST", "API_PORT",
        "FRONTEND_HOST", "FRONTEND_PORT", "DEBUG"
    ]
    
    # Store original values to restore them later, or ensure they are unset
    original_env = {var: os.getenv(var) for var in env_vars_to_clear}

    # Unset all relevant environment variables before each test
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)

    yield

    # Teardown: Restore environment variables to their original state
    for var, value in original_env.items():
        if value is None:
            monkeypatch.delenv(var, raising=False)
        else:
            monkeypatch.setenv(var, value)
            
    # Clear the lru_cache for get_settings after each test to ensure isolation.
    # We dynamically import here to ensure we get the latest state of the module
    # if it was reloaded by other fixtures.
    try:
        if CONFIG_MODULE_PATH in sys.modules:
            config_module = sys.modules[CONFIG_MODULE_PATH]
            if hasattr(config_module, 'get_settings'):
                config_module.get_settings.cache_clear()
    except (ImportError, AttributeError):
        # Handle cases where the module might not have been imported or get_settings isn't available
        pass

@pytest.fixture
def mock_logger_error(mocker):
    """
    Mocks the logger.error method in app.utils.config to check for error logging.
    """
    # Patch the logger.error method directly within the module's scope
    return mocker.patch(f'{CONFIG_MODULE_PATH}.logger.error')

@pytest.fixture
def reimport_config_module_for_test(monkeypatch):
    """
    A helper fixture to re-import the app.utils.config module dynamically.
    This is crucial for testing import-time behavior (like the global `settings` variable).
    It cleans up sys.modules and sets environment variables before re-importing.
    """
    def _reimport(env_vars: dict = None):
        # Set specified environment variables
        if env_vars:
            for key, value in env_vars.items():
                monkeypatch.setenv(key, str(value))
        
        # Remove the module from sys.modules to force a fresh import
        if CONFIG_MODULE_PATH in sys.modules:
            del sys.modules[CONFIG_MODULE_PATH]
        
        # Re-import the module. This will execute global code, including `settings = get_settings()`
        config_module = importlib.import_module(CONFIG_MODULE_PATH)
        
        # Immediately clear cache for the newly imported module's get_settings
        # to ensure predictable behavior for subsequent calls within the same test context.
        config_module.get_settings.cache_clear()
        
        return config_module

    yield _reimport

    # Teardown: Ensure the module is cleared from sys.modules after the test
    # to prevent interference with other tests.
    if CONFIG_MODULE_PATH in sys.modules:
        del sys.modules[CONFIG_MODULE_PATH]

# --- Tests for Settings class ---

def test_settings_init_raises_error_if_google_api_key_is_empty(monkeypatch, mock_logger_error):
    """
    Test that Settings.__init__ raises ValueError if GOOGLE_API_KEY is an empty string.
    Verifies error logging.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    from app.utils.config import Settings
    with pytest.raises(ValueError) as excinfo:
        Settings()
    assert "GOOGLE_API_KEY must be set" in str(excinfo.value)
    mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

def test_settings_init_raises_error_if_google_api_key_is_default_value(monkeypatch, mock_logger_error):
    """
    Test that Settings.__init__ raises ValueError if GOOGLE_API_KEY is the default placeholder.
    Verifies error logging.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")
    from app.utils.config import Settings
    with pytest.raises(ValueError) as excinfo:
        Settings()
    assert "GOOGLE_API_KEY must be set" in str(excinfo.value)
    mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

def test_settings_loads_with_valid_api_key_and_default_values(monkeypatch):
    """
    Test that Settings loads correctly with a valid API key and default values for other fields.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "valid-api-key-123")
    from app.utils.config import Settings
    settings_instance = Settings()
    assert settings_instance.GOOGLE_API_KEY == "valid-api-key-123"
    assert settings_instance.API_HOST == "localhost"
    assert settings_instance.API_PORT == 8000
    assert settings_instance.FRONTEND_HOST == "localhost"
    assert settings_instance.FRONTEND_PORT == 8501
    assert settings_instance.DEBUG is True

def test_settings_loads_from_all_env_variables(monkeypatch):
    """
    Test that Settings correctly loads all fields with overridden values from environment variables.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "custom-api-key")
    monkeypatch.setenv("API_HOST", "api.prod.com")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("FRONTEND_HOST", "front.prod.com")
    monkeypatch.setenv("FRONTEND_PORT", "3000")
    monkeypatch.setenv("DEBUG", "False")

    from app.utils.config import Settings
    settings_instance = Settings()

    assert settings_instance.GOOGLE_API_KEY == "custom-api-key"
    assert settings_instance.API_HOST == "api.prod.com"
    assert settings_instance.API_PORT == 9000
    assert settings_instance.FRONTEND_HOST == "front.prod.com"
    assert settings_instance.FRONTEND_PORT == 3000
    assert settings_instance.DEBUG is False

def test_settings_debug_field_true_by_default(monkeypatch):
    """Test that DEBUG is True by default when not explicitly set."""
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy-key")
    from app.utils.config import Settings
    settings_instance = Settings()
    assert settings_instance.DEBUG is True

def test_settings_debug_field_can_be_set_to_false(monkeypatch):
    """Test that DEBUG can be set to False via environment variable."""
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy-key")
    monkeypatch.setenv("DEBUG", "False")
    from app.utils.config import Settings
    settings_instance = Settings()
    assert settings_instance.DEBUG is False

# --- Tests for get_settings function ---

def test_get_settings_returns_settings_instance(monkeypatch):
    """
    Test that get_settings returns an instance of the Settings class.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-for-get_settings")
    from app.utils.config import get_settings, Settings
    settings_instance = get_settings()
    assert isinstance(settings_instance, Settings)
    assert settings_instance.GOOGLE_API_KEY == "test-key-for-get_settings"

def test_get_settings_caches_instance(monkeypatch):
    """
    Test that get_settings uses lru_cache and returns the exact same instance on subsequent calls.
    Changes to environment variables after the first call should not affect the cached instance.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "initial-cached-key")
    from app.utils.config import get_settings
    
    first_call_instance = get_settings()
    
    # Change environment variable; should not affect the cached instance
    monkeypatch.setenv("GOOGLE_API_KEY", "changed-key-after-cache") 
    second_call_instance = get_settings()
    
    assert first_call_instance is second_call_instance # Assert same object
    assert first_call_instance.GOOGLE_API_KEY == "initial-cached-key" # Assert original value is kept
    assert second_call_instance.GOOGLE_API_KEY == "initial-cached-key" # Assert original value is kept

def test_get_settings_cache_clear(monkeypatch):
    """
    Test that calling get_settings.cache_clear() makes subsequent calls return a new instance,
    reflecting updated environment variables.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "key-for-first-instance")
    from app.utils.config import get_settings
    
    first_instance = get_settings()
    
    # Clear the lru_cache
    get_settings.cache_clear()
    
    # Set a new environment variable to ensure the new instance picks it up
    monkeypatch.setenv("GOOGLE_API_KEY", "key-for-second-instance")
    second_instance = get_settings()
    
    assert first_instance is not second_instance
    assert first_instance.GOOGLE_API_KEY == "key-for-first-instance"
    assert second_instance.GOOGLE_API_KEY == "key-for-second-instance"

# --- Tests for global settings variable (import-time behavior) ---

def test_global_settings_variable_loads_correctly_on_import(reimport_config_module_for_test):
    """
    Test that the global 'settings' variable is initialized correctly on module import
    when GOOGLE_API_KEY is valid and other settings use defaults.
    """
    # Simulate import with a valid API key
    config_module = reimport_config_module_for_test(env_vars={"GOOGLE_API_KEY": "valid-global-key-on-import"})
    
    assert config_module.settings.GOOGLE_API_KEY == "valid-global-key-on-import"
    assert config_module.settings.API_HOST == "localhost" # Default value
    assert config_module.settings.API_PORT == 8000 # Default value
    assert config_module.settings.DEBUG is True # Default value

def test_global_settings_variable_raises_error_on_invalid_api_key_at_import(reimport_config_module_for_test, mock_logger_error):
    """
    Test that importing app.utils.config raises ValueError if GOOGLE_API_KEY is invalid
    at the time of module import (due to the global `settings = get_settings()` line).
    Verifies error logging during import.
    """
    with pytest.raises(ValueError) as excinfo:
        reimport_config_module_for_test(env_vars={"GOOGLE_API_KEY": "your-google-api-key-here"})
    
    assert "GOOGLE_API_KEY must be set" in str(excinfo.value)
    mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

def test_global_settings_variable_is_cached_and_new_on_reimport(reimport_config_module_for_test):
    """
    Test that the global 'settings' variable is the same instance as returned by get_settings
    within a single import, and that re-importing the module provides a new, distinct instance
    reflecting updated environment variables.
    """
    # First import: setup with key1
    config_module_1 = reimport_config_module_for_test(env_vars={"GOOGLE_API_KEY": "key1"})
    
    # Within the first import, global settings should be the cached get_settings result
    settings_from_module_1 = config_module_1.settings
    get_settings_from_module_1_call = config_module_1.get_settings()
    
    assert settings_from_module_1 is get_settings_from_module_1_call
    assert settings_from_module_1.GOOGLE_API_KEY == "key1"

    # Re-import: setup with key2
    config_module_2 = reimport_config_module_for_test(env_vars={"GOOGLE_API_KEY": "key2"})
    
    # The global settings variable from the second import should be a new instance
    settings_from_module_2 = config_module_2.settings
    
    assert settings_from_module_1 is not settings_from_module_2
    assert settings_from_module_2.GOOGLE_API_KEY == "key2"