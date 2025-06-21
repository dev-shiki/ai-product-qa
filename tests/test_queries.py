import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
@patch("app.api.queries.ai_service")
@patch("app.main.get_settings")
async def test_ask_question(mock_settings, mock_ai, mock_product):
    mock_settings.return_value.GOOGLE_API_KEY = "dummy-key"
    mock_ai.get_response = AsyncMock(return_value="Jawaban AI")
    mock_product.search_products = AsyncMock(return_value=[{"id": "1"}])
    # Import after mocking
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/api/queries/ask", json={"question": "Apa laptop terbaik?"})
    assert resp.status_code == 200
    assert resp.json()["answer"] == "Jawaban AI"
    assert resp.json()["products"]

@pytest.mark.asyncio
@patch("app.main.get_settings")
async def test_get_suggestions(mock_settings):
    mock_settings.return_value.GOOGLE_API_KEY = "dummy-key"
    # Import after mocking
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/api/queries/suggestions")
    assert resp.status_code == 200
    assert "suggestions" in resp.json()

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
@patch("app.main.get_settings")
async def test_get_categories(mock_settings, mock_service):
    mock_settings.return_value.GOOGLE_API_KEY = "dummy-key"
    mock_service.get_categories.return_value = ["A", "B"]
    # Import after mocking
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/api/queries/categories")
    assert resp.status_code == 200
    assert "categories" in resp.json()

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
@patch("app.main.get_settings")
async def test_get_brands(mock_settings, mock_service):
    mock_settings.return_value.GOOGLE_API_KEY = "dummy-key"
    mock_service.get_brands.return_value = ["BrandA"]
    # Import after mocking
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/api/queries/brands")
    assert resp.status_code == 200
    assert "brands" in resp.json() 