import pytest
import os
import logging
from unittest.mock import patch

# Dynamically import the module under test
# This assumes the test is run from the project root or python path is set
try:
    from app.utils import config
except ImportError:
    # Fallback for environments where app is not directly in path, e.g., CI or specific IDE setups
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.utils import config

# --- Fixtures ---

@pytest.fixture(autouse=True)
def clear_get_settings_cache():
    """
    Clears the lru_cache for the get_settings function before and after each test.
    This ensures that each test gets a fresh, un-cached instance of Settings
    unless explicitly testing the cache behavior.
    """
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()

@pytest.fixture(autouse=True)
def set_default_valid_api_key_and_env_vars(monkeypatch):
    """
    Sets a default valid GOOGLE_API_KEY and other environment variables
    for most tests to ensure successful module import and Settings initialization.
    These values can be overridden within specific test cases.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key-123")
    monkeypatch.setenv("API_HOST", "test-host")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("FRONTEND_HOST", "test-frontend-host")
    monkeypatch.setenv("FRONTEND_PORT", "9500")
    monkeypatch.setenv("DEBUG", "False")


# --- Test Cases for Settings Class ---

class TestSettings:
    """
    Tests for the Settings Pydantic model initialization and validation.
    """

    def test_settings_initialization_success(self):
        """
        Verify that Settings initializes correctly when all required environment variables
        are provided and valid.
        """
        # Environment variables are set by the autouse fixture `set_default_valid_api_key_and_env_vars`
        settings_instance = config.Settings()

        assert settings_instance.GOOGLE_API_KEY == "test-api-key-123"
        assert settings_instance.API_HOST == "test-host"
        assert settings_instance.API_PORT == 9000
        assert settings_instance.FRONTEND_HOST == "test-frontend-host"
        assert settings_instance.FRONTEND_PORT == 9500
        assert settings_instance.DEBUG is False

    def test_settings_initialization_with_default_values(self, monkeypatch):
        """
        Verify that Settings initializes correctly, using default values for optional
        attributes when their corresponding environment variables are not set.
        GOOGLE_API_KEY must still be provided.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "some-other-key")
        monkeypatch.delenv("API_HOST", raising=False)
        monkeypatch.delenv("API_PORT", raising=False)
        monkeypatch.delenv("FRONTEND_HOST", raising=False)
        monkeypatch.delenv("FRONTEND_PORT", raising=False)
        monkeypatch.delenv("DEBUG", raising=False)

        settings_instance = config.Settings()

        assert settings_instance.GOOGLE_API_KEY == "some-other-key"
        assert settings_instance.API_HOST == "localhost"
        assert settings_instance.API_PORT == 8000
        assert settings_instance.FRONTEND_HOST == "localhost"
        assert settings_instance.FRONTEND_PORT == 8501
        assert settings_instance.DEBUG is True

    def test_settings_initialization_raises_error_when_api_key_missing(self, monkeypatch, caplog):
        """
        Test that a ValueError is raised and an error log is recorded when
        GOOGLE_API_KEY is not set in the environment.
        """
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError) as excinfo:
                config.Settings()

            assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
            assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text

    def test_settings_initialization_raises_error_when_api_key_is_default_placeholder(self, monkeypatch, caplog):
        """
        Test that a ValueError is raised and an error log is recorded when
        GOOGLE_API_KEY is set to its default placeholder value.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError) as excinfo:
                config.Settings()

            assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
            assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text

    def test_settings_initialization_kwargs_override_env_vars(self):
        """
        Verify that keyword arguments passed during Settings instantiation
        take precedence over environment variables.
        """
        # Environment variables are already set by the autouse fixture
        settings_instance = config.Settings(
            GOOGLE_API_KEY="kwarg-api-key",
            API_HOST="kwarg-host",
            API_PORT=1234,
            FRONTEND_HOST="kwarg-f-host",
            FRONTEND_PORT=5678,
            DEBUG=False
        )
        assert settings_instance.GOOGLE_API_KEY == "kwarg-api-key"
        assert settings_instance.API_HOST == "kwarg-host"
        assert settings_instance.API_PORT == 1234
        assert settings_instance.FRONTEND_HOST == "kwarg-f-host"
        assert settings_instance.FRONTEND_PORT == 5678
        assert settings_instance.DEBUG is False


# --- Test Cases for get_settings Function ---

class TestGetSettings:
    """
    Tests for the get_settings function, including its lru_cache behavior.
    """

    def test_get_settings_returns_settings_instance(self):
        """
        Verify that get_settings successfully returns an instance of the Settings class.
        """
        settings_instance = config.get_settings()
        assert isinstance(settings_instance, config.Settings)
        assert settings_instance.GOOGLE_API_KEY == "test-api-key-123"

    def test_get_settings_is_cached(self, monkeypatch):
        """
        Verify that get_settings utilizes lru_cache, returning the same Settings
        instance on subsequent calls even if environment variables change.
        """
        # First call populates the cache
        first_settings_instance = config.get_settings()
        first_id = id(first_settings_instance)
        assert first_settings_instance.GOOGLE_API_KEY == "test-api-key-123"

        # Change environment variable - this should NOT affect the cached instance
        monkeypatch.setenv("GOOGLE_API_KEY", "new-key-should-be-ignored-due-to-cache")
        monkeypatch.setenv("API_HOST", "new-host-should-be-ignored-due-to-cache")

        # Second call should retrieve from cache
        second_settings_instance = config.get_settings()
        second_id = id(second_settings_instance)

        assert first_id == second_id
        # Verify attributes are still from the first initialization
        assert second_settings_instance.GOOGLE_API_KEY == "test-api-key-123"
        assert second_settings_instance.API_HOST == "test-host"


    def test_get_settings_propagates_settings_error(self, monkeypatch, caplog):
        """
        Verify that get_settings propagates the ValueError from Settings
        initialization if the GOOGLE_API_KEY is invalid.
        """
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False) # Cause Settings to fail

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError) as excinfo:
                config.get_settings()

            assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
            assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text


# --- Test Cases for Global Settings Instance ---

class TestGlobalSettings:
    """
    Tests related to the globally available 'settings' instance in the config module.
    """

    def test_global_settings_is_instance_of_settings(self):
        """
        Verify that the global 'settings' object is an instance of the Settings class.
        This confirms the `settings = get_settings()` line was executed successfully on import.
        """
        assert isinstance(config.settings, config.Settings)
        assert config.settings.GOOGLE_API_KEY == "test-api-key-123"
        assert config.settings.API_HOST == "test-host"

    def test_global_settings_reflects_initial_load(self, monkeypatch):
        """
        Verify that the global `settings` object correctly reflects the environment
        variables present at the time the module was first imported.
        """
        # The autouse fixture `set_default_valid_api_key_and_env_vars`
        # ensures these are the values at initial module import.
        assert config.settings.GOOGLE_API_KEY == "test-api-key-123"
        assert config.settings.API_HOST == "test-host"
        assert config.settings.API_PORT == 9000
        assert config.settings.FRONTEND_HOST == "test-frontend-host"
        assert config.settings.FRONTEND_PORT == 9500
        assert config.settings.DEBUG is False

        # Changing env vars AFTER module import should not change the global settings object
        monkeypatch.setenv("GOOGLE_API_KEY", "changed-after-import")
        monkeypatch.setenv("API_PORT", "9999")
        assert config.settings.GOOGLE_API_KEY == "test-api-key-123"
        assert config.settings.API_PORT == 9000

    def test_global_settings_and_get_settings_are_same_instance(self):
        """
        Verify that subsequent calls to `get_settings()` return the exact same
        instance as the global `settings` object, due to `lru_cache`.
        """
        assert id(config.settings) == id(config.get_settings())