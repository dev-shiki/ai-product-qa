import pytest
from app.services.product_data_service import ProductDataService
from unittest.mock import patch, AsyncMock

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

@pytest.mark.asyncio
async def test_search_products():
    service = ProductDataService()
    with patch.object(service.external_service, 'search_products') as mock_external:
        mock_external.return_value = [{"id": "1", "name": "External Product"}]
        result = await service.search_products("test", 5, "fakestoreapi")
        assert len(result) > 0
        assert result[0]["name"] == "External Product"

@pytest.mark.asyncio
async def test_search_products_local():
    service = ProductDataService()
    with patch.object(service.local_service, 'search_products') as mock_local:
        mock_local.return_value = [{"id": "1", "name": "Local Product"}]
        result = await service.search_products("test", 5, "local")
        assert len(result) > 0
        assert result[0]["name"] == "Local Product"

@pytest.mark.asyncio
async def test_search_products_fallback():
    service = ProductDataService()
    with patch.object(service.external_service, 'search_products') as mock_external:
        mock_external.side_effect = Exception("API Error")
        with patch.object(service.local_service, 'search_products') as mock_local:
            mock_local.return_value = [{"id": "1", "name": "Fallback Product"}]
            result = await service.search_products("test", 5, "fakestoreapi")
            assert len(result) > 0
            assert result[0]["name"] == "Fallback Product"

def test_get_categories():
    service = ProductDataService()
    with patch.object(service.external_service, 'get_categories') as mock_external:
        mock_external.return_value = ["Electronics", "Clothing"]
        result = service.get_categories()
        assert len(result) > 0
        assert "Electronics" in result

def test_get_categories_fallback():
    service = ProductDataService()
    with patch.object(service.external_service, 'get_categories') as mock_external:
        mock_external.side_effect = Exception("API Error")
        with patch.object(service.local_service, 'get_categories') as mock_local:
            mock_local.return_value = ["Smartphone", "Laptop"]
            result = service.get_categories()
            assert len(result) > 0
            assert "Smartphone" in result

def test_get_brands():
    service = ProductDataService()
    with patch.object(service.external_service, 'get_brands') as mock_external:
        mock_external.return_value = ["Apple", "Samsung"]
        result = service.get_brands()
        assert len(result) > 0
        assert "Apple" in result

def test_get_brands_fallback():
    service = ProductDataService()
    with patch.object(service.external_service, 'get_brands') as mock_external:
        mock_external.side_effect = Exception("API Error")
        with patch.object(service.local_service, 'get_brands') as mock_local:
            mock_local.return_value = ["Apple", "Samsung"]
            result = service.get_brands()
            assert len(result) > 0
            assert "Apple" in result

@pytest.mark.asyncio
async def test_get_product_details():
    service = ProductDataService()
    with patch.object(service.external_service, 'get_product_details') as mock_external:
        mock_external.return_value = {"id": "1", "name": "Test Product"}
        result = await service.get_product_details("1", "fakestoreapi")
        assert result is not None
        assert result["name"] == "Test Product"

@pytest.mark.asyncio
async def test_get_product_details_local():
    service = ProductDataService()
    with patch.object(service.local_service, 'get_product_details') as mock_local:
        mock_local.return_value = {"id": "1", "name": "Local Product"}
        result = await service.get_product_details("1", "local")
        assert result is not None
        assert result["name"] == "Local Product"

@pytest.mark.asyncio
async def test_get_product_details_fallback():
    service = ProductDataService()
    with patch.object(service.external_service, 'get_product_details') as mock_external:
        mock_external.side_effect = Exception("API Error")
        with patch.object(service.local_service, 'get_product_details') as mock_local:
            mock_local.return_value = {"id": "1", "name": "Fallback Product"}
            result = await service.get_product_details("1", "fakestoreapi")
            assert result is not None
            assert result["name"] == "Fallback Product"

def test_get_products():
    service = ProductDataService()
    with patch.object(service.external_service, 'get_products') as mock_external:
        mock_external.return_value = [{"id": "1", "name": "External Product"}]
        result = service.get_products(5)
        assert len(result) > 0
        assert result[0]["name"] == "External Product"

def test_get_products_fallback():
    service = ProductDataService()
    with patch.object(service.external_service, 'get_products') as mock_external:
        mock_external.side_effect = Exception("API Error")
        with patch.object(service.local_service, 'get_products') as mock_local:
            mock_local.return_value = [{"id": "1", "name": "Fallback Product"}]
            result = service.get_products(5)
            assert len(result) > 0
            assert result[0]["name"] == "Fallback Product"

def test_get_top_rated_products():
    service = ProductDataService()
    with patch.object(service.external_service, 'get_top_rated_products') as mock_external:
        mock_external.return_value = [{"id": "1", "name": "Top Rated"}]
        result = service.get_top_rated_products(5)
        assert len(result) > 0
        assert result[0]["name"] == "Top Rated"

def test_get_top_rated_products_fallback():
    service = ProductDataService()
    with patch.object(service.external_service, 'get_top_rated_products') as mock_external:
        mock_external.side_effect = Exception("API Error")
        with patch.object(service.local_service, 'get_top_rated_products') as mock_local:
            mock_local.return_value = [{"id": "1", "name": "Fallback Top Rated"}]
            result = service.get_top_rated_products(5)
            assert len(result) > 0
            assert result[0]["name"] == "Fallback Top Rated"

def test_get_best_selling_products():
    service = ProductDataService()
    with patch.object(service.external_service, 'get_best_selling_products') as mock_external:
        mock_external.return_value = [{"id": "1", "name": "Best Selling"}]
        result = service.get_best_selling_products(5)
        assert len(result) > 0
        assert result[0]["name"] == "Best Selling"

def test_get_best_selling_products_fallback():
    service = ProductDataService()
    with patch.object(service.external_service, 'get_best_selling_products') as mock_external:
        mock_external.side_effect = Exception("API Error")
        with patch.object(service.local_service, 'get_best_selling_products') as mock_local:
            mock_local.return_value = [{"id": "1", "name": "Fallback Best Selling"}]
            result = service.get_best_selling_products(5)
            assert len(result) > 0
            assert result[0]["name"] == "Fallback Best Selling"

def test_test_connection():
    service = ProductDataService()
    with patch.object(service.external_service, 'test_connection') as mock_external:
        mock_external.return_value = True
        result = service.test_connection()
        assert result == True

def test_test_connection_failure():
    service = ProductDataService()
    with patch.object(service.external_service, 'test_connection') as mock_external:
        mock_external.return_value = False
        result = service.test_connection()
        assert result == False 