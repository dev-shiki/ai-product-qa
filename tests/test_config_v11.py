import pytest
import os
import logging
import sys
import importlib
from functools import lru_cache

# Define the module path to allow for clean re-imports
CONFIG_MODULE_NAME = "app.utils.config"

@pytest.fixture(autouse=True)
def clean_env_and_modules(monkeypatch):
    """
    Fixture to clean up environment variables and ensure a fresh module state
    for each test. This is crucial for testing global singleton patterns
    like `lru_cache` and module-level variable assignments.
    """
    # Clean environment variables
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("FRONTEND_HOST", raising=False)
    monkeypatch.delenv("FRONTEND_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    # Remove the module from sys.modules to force a fresh import for subsequent tests
    # that directly import app.utils.config or use the config_module fixture.
    if CONFIG_MODULE_NAME in sys.modules:
        del sys.modules[CONFIG_MODULE_NAME]

    yield # Let the test run

    # Ensure cleanup after test if it re-imported the module
    if CONFIG_MODULE_NAME in sys.modules:
        del sys.modules[CONFIG_MODULE_NAME]


@pytest.fixture
def config_module(clean_env_and_modules, monkeypatch):
    """
    Provides a reloaded (fresh) instance of the config module,
    ensuring `get_settings` cache is cleared and environment
    variables are reset before each test.
    """
    # Set a default valid API key for the general case where it's needed for import
    # This can be overridden by specific tests using monkeypatch.setenv
    monkeypatch.setenv("GOOGLE_API_KEY", "default-valid-key-for-fixture")

    # Import the module here to ensure it's reloaded for each test that uses this fixture.
    # It will pick up the environment variables set by monkeypatch.
    import app.utils.config as config
    importlib.reload(config) # Ensures a fresh load based on current env
    config.get_settings.cache_clear() # Clear the lru_cache explicitly

    yield config

    # Clean up after test: clear cache again to ensure no state leaks
    config.get_settings.cache_clear()


# --- Test Cases for Settings Class ---

def test_settings_google_api_key_valid(monkeypatch, caplog):
    """
    Test Settings initialization with a valid GOOGLE_API_KEY.
    Ensures no ValueError is raised and no error is logged.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "valid-api-key")
    from app.utils.config import Settings
    settings = Settings()
    assert settings.GOOGLE_API_KEY == "valid-api-key"
    assert "GOOGLE_API_KEY is not set" not in caplog.text


def test_settings_google_api_key_empty(monkeypatch, caplog):
    """
    Test Settings initialization with an empty GOOGLE_API_KEY, expecting ValueError.
    Also verifies the error message is logged.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    with caplog.at_level(logging.ERROR):
        from app.utils.config import Settings
        with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
            Settings()
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text


def test_settings_google_api_key_default_value_error(monkeypatch, caplog):
    """
    Test Settings initialization with the default placeholder GOOGLE_API_KEY,
    expecting ValueError and a logged error.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")
    with caplog.at_level(logging.ERROR):
        from app.utils.config import Settings
        with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
            Settings()
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text


def test_settings_google_api_key_not_set_error(monkeypatch, caplog):
    """
    Test Settings initialization when GOOGLE_API_KEY is not set at all,
    expecting ValueError and a logged error.
    """
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with caplog.at_level(logging.ERROR):
        from app.utils.config import Settings
        with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
            Settings()
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text


def test_settings_default_values(monkeypatch):
    """
    Test that other settings fields use their default values when not provided
    via environment variables.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-for-defaults")
    # Ensure other env vars are not set
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("FRONTEND_HOST", raising=False)
    monkeypatch.delenv("FRONTEND_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    from app.utils.config import Settings
    settings = Settings()
    assert settings.API_HOST == "localhost"
    assert settings.API_PORT == 8000
    assert settings.FRONTEND_HOST == "localhost"
    assert settings.FRONTEND_PORT == 8501
    assert settings.DEBUG is True


def test_settings_env_variable_override(monkeypatch):
    """
    Test that settings fields are correctly overridden by environment variables.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "env-key-override")
    monkeypatch.setenv("API_HOST", "test-host-env")
    monkeypatch.setenv("API_PORT", "9000") # Pydantic converts string to int
    monkeypatch.setenv("FRONTEND_HOST", "test-frontend-env")
    monkeypatch.setenv("FRONTEND_PORT", "9500")
    monkeypatch.setenv("DEBUG", "False") # Pydantic converts "False" to bool False

    from app.utils.config import Settings
    settings = Settings()
    assert settings.GOOGLE_API_KEY == "env-key-override"
    assert settings.API_HOST == "test-host-env"
    assert settings.API_PORT == 9000
    assert settings.FRONTEND_HOST == "test-frontend-env"
    assert settings.FRONTEND_PORT == 9500
    assert settings.DEBUG is False


def test_settings_debug_env_var_true(monkeypatch):
    """
    Test that DEBUG is correctly set to True from various true-like environment variable values.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "key")
    monkeypatch.setenv("DEBUG", "True")
    from app.utils.config import Settings
    assert Settings().DEBUG is True

    monkeypatch.setenv("DEBUG", "1")
    assert Settings().DEBUG is True


def test_settings_debug_env_var_false(monkeypatch):
    """
    Test that DEBUG is correctly set to False from various false-like environment variable values.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "key")
    monkeypatch.setenv("DEBUG", "False")
    from app.utils.config import Settings
    assert Settings().DEBUG is False

    monkeypatch.setenv("DEBUG", "0")
    assert Settings().DEBUG is False


# --- Test Cases for get_settings() Function ---

def test_get_settings_returns_settings_instance(config_module, monkeypatch):
    """
    Test that get_settings returns an instance of the Settings class.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-for-get-settings")
    settings_instance = config_module.get_settings()
    assert isinstance(settings_instance, config_module.Settings)
    assert settings_instance.GOOGLE_API_KEY == "test-key-for-get-settings"


def test_get_settings_lru_cache_behavior(config_module, monkeypatch):
    """
    Test that get_settings caches its result, returning the exact same instance
    on subsequent calls, even if environment variables change.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "initial-cached-key")
    first_call_settings = config_module.get_settings()

    # Change environment variable *after* the first call.
    # The cached instance should still be returned.
    monkeypatch.setenv("GOOGLE_API_KEY", "new-key-should-be-ignored-by-cache")
    second_call_settings = config_module.get_settings()

    assert first_call_settings is second_call_settings # Verify same instance due to caching
    assert first_call_settings.GOOGLE_API_KEY == "initial-cached-key"


def test_get_settings_cache_clear_behavior(config_module, monkeypatch):
    """
    Test that calling get_settings.cache_clear() forces a new instance
    to be created on the next call.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "first-settings-key")
    first_settings = config_module.get_settings()

    config_module.get_settings.cache_clear() # Clear the cache

    monkeypatch.setenv("GOOGLE_API_KEY", "second-settings-key-after-clear")
    second_settings = config_module.get_settings()

    assert first_settings is not second_settings # Verify different instances
    assert first_settings.GOOGLE_API_KEY == "first-settings-key"
    assert second_settings.GOOGLE_API_KEY == "second-settings-key-after-clear"


