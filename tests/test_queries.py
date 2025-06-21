import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
@patch("app.api.queries.ai_service")
async def test_ask_question(mock_ai, mock_product):
    mock_ai.get_response = AsyncMock(return_value="Jawaban AI")
    mock_product.search_products = AsyncMock(return_value=[{"id": "1"}])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/queries/ask", json={"question": "Apa laptop terbaik?"})
    assert resp.status_code == 200
    assert resp.json()["answer"] == "Jawaban AI"
    assert resp.json()["products"]

@pytest.mark.asyncio
async def test_get_suggestions():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/suggestions")
    assert resp.status_code == 200
    assert "suggestions" in resp.json()

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_categories(mock_service):
    mock_service.get_categories.return_value = ["A", "B"]
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/categories")
    assert resp.status_code == 200
    assert "categories" in resp.json()

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_brands(mock_service):
    mock_service.get_brands.return_value = ["BrandA"]
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/brands")
    assert resp.status_code == 200
    assert "brands" in resp.json()

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_search_products(mock_service):
    mock_service.search_products.return_value = [{"id": "1", "name": "Test"}]
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/search?keyword=test&limit=5&source=local")
    assert resp.status_code == 200
    assert "products" in resp.json()
    assert resp.json()["keyword"] == "test"
    assert resp.json()["source"] == "local"

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_products_by_category(mock_service):
    mock_service.search_products.return_value = [
        {"id": "1", "name": "Test", "category": "Electronics"},
        {"id": "2", "name": "Test2", "category": "Electronics"}
    ]
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/category/Electronics")
    assert resp.status_code == 200
    assert "products" in resp.json()
    assert resp.json()["category"] == "Electronics"

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_products_by_brand(mock_service):
    mock_service.search_products.return_value = [
        {"id": "1", "name": "Test", "brand": "Apple"},
        {"id": "2", "name": "Test2", "brand": "Apple"}
    ]
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/brand/Apple")
    assert resp.status_code == 200
    assert "products" in resp.json()
    assert resp.json()["brand"] == "Apple"

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_top_rated_products(mock_service):
    mock_service.search_products.return_value = [
        {"id": "1", "specifications": {"rating": 4.5}},
        {"id": "2", "specifications": {"rating": 4.8}}
    ]
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/top-rated?limit=3&source=local")
    assert resp.status_code == 200
    assert "products" in resp.json()
    assert resp.json()["source"] == "local"

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_best_selling_products(mock_service):
    mock_service.search_products.return_value = [
        {"id": "1", "specifications": {"sold": 100}},
        {"id": "2", "specifications": {"sold": 200}}
    ]
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/best-selling?limit=3&source=local")
    assert resp.status_code == 200
    assert "products" in resp.json()
    assert resp.json()["source"] == "local"

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_product_details(mock_service):
    mock_service.get_product_details.return_value = {"id": "1", "name": "Test Product"}
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/1?source=local")
    assert resp.status_code == 200
    assert "product" in resp.json()
    assert resp.json()["source"] == "local"

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_product_details_not_found(mock_service):
    mock_service.get_product_details.return_value = None
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/999")
    assert resp.status_code == 404

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_test_connection(mock_service):
    mock_service.test_connection.return_value = True
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/test-connection")
    assert resp.status_code == 200
    assert resp.json()["success"] == True

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_categories_error(mock_service):
    mock_service.get_categories.side_effect = Exception("Database error")
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/categories")
    assert resp.status_code == 500

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_brands_error(mock_service):
    mock_service.get_brands.side_effect = Exception("Database error")
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/brands")
    assert resp.status_code == 500 