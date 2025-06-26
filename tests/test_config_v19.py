import pytest
import os
from unittest.mock import patch
from functools import lru_cache

# We will import the module under test after setting up environment
# for its initial load, or within tests where we manipulate environment variables.

# Use a session-scoped autouse fixture to ensure GOOGLE_API_KEY is present
# when the app.utils.config module is first imported by pytest.
# This prevents the module-level 'settings = get_settings()' from raising an error
# and failing test collection if GOOGLE_API_KEY is not set in the test environment.
@pytest.fixture(scope="session", autouse=True)
def ensure_google_api_key_for_module_import():
    """
    Ensures GOOGLE_API_KEY is set in the environment when app.utils.config is first imported
    by pytest. This allows the module-level 'settings' object to be initialized successfully.
    """
    original_api_key = os.environ.get("GOOGLE_API_KEY")
    if original_api_key is None:
        os.environ["GOOGLE_API_KEY"] = "dummy-key-for-initial-load"
    try:
        # Yield to allow tests to run
        yield
    finally:
        # Clean up: restore original state or remove if we added it
        if original_api_key is None:
            del os.environ["GOOGLE_API_KEY"]
        else:
            os.environ["GOOGLE_API_KEY"] = original_api_key

# Now import the module under test. The module-level `settings` object will be
# initialized based on the environment set by the `ensure_google_api_key_for_module_import` fixture.
from app.utils.config import Settings, get_settings, settings, logger

# Fixture to clear the lru_cache for get_settings before and after each test
@pytest.fixture(autouse=True)
def clear_settings_cache():
    """
    Clears the lru_cache for the `get_settings` function before and after each test.
    This ensures that each test dealing with `get_settings` starts with a fresh cache state,
    preventing test interference.
    """
    get_settings.cache_clear()
    yield
    get_settings.cache_clear() # Clear again after test completion


# --- Fixtures for specific environment states for GOOGLE_API_KEY ---
@pytest.fixture
def mock_google_api_key(monkeypatch):
    """Sets a valid GOOGLE_API_KEY environment variable for the duration of a test."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key-123-valid")

@pytest.fixture
def mock_google_api_key_default(monkeypatch):
    """Sets GOOGLE_API_KEY to the default placeholder value for the duration of a test."""
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")

@pytest.fixture
def unset_google_api_key(monkeypatch):
    """Ensures GOOGLE_API_KEY environment variable is not set for the duration of a test."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)


# --- Test Cases for the Settings class ---
class TestSettings:
    """Tests for the Settings class initialization and validation."""

    def test_settings_initialization_success_with_env_overrides(self, mock_google_api_key, monkeypatch):
        """
        Tests successful initialization of Settings when GOOGLE_API_KEY is provided
        and verifies that other settings can be overridden by environment variables.
        """
        # Override some default values using monkeypatch to test pydantic-settings env loading
        monkeypatch.setenv("API_HOST", "192.168.1.100")
        monkeypatch.setenv("API_PORT", "9000")
        monkeypatch.setenv("DEBUG", "False")
        monkeypatch.setenv("FRONTEND_HOST", "my-frontend.com")
        monkeypatch.setenv("FRONTEND_PORT", "3000")

        settings_instance = Settings()

        assert settings_instance.GOOGLE_API_KEY == "test-api-key-123-valid"
        assert settings_instance.API_HOST == "192.168.1.100"
        assert settings_instance.API_PORT == 9000
        assert settings_instance.FRONTEND_HOST == "my-frontend.com"
        assert settings_instance.FRONTEND_PORT == 3000
        assert settings_instance.DEBUG is False

    def test_settings_initialization_with_class_defaults(self, mock_google_api_key):
        """
        Tests that Settings uses its class-defined default values when environment
        variables are not provided for fields other than GOOGLE_API_KEY.
        """
        settings_instance = Settings()
        assert settings_instance.GOOGLE_API_KEY == "test-api-key-123-valid" # From fixture
        assert settings_instance.API_HOST == "localhost"
        assert settings_instance.API_PORT == 8000
        assert settings_instance.FRONTEND_HOST == "localhost"
        assert settings_instance.FRONTEND_PORT == 8501
        assert settings_instance.DEBUG is True

    def test_settings_initialization_no_api_key_raises_value_error(self, unset_google_api_key):
        """
        Tests that Settings initialization raises ValueError when GOOGLE_API_KEY is not set.
        Verifies the specific error message and that logger.error is called once.
        """
        with patch.object(logger, 'error') as mock_log_error:
            with pytest.raises(ValueError) as excinfo:
                Settings()
            assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
            mock_log_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

    def test_settings_initialization_default_api_key_raises_value_error(self, mock_google_api_key_default):
        """
        Tests that Settings initialization raises ValueError when GOOGLE_API_KEY is the
        default placeholder "your-google-api-key-here".
        Verifies the specific error message and that logger.error is called once.
        """
        with patch.object(logger, 'error') as mock_log_error:
            with pytest.raises(ValueError) as excinfo:
                Settings()
            assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
            mock_log_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")


