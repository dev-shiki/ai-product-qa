import pytest
import os
import logging
import importlib
from unittest.mock import patch

# IMPORTANT: Do NOT import app.utils.config at the top level of this test file
# if you plan to test scenarios where its module-level `settings` variable
# should fail to initialize due to environment variables.
# Instead, import/reload it within specific test functions that control the environment.
# We will only import `Settings` and `get_settings` (the class/function definitions)
# at the top, as their behavior can be controlled by specific calls.
from app.utils.config import Settings, get_settings


@pytest.fixture(autouse=True)
def common_config_env_setup(monkeypatch):
    """
    An autouse fixture to set up a basic, valid environment for all config-related tests.
    It ensures a default valid GOOGLE_API_KEY is present to prevent module import errors
    for tests that might implicitly rely on `app.utils.config` being loadable.
    It also ensures the lru_cache for `get_settings` is cleared after each test.
    """
    # Set default valid environment variables for general tests
    monkeypatch.setenv("GOOGLE_API_KEY", "default-valid-test-key")
    monkeypatch.setenv("API_HOST", "default_test_host")
    monkeypatch.setenv("API_PORT", "9001")
    monkeypatch.setenv("FRONTEND_HOST", "default_test_frontend_host")
    monkeypatch.setenv("FRONTEND_PORT", "9501")
    monkeypatch.setenv("DEBUG", "True")

    # Yield to allow the test to run
    yield

    # Clean up: monkeypatch automatically undoes setenv.
    # Ensure the lru_cache for get_settings is cleared after each test to prevent state leakage.
    get_settings.cache_clear()


class TestSettings:
    """
    Tests for the Settings class, including its initialization,
    environment variable loading, and validation logic.
    """

    def test_settings_init_success_with_all_env_vars(self, monkeypatch):
        """
        Tests that Settings class correctly loads all specified values
        from environment variables, overriding defaults.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "my-secret-key-env")
        monkeypatch.setenv("API_HOST", "customapi.example.com")
        monkeypatch.setenv("API_PORT", "5000")
        monkeypatch.setenv("FRONTEND_HOST", "customfrontend.example.com")
        monkeypatch.setenv("FRONTEND_PORT", "3000")
        monkeypatch.setenv("DEBUG", "False")

        settings_obj = Settings()

        assert settings_obj.GOOGLE_API_KEY == "my-secret-key-env"
        assert settings_obj.API_HOST == "customapi.example.com"
        assert settings_obj.API_PORT == 5000
        assert settings_obj.FRONTEND_HOST == "customfrontend.example.com"
        assert settings_obj.FRONTEND_PORT == 3000
        assert settings_obj.DEBUG is False

    def test_settings_init_success_with_default_values(self, monkeypatch):
        """
        Tests that Settings class uses its defined default values for fields
        when their corresponding environment variables are not explicitly set.
        GOOGLE_API_KEY must still be provided.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "another-secret-key-default")
        # Ensure default values are used by removing env vars if they were set by autouse fixture
        monkeypatch.delenv("API_HOST", raising=False)
        monkeypatch.delenv("API_PORT", raising=False)
        monkeypatch.delenv("FRONTEND_HOST", raising=False)
        monkeypatch.delenv("FRONTEND_PORT", raising=False)
        monkeypatch.delenv("DEBUG", raising=False)

        settings_obj = Settings()

        assert settings_obj.GOOGLE_API_KEY == "another-secret-key-default"
        assert settings_obj.API_HOST == "localhost"
        assert settings_obj.API_PORT == 8000
        assert settings_obj.FRONTEND_HOST == "localhost"
        assert settings_obj.FRONTEND_PORT == 8501
        assert settings_obj.DEBUG is True  # Default value

    @pytest.mark.parametrize("invalid_key_value", ["", "your-google-api-key-here"])
    def test_settings_init_raises_error_invalid_google_api_key_value(self, monkeypatch, caplog, invalid_key_value):
        """
        Tests that Settings instantiation raises ValueError and logs an error
        when GOOGLE_API_KEY is an empty string or the default placeholder value.
        """
        # Set logging level to capture ERROR messages
        caplog.set_level(logging.ERROR)

        monkeypatch.setenv("GOOGLE_API_KEY", invalid_key_value)

        with pytest.raises(ValueError) as excinfo:
            Settings()

        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)

        # Verify that the correct error message was logged
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.records[0].message

    def test_settings_init_raises_error_google_api_key_not_set(self, monkeypatch, caplog):
        """
        Tests that Settings instantiation raises ValueError and logs an error
        when GOOGLE_API_KEY is not set in the environment at all.
        """
        caplog.set_level(logging.ERROR)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)  # Ensure it's not set

        with pytest.raises(ValueError) as excinfo:
            Settings()

        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.records[0].message

    def test_settings_config_env_file_attribute(self):
        """
        Tests that the internal Config class correctly specifies `env_file = ".env"`.
        This verifies the pydantic-settings configuration.
        """
        assert Settings.Config.env_file == ".env"


