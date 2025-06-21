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