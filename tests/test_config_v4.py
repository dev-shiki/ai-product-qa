import pytest
import os
from unittest.mock import patch, MagicMock

# Import the module under test
# Assuming the test file is test_utils/config.py and the source is app/utils/config.py
# Adjust import path if directory structure differs
from app.utils import config 

# --- Fixtures ---

@pytest.fixture(autouse=True)
def clear_settings_cache():
    """
    Clears the lru_cache for get_settings before and after each test.
    This ensures that each test for get_settings starts with a clean cache,
    preventing test interference due to caching.
    """
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear() # Clear again after test for good measure


@pytest.fixture
def mock_google_api_key(monkeypatch):
    """
    Fixture to set a valid GOOGLE_API_KEY environment variable.
    Uses monkeypatch to manage environment variables safely for the test's scope.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key-123-valid")
    yield
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False) # Clean up after test


@pytest.fixture
def unset_google_api_key(monkeypatch):
    """
    Fixture to ensure the GOOGLE_API_KEY environment variable is not set.
    """
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)


@pytest.fixture
def empty_google_api_key(monkeypatch):
    """
    Fixture to set the GOOGLE_API_KEY environment variable to an empty string.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "")


@pytest.fixture
def default_google_api_key(monkeypatch):
    """
    Fixture to set the GOOGLE_API_KEY environment variable to its default placeholder value.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")


# --- Test Classes ---

class TestSettings:
    """
    Comprehensive tests for the Settings class.
    """

    def test_settings_initialization_success(self, mock_google_api_key):
        """
        GIVEN a valid GOOGLE_API_KEY is set in the environment.
        WHEN the Settings class is initialized without specific overrides.
        THEN it should successfully create a Settings instance with expected default values
             and the provided API key.
        """
        settings = config.Settings()
        assert isinstance(settings, config.Settings)
        assert settings.GOOGLE_API_KEY == "test-api-key-123-valid"
        assert settings.API_HOST == "localhost"
        assert settings.API_PORT == 8000
        assert settings.FRONTEND_HOST == "localhost"
        assert settings.FRONTEND_PORT == 8501
        assert settings.DEBUG is True

    def test_settings_initialization_with_overrides(self, mock_google_api_key):
        """
        GIVEN a valid GOOGLE_API_KEY is set and specific configuration overrides are provided.
        WHEN the Settings class is initialized with keyword arguments.
        THEN it should create a Settings instance with the overrides applied,
             while other values remain at their defaults.
        """
        settings = config.Settings(
            API_HOST="192.168.1.1",
            API_PORT=9090,
            FRONTEND_HOST="example.com",
            FRONTEND_PORT=3000,
            DEBUG=False
        )
        assert settings.GOOGLE_API_KEY == "test-api-key-123-valid"
        assert settings.API_HOST == "192.168.1.1"
        assert settings.API_PORT == 9090
        assert settings.FRONTEND_HOST == "example.com"
        assert settings.FRONTEND_PORT == 3000
        assert settings.DEBUG is False

    @patch.object(config.logger, 'error') # Patch the specific logger instance used in the module
    def test_settings_initialization_no_google_api_key_raises_error(self, mock_error_logger, unset_google_api_key):
        """
        GIVEN GOOGLE_API_KEY is not set in the environment.
        WHEN the Settings class is initialized.
        THEN it should raise a ValueError and log an appropriate error message.
        """
        with pytest.raises(ValueError) as excinfo:
            config.Settings()
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        mock_error_logger.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

    @patch.object(config.logger, 'error')
    def test_settings_initialization_empty_google_api_key_raises_error(self, mock_error_logger, empty_google_api_key):
        """
        GIVEN GOOGLE_API_KEY is set to an empty string.
        WHEN the Settings class is initialized.
        THEN it should raise a ValueError and log an appropriate error message.
        """
        with pytest.raises(ValueError) as excinfo:
            config.Settings()
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        mock_error_logger.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

    @patch.object(config.logger, 'error')
    def test_settings_initialization_default_google_api_key_raises_error(self, mock_error_logger, default_google_api_key):
        """
        GIVEN GOOGLE_API_KEY is set to its default placeholder value ("your-google-api-key-here").
        WHEN the Settings class is initialized.
        THEN it should raise a ValueError and log an appropriate error message.
        """
        with pytest.raises(ValueError) as excinfo:
            config.Settings()
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        mock_error_logger.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")


class TestGetSettings:
    """
    Comprehensive tests for the get_settings function, including lru_cache behavior.
    """

    def test_get_settings_returns_settings_instance(self, mock_google_api_key):
        """
        GIVEN a valid GOOGLE_API_KEY is set.
        WHEN get_settings is called for the first time.
        THEN it should return a valid instance of Settings.
        """
        settings_instance = config.get_settings()
        assert isinstance(settings_instance, config.Settings)
        assert settings_instance.GOOGLE_API_KEY == "test-api-key-123-valid"

    def test_get_settings_uses_cache(self, mock_google_api_key):
        """
        GIVEN get_settings has been called once and cached the Settings instance.
        WHEN get_settings is called again.
        THEN it should return the exact same cached instance (object identity).
        """
        first_call_settings = config.get_settings()
        second_call_settings = config.get_settings()

        assert first_call_settings is second_call_settings
        assert id(first_call_settings) == id(second_call_settings)
        # Verify the cache info
        cache_info = config.get_settings.cache_info()
        assert cache_info.hits == 1
        assert cache_info.misses == 1

    @patch.object(config, 'Settings', wraps=config.Settings) # Use wraps to call original constructor but track calls
    def test_get_settings_calls_settings_constructor_once_due_to_cache(self, mock_settings_class, mock_google_api_key):
        """
        GIVEN get_settings is called multiple times.
        WHEN the Settings constructor is mocked to track calls.
        THEN the Settings constructor should only be called once, due to lru_cache.
        """
        # Call it multiple times to ensure cache is hit on subsequent calls
        config.get_settings()
        config.get_settings()
        config.get_settings()

        # The Settings constructor should only be called for the very first get_settings() call
        mock_settings_class.assert_called_once()
        cache_info = config.get_settings.cache_info()
        assert cache_info.hits == 2 # 2 hits after the first miss
        assert cache_info.misses == 1 # Only 1 miss for the initial call

    @patch.object(config.logger, 'error')
    def test_get_settings_propagates_value_error_from_settings(self, mock_error_logger, unset_google_api_key):
        """
        GIVEN GOOGLE_API_KEY is not set (causing Settings initialization to fail).
        WHEN get_settings is called.
        THEN it should propagate the ValueError raised by the Settings constructor.
        """
        with pytest.raises(ValueError) as excinfo:
            config.get_settings()
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        mock_error_logger.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")


class TestGlobalSettingsVariable:
    """
    Tests for the module-level global 'settings' variable.
    """

    def test_global_settings_variable_is_settings_instance(self, mock_google_api_key):
        """
        GIVEN the app.utils.config module has been imported (which initializes the global settings).
        WHEN the 'config.settings' variable is accessed.
        THEN it should be a valid instance of the Settings class.

        Note: The global 'settings' variable is initialized *once* when the module is imported.
        To ensure its successful initialization for testing, a valid GOOGLE_API_KEY must be
        set in the environment *before* pytest imports this module for the first time.
        The `mock_google_api_key` fixture helps establish this environment.
        """
        assert isinstance(config.settings, config.Settings)
        assert config.settings.GOOGLE_API_KEY == "test-api-key-123-valid"
        assert config.settings.API_HOST == "localhost" # Ensure it retains default values