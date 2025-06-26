import pytest
import os
import logging
from unittest.mock import patch, MagicMock
from functools import lru_cache

# Import the module under test.
# The global 'settings' variable in app/utils/config.py is initialized
# when this module is first imported by pytest. Its state depends on the
# environment variables present at that exact moment.
# For robust testing of its initial state, ensure `GOOGLE_API_KEY` is set
# in your test environment (e.g., via `pytest --import-mode=importlib` or by setting
# the environment variable before running pytest, e.g., `GOOGLE_API_KEY=dummy pytest`).
from app.utils.config import Settings, get_settings, logger as app_logger, settings as global_settings_instance


@pytest.fixture(scope="function")
def clear_settings_cache_for_test():
    """
    Fixture to clear the lru_cache for get_settings before and after each test.
    This ensures that each test calling `get_settings()` receives a fresh instance
    based on the current environment variables, enabling isolated testing of `get_settings()`.
    """
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(scope="function")
def mock_logger():
    """
    Fixture to mock the specific logger instance used in app/utils/config.py.
    This allows us to check if error messages are logged during validation failures.
    `autospec=True` ensures the mock has the same methods as the original object.
    """
    with patch('app.utils.config.logging.getLogger', autospec=True) as mock_get_logger:
        # Configure the mock to return a mock logger instance
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance


