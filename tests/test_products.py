import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_products(mock_service):
    mock_service.get_products = AsyncMock(return_value=[{
        "id": "1", 
        "name": "Test Product",
        "category": "smartphone",
        "brand": "Apple",
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
async def test_get_products_with_category(mock_service):
    mock_service.get_products = AsyncMock(return_value=[{
        "id": "1", 
        "name": "iPhone",
        "category": "smartphone",
        "brand": "Apple"
    }])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/products/?category=smartphone")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_products_with_search(mock_service):
    mock_service.get_products = AsyncMock(return_value=[{
        "id": "1", 
        "name": "iPhone",
        "category": "smartphone",
        "brand": "Apple"
    }])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/products/?search=iPhone")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_categories(mock_service):
    mock_service.get_categories = AsyncMock(return_value=["smartphone", "laptop"])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/products/categories")
    assert resp.status_code == 200
    assert "categories" in resp.json()

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_search_products(mock_service):
    mock_service.search_products = AsyncMock(return_value=[{"id": "1", "name": "iPhone"}])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/products/search?query=iPhone")
    assert resp.status_code == 200
    assert "products" in resp.json()
    assert "query" in resp.json()
    assert resp.json()["source"] == "local"

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_top_rated_products(mock_service):
    mock_service.get_top_rated_products = AsyncMock(return_value=[{"id": "1", "rating": 4.9}])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/products/categories")
    assert resp.status_code == 500

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_search_products_error(mock_service):
    mock_service.search_products = AsyncMock(side_effect=Exception("Search error"))
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/products/search?query=test")
    assert resp.status_code == 500

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_top_rated_products_error(mock_service):
    mock_service.get_top_rated_products = AsyncMock(side_effect=Exception("Rating error"))
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/products/top-rated")
    assert resp.status_code == 500

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_best_selling_products_error(mock_service):
    mock_service.get_best_selling_products = AsyncMock(side_effect=Exception("Selling error"))
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/products/best-selling")
    assert resp.status_code == 500 