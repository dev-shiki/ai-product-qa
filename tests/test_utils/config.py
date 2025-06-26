import pytest
import sys
import os
from functools import lru_cache
from pydantic import ValidationError
from pathlib import Path

# Define a comprehensive fixture to ensure a clean state for testing module-level imports
# and cached functions.
@pytest.fixture
def clean_config_module():
    """
    Cleans the app.utils.config module state by:
    1. Clearing the lru_cache for get_settings if the module is already loaded.
    2. Removing the module from sys.modules to force a fresh import in subsequent tests.
    """
    # Store initial sys.path for restoration
    initial_sys_path = list(sys.path)

    # Ensure the module is not already loaded or clear its state if it is.
    if 'app.utils.config' in sys.modules:
        _config_module = sys.modules['app.utils.config']
        if hasattr(_config_module, 'get_settings') and callable(getattr(_config_module.get_settings, 'cache_clear', None)):
            _config_module.get_settings.cache_clear()
        del sys.modules['app.utils.config']
    
    yield # Allow the test to run

    # Clean up again after the test, in case it re-imported the module
    # or for subsequent tests in the same test run. This ensures isolation.
    if 'app.utils.config' in sys.modules:
        _config_module = sys.modules['app.utils.config']
        if hasattr(_config_module, 'get_settings') and callable(getattr(_config_module.get_settings, 'cache_clear', None)):
            _config_module.get_settings.cache_clear()
        del sys.modules['app.utils.config']
    
    # Restore sys.path to its initial state to prevent test interference
    sys.path = initial_sys_path


@pytest.fixture
def create_env_file(tmp_path):
    """
    Creates a temporary .env file in a temporary directory and changes the CWD
    to this directory so that pydantic-settings can find the .env file.
    Restores the original CWD after the test.
    """
    original_cwd = os.getcwd()
    os.chdir(tmp_path) # Change CWD to the temporary directory

    env_file_path = tmp_path / ".env"
    
    yield env_file_path # Yield the path for the test to write to

    # Teardown: Restore original CWD and ensure the temporary .env file is removed
    os.chdir(original_cwd)
    if env_file_path.exists():
        env_file_path.unlink()