class TestSettings:
    """
    Comprehensive test suite for the `Settings` class, covering initialization,
    default values, environment variable loading, keyword argument overrides,
    and validation logic for `GOOGLE_API_KEY`.
    """

    def test_settings_valid_initialization_from_env(self, monkeypatch, mock_logger, clear_settings_cache_for_test):
        """
        Test that `Settings` correctly initializes when all fields are provided
        via environment variables, including type conversions (e.g., int, bool).
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "env-api-key-123")
        monkeypatch.setenv("API_HOST", "api.example.com")
        monkeypatch.setenv("API_PORT", "9001")
        monkeypatch.setenv("FRONTEND_HOST", "frontend.example.com")
        monkeypatch.setenv("FRONTEND_PORT", "8502")
        monkeypatch.setenv("DEBUG", "False")

        settings = Settings()

        assert settings.GOOGLE_API_KEY == "env-api-key-123"
        assert settings.API_HOST == "api.example.com"
        assert settings.API_PORT == 9001
        assert settings.FRONTEND_HOST == "frontend.example.com"
        assert settings.FRONTEND_PORT == 8502
        assert settings.DEBUG is False
        mock_logger.error.assert_not_called()

    def test_settings_valid_initialization_from_kwargs(self, mock_logger, clear_settings_cache_for_test):
        """
        Test that `Settings` correctly initializes when fields are provided
        as keyword arguments, and defaults are used for unprovided ones.
        """
        settings = Settings(
            GOOGLE_API_KEY="kwarg-api-key-456",
            API_HOST="kwarg-api.test",
            API_PORT=9003
        )

        assert settings.GOOGLE_API_KEY == "kwarg-api-key-456"
        assert settings.API_HOST == "kwarg-api.test"
        assert settings.API_PORT == 9003
        # Verify that default values are maintained for attributes not provided
        assert settings.FRONTEND_HOST == "localhost"
        assert settings.FRONTEND_PORT == 8501
        assert settings.DEBUG is True
        mock_logger.error.assert_not_called()

    def test_settings_default_values_are_applied(self, monkeypatch, mock_logger, clear_settings_cache_for_test):
        """
        Test that `Settings` correctly uses its predefined default values
        when corresponding environment variables or kwargs are not provided.
        `GOOGLE_API_KEY` is explicitly set to satisfy validation.
        """
        # Ensure only GOOGLE_API_KEY is set to avoid validation error, others should default
        monkeypatch.setenv("GOOGLE_API_KEY", "valid-key-for-defaults")
        # Explicitly remove other env vars if they might persist from other tests
        for var in ["API_HOST", "API_PORT", "FRONTEND_HOST", "FRONTEND_PORT", "DEBUG"]:
            if var in os.environ:
                monkeypatch.delenv(var)

        settings = Settings()

        assert settings.GOOGLE_API_KEY == "valid-key-for-defaults"
        assert settings.API_HOST == "localhost"
        assert settings.API_PORT == 8000
        assert settings.FRONTEND_HOST == "localhost"
        assert settings.FRONTEND_PORT == 8501
        assert settings.DEBUG is True
        mock_logger.error.assert_not_called()

    def test_settings_raises_value_error_if_google_api_key_missing(self, monkeypatch, mock_logger, clear_settings_cache_for_test):
        """
        Test that `Settings` raises a `ValueError` and logs an error
        when `GOOGLE_API_KEY` is not set in the environment or kwargs.
        """
        # Ensure GOOGLE_API_KEY is not present in the environment for this test
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
            Settings()

        mock_logger.error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

    def test_settings_raises_value_error_if_google_api_key_empty(self, monkeypatch, mock_logger, clear_settings_cache_for_test):
        """
        Test that `Settings` raises a `ValueError` and logs an error
        when `GOOGLE_API_KEY` is explicitly set to an empty string.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "")

        with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
            Settings()

        mock_logger.error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

    def test_settings_raises_value_error_if_google_api_key_is_placeholder(self, monkeypatch, mock_logger, clear_settings_cache_for_test):
        """
        Test that `Settings` raises a `ValueError` and logs an error
        when `GOOGLE_API_KEY` is set to the default placeholder value.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")

        with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
            Settings()

        mock_logger.error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

    def test_settings_pydantic_validation_error_propagation(self, monkeypatch, mock_logger, clear_settings_cache_for_test):
        """
        Test that `pydantic-settings`'s underlying validation errors (e.g., type coercion failures)
        are propagated correctly, ensuring the `super().__init__` call behaves as expected.
        """
        # Set a valid GOOGLE_API_KEY to bypass our custom validation
        monkeypatch.setenv("GOOGLE_API_KEY", "valid-key")
        # Introduce a type mismatch for an integer field to trigger pydantic's validation
        monkeypatch.setenv("API_PORT", "not-an-integer")

        # pydantic will raise a ValidationError (or a wrapper around it)
        with pytest.raises(Exception) as excinfo:
            Settings()

        # Check if the exception message contains typical pydantic validation error indicators
        assert "validation error" in str(excinfo.value).lower()
        # Our custom error logging should not be called in this scenario
        mock_logger.error.assert_not_called()


class TestGetSettings:
    """
    Comprehensive test suite for the `get_settings()` function,
    focusing on its instantiation of `Settings`, `lru_cache` behavior,
    and error propagation.
    """

    def test_get_settings_returns_settings_instance(self, monkeypatch, mock_logger, clear_settings_cache_for_test):
        """
        Verify that `get_settings()` correctly returns an instance of `Settings`.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "key-for-get-settings-test")
        settings_instance = get_settings()
        assert isinstance(settings_instance, Settings)
        assert settings_instance.GOOGLE_API_KEY == "key-for-get-settings-test"
        mock_logger.error.assert_not_called()

    def test_get_settings_lru_cache_behavior(self, monkeypatch, mock_logger, clear_settings_cache_for_test):
        """
        Test that `get_settings()` utilizes `lru_cache`, returning the same instance
        on subsequent calls until the cache is cleared.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "lru-cache-test-key")

        first_settings = get_settings()
        second_settings = get_settings()

        # Both calls should return the exact same object due to caching
        assert first_settings is second_settings
        assert first_settings.GOOGLE_API_KEY == "lru-cache-test-key"
        mock_logger.error.assert_not_called()

        # Verify that clearing the cache allows a new instance to be created
        clear_settings_cache_for_test()  # This fixture ensures cache is cleared for fresh start
        monkeypatch.setenv("GOOGLE_API_KEY", "new-lru-cache-test-key")
        third_settings = get_settings()

        # The third instance should be different from the first two
        assert first_settings is not third_settings
        assert third_settings.GOOGLE_API_KEY == "new-lru-cache-test-key"
        mock_logger.error.assert_not_called()

    def test_get_settings_propagates_settings_init_error(self, monkeypatch, mock_logger, clear_settings_cache_for_test):
        """
        Test that `get_settings()` correctly propagates the `ValueError`
        raised by `Settings.__init__` when `GOOGLE_API_KEY` is invalid.
        """
        # Set an empty GOOGLE_API_KEY to trigger the validation error within Settings.__init__
        monkeypatch.setenv("GOOGLE_API_KEY", "")

        with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
            get_settings()

        mock_logger.error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")


class TestGlobalSettingsInstance:
    """
    Tests for the globally initialized 'settings' variable (defined as `settings = get_settings()`).
    Note: This variable is initialized once when `app/utils/config.py` is first imported.
    Its content depends on the environment at that exact moment of import.
    These tests verify its type and that it references a `Settings` object.
    """

    def test_global_settings_instance_type(self, mock_logger):
        """
        Verify that the `global_settings_instance` is indeed an instance of `Settings`.
        This test implicitly relies on `app/utils/config.py` being able to load
        successfully during the test session setup (i.e., GOOGLE_API_KEY was valid
        when the module was first imported).
        """
        assert isinstance(global_settings_instance, Settings)
        # We cannot reliably assert the specific GOOGLE_API_KEY value here
        # as it depends on the environment at the moment of initial module load,
        # which is outside the scope of individual test function fixtures.
        mock_logger.error.assert_not_called()