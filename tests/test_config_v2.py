import pytest
import os
import logging
from unittest.mock import patch
from pydantic import ValidationError

# Import the module to be tested.
# The `settings = get_settings()` line in app.utils.config will execute upon import.
# Autouse fixtures will ensure the environment is correctly set up for this initial import.
from app.utils.config import Settings, get_settings, settings as module_settings, logger


@pytest.fixture(autouse=True)
def quiet_logger_for_module():
    """
    Sets the logging level for the config module to CRITICAL to suppress
    INFO/ERROR messages during most tests, unless caplog is explicitly used.
    Resets the level after the test.
    """
    original_level = logger.level
    logger.setLevel(logging.CRITICAL)
    yield
    logger.setLevel(original_level)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """
    Clears the lru_cache for get_settings before and after each test.
    This ensures that each test involving `get_settings()` starts with a fresh cache.
    """
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """
    Sets up common environment variables for tests.
    `autouse=True` ensures these are set before any test runs, including the initial
    import of `app.utils.config` (which triggers `settings = get_settings()`).
    """
    # Default valid API key for successful module load and most tests
    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key-123")
    # Set other optional variables to ensure they are read correctly
    monkeypatch.setenv("API_HOST", "test-host")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("FRONTEND_HOST", "test-frontend-host")
    monkeypatch.setenv("FRONTEND_PORT", "9500")
    monkeypatch.setenv("DEBUG", "False")
    yield
    # Clean up environment variables after the test
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("FRONTEND_HOST", raising=False)
    monkeypatch.delenv("FRONTEND_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)


class TestSettings:
    """Comprehensive tests for the Settings class and its initialization."""

    def test_settings_init_success_with_all_env_vars(self):
        """
        Test that Settings initializes successfully with valid environment variables,
        overriding all default values. `mock_env_vars` fixture provides these.
        """
        settings_instance = Settings()
        assert settings_instance.GOOGLE_API_KEY == "test-api-key-123"
        assert settings_instance.API_HOST == "test-host"
        assert settings_instance.API_PORT == 9000
        assert settings_instance.FRONTEND_HOST == "test-frontend-host"
        assert settings_instance.FRONTEND_PORT == 9500
        assert settings_instance.DEBUG is False

    def test_settings_init_success_with_default_values(self, monkeypatch):
        """
        Test that Settings initializes successfully using default values
        when optional environment variables are not set.
        """
        # Ensure GOOGLE_API_KEY is present for successful initialization
        monkeypatch.setenv("GOOGLE_API_KEY", "another-valid-key")
        # Unset optional environment variables to check for default values
        monkeypatch.delenv("API_HOST", raising=False)
        monkeypatch.delenv("API_PORT", raising=False)
        monkeypatch.delenv("FRONTEND_HOST", raising=False)
        monkeypatch.delenv("FRONTEND_PORT", raising=False)
        monkeypatch.delenv("DEBUG", raising=False)

        settings_instance = Settings()
        assert settings_instance.GOOGLE_API_KEY == "another-valid-key"
        assert settings_instance.API_HOST == "localhost"
        assert settings_instance.API_PORT == 8000
        assert settings_instance.FRONTEND_HOST == "localhost"
        assert settings_instance.FRONTEND_PORT == 8501
        assert settings_instance.DEBUG is True  # Default value for DEBUG

    def test_settings_init_fail_pydantic_validation_error_missing_key(self, monkeypatch):
        """
        Test that `Settings` raises `pydantic.ValidationError` when `GOOGLE_API_KEY` is
        completely missing from the environment, as it's a required field by Pydantic's `BaseSettings`.
        This tests Pydantic's validation behavior *before* `Settings`'s custom `__init__` logic.
        """
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)  # Ensure it's not set
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        # Verify the error message indicates a missing required field
        assert "field required" in str(exc_info.value).lower()
        assert "google_api_key" in str(exc_info.value).lower()

    def test_settings_init_fail_empty_google_api_key(self, monkeypatch, caplog):
        """
        Test that `Settings` raises `ValueError` from its custom `__init__`
        when `GOOGLE_API_KEY` is explicitly set to an empty string.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "")
        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError) as exc_info:
                Settings()
            assert "GOOGLE_API_KEY must be set in .env file" in str(exc_info.value)
            assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text

    def test_settings_init_fail_placeholder_google_api_key(self, monkeypatch, caplog):
        """
        Test that `Settings` raises `ValueError` from its custom `__init__`
        when `GOOGLE_API_KEY` is the default placeholder string.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")
        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError) as exc_info:
                Settings()
            assert "GOOGLE_API_KEY must be set in .env file" in str(exc_info.value)
            assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text

    def test_settings_init_with_kwargs_override_and_validation(self, monkeypatch):
        """
        Test that Settings can be initialized with keyword arguments, which
        should override environment variables, and that custom validation still applies.
        """
        # Set a placeholder in env, but provide a valid one via kwargs
        monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")
        settings_instance = Settings(GOOGLE_API_KEY="valid-key-from-kwargs")
        assert settings_instance.GOOGLE_API_KEY == "valid-key-from-kwargs"
        # No ValueError should be raised because kwargs provide a valid key

        # Test that custom validation still triggers for invalid kwargs
        with pytest.raises(ValueError):
            Settings(GOOGLE_API_KEY="")

        with pytest.raises(ValueError):
            Settings(GOOGLE_API_KEY="your-google-api-key-here")

        # Test that kwargs take precedence over environment variables (Pydantic's default behavior)
        monkeypatch.setenv("GOOGLE_API_KEY", "env-key")
        settings_instance_kwarg_preferred = Settings(GOOGLE_API_KEY="kwarg-key")
        assert settings_instance_kwarg_preferred.GOOGLE_API_KEY == "kwarg-key"