def test_get_settings_propagates_settings_error(config_module, monkeypatch, caplog):
    """
    Test that if Settings initialization fails (e.g., due to missing API key),
    get_settings also propagates that ValueError and logs the error.
    """
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False) # Make Settings fail
    config_module.get_settings.cache_clear() # Ensure no valid settings are cached

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
            config_module.get_settings()
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text


# --- Test Cases for Global 'settings' Instance ---

def test_global_settings_instance_initialization(config_module, monkeypatch):
    """
    Test that the global 'settings' instance is correctly initialized on module load
    and is the same as what `get_settings()` returns initially.
    """
    # The config_module fixture ensures a fresh module import
    # and sets a default valid GOOGLE_API_KEY for the initial load.
    monkeypatch.setenv("GOOGLE_API_KEY", "key-for-global-settings")
    # Reload the module to pick up the specific GOOGLE_API_KEY for this test
    # (config_module fixture already handles this for us).
    # We can just access config_module.settings directly.
    assert isinstance(config_module.settings, config_module.Settings)
    assert config_module.settings.GOOGLE_API_KEY == "key-for-global-settings"
    # The global 'settings' object should be the result of the first get_settings call
    assert config_module.settings is config_module.get_settings()


def test_global_settings_instance_initialization_error(clean_env_and_modules, monkeypatch, caplog):
    """
    Test that the global 'settings' instance fails to initialize if GOOGLE_API_KEY is invalid
    during the initial module import, leading to a ValueError.
    This test needs to be very careful with `sys.modules`.
    """
    # Ensure GOOGLE_API_KEY is unset to trigger the error on module import
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    # Force a fresh import by ensuring the module is not in sys.modules
    # (handled by `clean_env_and_modules` fixture)
    assert CONFIG_MODULE_NAME not in sys.modules

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError, match="GOOGLE_API_KEY must be set in .env file"):
            # Attempt to import the module, which triggers the global 'settings' initialization
            import app.utils.config
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text

    # Ensure module is cleaned up from sys.modules after this test too
    if CONFIG_MODULE_NAME in sys.modules:
        del sys.modules[CONFIG_MODULE_NAME]