# --- Test Cases for the get_settings function ---
class TestGetSettings:
    """Tests for the get_settings function and its caching behavior."""

    def test_get_settings_returns_settings_instance(self, mock_google_api_key):
        """Tests that get_settings successfully returns a valid Settings instance."""
        settings_instance = get_settings()
        assert isinstance(settings_instance, Settings)
        assert settings_instance.GOOGLE_API_KEY == "test-api-key-123-valid"

    def test_get_settings_is_cached(self, mock_google_api_key):
        """
        Tests that get_settings utilizes lru_cache by returning the exact same object
        on subsequent calls, demonstrating caching behavior.
        """
        first_call = get_settings()
        second_call = get_settings()
        assert first_call is second_call # Verifies object identity, proving caching
        assert isinstance(first_call, Settings)

    def test_get_settings_propagates_error_from_settings_init(self, unset_google_api_key):
        """
        Tests that get_settings correctly propagates the ValueError originating from
        Settings initialization when GOOGLE_API_KEY is invalid or missing.
        """
        with patch.object(logger, 'error') as mock_log_error:
            with pytest.raises(ValueError) as excinfo:
                get_settings()
            assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
            mock_log_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")

    def test_get_settings_re_evaluates_after_previous_error(self, monkeypatch):
        """
        Tests that if get_settings previously failed (due to invalid config),
        it will re-evaluate and succeed if the environment is corrected.
        This demonstrates that `lru_cache` does not cache exceptions.
        """
        # 1. First call fails due to missing GOOGLE_API_KEY
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        with patch.object(logger, 'error') as mock_log_error:
            with pytest.raises(ValueError):
                get_settings()
            mock_log_error.assert_called_once()

        # 2. Correct the environment variable for a subsequent call
        monkeypatch.setenv("GOOGLE_API_KEY", "new-valid-key-after-error")
        # The `clear_settings_cache` autouse fixture ensures cache is clear before this test runs.
        # Within this sequence, lru_cache doesn't cache exceptions, so a new call will re-execute.

        # 3. Second call should now succeed
        settings_instance = get_settings()
        assert isinstance(settings_instance, Settings)
        assert settings_instance.GOOGLE_API_KEY == "new-valid-key-after-error"


# --- Test Cases for the globally initialized 'settings' object ---
class TestGlobalSettingsObject:
    """
    Tests for the module-level 'settings' object.
    This object is initialized when the `app.utils.config` module is first imported.
    The `ensure_google_api_key_for_module_import` fixture ensures a valid
    environment for this initial load, allowing the object to be created.
    """

    def test_global_settings_is_initialized_and_valid(self):
        """
        Tests that the global 'settings' variable is correctly initialized
        as an instance of Settings and its GOOGLE_API_KEY is not the default placeholder.
        It also verifies that other default properties are loaded.
        """
        # The `settings` object is already imported at the top of the file,
        # and its state reflects the environment at the time of module import.
        assert isinstance(settings, Settings)
        # It should not be the placeholder, given `ensure_google_api_key_for_module_import`
        assert settings.GOOGLE_API_KEY != "your-google-api-key-here"
        assert len(settings.GOOGLE_API_KEY) > 0 # Should be populated by the session fixture or actual env

        # Verify default properties are also loaded correctly
        assert settings.API_HOST == "localhost"
        assert settings.API_PORT == 8000
        assert settings.FRONTEND_HOST == "localhost"
        assert settings.FRONTEND_PORT == 8501
        assert settings.DEBUG is True