# Test cases for the Settings class itself
class TestSettings:
    """
    Tests for the Settings Pydantic model's instantiation and validation.
    """

    # Use the clean_config_module fixture for all tests in this class
    # to ensure isolated environment variable handling.
    @pytest.fixture(autouse=True)
    def setup(self, clean_config_module):
        pass

    def test_settings_init_success_with_all_variables(self, monkeypatch):
        """
        Tests successful initialization of Settings when all environment variables are provided.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key-123")
        monkeypatch.setenv("API_HOST", "custom_host")
        monkeypatch.setenv("API_PORT", "9000")
        monkeypatch.setenv("FRONTEND_HOST", "custom_frontend")
        monkeypatch.setenv("FRONTEND_PORT", "9500")
        monkeypatch.setenv("DEBUG", "False")

        from app.utils.config import Settings
        settings = Settings()

        assert settings.GOOGLE_API_KEY == "test-api-key-123"
        assert settings.API_HOST == "custom_host"
        assert settings.API_PORT == 9000
        assert settings.FRONTEND_HOST == "custom_frontend"
        assert settings.FRONTEND_PORT == 9500
        assert settings.DEBUG is False

    def test_settings_init_success_with_defaults(self, monkeypatch):
        """
        Tests successful initialization when only GOOGLE_API_KEY is provided,
        and other fields fall back to their default values.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "valid-api-key-default")
        # Ensure other variables are NOT set to check defaults
        monkeypatch.delenv("API_HOST", raising=False)
        monkeypatch.delenv("API_PORT", raising=False)
        monkeypatch.delenv("FRONTEND_HOST", raising=False)
        monkeypatch.delenv("FRONTEND_PORT", raising=False)
        monkeypatch.delenv("DEBUG", raising=False)

        from app.utils.config import Settings
        settings = Settings()

        assert settings.GOOGLE_API_KEY == "valid-api-key-default"
        assert settings.API_HOST == "localhost"
        assert settings.API_PORT == 8000
        assert settings.FRONTEND_HOST == "localhost"
        assert settings.FRONTEND_PORT == 8501
        assert settings.DEBUG is True

    def test_settings_init_with_direct_kwargs(self, monkeypatch):
        """
        Tests that Settings can be initialized by passing arguments directly,
        which should override environment variables.
        """
        # Set some environment variables that should be overridden by kwargs
        monkeypatch.setenv("GOOGLE_API_KEY", "env-key-should-be-overridden")
        monkeypatch.setenv("API_PORT", "1234") # This should be overridden

        from app.utils.config import Settings
        
        # Initialize with direct kwargs
        settings = Settings(GOOGLE_API_KEY="direct-kwarg-key", API_PORT=9999)

        assert settings.GOOGLE_API_KEY == "direct-kwarg-key"
        assert settings.API_PORT == 9999
        assert settings.API_HOST == "localhost" # Should fall back to default as not in env or kwargs
        assert settings.FRONTEND_PORT == 8501 # Should fall back to default
        assert settings.DEBUG is True # Should fall back to default

    def test_settings_init_success_from_env_file(self, create_env_file, monkeypatch):
        """
        Tests that Settings loads configuration correctly from a .env file,
        demonstrating the `env_file` attribute functionality.
        """
        env_content = """
        GOOGLE_API_KEY=key_from_env_file
        API_HOST=host_from_env_file
        API_PORT=9001
        DEBUG=false
        """
        create_env_file.write_text(env_content.strip())

        # Ensure no conflicting environment variables are set that would override the .env file
        # pydantic-settings prioritizes env vars over .env file.
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("API_HOST", raising=False)
        monkeypatch.delenv("API_PORT", raising=False)
        monkeypatch.delenv("FRONTEND_HOST", raising=False)
        monkeypatch.delenv("FRONTEND_PORT", raising=False)
        monkeypatch.delenv("DEBUG", raising=False)

        from app.utils.config import Settings
        settings = Settings()

        assert settings.GOOGLE_API_KEY == "key_from_env_file"
        assert settings.API_HOST == "host_from_env_file"
        assert settings.API_PORT == 9001
        assert settings.FRONTEND_HOST == "localhost" # Default, as not in .env or env vars
        assert settings.FRONTEND_PORT == 8501 # Default
        assert settings.DEBUG is False

    def test_settings_init_raises_error_on_missing_google_api_key(self, monkeypatch, caplog):
        """
        Tests that Settings raises ValueError and logs an error when GOOGLE_API_KEY is missing.
        This covers the 'not self.GOOGLE_API_KEY' part when the variable is entirely absent.
        """
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False) # Ensure it's unset

        with caplog.at_level('ERROR'):
            with pytest.raises(ValueError) as excinfo:
                from app.utils.config import Settings
                Settings()

        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text
        assert caplog.records[0].levelname == "ERROR"

    def test_settings_init_raises_error_on_placeholder_google_api_key(self, monkeypatch, caplog):
        """
        Tests that Settings raises ValueError and logs an error when GOOGLE_API_KEY is the default placeholder.
        This covers the 'self.GOOGLE_API_KEY == "your-google-api-key-here"' part.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")

        with caplog.at_level('ERROR'):
            with pytest.raises(ValueError) as excinfo:
                from app.utils.config import Settings
                Settings()

        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text
        assert caplog.records[0].levelname == "ERROR"

    def test_settings_init_raises_error_on_empty_string_google_api_key_kwarg(self, caplog):
        """
        Tests that Settings raises ValueError and logs an error when GOOGLE_API_KEY
        is provided as an empty string directly via kwargs.
        Pydantic allows empty strings for `str` type, but our custom __init__ checks this
        via the 'not self.GOOGLE_API_KEY' condition.
        """
        with caplog.at_level('ERROR'):
            with pytest.raises(ValueError) as excinfo:
                from app.utils.config import Settings
                Settings(GOOGLE_API_KEY="")

        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text
        assert caplog.records[0].levelname == "ERROR"

    def test_settings_init_raises_error_on_empty_string_google_api_key_env_var(self, monkeypatch, caplog):
        """
        Tests that Settings raises ValueError and logs an error when GOOGLE_API_KEY
        is provided as an empty string via an environment variable.
        This covers the 'not self.GOOGLE_API_KEY' condition for env var input.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "")

        with caplog.at_level('ERROR'):
            with pytest.raises(ValueError) as excinfo:
                from app.utils.config import Settings
                Settings()

        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text
        assert caplog.records[0].levelname == "ERROR"

    def test_settings_init_raises_validation_error_on_none_google_api_key_kwarg(self):
        """
        Tests that Settings raises Pydantic ValidationError when GOOGLE_API_KEY
        is provided as None directly via kwargs, as it's a non-optional string field.
        This validates Pydantic's behavior *before* our custom __init__ check.
        """
        with pytest.raises(ValidationError) as excinfo:
            from app.utils.config import Settings
            # Mypy will complain about `None` for `str` type, but we're testing Pydantic's behavior.
            Settings(GOOGLE_API_KEY=None) # type: ignore 

        assert "GOOGLE_API_KEY" in str(excinfo.value)
        # Check for typical Pydantic v1 or v2 error messages
        assert any(msg in str(excinfo.value) for msg in ["value is not a valid string", "Input should be a valid string"])


    def test_settings_init_fails_on_invalid_port_type(self, monkeypatch):
        """
        Tests that Settings raises a Pydantic ValidationError when API_PORT is not a valid integer.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "valid-key")
        monkeypatch.setenv("API_PORT", "not_an_integer")

        from app.utils.config import Settings

        with pytest.raises(ValidationError) as excinfo:
            Settings()
        
        assert "API_PORT" in str(excinfo.value)
        assert any(msg in str(excinfo.value) for msg in ["value is not a valid integer", "Input should be a valid integer", "Input should be a valid number", "invalid literal for int()"])

    def test_settings_init_fails_on_invalid_debug_type(self, monkeypatch):
        """
        Tests that Settings raises a Pydantic ValidationError when DEBUG is not a valid boolean.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "valid-key")
        monkeypatch.setenv("DEBUG", "not_a_boolean")

        from app.utils.config import Settings

        with pytest.raises(ValidationError) as excinfo:
            Settings()
        
        assert "DEBUG" in str(excinfo.value)
        assert any(msg in str(excinfo.value) for msg in ["value could not be parsed to a boolean", "Input should be a valid boolean"])

    def test_settings_init_success_debug_from_string_true(self, monkeypatch):
        """
        Tests that DEBUG field correctly parses string "true" (case-insensitive) to boolean True.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "valid-key")
        monkeypatch.setenv("DEBUG", "true")

        from app.utils.config import Settings
        settings = Settings()
        assert settings.DEBUG is True

    def test_settings_init_success_debug_from_string_false(self, monkeypatch):
        """
        Tests that DEBUG field correctly parses string "false" (case-insensitive) to boolean False.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "valid-key")
        monkeypatch.setenv("DEBUG", "false")

        from app.utils.config import Settings
        settings = Settings()
        assert settings.DEBUG is False

    def test_settings_init_success_debug_from_string_one(self, monkeypatch):
        """
        Tests that DEBUG field correctly parses string "1" to boolean True.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "valid-key")
        monkeypatch.setenv("DEBUG", "1")

        from app.utils.config import Settings
        settings = Settings()
        assert settings.DEBUG is True

    def test_settings_init_success_debug_from_string_zero(self, monkeypatch):
        """
        Tests that DEBUG field correctly parses string "0" to boolean False.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "valid-key")
        monkeypatch.setenv("DEBUG", "0")

        from app.utils.config import Settings
        settings = Settings()
        assert settings.DEBUG is False