class TestGetSettings:
    """Tests for the get_settings function and its lru_cache behavior."""

    def test_get_settings_returns_settings_instance(self):
        """
        Test that get_settings returns an instance of Settings.
        The `mock_env_vars` autouse fixture ensures a valid environment for instantiation.
        """
        settings_instance = get_settings()
        assert isinstance(settings_instance, Settings)
        assert settings_instance.GOOGLE_API_KEY == "test-api-key-123"

    def test_get_settings_is_cached(self):
        """
        Test that get_settings uses lru_cache, returning the same instance
        on subsequent calls and not re-initializing Settings.
        """
        # Patch the Settings constructor to verify it's called only once
        with patch('app.utils.config.Settings', wraps=Settings) as mock_settings_cls:
            first_call = get_settings()
            second_call = get_settings()

            # Assert that the Settings constructor was called exactly once
            mock_settings_cls.assert_called_once()
            # Assert that the same object is returned from the cache
            assert first_call is second_call

            # Verify the content of the cached settings
            assert first_call.GOOGLE_API_KEY == "test-api-key-123"

    def test_get_settings_reflects_env_after_cache_clear(self, monkeypatch):
        """
        Test that after environment variables are changed and the cache is cleared,
        get_settings reflects the new environment on a subsequent call.
        (Cache clearing is handled by the `clear_settings_cache` autouse fixture).
        """
        # First, ensure an initial state with a specific key.
        # `mock_env_vars` autouse fixture provides "test-api-key-123".
        initial_settings = get_settings()
        assert initial_settings.GOOGLE_API_KEY == "test-api-key-123"

        # Change the environment variable. The `clear_settings_cache` autouse fixture
        # will ensure the cache is cleared before the next `get_settings()` call.
        monkeypatch.setenv("GOOGLE_API_KEY", "new-key-after-env-change")

        # Call get_settings() again; it should re-initialize with the new key
        new_settings = get_settings()
        assert new_settings.GOOGLE_API_KEY == "new-key-after-env-change"
        assert initial_settings is not new_settings  # Should be a different instance because cache was cleared


class TestModuleLevelSettings:
    """Tests for the module-level 'settings' instance."""

    def test_module_level_settings_instance_exists_and_is_valid(self):
        """
        Test that the module-level `settings` instance is correctly initialized
        upon module import and is an instance of `Settings`.
        The `mock_env_vars` autouse fixture ensures `GOOGLE_API_KEY` is valid during module import.
        """
        assert isinstance(module_settings, Settings)
        assert module_settings.GOOGLE_API_KEY == "test-api-key-123"
        assert module_settings.API_HOST == "test-host"
        assert module_settings.API_PORT == 9000

    def test_module_level_settings_uses_cache_from_initial_load(self):
        """
        Test that calling `get_settings()` after the module has loaded returns
        the same cached instance as the module-level `settings` variable.
        This confirms the cache mechanism for the initial module load.
        """
        # `module_settings` is already initialized via `get_settings()` when the module is imported.
        # Calling `get_settings()` again should return the same cached instance.
        retrieved_settings = get_settings()
        assert retrieved_settings is module_settings
        assert retrieved_settings.GOOGLE_API_KEY == "test-api-key-123"