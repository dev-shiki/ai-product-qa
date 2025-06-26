import pytest
import os
import logging
from unittest.mock import patch

# Import the module under test.
# We import specific components to avoid issues with the global 'settings' variable
# being initialized at import time before test setup can occur.
# The get_settings.cache_clear() fixture handles resetting its state.
from app.utils.config import Settings, get_settings

# Get the logger instance used in the config module
config_logger = logging.getLogger('app.utils.config')

@pytest.fixture(autouse=True)
def clear_settings_cache():
    """
    Fixture to clear the lru_cache for get_settings before each test.
    This ensures that each test gets a fresh Settings instance,
    allowing environment variables to be properly mocked.
    """
    get_settings.cache_clear()
    yield

@pytest.fixture
def mock_env_valid_api_key(monkeypatch):
    """
    Fixture to set a valid GOOGLE_API_KEY environment variable.
    Ensures a clean state by deleting it after the test.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "test_valid_api_key_123")
    yield
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)


class TestSettings:
    """
    Comprehensive tests for the Settings class initialization and validation.
    """

    def test_settings_init_success_with_env_vars(self, monkeypatch, mock_env_valid_api_key):
        """
        Test that Settings initializes correctly when all fields are overridden
        by environment variables.
        """
        monkeypatch.setenv("API_HOST", "test_host")
        monkeypatch.setenv("API_PORT", "9000")
        monkeypatch.setenv("FRONTEND_HOST", "test_frontend_host")
        monkeypatch.setenv("FRONTEND_PORT", "9500")
        monkeypatch.setenv("DEBUG", "False")

        settings_instance = Settings()

        assert settings_instance.GOOGLE_API_KEY == "test_valid_api_key_123"
        assert settings_instance.API_HOST == "test_host"
        assert settings_instance.API_PORT == 9000
        assert settings_instance.FRONTEND_HOST == "test_frontend_host"
        assert settings_instance.FRONTEND_PORT == 9500
        assert settings_instance.DEBUG is False

    def test_settings_init_success_with_default_values(self, mock_env_valid_api_key):
        """
        Test that Settings initializes correctly with default values when
        environment variables for optional fields are not set.
        """
        settings_instance = Settings()

        assert settings_instance.GOOGLE_API_KEY == "test_valid_api_key_123"
        assert settings_instance.API_HOST == "localhost"
        assert settings_instance.API_PORT == 8000
        assert settings_instance.FRONTEND_HOST == "localhost"
        assert settings_instance.FRONTEND_PORT == 8501
        assert settings_instance.DEBUG is True

    @pytest.mark.parametrize("invalid_key_value", ["", "your-google-api-key-here"])
    def test_settings_init_raises_value_error_for_invalid_api_key_from_env(
        self, monkeypatch, caplog, invalid_key_value
    ):
        """
        Test that Settings raises a ValueError and logs an error when
        GOOGLE_API_KEY is an invalid string (empty or default placeholder)
        from environment variables.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", invalid_key_value)

        with caplog.at_level(logging.ERROR, logger=config_logger):
            with pytest.raises(ValueError) as excinfo:
                Settings()

            assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
            assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text

    def test_settings_init_raises_value_error_when_api_key_is_not_set_in_env(
        self, monkeypatch, caplog
    ):
        """
        Test that Settings raises a ValueError and logs an error when
        GOOGLE_API_KEY environment variable is not set at all.
        """
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        with caplog.at_level(logging.ERROR, logger=config_logger):
            with pytest.raises(ValueError) as excinfo:
                Settings()

            assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
            assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text

    def test_settings_init_with_kwargs(self):
        """
        Test that Settings can be initialized successfully by passing
        values directly as keyword arguments, overriding defaults.
        """
        settings_instance = Settings(
            GOOGLE_API_KEY="kwarg_key",
            API_HOST="kwarg_host",
            API_PORT=1234,
            DEBUG=False
        )
        assert settings_instance.GOOGLE_API_KEY == "kwarg_key"
        assert settings_instance.API_HOST == "kwarg_host"
        assert settings_instance.API_PORT == 1234
        assert settings_instance.DEBUG is False
        # Ensure default values are used for fields not provided as kwargs
        assert settings_instance.FRONTEND_HOST == "localhost"
        assert settings_instance.FRONTEND_PORT == 8501

    @pytest.mark.parametrize("invalid_key_value", ["", "your-google-api-key-here"])
    def test_settings_init_raises_value_error_for_invalid_api_key_from_kwargs(
        self, caplog, invalid_key_value
    ):
        """
        Test that Settings raises a ValueError and logs an error when
        GOOGLE_API_KEY is an invalid string passed as a keyword argument.
        """
        with caplog.at_level(logging.ERROR, logger=config_logger):
            with pytest.raises(ValueError) as excinfo:
                Settings(GOOGLE_API_KEY=invalid_key_value)
            assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
            assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text


