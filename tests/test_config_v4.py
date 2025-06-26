import pytest
import os
import logging
from unittest.mock import patch

# Import the module under test.
# This will execute `settings = get_settings()` at import time.
# The `clear_settings_cache` fixture ensures a clean state for `get_settings()`
# cache before each test, allowing environment variable changes to take effect.
from app.utils.config import Settings, get_settings, logger

# Fixture to clear the lru_cache for get_settings before each test.
# This is crucial because `settings = get_settings()` is a global assignment
# in the module, and `lru_cache` caches the result of `get_settings()`.
# Clearing the cache ensures that each test gets a fresh `Settings` instance
# reflecting the environment variables set by that test's fixtures.
@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clears the lru_cache for get_settings before and after each test."""
    get_settings.cache_clear()
    yield  # Allow the test to run
    get_settings.cache_clear()  # Clear again after test for good measure


# Fixture to set a valid GOOGLE_API_KEY environment variable and clear others.
@pytest.fixture
def mock_env_valid_api_key(monkeypatch):
    """Sets a valid GOOGLE_API_KEY and ensures other config variables are unset
    to allow default values to be tested or to prevent interference."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key-123")
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("FRONTEND_HOST", raising=False)
    monkeypatch.delenv("FRONTEND_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)


# Fixture to set all environment variables with custom values.
@pytest.fixture
def mock_env_all_custom_values(monkeypatch):
    """Sets all environment variables with custom values for comprehensive testing."""
    monkeypatch.setenv("GOOGLE_API_KEY", "custom-google-key")
    monkeypatch.setenv("API_HOST", "custom_host.com")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("FRONTEND_HOST", "custom_frontend.org")
    monkeypatch.setenv("FRONTEND_PORT", "9501")
    monkeypatch.setenv("DEBUG", "False")  # Test boolean parsing


class TestSettingsClass:
    """Comprehensive tests for the Settings class's instantiation and validation."""

    def test_settings_loads_with_defaults(self, mock_env_valid_api_key, caplog):
        """
        Test that Settings loads correctly with default values for most fields
        when only GOOGLE_API_KEY is provided.
        """
        s = Settings()

        assert s.GOOGLE_API_KEY == "test-api-key-123"
        assert s.API_HOST == "localhost"
        assert s.API_PORT == 8000
        assert s.FRONTEND_HOST == "localhost"
        assert s.FRONTEND_PORT == 8501
        assert s.DEBUG is True  # Default boolean value

        # Ensure no error was logged during valid initialization
        assert not caplog.records

    def test_settings_loads_with_custom_values(self, mock_env_all_custom_values, caplog):
        """
        Test that Settings loads correctly with all custom environment variables.
        """
        s = Settings()

        assert s.GOOGLE_API_KEY == "custom-google-key"
        assert s.API_HOST == "custom_host.com"
        assert s.API_PORT == 9000
        assert s.FRONTEND_HOST == "custom_frontend.org"
        assert s.FRONTEND_PORT == 9501
        assert s.DEBUG is False  # Custom boolean value

        # Ensure no error was logged during valid initialization
        assert not caplog.records

    @pytest.mark.parametrize("key_value", [
        "",  # Empty string
        "your-google-api-key-here"  # Default placeholder value
    ])
    def test_settings_google_api_key_invalid_raises_value_error(self, monkeypatch, caplog, key_value):
        """
        Test that Settings raises ValueError and logs an error if GOOGLE_API_KEY is
        an empty string or the default placeholder value.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", key_value)

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError) as excinfo:
                Settings()

            assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
            assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text
            assert caplog.records[0].levelname == "ERROR"

    def test_settings_google_api_key_missing_raises_value_error(self, monkeypatch, caplog):
        """
        Test that Settings raises ValueError and logs an error if GOOGLE_API_KEY
        is not set at all in the environment.
        """
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)  # Ensure it's not set

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError) as excinfo:
                Settings()

            assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
            assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text
            assert caplog.records[0].levelname == "ERROR"

    def test_settings_google_api_key_valid_no_error(self, mock_env_valid_api_key, caplog):
        """
        Test that Settings initializes successfully when GOOGLE_API_KEY is valid.
        """
        s = Settings()
        assert s.GOOGLE_API_KEY == "test-api-key-123"
        assert not caplog.records  # No error should be logged for a valid key

    @pytest.mark.parametrize("api_port_val, frontend_port_val", [
        ("12345", "67890"),  # Strings that should be coerced to int
        (12345, 67890)      # Already integers (pydantic handles this, but env vars are strings)
    ])
    def test_settings_type_coercion_for_ports(self, mock_env_valid_api_key, monkeypatch, api_port_val, frontend_port_val):
        """
        Test that port numbers are correctly coerced to integers from environment variables.
        """
        monkeypatch.setenv("API_PORT", str(api_port_val))
        monkeypatch.setenv("FRONTEND_PORT", str(frontend_port_val))

        s = Settings()
        assert isinstance(s.API_PORT, int)
        assert s.API_PORT == 12345
        assert isinstance(s.FRONTEND_PORT, int)
        assert s.FRONTEND_PORT == 67890

    @pytest.mark.parametrize("debug_env_val, expected_debug_bool", [
        ("0", False),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("f", False),
        ("F", False),
        ("1", True),
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("t", True),
        ("T", True),
    ])
    def test_settings_type_coercion_for_debug(self, mock_env_valid_api_key, monkeypatch, debug_env_val, expected_debug_bool):
        """
        Test that DEBUG boolean is correctly coerced from various string representations.
        """
        monkeypatch.setenv("DEBUG", debug_env_val)
        s = Settings()
        assert s.DEBUG is expected_debug_bool


class TestGetSettingsFunction:
    """Tests for the get_settings function, including lru_cache behavior."""

    def test_get_settings_returns_settings_instance(self, mock_env_valid_api_key):
        """
        Test that get_settings returns an instance of Settings.
        The `clear_settings_cache` autouse fixture ensures a fresh call to `Settings()`
        is made by `get_settings()` during this test.
        """
        s_instance = get_settings()
        assert isinstance(s_instance, Settings)
        assert s_instance.GOOGLE_API_KEY == "test-api-key-123"

    def test_get_settings_is_cached(self, mock_env_valid_api_key, caplog):
        """
        Test that get_settings uses lru_cache and returns the same instance
        on subsequent calls without re-initializing Settings.
        """
        # First call: Settings() constructor should be called.
        s1 = get_settings()
        assert isinstance(s1, Settings)
        assert not caplog.records  # No error logged if key is valid

        # Clear logs to ensure no new logs appear on subsequent cached calls.
        caplog.clear()

        # Second call: Should return cached instance, Settings() constructor should NOT be called again.
        s2 = get_settings()
        assert s1 is s2  # Assert it's the exact same instance
        assert not caplog.records  # No new logs, indicating cache hit and no re-initialization.

        # Clear cache and call again: Settings() constructor should be called again.
        get_settings.cache_clear()
        caplog.clear()  # Clear logs again
        s3 = get_settings()
        assert s1 is not s3  # Should be a new instance now
        assert isinstance(s3, Settings)
        assert not caplog.records  # No error logged if key is valid


class TestGlobalSettingsObject:
    """Tests for the globally initialized 'settings' object in app/utils/config.py."""

    def test_global_settings_is_settings_instance(self, mock_env_valid_api_key):
        """
        Test that the global 'settings' variable is an instance of Settings.
        This relies on `clear_settings_cache` and `mock_env_valid_api_key` to
        ensure a fresh, valid initialization.
        """
        # Import 'settings' *after* fixtures have set up the environment and cleared cache.
        # This guarantees that the global `settings` object reflects the test's environment.
        from app.utils.config import settings as global_settings_obj
        assert isinstance(global_settings_obj, Settings)
        assert global_settings_obj.GOOGLE_API_KEY == "test-api-key-123"

    def test_global_settings_is_cached_instance_of_get_settings(self, mock_env_valid_api_key):
        """
        Test that the global 'settings' variable is the exact same instance returned by get_settings().
        This confirms the `settings = get_settings()` assignment and `lru_cache` behavior.
        """
        # Ensure the environment is set and cache is clear (via autouse fixture `clear_settings_cache`).

        # The global `settings` object in `app.utils.config` is initialized via `get_settings()`
        # when the module is imported. Due to `clear_settings_cache`, the first access to `get_settings()`
        # within this test will re-evaluate and create a new Settings object.
        # Accessing `app.utils.config.settings` or calling `get_settings()` will trigger this.

        # Get the global settings object as it exists in the module.
        from app.utils.config import settings as global_settings_obj

        # Call get_settings() directly. Because it's cached, it should return the same object
        # that was created when `global_settings_obj` was first accessed (or the module was imported
        # and `settings = get_settings()` ran, if it was the first time `get_settings()` was called).
        retrieved_settings = get_settings()

        # Assert that the global settings object and the one retrieved via get_settings() are the same instance.
        assert global_settings_obj is retrieved_settings
        assert isinstance(global_settings_obj, Settings)
        assert isinstance(retrieved_settings, Settings)
        assert global_settings_obj.GOOGLE_API_KEY == "test-api-key-123"