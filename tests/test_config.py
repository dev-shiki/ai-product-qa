import os
import pytest
from unittest import mock

def test_settings_valid(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy-key")
    # Import after setting env
    from app.utils import config
    s = config.Settings(GOOGLE_API_KEY="dummy-key")
    assert s.GOOGLE_API_KEY == "dummy-key"
    assert s.API_PORT == 8000

def test_settings_invalid(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "your-google-api-key-here")
    from app.utils import config
    with pytest.raises(ValueError):
        config.Settings(GOOGLE_API_KEY="your-google-api-key-here") 