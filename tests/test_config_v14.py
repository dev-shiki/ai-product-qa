import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Dynamically add the project root to sys.path if 'app' is not directly importable.
# This ensures that imports like 'from app.utils.config import ...' work correctly,
# especially when tests are run from a subdirectory (e.g., 'tests/').
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Fixture to clear the lru_cache for get_settings before each test.
# This is crucial to ensure tests for caching behavior are isolated and
# subsequent calls to get_settings get a fresh or expected cached instance.
@pytest.fixture(autouse=True)
def clear_settings_cache():
    """
    Clears the lru_cache for the `get_settings` function before each test.
    This ensures that each test starts with a clean state regarding cached settings.
    A try-except block is used in case the module hasn't been imported yet in a specific test,
    preventing an ImportError.
    """
    try:
        from app.utils.config import get_settings
        get_settings.cache_clear()
    except ImportError:
        pass # Module not imported yet, nothing to clear


# Fixture to prepare the environment for testing the global 'settings' variable.
# This is necessary because the global 'settings' is initialized at module import time.
@pytest.fixture
def reset_config_module():
    """
    Fixture to remove 'app.utils.config' from `sys.modules`.
    This forces a fresh re-import of the module in the subsequent test,
    allowing environment variables set by monkeypatch to affect the global
    'settings' initialization.
    """
    # Store original state if the module was already imported
    original_config_module = sys.modules.get('app.utils.config', None)

    # Remove config from sys.modules to ensure a fresh import
    if 'app.utils.config' in sys.modules:
        del sys.modules['app.utils.config']

    yield # Allow the test to run

    # Clean up: remove the module again after the test, or restore original state
    if 'app.utils.config' in sys.modules:
        del sys.modules['app.utils.config']
    if original_config_module is not None:
        sys.modules['app.utils.config'] = original_config_module


# --- Tests for the Settings class ---

def test_settings_successful_initialization_defaults(monkeypatch):
    """
    Test that the `Settings` class initializes correctly with a valid API key
    and uses default values for fields not specified via environment variables.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "test_valid_api_key_123")
    
    # Import Settings after setting the environment variable to ensure it's picked up.
    from app.utils.config import Settings

    settings = Settings()

    assert settings.GOOGLE_API_KEY == "test_valid_api_key_123"
    assert settings.API_HOST == "localhost"
    assert settings.API_PORT == 8000
    assert settings.FRONTEND_HOST == "localhost"
    assert settings.FRONTEND_PORT == 8501
    assert settings.DEBUG is True

def test_settings_successful_initialization_custom_values(monkeypatch):
    """
    Test that the `Settings` class initializes correctly, overriding default values
    with custom values provided via environment variables.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "custom_api_key_xyz")
    monkeypatch.setenv("API_HOST", "api.example.com")
    monkeypatch.setenv("API_PORT", "9001")
    monkeypatch.setenv("FRONTEND_HOST", "app.example.com")
    monkeypatch.setenv("FRONTEND_PORT", "3000")
    monkeypatch.setenv("DEBUG", "false") # Pydantic settings handles 'false' as boolean False
    
    from app.utils.config import Settings
    
    settings = Settings()

    assert settings.GOOGLE_API_KEY == "custom_api_key_xyz"
    assert settings.API_HOST == "api.example.com"
    assert settings.API_PORT == 9001
    assert settings.FRONTEND_HOST == "app.example.com"
    assert settings.FRONTEND_PORT == 3000
    assert settings.DEBUG is False

def test_settings_google_api_key_empty_raises_value_error(monkeypatch):
    """
    Test that `Settings` raises a ValueError when `GOOGLE_API_KEY` is set to an empty string,
    and verifies that an error message is logged.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    
    # We need to import `logger` from the module under test before patching it.
    from app.utils.config import logger

    with patch.object(logger, 'error') as mock_logger_error:
        # Import Settings within the patch scope to ensure the patched logger is used.
        from app.utils.config import Settings
        with pytest.raises(ValueError) as excinfo:
            Settings() # Instantiating Settings should trigger the validation logic
        
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

def test_settings_google_api_key_default_placeholder_raises_value_error(monkeypatch):
    """
    Test that `Settings` raises a ValueError when `GOOGLE_API_KEY` is the default placeholder
    "your-google-api-key-here", and verifies that an error message is logged.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")

    from app.utils.config import logger

    with patch.object(logger, 'error') as mock_logger_error:
        from app.utils.config import Settings
        with pytest.raises(ValueError) as excinfo:
            Settings()
        
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

# --- Tests for the get_settings function ---

def test_get_settings_returns_settings_instance(monkeypatch):
    """
    Test that `get_settings` returns a valid instance of the `Settings` class.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "key_for_get_settings_test")
    from app.utils.config import Settings, get_settings

    settings_instance = get_settings()
    assert isinstance(settings_instance, Settings)
    assert settings_instance.GOOGLE_API_KEY == "key_for_get_settings_test"
    assert settings_instance.API_PORT == 8000 # Verify a default value is also set

def test_get_settings_is_cached(monkeypatch):
    """
    Test that `get_settings` utilizes `lru_cache`, returning the exact same instance
    on subsequent calls, even if environment variables change.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "initial_cached_key")
    from app.utils.config import get_settings

    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2 # Verify it's the exact same object, not just equal

    # Change environment variable and call again; the cached instance should still be returned
    monkeypatch.setenv("GOOGLE_API_KEY", "new_key_that_should_not_be_used")
    settings3 = get_settings()

    assert settings3 is settings1 # Still the same object
    # The API key should reflect the value from the *first* call, not the changed env var
    assert settings3.GOOGLE_API_KEY == "initial_cached_key" 

# --- Tests for the global 'settings' variable ---

def test_global_settings_initialization_success(monkeypatch, reset_config_module):
    """
    Test that the global 'settings' variable is successfully initialized on module import
    when `GOOGLE_API_KEY` is valid, and correctly picks up environment variables.
    The `reset_config_module` fixture ensures a fresh module import.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "global_valid_api_key_success")
    monkeypatch.setenv("API_PORT", "9999") # Custom value for the global settings instance

    # Re-import the module to trigger the global 'settings' initialization with the new env vars
    from app.utils.config import settings as global_settings_var
    from app.utils.config import Settings # For type checking against the class

    assert isinstance(global_settings_var, Settings)
    assert global_settings_var.GOOGLE_API_KEY == "global_valid_api_key_success"
    assert global_settings_var.API_PORT == 9999
    assert global_settings_var.DEBUG is True # Should still be default True

def test_global_settings_initialization_failure(monkeypatch, reset_config_module):
    """
    Test that the global 'settings' variable initialization fails on module import
    if `GOOGLE_API_KEY` is invalid (empty in this case), and verifies that an error is logged.
    The `reset_config_module` fixture ensures a fresh module import.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "") # Invalid key

    # Patch the `logger` *before* the module import, as the error occurs during module loading.
    with patch('app.utils.config.logger', spec=True) as mock_logger:
        with pytest.raises(ValueError) as excinfo:
            # Attempting to import the module will trigger the global settings initialization
            # which will then raise the ValueError due to the invalid API key.
            import app.utils.config
            # No need to access `app.utils.config.settings` directly; the import process itself
            # will trigger the error and the logger call.

        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        mock_logger.error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")