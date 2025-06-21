import pytest
from fastapi.testclient import AsyncClient

@pytest.mark.asyncio
async def test_root():
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Product Assistant API - Ready to help you find products"}

@pytest.mark.asyncio
async def test_health():
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["version"] == "1.0.0" 