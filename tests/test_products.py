import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_products(mock_service):
    mock_service.get_products = AsyncMock(return_value=[{
        "id": "1", 
        "name": "Test Product",
        "category": "Test Category",
        "brand": "Test Brand",
        "price": 100000,
        "currency": "IDR",
        "description": "Test description",
        "specifications": {
            "rating": 4.5,
            "sold": 100,
            "stock": 50,
            "condition": "Baru",
            "shop_location": "Jakarta",
            "shop_name": "Test Shop"
        },
        "images": [],
        "url": ""
    }])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/products/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_categories(mock_service):
    mock_service.get_categories = AsyncMock(return_value=["A", "B"])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/products/categories")
    assert resp.status_code == 200
    assert "categories" in resp.json()

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_search_products(mock_service):
    mock_service.search_products = AsyncMock(return_value=[{"id": "1"}])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/products/search?query=test")
    assert resp.status_code == 200
    assert "products" in resp.json()

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_top_rated_products(mock_service):
    mock_service.get_top_rated_products = AsyncMock(return_value=[{"id": "1"}])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/products/top-rated")
    assert resp.status_code == 200
    assert "products" in resp.json()

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_best_selling_products(mock_service):
    mock_service.get_best_selling_products = AsyncMock(return_value=[{"id": "1"}])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/products/best-selling")
    assert resp.status_code == 200
    assert "products" in resp.json() 