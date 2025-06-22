import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
@patch("app.api.queries.ai_service")
async def test_ask_question(mock_ai, mock_product):
    mock_ai.get_response = AsyncMock(return_value="Jawaban AI")
    mock_product.search_products = AsyncMock(return_value=[{"id": "P001", "name": "iPhone 15 Pro Max"}])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/queries/ask", json={"question": "Apa laptop terbaik?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "Jawaban AI"
    assert isinstance(data["products"], list)
    assert len(data["products"]) > 0

@pytest.mark.asyncio
async def test_get_suggestions():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/suggestions")
    assert resp.status_code == 200
    data = resp.json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_categories(mock_service):
    mock_service.get_categories = AsyncMock(return_value=["smartphone", "laptop", "tablet"])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert "categories" in data
    assert set(data["categories"]) >= {"smartphone", "laptop", "tablet"}

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_brands(mock_service):
    mock_service.get_brands.return_value = ["Apple", "Samsung", "Sony"]
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/brands")
    assert resp.status_code == 200
    data = resp.json()
    assert "brands" in data
    assert set(["Apple", "Samsung", "Sony"]).issubset(set(data["brands"]))

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_search_products(mock_service):
    mock_service.search_products = AsyncMock(return_value=[{"id": "P001", "name": "iPhone 15 Pro Max"}])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/search?keyword=iPhone&limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "products" in data
    assert data["keyword"] == "iPhone"
    assert data["source"] == "local"
    assert isinstance(data["products"], list)
    assert len(data["products"]) > 0
    assert any("iPhone" in p["name"] for p in data["products"])

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_products_by_category(mock_service):
    mock_service.get_products_by_category.return_value = [
        {"id": "P001", "name": "iPhone 15 Pro Max", "category": "smartphone"},
        {"id": "P002", "name": "iPhone 15 Pro", "category": "smartphone"}
    ]
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/category/smartphone")
    assert resp.status_code == 200
    data = resp.json()
    assert "products" in data
    assert data["category"] == "smartphone"
    assert data["source"] == "local"
    assert isinstance(data["products"], list)
    assert len(data["products"]) > 0
    assert all(p["category"] == "smartphone" for p in data["products"])

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_products_by_brand(mock_service):
    mock_service.get_products_by_brand.return_value = [
        {"id": "P001", "name": "iPhone 15 Pro Max", "brand": "Apple"},
        {"id": "P002", "name": "iPhone 15 Pro", "brand": "Apple"}
    ]
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/brand/Apple")
    assert resp.status_code == 200
    data = resp.json()
    assert "products" in data
    assert data["brand"] == "Apple"
    assert data["source"] == "local"
    assert isinstance(data["products"], list)
    assert len(data["products"]) > 0
    assert all(p["brand"] == "Apple" for p in data["products"])

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_top_rated_products(mock_service):
    mock_service.get_top_rated_products = AsyncMock(return_value=[
        {"id": "P008", "name": "MacBook Pro 16-inch M3 Pro", "specifications": {"rating": 4.9}},
        {"id": "P015", "name": "iPad Pro 12.9-inch M2", "specifications": {"rating": 4.9}}
    ])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/top-rated?limit=3")
    assert resp.status_code == 200
    data = resp.json()
    assert "products" in data
    assert data["source"] == "local"
    assert isinstance(data["products"], list)
    assert len(data["products"]) > 0
    assert all("specifications" in p and p["specifications"].get("rating", 0) >= 4.5 for p in data["products"])

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_best_selling_products(mock_service):
    mock_service.get_best_selling_products = AsyncMock(return_value=[
        {"id": "P016", "name": "iPad Pro 11-inch M2", "specifications": {"sold": 2000}},
        {"id": "P045", "name": "Kindle Paperwhite", "specifications": {"sold": 1500}}
    ])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/best-selling?limit=3")
    assert resp.status_code == 200
    data = resp.json()
    assert "products" in data
    assert data["source"] == "local"
    assert isinstance(data["products"], list)
    assert len(data["products"]) > 0
    assert all("specifications" in p and "sold" in p["specifications"] for p in data["products"])

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_product_details(mock_service):
    mock_service.get_product_details.return_value = {"id": "P001", "name": "iPhone 15 Pro Max", "price": 21999000}
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/P001")
    assert resp.status_code == 200
    data = resp.json()
    assert "product" in data
    assert data["source"] == "local"
    assert isinstance(data["product"], dict)
    assert data["product"]["id"] == "P001"
    assert "name" in data["product"]

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_product_details_not_found(mock_service):
    mock_service.get_product_details.return_value = None
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/nonexistent")
    assert resp.status_code == 404

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_test_connection(mock_service):
    mock_service.get_all_products.return_value = [{"id": "P001", "name": "iPhone 15 Pro Max"}]
    mock_service.local_service.products = [{"id": "P001"}, {"id": "P002"}]
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/test-connection")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] == True
    assert data["source"] == "local"
    assert "products_count" in data
    assert data["products_count"] > 0

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_categories_error(mock_service):
    mock_service.get_categories = AsyncMock(side_effect=Exception("Database error"))
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

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_search_products_error(mock_service):
    mock_service.search_products = AsyncMock(side_effect=Exception("Search error"))
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/search?keyword=test")
    assert resp.status_code == 500

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_products_by_category_error(mock_service):
    mock_service.get_products_by_category.side_effect = Exception("Category error")
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/category/smartphone")
    assert resp.status_code == 500

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_products_by_brand_error(mock_service):
    mock_service.get_products_by_brand.side_effect = Exception("Brand error")
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/brand/Apple")
    assert resp.status_code == 500

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_top_rated_products_error(mock_service):
    mock_service.get_top_rated_products = AsyncMock(side_effect=Exception("Rating error"))
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/top-rated")
    assert resp.status_code == 500

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_best_selling_products_error(mock_service):
    mock_service.get_best_selling_products = AsyncMock(side_effect=Exception("Selling error"))
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/best-selling")
    assert resp.status_code == 500

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_products(mock_service):
    mock_service.get_products = AsyncMock(return_value=[{
        "id": "P001",
        "name": "iPhone 15 Pro Max",
        "category": "smartphone",
        "brand": "Apple",
        "price": 21999000,
        "currency": "IDR",
        "description": "iPhone 15 Pro Max dengan titanium design, kamera 48MP, dan performa terbaik",
        "specifications": {
            "rating": 4.8,
            "sold": 100,
            "stock": 25,
            "condition": "Baru",
            "shop_location": "Indonesia",
            "shop_name": "Apple Store"
        },
        "images": ["https://example.com/P001.jpg"],
        "url": "https://shopee.co.id/P001"
    }])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("id" in p and "name" in p for p in data)

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_products_with_limit(mock_service):
    mock_service.get_products = AsyncMock(return_value=[{
        "id": "P001",
        "name": "iPhone 15 Pro Max",
        "category": "smartphone",
        "brand": "Apple"
    }])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert len(data) <= 5

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_products_with_category(mock_service):
    mock_service.get_products = AsyncMock(return_value=[{
        "id": "P001",
        "name": "iPhone 15 Pro Max",
        "category": "smartphone",
        "brand": "Apple"
    }])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/?category=smartphone")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(p["category"] == "smartphone" for p in data)

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_products_with_brand(mock_service):
    mock_service.get_products = AsyncMock(return_value=[{
        "id": "P001",
        "name": "iPhone 15 Pro Max",
        "category": "smartphone",
        "brand": "Apple"
    }])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/?brand=Apple")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(p["brand"] == "Apple" for p in data)

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_products_with_search(mock_service):
    mock_service.get_products = AsyncMock(return_value=[{
        "id": "P001",
        "name": "iPhone 15 Pro Max",
        "category": "smartphone",
        "brand": "Apple"
    }])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/?search=iPhone")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any("iPhone" in p["name"] for p in data)

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_products_with_multiple_params(mock_service):
    mock_service.get_products = AsyncMock(return_value=[{
        "id": "P001",
        "name": "iPhone 15 Pro Max",
        "category": "smartphone",
        "brand": "Apple"
    }])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/products/?category=smartphone&brand=Apple&limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(p["category"] == "smartphone" and p["brand"] == "Apple" for p in data) 