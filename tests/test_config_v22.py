import pytest
import os
import logging
from functools import lru_cache

# Import the module under test
# The module-level 'settings = get_settings()' execution requires
# 'GOOGLE_API_KEY' to be set in the environment when this module is imported.
# It is assumed that a pytest 'conftest.py' file handles this,
# e.g., using a session-scoped autouse fixture:
#
# # conftest.py example:
# import pytest
# import os
# @pytest.fixture(scope="session", autouse=True)
# def _set_env_for_initial_module_import():
#     original_api_key = os.environ.get("GOOGLE_API_KEY")
#     os.environ["GOOGLE_API_KEY"] = "initial-test-api-key"
#     yield
#     if original_api_key is None:
#         del os.environ["GOOGLE_API_KEY"]
#     else:
#         os.environ["GOOGLE_API_KEY"] = original_api_key
#
# This setup ensures that the 'app.utils.config' module can be loaded
# without raising a ValueError during test collection.
from app.utils.config import Settings, get_settings, logger

@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Fixture to clear the lru_cache for get_settings before and after each test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear() # Clear again after test to ensure isolation

@pytest.fixture
def mock_google_api_key(monkeypatch):
    """Fixture to mock a valid GOOGLE_API_KEY."""
    monkeypatch.setenv("GOOGLE_API_KEY", "valid-test-api-key-123")

@pytest.fixture
def mock_all_env_vars(monkeypatch):
    """Fixture to mock all relevant environment variables."""
    monkeypatch.setenv("GOOGLE_API_KEY", "all-mocked-api-key")
    monkeypatch.setenv("API_HOST", "mocked-api-host")
    monkeypatch.setenv("API_PORT", "9001")
    monkeypatch.setenv("FRONTEND_HOST", "mocked-frontend-host")
    monkeypatch.setenv("FRONTEND_PORT", "9502")
    monkeypatch.setenv("DEBUG", "False")

# Test cases for Settings class initialization

def test_settings_init_success_with_defaults(mock_google_api_key):
    """
    Test that Settings initializes successfully with a valid API key
    and uses default values for other fields when not overridden.
    """
    settings_instance = Settings()
    assert settings_instance.GOOGLE_API_KEY == "valid-test-api-key-123"
    assert settings_instance.API_HOST == "localhost"
    assert settings_instance.API_PORT == 8000
    assert settings_instance.FRONTEND_HOST == "localhost"
    assert settings_instance.FRONTEND_PORT == 8501
    assert settings_instance.DEBUG is True

def test_settings_init_all_env_vars_overridden(mock_all_env_vars):
    """
    Test that Settings initializes correctly when all environment variables
    are provided and override defaults.
    """
    settings_instance = Settings()
    assert settings_instance.GOOGLE_API_KEY == "all-mocked-api-key"
    assert settings_instance.API_HOST == "mocked-api-host"
    assert settings_instance.API_PORT == 9001
    assert settings_instance.FRONTEND_HOST == "mocked-frontend-host"
    assert settings_instance.FRONTEND_PORT == 9502
    assert settings_instance.DEBUG is False

def test_settings_init_missing_google_api_key_raises_value_error(monkeypatch, caplog):
    """
    Test that Settings raises ValueError and logs an error when GOOGLE_API_KEY
    is not set in the environment.
    """
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False) # Ensure it's absent
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError) as excinfo:
            Settings()
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text
    assert len(caplog.records) == 1

def test_settings_init_empty_google_api_key_raises_value_error(monkeypatch, caplog):
    """
    Test that Settings raises ValueError and logs an error when GOOGLE_API_KEY
    is set to an empty string.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError) as excinfo:
            Settings()
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text
    assert len(caplog.records) == 1

def test_settings_init_default_google_api_key_raises_value_error(monkeypatch, caplog):
    """
    Test that Settings raises ValueError and logs an error when GOOGLE_API_KEY
    is set to the default placeholder value.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError) as excinfo:
            Settings()
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text
    assert len(caplog.records) == 1

# Test cases for get_settings function

def test_get_settings_returns_settings_instance(mock_google_api_key):
    """Test that get_settings returns an instance of the Settings class."""
    settings_instance = get_settings()
    assert isinstance(settings_instance, Settings)
    assert settings_instance.GOOGLE_API_KEY == "valid-test-api-key-123"

def test_get_settings_is_cached(mock_google_api_key):
    """Test that get_settings uses lru_cache and returns the same instance on subsequent calls."""
    first_call_settings = get_settings()
    second_call_settings = get_settings()
    assert first_call_settings is second_call_settings

def test_get_settings_cache_clear_creates_new_instance(monkeypatch):
    """
    Test that clearing the lru_cache for get_settings results in a new
    Settings instance being created on the next call.
    """
    # Ensure a valid key for the first instance
    monkeypatch.setenv("GOOGLE_API_KEY", "first-key")
    initial_settings = get_settings()
    initial_settings.API_PORT = 12345 # Modify to check for new instance state

    # Clear cache
    get_settings.cache_clear()

    # Change env var to ensure the new instance picks up the change
    monkeypatch.setenv("GOOGLE_API_KEY", "second-key")
    new_settings = get_settings()

    assert initial_settings is not new_settings
    assert new_settings.GOOGLE_API_KEY == "second-key"
    assert new_settings.API_PORT == 8000 # Should revert to default as it's a new instance

def test_get_settings_with_bad_api_key_after_cache_clear_raises_error(monkeypatch, caplog):
    """
    Test that calling get_settings with a bad API key after clearing its cache
    still raises a ValueError, demonstrating the Settings validation.
    """
    # Ensure current settings are valid from the initial module load/previous test runs
    _ = get_settings()

    # Clear cache so the next call creates a new instance
    get_settings.cache_clear()

    # Set up a bad environment variable for the new instance creation
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError) as excinfo:
            get_settings()
        assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
        assert "GOOGLE_API_KEY is not set or is using default value" in caplog.text
    assert len(caplog.records) == 1