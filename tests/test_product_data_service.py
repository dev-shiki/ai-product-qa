import pytest
from app.services.product_data_service import ProductDataService

@pytest.fixture
def service():
    return ProductDataService()

@pytest.mark.asyncio
async def test_get_products(service):
    # Test with default params (mocked/fake data)
    result = await service.get_products(limit=1, category=None, search=None)
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_get_categories(service):
    result = await service.get_categories()
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_search_products(service):
    result = await service.search_products("test", limit=1)
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_get_top_rated_products(service):
    result = await service.get_top_rated_products(limit=1)
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_get_best_selling_products(service):
    result = await service.get_best_selling_products(limit=1)
    assert isinstance(result, list) 