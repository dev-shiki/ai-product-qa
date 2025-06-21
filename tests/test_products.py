import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
@patch("app.api.products.product_service")
@patch("app.main.get_settings")
async def test_get_products(mock_settings, mock_service):
    mock_settings.return_value.GOOGLE_API_KEY = "dummy-key"
    mock_service.get_products = AsyncMock(return_value=[{"id": "1", "name": "Test Product"}])
    # Import after mocking
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/api/products/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

@pytest.mark.asyncio
@patch("app.api.products.product_service")
@patch("app.main.get_settings")
async def test_get_categories(mock_settings, mock_service):
    mock_settings.return_value.GOOGLE_API_KEY = "dummy-key"
    mock_service.get_categories = AsyncMock(return_value=["A", "B"])
    # Import after mocking
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/api/products/categories")
    assert resp.status_code == 200
    assert "categories" in resp.json()

@pytest.mark.asyncio
@patch("app.api.products.product_service")
@patch("app.main.get_settings")
async def test_search_products(mock_settings, mock_service):
    mock_settings.return_value.GOOGLE_API_KEY = "dummy-key"
    mock_service.search_products = AsyncMock(return_value=[{"id": "1"}])
    # Import after mocking
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/api/products/search?query=test")
    assert resp.status_code == 200
    assert "products" in resp.json()

@pytest.mark.asyncio
@patch("app.api.products.product_service")
@patch("app.main.get_settings")
async def test_get_top_rated_products(mock_settings, mock_service):
    mock_settings.return_value.GOOGLE_API_KEY = "dummy-key"
    mock_service.get_top_rated_products = AsyncMock(return_value=[{"id": "1"}])
    # Import after mocking
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/api/products/top-rated")
    assert resp.status_code == 200
    assert "products" in resp.json()

@pytest.mark.asyncio
@patch("app.api.products.product_service")
@patch("app.main.get_settings")
async def test_get_best_selling_products(mock_settings, mock_service):
    mock_settings.return_value.GOOGLE_API_KEY = "dummy-key"
    mock_service.get_best_selling_products = AsyncMock(return_value=[{"id": "1"}])
    # Import after mocking
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/api/products/best-selling")
    assert resp.status_code == 200
    assert "products" in resp.json() 