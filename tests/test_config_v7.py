import pytest
from unittest.mock import patch
import os
import logging

# It's important to import the module under test AFTER defining fixtures that might
# influence its global state (like environment variables), or to ensure that
# cache clearing mechanisms are in place. The `clear_settings_cache` fixture
# below handles the latter by ensuring `get_settings()` re-evaluates.
from app.utils.config import Settings, get_settings, settings as global_settings_instance


# --- Fixtures ---

@pytest.fixture(autouse=True)
def clear_settings_cache():
    """
    Fixture to clear the lru_cache for get_settings before each test.
    This ensures that get_settings re-reads environment variables for each test,
    providing a clean slate and making tests independent.
    """
    get_settings.cache_clear()
    yield
    # Clear again after the test to ensure no side effects for other tests,
    # especially if `autouse=True` isn't applied globally or if a test
    # somehow modifies the cache without cleaning up.
    get_settings.cache_clear()


@pytest.fixture
def mock_env_valid(monkeypatch):
    """
    Fixture to set up a valid set of environment variables for Settings to load.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "test_api_key_123")
    monkeypatch.setenv("API_HOST", "test_host_env")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("FRONTEND_HOST", "test_frontend_host_env")
    monkeypatch.setenv("FRONTEND_PORT", "9500")
    monkeypatch.setenv("DEBUG", "False")


@pytest.fixture
def mock_env_missing_api_key(monkeypatch):
    """
    Fixture to simulate GOOGLE_API_KEY being completely unset.
    """
    if "GOOGLE_API_KEY" in os.environ:
        monkeypatch.delenv("GOOGLE_API_KEY")
    # Set other required env vars to avoid other Pydantic validation errors
    monkeypatch.setenv("API_HOST", "some_host")
    monkeypatch.setenv("API_PORT", "1234")


@pytest.fixture
def mock_env_default_api_key(monkeypatch):
    """
    Fixture to simulate GOOGLE_API_KEY being set to the default placeholder value.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")
    # Set other required env vars
    monkeypatch.setenv("API_HOST", "some_host")
    monkeypatch.setenv("API_PORT", "1234")


@pytest.fixture
def mock_env_empty_api_key(monkeypatch):
    """
    Fixture to simulate GOOGLE_API_KEY being an empty string.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    # Set other required env vars
    monkeypatch.setenv("API_HOST", "some_host")
    monkeypatch.setenv("API_PORT", "1234")


@pytest.fixture
def mock_logger_error(mocker):
    """
    Fixture to mock the `logger.error` method and return the mock object
    for assertions.
    """
    return mocker.patch('app.utils.config.logger.error')


# --- Tests for get_settings() function ---

def test_get_settings_returns_settings_instance(mock_env_valid):
    """
    Test that `get_settings()` returns an instance of the `Settings` class
    when environment variables are valid.
    """
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.GOOGLE_API_KEY == "test_api_key_123"


def test_get_settings_is_cached(mock_env_valid):
    """
    Test that `get_settings()` uses `lru_cache`, returning the same instance on
    subsequent calls within the same test (without cache clear in between).
    """
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2

    # Verify cache info to ensure caching is active
    cache_info = get_settings.cache_info()
    assert cache_info.hits == 1
    assert cache_info.misses == 1
    assert cache_info.currsize == 1


def test_get_settings_loads_from_env_variables(mock_env_valid):
    """
    Test that `Settings` correctly loads specific values from mocked
    environment variables.
    """
    settings = get_settings()
    assert settings.GOOGLE_API_KEY == "test_api_key_123"
    assert settings.API_HOST == "test_host_env"
    assert settings.API_PORT == 9000
    assert settings.FRONTEND_HOST == "test_frontend_host_env"
    assert settings.FRONTEND_PORT == 9500
    assert settings.DEBUG is False


def test_get_settings_loads_default_values_when_not_overridden(monkeypatch):
    """
    Test that `Settings` uses its default values for fields when corresponding
    environment variables are not set. `GOOGLE_API_KEY` is set to a valid value
    to allow initialization.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "valid_key_for_defaults")
    # Ensure other optional env vars are not set
    for var in ["API_HOST", "API_PORT", "FRONTEND_HOST", "FRONTEND_PORT", "DEBUG"]:
        if var in os.environ:
            monkeypatch.delenv(var)

    settings = get_settings()
    assert settings.GOOGLE_API_KEY == "valid_key_for_defaults"
    assert settings.API_HOST == "localhost"  # Default
    assert settings.API_PORT == 8000        # Default
    assert settings.FRONTEND_HOST == "localhost"  # Default
    assert settings.FRONTEND_PORT == 8501   # Default
    assert settings.DEBUG is True           # Default