class TestGetSettings:
    """
    Comprehensive tests for the get_settings function, including caching.
    """

    def test_get_settings_returns_settings_instance(self, mock_env_valid_api_key):
        """
        Test that get_settings returns an instance of the Settings class.
        """
        settings_instance = get_settings()
        assert isinstance(settings_instance, Settings)
        assert settings_instance.GOOGLE_API_KEY == "test_valid_api_key_123"

    def test_get_settings_is_cached(self, mock_env_valid_api_key, monkeypatch):
        """
        Test that get_settings utilizes lru_cache correctly, returning the
        same instance on subsequent calls and not reloading if environment
        variables change.
        """
        first_call_settings = get_settings()
        second_call_settings = get_settings()
        assert first_call_settings is second_call_settings  # Should be the exact same instance

        # Modify environment variable to confirm caching prevents reload
        monkeypatch.setenv("GOOGLE_API_KEY", "another_api_key_that_should_be_ignored")
        third_call_settings = get_settings()

        assert third_call_settings is first_call_settings  # Still the same instance
        # Value should be from the first instantiation, not the new env var
        assert third_call_settings.GOOGLE_API_KEY == "test_valid_api_key_123"

    def test_get_settings_clears_cache_and_reloads(self, mock_env_valid_api_key, monkeypatch):
        """
        Test that get_settings reloads a new Settings instance after
        get_settings.cache_clear() is called.
        """
        initial_settings = get_settings()
        assert initial_settings.GOOGLE_API_KEY == "test_valid_api_key_123"

        get_settings.cache_clear()  # Manually clear the cache

        # Set a new environment variable for the next load
        monkeypatch.setenv("GOOGLE_API_KEY", "new_api_key_after_clear")
        reloaded_settings = get_settings()

        assert reloaded_settings is not initial_settings  # Should be a new instance
        assert reloaded_settings.GOOGLE_API_KEY == "new_api_key_after_clear"

    def test_get_settings_raises_error_if_api_key_invalid_on_first_load(
        self, monkeypatch, caplog
    ):
        """
        Test that get_settings propagates the ValueError from Settings.__init__
        if the GOOGLE_API_KEY is invalid on its initial call.
        """
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)  # Ensure API key is not set

        with caplog.at_level(logging.ERROR, logger=config_logger):
            with pytest.raises(ValueError) as excinfo:
                get_settings()  # This will trigger the first instantiation of Settings
            
            assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
            assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text


class TestGlobalSettings:
    """
    Tests for the global 'settings' variable, which is initialized at module import time.
    Relies heavily on the `clear_settings_cache` autouse fixture to ensure a fresh state.
    """

    def test_global_settings_variable_is_settings_instance(self, mock_env_valid_api_key):
        """
        Test that the global 'settings' variable is an instance of Settings.
        This test benefits from `clear_settings_cache` fixture resetting the cache
        before this test runs, ensuring `app.utils.config.settings` will
        cause a fresh `Settings()` instantiation when accessed.
        """
        # When `app/utils/config.py` is imported (e.g., by this test file or pytest),
        # the `settings = get_settings()` line executes.
        # Due to `clear_settings_cache` fixture, this execution within this test
        # will result in a fresh Settings instance being created.
        from app.utils import config as config_module

        assert isinstance(config_module.settings, Settings)
        assert config_module.settings.GOOGLE_API_KEY == "test_valid_api_key_123"

    def test_global_settings_variable_reflects_caching(self, mock_env_valid_api_key, monkeypatch):
        """
        Test that the global 'settings' variable reflects the caching behavior
        of `get_settings()`.
        """
        from app.utils import config as config_module

        first_access = config_module.settings
        assert first_access.GOOGLE_API_KEY == "test_valid_api_key_123"

        # Change environment variable
        monkeypatch.setenv("GOOGLE_API_KEY", "changed_key_after_first_access")

        second_access = config_module.settings
        # The global 'settings' variable should still hold the *cached* value
        # from its initial load, despite the env var change.
        assert second_access.GOOGLE_API_KEY == "test_valid_api_key_123"
        assert second_access is first_access  # Verify it's the same cached instance

    def test_global_settings_variable_reflects_cache_cleared(self, mock_env_valid_api_key, monkeypatch):
        """
        Test that after the cache is cleared (e.g., by the autouse fixture),
        accessing the global 'settings' variable reloads it based on current env.
        """
        from app.utils import config as config_module

        # First access will get initial key due to clear_settings_cache
        original_settings = config_module.settings
        assert original_settings.GOOGLE_API_KEY == "test_valid_api_key_123"

        # The autouse `clear_settings_cache` fixture would have run before this test.
        # So when `config_module.settings` is accessed again (or the module is imported),
        # it will trigger a fresh `get_settings()` call.

        # Manually clear the cache again just to show the effect within a single test.
        # (This is mostly for demonstration; the autouse fixture handles it for new tests).
        get_settings.cache_clear()

        # Set new env var for the next load
        monkeypatch.setenv("GOOGLE_API_KEY", "global_settings_reloaded_key")

        # Accessing the global settings again will now cause get_settings to run and reload
        reloaded_settings = config_module.settings
        assert reloaded_settings.GOOGLE_API_KEY == "global_settings_reloaded_key"
        assert reloaded_settings is not original_settings