# Test cases for the get_settings function and the global settings object
class TestGetSettingsAndGlobal:
    """
    Tests for the get_settings function (including lru_cache behavior)
    and the global 'settings' instance created on module import.
    """

    # This fixture must be autoused for this class to ensure a fresh module import for each test
    @pytest.fixture(autouse=True)
    def setup(self, clean_config_module):
        pass

    def test_get_settings_returns_settings_instance(self, monkeypatch):
        """
        Verifies that get_settings successfully returns an instance of Settings.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "key-for-get-settings")
        
        from app.utils.config import get_settings, Settings
        settings_instance = get_settings()

        assert isinstance(settings_instance, Settings)
        assert settings_instance.GOOGLE_API_KEY == "key-for-get-settings"

    def test_get_settings_uses_lru_cache(self, monkeypatch):
        """
        Tests that get_settings utilizes lru_cache by returning the same instance on subsequent calls.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "cache-test-key")
        
        from app.utils.config import get_settings
        
        first_call_settings = get_settings()
        second_call_settings = get_settings()
        
        # Verify that both calls return the exact same object instance
        assert first_call_settings is second_call_settings
        assert first_call_settings.GOOGLE_API_KEY == "cache-test-key"
        # Ensure the cache prevented re-reading environment variables, even if they change.
        monkeypatch.setenv("GOOGLE_API_KEY", "changed-key-after-cache") # Change env var *after* first call
        assert second_call_settings.GOOGLE_API_KEY == "cache-test-key" # Still the original key, proving caching

    def test_global_settings_is_initialized_correctly(self, monkeypatch):
        """
        Tests that the global 'settings' variable is correctly initialized on module import.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "global-key-on-import")
        monkeypatch.setenv("API_HOST", "global-host-on-import")
        
        # Importing the module triggers the global 'settings = get_settings()' line
        from app.utils.config import settings, Settings

        assert isinstance(settings, Settings)
        assert settings.GOOGLE_API_KEY == "global-key-on-import"
        assert settings.API_HOST == "global-host-on-import"
        assert settings.API_PORT == 8000 # Should be default

    def test_global_settings_is_immutable_after_initial_import(self, monkeypatch):
        """
        Tests that the global 'settings' object, once initialized on module import,
        remains the same instance and does not reflect subsequent environment variable changes,
        due to the lru_cache on get_settings.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "initial-global-key")
        
        # First import, sets global settings
        from app.utils.config import settings as initial_settings_instance
        
        assert initial_settings_instance.GOOGLE_API_KEY == "initial-global-key"

        # Change environment variable *after* initial import
        monkeypatch.setenv("GOOGLE_API_KEY", "changed-global-key")
        
        # Re-import (or access again) - the cached instance should still be used.
        # The clean_config_module fixture ensures a fresh import for each test,
        # but within a single test, accessing `app.utils.config.settings`
        # after it's been imported will return the same cached instance due to `lru_cache`.
        from app.utils.config import settings as current_settings_instance

        # It should be the *same* instance and reflect the *original* value
        assert current_settings_instance is initial_settings_instance
        assert current_settings_instance.GOOGLE_API_KEY == "initial-global-key"


    def test_global_settings_fails_on_missing_key_at_import(self, monkeypatch, caplog):
        """
        Tests that importing the config module fails if GOOGLE_API_KEY is missing,
        due to the global 'settings' initialization, and logs an error.
        """
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False) # Ensure it's unset

        with caplog.at_level('ERROR'):
            with pytest.raises(ValueError) as excinfo:
                # This import statement will trigger the global settings initialization and thus the error
                from app.utils import config 
                _ = config # Avoid "unused import" warning if not explicitly used

        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text
        assert caplog.records[0].levelname == "ERROR"

    def test_global_settings_fails_on_placeholder_key_at_import(self, monkeypatch, caplog):
        """
        Tests that importing the config module fails if GOOGLE_API_KEY is the placeholder,
        due to the global 'settings' initialization, and logs an error.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")

        with caplog.at_level('ERROR'):
            with pytest.raises(ValueError) as excinfo:
                from app.utils import config
                _ = config

        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text
        assert caplog.records[0].levelname == "ERROR"

    def test_get_settings_cache_clear_functionality(self, monkeypatch):
        """
        Tests that get_settings.cache_clear() correctly clears the cached instance,
        allowing a new instance to be created on the next call, reflecting updated env vars.
        """
        monkeypatch.setenv("GOOGLE_API_KEY", "first-key")
        
        from app.utils.config import get_settings
        
        first_settings = get_settings()
        assert first_settings.GOOGLE_API_KEY == "first-key"

        # Clear the cache
        get_settings.cache_clear()

        # Change the environment variable
        monkeypatch.setenv("GOOGLE_API_KEY", "second-key")
        
        # Get settings again - should now pick up the new env var as cache was cleared
        second_settings = get_settings()

        # Verify that it's a new instance and has the new API key
        assert second_settings is not first_settings
        assert second_settings.GOOGLE_API_KEY == "second-key"