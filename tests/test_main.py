import pytest
from httpx import AsyncClient
from unittest.mock import patch

@pytest.mark.asyncio
@patch("app.main.get_settings")
async def test_root(mock_settings):
    mock_settings.return_value.GOOGLE_API_KEY = "dummy-key"
    # Import after mocking
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Product Assistant API - Ready to help you find products"}

@pytest.mark.asyncio
@patch("app.main.get_settings")
async def test_health(mock_settings):
    mock_settings.return_value.GOOGLE_API_KEY = "dummy-key"
    # Import after mocking
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["version"] == "1.0.0" 