import pytest
import os
import logging
import sys

# Import the module under test
# We import get_settings and Settings directly.
# The global 'settings' instance will be re-imported in a specific test to ensure its initialization is tested.
from app.utils.config import Settings, get_settings

@pytest.fixture(autouse=True)
def clear_settings_cache_and_env(monkeypatch):
    """
    Fixture to clear the lru_cache for get_settings before each test
    and ensure a clean environment for GOOGLE_API_KEY.
    This runs automatically for all tests.
    """
    get_settings.cache_clear()
    # Ensure GOOGLE_API_KEY is unset by default for most tests,
    # and explicitly set it when needed.
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    # Also unset other environment variables to ensure defaults are picked up
    # unless explicitly set by a test.
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("FRONTEND_HOST", raising=False)
    monkeypatch.delenv("FRONTEND_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    # For tests that need to re-import the module to test global state
    # yield allows the test to run, then this finalizer cleans up.
    yield
    # Clean up sys.modules if it was modified for re-import tests
    if 'app.utils.config' in sys.modules:
        # Restore a clean state for subsequent tests if a re-import happened
        # This is particularly important for test_global_settings_instance
        del sys.modules['app.utils.config']


@pytest.fixture
def set_valid_google_api_key(monkeypatch):
    """Fixture to set a valid GOOGLE_API_KEY."""
    monkeypatch.setenv("GOOGLE_API_KEY", "valid-test-key-123")

@pytest.fixture
def mock_all_env_vars(monkeypatch):
    """Fixture to set all environment variables to non-default values."""
    monkeypatch.setenv("GOOGLE_API_KEY", "full-test-key")
    monkeypatch.setenv("API_HOST", "my-api.test")
    monkeypatch.setenv("API_PORT", "9001")
    monkeypatch.setenv("FRONTEND_HOST", "my-frontend.test")
    monkeypatch.setenv("FRONTEND_PORT", "9502")
    monkeypatch.setenv("DEBUG", "False")

class TestSettings:
    """Comprehensive tests for the Settings class."""

    def test_settings_initialization_success_with_minimal_env(self, set_valid_google_api_key):
        """
        GIVEN only GOOGLE_API_KEY is set in environment variables
        WHEN Settings is initialized
        THEN it should initialize successfully with default values for other fields.
        """
        settings = Settings()

        assert settings.GOOGLE_API_KEY == "valid-test-key-123"
        assert settings.API_HOST == "localhost"
        assert settings.API_PORT == 8000
        assert settings.FRONTEND_HOST == "localhost"
        assert settings.FRONTEND_PORT == 8501
        assert settings.DEBUG is True

    def test_settings_initialization_success_with_all_env_vars_overridden(self, mock_all_env_vars):
        """
        GIVEN all configurable environment variables are set
        WHEN Settings is initialized
        THEN it should initialize successfully with all values overridden from env.
        """
        settings = Settings()

        assert settings.GOOGLE_API_KEY == "full-test-key"
        assert settings.API_HOST == "my-api.test"
        assert settings.API_PORT == 9001
        assert settings.FRONTEND_HOST == "my-frontend.test"
        assert settings.FRONTEND_PORT == 9502
        assert settings.DEBUG is False

    def test_settings_initialization_failure_missing_google_api_key(self, caplog):
        """
        GIVEN GOOGLE_API_KEY is not set in environment variables
        WHEN Settings is initialized
        THEN it should raise a ValueError and log an error message.
        """
        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError) as excinfo:
                Settings()

            assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
            assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text
            assert caplog.records[0].levelname == "ERROR"

    def test_settings_initialization_failure_default_google_api_key_value(self, monkeypatch, caplog):
        """
        GIVEN GOOGLE_API_KEY is set to its default placeholder value
        WHEN Settings is initialized
        THEN it should raise a ValueError and log an error message.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError) as excinfo:
                Settings()

            assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
            assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text
            assert caplog.records[0].levelname == "ERROR"

    def test_settings_initialization_with_kwargs_override_env(self, monkeypatch):
        """
        GIVEN environment variables are set and kwargs are provided
        WHEN Settings is initialized with kwargs
        THEN kwargs should take precedence over environment variables.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "env-key")
        monkeypatch.setenv("API_HOST", "env-api-host")
        monkeypatch.setenv("API_PORT", "1234")

        settings = Settings(GOOGLE_API_KEY="kwargs-key", API_HOST="kwargs-api-host")

        assert settings.GOOGLE_API_KEY == "kwargs-key"
        assert settings.API_HOST == "kwargs-api-host"
        assert settings.API_PORT == 8000  # Not provided in kwargs, so default
        assert settings.FRONTEND_HOST == "localhost" # Default
        assert settings.FRONTEND_PORT == 8501 # Default
        assert settings.DEBUG is True # Default

    def test_settings_initialization_with_kwargs_only(self):
        """
        GIVEN GOOGLE_API_KEY is provided only via kwargs (no env var set)
        WHEN Settings is initialized with kwargs
        THEN it should initialize successfully.
        """
        settings = Settings(GOOGLE_API_KEY="kwargs-only-key")
        assert settings.GOOGLE_API_KEY == "kwargs-only-key"
        assert settings.API_HOST == "localhost" # Default

