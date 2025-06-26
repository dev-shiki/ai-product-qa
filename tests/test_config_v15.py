import pytest
import os
import sys
from functools import lru_cache
import logging
from unittest.mock import MagicMock

# --- Fixtures ---

@pytest.fixture
def clear_get_settings_cache():
    """
    Fixture to clear the lru_cache of the get_settings function before and after each test.
    This ensures that each test starts with a fresh state for the cached settings.
    """
    # Attempt to import and clear cache, handling cases where it might not be imported yet
    try:
        from app.utils.config import get_settings
        get_settings.cache_clear()
    except (ImportError, AttributeError):
        pass # Module not imported or get_settings not found yet
    yield # Run the test
    try:
        from app.utils.config import get_settings
        get_settings.cache_clear()
    except (ImportError, AttributeError):
        pass # Module might be unloaded or get_settings removed by other fixtures/tests

@pytest.fixture
def mock_env_vars(monkeypatch):
    """
    Fixture to set up default environment variables for successful Settings initialization.
    These can be overridden or deleted by individual tests as needed.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key-123")
    monkeypatch.setenv("API_HOST", "test-host")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("FRONTEND_HOST", "test-frontend-host")
    monkeypatch.setenv("FRONTEND_PORT", "9500")
    monkeypatch.setenv("DEBUG", "False")
    yield # Allow the test to run
    # monkeypatch automatically handles cleanup/undoing the changes

@pytest.fixture
def mock_logger_error(mocker):
    """
    Fixture to mock the logger.error method from app.utils.config.
    This allows us to assert if and how the error log is called.
    """
    return mocker.patch("app.utils.config.logger.error")

@pytest.fixture
def reimport_config_module():
    """
    Fixture to clear the app.utils.config module from sys.modules and re-import it.
    This is crucial for testing module-level initialization logic (like the global 'settings' variable)
    where state needs to be reset between tests.
    """
    # Store original sys.modules state
    original_modules = sys.modules.copy()
    
    # Remove the module and its potential submodules to ensure a fresh import
    keys_to_delete = [k for k in sys.modules if k.startswith('app.utils.config')]
    for key in keys_to_delete:
        if key in sys.modules:
            del sys.modules[key]
    
    yield # Allow the test to run
    
    # Restore original sys.modules state to avoid interfering with other tests
    sys.modules.clear()
    sys.modules.update(original_modules)
    
    # Clear cache for the original get_settings if it was re-imported by other tests
    try:
        # After restoring sys.modules, the original config might be re-loaded by pytest,
        # ensure its cache is cleared for subsequent tests if this fixture is not used.
        from app.utils.config import get_settings
        get_settings.cache_clear()
    except (ImportError, AttributeError):
        pass


# --- Test Cases for Settings Class ---

class TestSettings:
    """Comprehensive tests for the Settings Pydantic model."""

    def test_settings_init_success_with_env_vars(self, mock_env_vars):
        """
        Test that Settings initializes successfully when environment variables
        are provided and correctly overrides default values.
        """
        # Import inside the test to ensure fixtures are active before import
        from app.utils.config import Settings
        settings = Settings()
        assert settings.GOOGLE_API_KEY == "test-api-key-123"
        assert settings.API_HOST == "test-host"
        assert settings.API_PORT == 9000
        assert settings.FRONTEND_HOST == "test-frontend-host"
        assert settings.FRONTEND_PORT == 9500
        assert settings.DEBUG is False

    def test_settings_init_success_with_kwargs(self, monkeypatch):
        """
        Test that Settings initializes successfully using keyword arguments
        and that kwargs take precedence over environment variables/defaults.
        """
        # Ensure no environment variables interfere with kwarg testing
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("API_HOST", raising=False)
        monkeypatch.delenv("API_PORT", raising=False)
        monkeypatch.delenv("FRONTEND_HOST", raising=False)
        monkeypatch.delenv("FRONTEND_PORT", raising=False)
        monkeypatch.delenv("DEBUG", raising=False)

        from app.utils.config import Settings
        settings = Settings(
            GOOGLE_API_KEY="kwarg-api-key-xyz",
            API_HOST="kwarg-host",
            API_PORT=9001,
            FRONTEND_HOST="kwarg-frontend-host",
            FRONTEND_PORT=9501,
            DEBUG=True
        )
        assert settings.GOOGLE_API_KEY == "kwarg-api-key-xyz"
        assert settings.API_HOST == "kwarg-host"
        assert settings.API_PORT == 9001
        assert settings.FRONTEND_HOST == "kwarg-frontend-host"
        assert settings.FRONTEND_PORT == 9501
        assert settings.DEBUG is True

    def test_settings_init_defaults_used_when_not_in_env_or_kwargs(self, mock_env_vars):
        """
        Test that default values specified in the Settings class are used
        for fields not provided via environment variables or kwargs
        (except GOOGLE_API_KEY which is mandatory and handled separately).
        """
        # Delete specific env vars set by mock_env_vars to ensure defaults are picked up
        mock_env_vars.monkeypatch.delenv("API_HOST", raising=False)
        mock_env_vars.monkeypatch.delenv("API_PORT", raising=False)
        mock_env_vars.monkeypatch.delenv("FRONTEND_HOST", raising=False)
        mock_env_vars.monkeypatch.delenv("FRONTEND_PORT", raising=False)
        mock_env_vars.monkeypatch.delenv("DEBUG", raising=False)

        from app.utils.config import Settings
        settings = Settings()
        assert settings.GOOGLE_API_KEY == "test-api-key-123" # Still from mock_env_vars
        assert settings.API_HOST == "localhost" # Default value
        assert settings.API_PORT == 8000 # Default value
        assert settings.FRONTEND_HOST == "localhost" # Default value
        assert settings.FRONTEND_PORT == 8501 # Default value
        assert settings.DEBUG is True # Default value

    @pytest.mark.parametrize("api_key_value", ["", "your-google-api-key-here"])
    def test_settings_init_raises_value_error_on_invalid_api_key_value(self, mock_env_vars, mock_logger_error, api_key_value):
        """
        Test that a ValueError is raised and an error is logged when GOOGLE_API_KEY
        is explicitly set to an empty string or the default placeholder value.
        """
        mock_env_vars.monkeypatch.setenv("GOOGLE_API_KEY", api_key_value)
        from app.utils.config import Settings
        with pytest.raises(ValueError) as excinfo:
            Settings()
        
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

    def test_settings_init_raises_value_error_if_api_key_missing_from_env(self, mock_env_vars, mock_logger_error):
        """
        Test that a ValueError is raised and an error is logged when GOOGLE_API_KEY
        is not set in the environment at all. Pydantic-settings would typically
        default it to an empty string if not found, triggering our validation.
        """
        mock_env_vars.monkeypatch.delenv("GOOGLE_API_KEY") # Delete the key
        from app.utils.config import Settings
        with pytest.raises(ValueError) as excinfo:
            Settings()
        
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")


# --- Test Cases for get_settings function ---

class TestGetSettings:
    """Comprehensive tests for the get_settings function and its caching."""

    def test_get_settings_returns_settings_instance(self, clear_get_settings_cache, mock_env_vars):
        """Test that get_settings returns an instance of the Settings class."""
        from app.utils.config import get_settings, Settings
        settings_instance = get_settings()
        assert isinstance(settings_instance, Settings)
        assert settings_instance.GOOGLE_API_KEY == "test-api-key-123"

    def test_get_settings_caches_instance(self, clear_get_settings_cache, mock_env_vars):
        """
        Test that get_settings caches the Settings instance using lru_cache,
        returning the same instance on subsequent calls.
        """
        from app.utils.config import get_settings
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2 # Verify that both are the same instance due to caching

    def test_get_settings_propagates_settings_init_error(self, clear_get_settings_cache, mock_env_vars, mock_logger_error):
        """
        Test that get_settings propagates the ValueError raised from Settings.__init__
        when the GOOGLE_API_KEY is invalid.
        """
        mock_env_vars.monkeypatch.setenv("GOOGLE_API_KEY", "") # Set an invalid key for the test
        from app.utils.config import get_settings
        with pytest.raises(ValueError) as excinfo:
            get_settings()
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")


# --- Test Cases for Global Settings Variable ---

class TestGlobalSettings:
    """
    Tests for the module-level 'settings' variable initialization.
    These tests require re-importing the module to properly simulate its initial load.
    """

    def test_global_settings_init_success(self, mock_env_vars, reimport_config_module):
        """
        Test that the global 'settings' variable is successfully initialized
        when the module is imported with a valid GOOGLE_API_KEY.
        """
        # reimport_config_module ensures a fresh import of app.utils.config
        # after mock_env_vars has set up the environment
        from app.utils import config
        assert config.settings.GOOGLE_API_KEY == "test-api-key-123"
        assert isinstance(config.settings, config.Settings)
        # Verify it's indeed the cached instance by comparing with get_settings() result
        assert config.settings is config.get_settings()

    def test_global_settings_init_failure(self, mock_env_vars, mock_logger_error, reimport_config_module):
        """
        Test that the module-level 'settings' variable initialization fails
        (i.e., raises ValueError during module import) when GOOGLE_API_KEY is invalid.
        """
        mock_env_vars.monkeypatch.setenv("GOOGLE_API_KEY", "") # Set an invalid key before reimport
        
        # Since 'settings = get_settings()' is executed at the module level (top-level code),
        # a ValueError during its call will prevent the module from being successfully imported.
        with pytest.raises(ValueError) as excinfo:
            # Attempting to import the module will trigger its initialization logic
            from app.utils import config as reimported_config_module_for_failure
            # This line should not be reached if the ValueError is raised during import.
        
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")