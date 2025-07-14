# Documentation Improvement

**File**: `./tests/test_product_data_service.py`  
**Time**: 03:52:29  
**Type**: documentation_improvement

## Improvement

```python
import pytest
from unittest.mock import patch, MagicMock
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService

@pytest.fixture
def mock_local_service():
    return MagicMock()

@pytest.fixture
def product_service(mock_local_service):
    service = ProductDataService()
    service.local_service = mock_local_service
    return service

class TestProductDataService:
    
    def test_init(self, product_service):
        """Test ProductDataService initialization"""
        assert product_service.local_service is not None
        assert isinstance(product_service.local_service, MagicMock)
    
    @pytest.mark.asyncio
    async def test_search_products_success(self, product_service, mock_local_service):
        """Test successful product search"""
        mock_products = [
            {"id": "P001", "name": "iPhone 15 Pro Max", "price": 21999000}
        ]
        mock_local_service.search_products.return_value = mock_products
        
        result = await product_service.search_products("iPhone", 5)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("id" in p and "name" in p for p in result)
        mock_local_service.search_products.assert_called_once_with("iPhone", 5)
    
    @pytest.mark.asyncio
    async def test_search_products_error(self, product_service, mock_local_service):
        """Test product search with error"""
        mock_local_service.search_products.side_effect = Exception("Test error")
        
        result = await product_service.search_products("test", 5)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_products_with_search(self, product_service, mock_local_service):
        """Test get_products with search parameter"""
        mock_products = [{"id": "P001", "name": "iPhone 15 Pro Max"}]
        mock_local_service.get_products.return_value = mock_products
        
        result = await product_service.get_products(search="iPhone")
        
        assert isinstance(result, list)
        assert len(result) > 0
        mock_local_service.get_products.assert_called_once_with(search="iPhone", limit=100)
    
    @pytest.mark.asyncio
    async def test_get_products_no_search(self, product_service, mock_local_service):
        """Test get_products without search parameter"""
        mock_products = [{"id": "P002", "name": "Samsung Galaxy S23"}]
        mock_local_service.get_products.return_value = mock_products
        
        result = await product_service.get_products()
        
        assert isinstance(result, list)
        assert len(result) > 0
        mock_local_service.get_products.assert_called_once_with(search=None, limit=100)
    
    @pytest.mark.asyncio
    async def test_get_product_by_id_success(self, product_service, mock_local_service):
        """Test successful retrieval of product by ID"""
        mock_product = {"id": "P001", "name": "iPhone 15 Pro Max"}
        mock_local_service.get_product_by_id.return_value = mock_product
        
        result = await product_service.get_product_by_id("P001")
        
        assert isinstance(result, dict)
        assert result["id"] == "P001"
        mock_local_service.get_product_by_id.assert_called_once_with("P001")
    
    @pytest.mark.asyncio
    async def test_get_product_by_id_not_found(self, product_service, mock_local_service):
        """Test retrieval of product by ID when not found"""
        mock_local_service.get_product_by_id.return_value = None
        
        result = await product_service.get_product_by_id("NonExistentID")
        
        assert result is None
        mock_local_service.get_product_by_id.assert_called_once_with("NonExistentID")

    @pytest.mark.asyncio
    async def test_update_product_success(self, product_service, mock_local_service):
        """Test successful product update."""
        mock_product = {"id": "P001", "name": "Updated Product Name"}
        mock_local_service.update_product.return_value = mock_product

        result = await product_service.update_product("P001", {"name": "Updated Product Name"})

        assert isinstance(result, dict)
        assert result["id"] == "P001"
        assert result["name"] == "Updated Product Name"
        mock_local_service.update_product.assert_called_once_with("P001", {"name": "Updated Product Name"})

    @pytest.mark.asyncio
    async def test_update_product_not_found(self, product_service, mock_local_service):
        """Test product update when the product is not found."""
        mock_local_service.update_product.return_value = None

        result = await product_service.update_product("NonExistentID", {"name": "Updated Product Name"})

        assert result is None
        mock_local_service.update_product.assert_called_once_with("NonExistentID", {"name": "Updated Product Name"})
```

---
*Generated by Smart AI Bot*