class TestGetSettings:
    """
    Tests for the `get_settings` function, focusing on its caching behavior.
    """

    def test_get_settings_returns_settings_instance(self, monkeypatch):
        """
        Tests that `get_settings()` successfully returns an instance of `Settings`.
        """
        # Ensure a valid key is set for this call (though autouse fixture also does this)
        monkeypatch.setenv("GOOGLE_API_KEY", "valid-key-for-get-settings-test")
        get_settings.cache_clear()  # Ensure clean state before this call

        s = get_settings()
        assert isinstance(s, Settings)
        assert s.GOOGLE_API_KEY == "valid-key-for-get-settings-test"

    def test_get_settings_lru_cache_behavior(self, monkeypatch):
        """
        Tests that `get_settings()` uses `lru_cache`, returning the same instance
        on subsequent calls, and that values are cached from the first call.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "cached-key-initial")
        monkeypatch.setenv("API_PORT", "1000") # Set another env var to cache
        get_settings.cache_clear()  # Ensure clean state

        settings1 = get_settings()
        settings2 = get_settings()  # Second call should return cached instance

        assert settings1 is settings2  # Identity check: same object
        assert settings1.GOOGLE_API_KEY == "cached-key-initial"
        assert settings1.API_PORT == 1000

        # Verify that even if env vars change, the cached instance's values are returned
        monkeypatch.setenv("GOOGLE_API_KEY", "changed-key-after-cache")
        monkeypatch.setenv("API_PORT", "2000") # Change another env var
        settings3 = get_settings()
        assert settings1 is settings3  # Still the same object
        # The values should be from the initial cached state, not the new env vars
        assert settings3.GOOGLE_API_KEY == "cached-key-initial"
        assert settings3.API_PORT == 1000


class TestModuleLevelSettings:
    """
    Tests for the module-level `settings` variable, which is initialized
    when `app/utils/config.py` is imported.
    """

    def test_module_level_settings_is_initialized_correctly_on_import(self, monkeypatch):
        """
        Tests that the module-level 'settings' variable is correctly initialized
        when the module is imported, picking up environment variables set before import.
        This requires `importlib.reload` to simulate a fresh module import.
        """
        # Ensure valid and custom env vars are set before reloading the module
        monkeypatch.setenv("GOOGLE_API_KEY", "module-level-api-key")
        monkeypatch.setenv("API_PORT", "1234")
        monkeypatch.setenv("DEBUG", "False")

        # Reload the module to force re-initialization of the module-level `settings` object
        # This is critical to test the actual module-level variable's initialization.
        import app.utils.config as reloaded_config
        importlib.reload(reloaded_config)

        assert isinstance(reloaded_config.settings, Settings)
        assert reloaded_config.settings.GOOGLE_API_KEY == "module-level-api-key"
        assert reloaded_config.settings.API_PORT == 1234
        assert reloaded_config.settings.DEBUG is False
        assert reloaded_config.settings.API_HOST == "localhost"  # Default value

        # Ensure the get_settings cache is cleared for the reloaded module for subsequent tests
        reloaded_config.get_settings.cache_clear()

    def test_module_level_settings_fails_with_invalid_api_key_on_import(self, monkeypatch, caplog):
        """
        Tests that the module-level 'settings' variable initialization fails
        if GOOGLE_API_KEY is invalid (empty or default placeholder) during module import.
        This requires `importlib.reload` within the test to simulate the import failure.
        """
        caplog.set_level(logging.ERROR)

        # Set an invalid API key for the module import
        monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")

        with pytest.raises(ValueError) as excinfo:
            # Attempt to reload the module, which will trigger the __init__ check
            # for the module-level 'settings' variable (`settings = get_settings()`).
            import app.utils.config as reloaded_config
            importlib.reload(reloaded_config)

        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)

        # Check logs: there should be at least one ERROR record from the config module.
        assert any(
            r.levelname == "ERROR" and "GOOGLE_API_KEY is not set or is using default value" in r.message
            for r in caplog.records
        )

        # Attempt to clear the cache for the (potentially failed) get_settings in the reloaded module.
        # This helps prevent state leakage to other tests if the module was partially initialized.
        try:
            # Re-import just to access the get_settings function in case the reload failed
            # before it could be fully defined/assigned.
            import app.utils.config as reloaded_config_cleanup
            reloaded_config_cleanup.get_settings.cache_clear()
        except Exception:
            # If reload itself failed completely, the module might not be fully initialized
            # and get_settings might not be accessible, so no cache to clear.
            pass