class TestGetSettings:
    """Comprehensive tests for the get_settings function and its caching."""

    def test_get_settings_returns_settings_instance(self, set_valid_google_api_key):
        """
        GIVEN get_settings is called with a valid GOOGLE_API_KEY in environment
        WHEN the function is executed
        THEN it should return an instance of Settings.
        """
        s = get_settings()
        assert isinstance(s, Settings)
        assert s.GOOGLE_API_KEY == "valid-test-key-123"

    def test_get_settings_caches_instance_on_subsequent_calls(self, monkeypatch):
        """
        GIVEN get_settings is called multiple times
        WHEN environment variables change between calls (after the first call)
        THEN it should return the same cached instance on subsequent calls,
             reflecting the environment at the time of the *first* call.
        """
        # Set initial environment variables
        monkeypatch.setenv("GOOGLE_API_KEY", "initial-key")
        monkeypatch.setenv("API_PORT", "1000")
        monkeypatch.setenv("DEBUG", "True")

        initial_settings = get_settings()

        # Change environment variables AFTER the first call
        monkeypatch.setenv("GOOGLE_API_KEY", "changed-key")
        monkeypatch.setenv("API_PORT", "2000")
        monkeypatch.setenv("DEBUG", "False")

        subsequent_settings = get_settings()

        # Assert that the same object instance is returned due to lru_cache
        assert initial_settings is subsequent_settings

        # Assert that the values reflect the environment at the time of the *initial* call
        assert subsequent_settings.GOOGLE_API_KEY == "initial-key"
        assert subsequent_settings.API_PORT == 1000
        assert subsequent_settings.DEBUG is True

    def test_get_settings_with_missing_key_after_cache_clear(self, monkeypatch, caplog):
        """
        GIVEN get_settings cache is cleared (by autouse fixture)
        AND GOOGLE_API_KEY is not set
        WHEN get_settings is called
        THEN it should raise ValueError and log an error.
        """
        # No need to explicitly clear cache here, autouse fixture handles it.
        # monkeypatch.delenv("GOOGLE_API_KEY", raising=False) is also handled by autouse fixture.

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError) as excinfo:
                get_settings()

            assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
            assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text

    def test_global_settings_instance_initialization(self, monkeypatch):
        """
        Tests that the global 'settings' instance is correctly initialized
        based on the environment variables present at module import time.
        This requires re-importing the module to simulate its initial load.
        """
        # Ensure a valid key and other values are set for the module load time
        monkeypatch.setenv("GOOGLE_API_KEY", "global-init-key")
        monkeypatch.setenv("API_HOST", "global-init-host")
        monkeypatch.setenv("API_PORT", "9999")
        monkeypatch.setenv("DEBUG", "False")

        # To properly test the global 'settings' instance's initial state,
        # we need to simulate a fresh import of the module.
        # Remove the module from sys.modules to force a fresh import.
        if 'app.utils.config' in sys.modules:
            del sys.modules['app.utils.config']
        
        # Re-import the module to get a fresh global_settings instance
        from app.utils.config import settings as reloaded_global_settings

        assert isinstance(reloaded_global_settings, Settings)
        assert reloaded_global_settings.GOOGLE_API_KEY == "global-init-key"
        assert reloaded_global_settings.API_HOST == "global-init-host"
        assert reloaded_global_settings.API_PORT == 9999
        assert reloaded_global_settings.DEBUG is False
        assert reloaded_global_settings.FRONTEND_HOST == "localhost" # Default

        # Verify that get_settings() also returns this same instance if called again,
        # as the initial call to get_settings() was cached as the global 'settings' instance.
        # (This assumes the clear_settings_cache_and_env fixture runs after this test setup,
        # or that we're within the same 'session' of the get_settings cache).
        # Since clear_settings_cache_and_env is autouse, it would have cleared before *this* test started.
        # So, the reloaded_global_settings *is* the first cached object.
        # Subsequent calls to get_settings() without clearing the cache again would return this.
        
        # Change environment variables to confirm the global instance is cached and doesn't change
        monkeypatch.setenv("GOOGLE_API_KEY", "changed-global-key")
        monkeypatch.setenv("API_HOST", "changed-global-host")

        # The reloaded_global_settings should *not* change, as it's a cached instance
        assert reloaded_global_settings.GOOGLE_API_KEY == "global-init-key"
        assert reloaded_global_settings.API_HOST == "global-init-host"

        # Calling get_settings() again should return the same cached instance
        another_settings_call = get_settings()
        assert another_settings_call is reloaded_global_settings