# --- Tests for Settings.__init__ custom validation logic ---

def test_settings_init_valid_api_key_no_error(mock_env_valid, mock_logger_error):
    """
    Test that `Settings` initializes successfully when `GOOGLE_API_KEY` is valid
    and no error is raised or logged by the custom validation.
    """
    settings = get_settings()
    assert settings.GOOGLE_API_KEY == "test_api_key_123"
    mock_logger_error.assert_not_called()


def test_settings_init_raises_value_error_on_missing_api_key(mock_env_missing_api_key, mock_logger_error):
    """
    Test that `Settings` initialization raises a `ValueError` and logs an error
    when `GOOGLE_API_KEY` is completely unset.
    """
    with pytest.raises(ValueError) as excinfo:
        get_settings()  # Calls Settings() internally

    assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
    mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")


def test_settings_init_raises_value_error_on_default_api_key(mock_env_default_api_key, mock_logger_error):
    """
    Test that `Settings` initialization raises a `ValueError` and logs an error
    when `GOOGLE_API_KEY` is the default placeholder value "your-google-api-key-here".
    """
    with pytest.raises(ValueError) as excinfo:
        get_settings()

    assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
    mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")


def test_settings_init_raises_value_error_on_empty_api_key(mock_env_empty_api_key, mock_logger_error):
    """
    Test that `Settings` initialization raises a `ValueError` and logs an error
    when `GOOGLE_API_KEY` is an empty string "".
    """
    with pytest.raises(ValueError) as excinfo:
        get_settings()

    assert "GOOGLE_API_KEY must be set in .env file" in str(excinfo.value)
    mock_logger_error.assert_called_once_with("GOOGLE_API_KEY is not set or is using default value")


def test_settings_init_with_kwargs_overrides_env(monkeypatch):
    """
    Test that direct initialization of `Settings` with keyword arguments
    takes precedence over environment variables.
    This tests the `__init__` method directly, not via `get_settings()`.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "env_key")
    monkeypatch.setenv("API_HOST", "env_host")
    monkeypatch.setenv("API_PORT", "9999")
    monkeypatch.setenv("FRONTEND_PORT", "8888")

    # Manually create Settings instance with kwargs
    # Note: Pydantic will still attempt to validate GOOGLE_API_KEY on instantiation,
    # so ensure the kwarg is not "your-google-api-key-here" or empty.
    settings = Settings(
        GOOGLE_API_KEY="kwarg_key",
        API_HOST="kwarg_host",
        API_PORT=1111,
        FRONTEND_PORT=2222,
        DEBUG=False
    )

    assert settings.GOOGLE_API_KEY == "kwarg_key"
    assert settings.API_HOST == "kwarg_host"
    assert settings.API_PORT == 1111
    assert settings.FRONTEND_PORT == 2222
    assert settings.DEBUG is False


# --- Test global settings instance ---

def test_global_settings_instance_initialization(mock_env_valid):
    """
    Test that the global `settings` variable is correctly initialized as an
    instance of `Settings` and reflects the mocked environment variables.
    This relies on the `autouse` `clear_settings_cache` fixture ensuring
    `get_settings()` (and thus the global `settings` variable on its first call)
    uses the environment variables set by `mock_env_valid`.
    """
    assert isinstance(global_settings_instance, Settings)
    assert global_settings_instance.GOOGLE_API_KEY == "test_api_key_123"
    assert global_settings_instance.API_HOST == "test_host_env"
    assert global_settings_instance.API_PORT == 9000
    assert global_settings_instance.FRONTEND_HOST == "test_frontend_host_env"
    assert global_settings_instance.FRONTEND_PORT == 9500
    assert global_settings_instance.DEBUG is False