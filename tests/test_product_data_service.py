import pytest
from unittest.mock import patch, MagicMock
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService

@pytest.fixture
def product_service():
    return ProductDataService()

@pytest.fixture
def mock_local_service():
    with patch('app.services.product_data_service.LocalProductService') as mock:
        service_instance = MagicMock()
        mock.return_value = service_instance
        yield service_instance

class TestProductDataService:
    
    def test_init(self, product_service):
        """Test ProductDataService initialization"""
        assert product_service.local_service is not None
        assert isinstance(product_service.local_service, LocalProductService)
    
    @pytest.mark.asyncio
    async def test_search_products_success(self, product_service, mock_local_service):
        """Test successful product search"""
        mock_products = [
            {"id": "1", "name": "Test Product", "price": 1000000}
        ]
        mock_local_service.search_products.return_value = mock_products
        
        result = await product_service.search_products("test", 5)
        
        assert result == mock_products
        mock_local_service.search_products.assert_called_once_with("test", 5)
    
    @pytest.mark.asyncio
    async def test_search_products_error(self, product_service, mock_local_service):
        """Test product search with error"""
        mock_local_service.search_products.side_effect = Exception("Test error")
        
        result = await product_service.search_products("test", 5)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_products_with_search(self, product_service, mock_local_service):
        """Test get_products with search parameter"""
        mock_products = [{"id": "1", "name": "Test"}]
        mock_local_service.search_products.return_value = mock_products
        
        result = await product_service.get_products(search="test", limit=5)
        
        assert result == mock_products
        mock_local_service.search_products.assert_called_once_with("test", 5)
    
    @pytest.mark.asyncio
    async def test_get_products_with_category(self, product_service, mock_local_service):
        """Test get_products with category parameter"""
        mock_products = [{"id": "1", "name": "Test", "category": "smartphone"}]
        mock_local_service.get_products_by_category.return_value = mock_products
        
        result = await product_service.get_products(category="smartphone", limit=5)
        
        assert result == mock_products
        mock_local_service.get_products_by_category.assert_called_once_with("smartphone", 5)
    
    @pytest.mark.asyncio
    async def test_get_products_default(self, product_service, mock_local_service):
        """Test get_products without parameters"""
        mock_products = [{"id": "1", "name": "Test"}]
        mock_local_service.get_products.return_value = mock_products
        
        result = await product_service.get_products(limit=10)
        
        assert result == mock_products
        mock_local_service.get_products.assert_called_once_with(10)
    
    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_service, mock_local_service):
        """Test getting categories successfully"""
        mock_categories = ["smartphone", "laptop", "tablet"]
        mock_local_service.get_categories.return_value = mock_categories
        
        result = await product_service.get_categories()
        
        assert result == mock_categories
        mock_local_service.get_categories.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_categories_error(self, product_service, mock_local_service):
        """Test getting categories with error"""
        mock_local_service.get_categories.side_effect = Exception("Test error")
        
        result = await product_service.get_categories()
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_top_rated_products(self, product_service, mock_local_service):
        """Test getting top rated products"""
        mock_products = [{"id": "1", "name": "Top Product", "rating": 4.9}]
        mock_local_service.get_top_rated_products.return_value = mock_products
        
        result = await product_service.get_top_rated_products(5)
        
        assert result == mock_products
        mock_local_service.get_top_rated_products.assert_called_once_with(5)
    
    @pytest.mark.asyncio
    async def test_get_best_selling_products(self, product_service, mock_local_service):
        """Test getting best selling products"""
        mock_products = [{"id": "1", "name": "Best Seller", "sold": 1000}]
        mock_local_service.get_best_selling_products.return_value = mock_products
        
        result = await product_service.get_best_selling_products(5)
        
        assert result == mock_products
        mock_local_service.get_best_selling_products.assert_called_once_with(5)
    
    def test_get_products_by_category(self, product_service, mock_local_service):
        """Test getting products by category"""
        mock_products = [{"id": "1", "name": "Smartphone", "category": "smartphone"}]
        mock_local_service.get_products_by_category.return_value = mock_products
        
        result = product_service.get_products_by_category("smartphone", 5)
        
        assert result == mock_products
        mock_local_service.get_products_by_category.assert_called_once_with("smartphone", 5)
    
    def test_get_all_products(self, product_service, mock_local_service):
        """Test getting all products"""
        mock_products = [{"id": "1", "name": "Product 1"}, {"id": "2", "name": "Product 2"}]
        mock_local_service.get_products.return_value = mock_products
        
        result = product_service.get_all_products(10)
        
        assert result == mock_products
        mock_local_service.get_products.assert_called_once_with(10)
    
    def test_get_product_details(self, product_service, mock_local_service):
        """Test getting product details"""
        mock_product = {"id": "1", "name": "Test Product", "price": 1000000}
        mock_local_service.get_product_details.return_value = mock_product
        
        result = product_service.get_product_details("1")
        
        assert result == mock_product
        mock_local_service.get_product_details.assert_called_once_with("1")
    
    def test_get_brands(self, product_service, mock_local_service):
        """Test getting brands"""
        mock_brands = ["Apple", "Samsung", "Sony"]
        mock_local_service.get_brands.return_value = mock_brands
        
        result = product_service.get_brands()
        
        assert result == mock_brands
        mock_local_service.get_brands.assert_called_once()
    
    def test_get_products_by_brand(self, product_service, mock_local_service):
        """Test getting products by brand"""
        mock_products = [{"id": "1", "name": "iPhone", "brand": "Apple"}]
        mock_local_service.get_products_by_brand.return_value = mock_products
        
        result = product_service.get_products_by_brand("Apple", 5)
        
        assert result == mock_products
        mock_local_service.get_products_by_brand.assert_called_once_with("Apple", 5) 