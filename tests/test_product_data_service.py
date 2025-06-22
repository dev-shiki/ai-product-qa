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
        mock_local_service.search_products.return_value = mock_products
        
        result = await product_service.get_products(search="iPhone", limit=5)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("id" in p and "name" in p for p in result)
        mock_local_service.search_products.assert_called_once_with("iPhone", 5)
    
    @pytest.mark.asyncio
    async def test_get_products_with_category(self, product_service, mock_local_service):
        """Test get_products with category parameter"""
        mock_products = [{"id": "P001", "name": "iPhone 15 Pro Max", "category": "smartphone"}]
        mock_local_service.get_products_by_category.return_value = mock_products
        
        result = await product_service.get_products(category="smartphone", limit=5)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(p["category"] == "smartphone" for p in result)
        mock_local_service.get_products_by_category.assert_called_once_with("smartphone")
    
    @pytest.mark.asyncio
    async def test_get_products_default(self, product_service, mock_local_service):
        """Test get_products without parameters"""
        mock_products = [{"id": "P001", "name": "iPhone 15 Pro Max"}]
        mock_local_service.get_products.return_value = mock_products
        
        result = await product_service.get_products(limit=10)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("id" in p and "name" in p for p in result)
        mock_local_service.get_products.assert_called_once_with(10)
    
    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_service, mock_local_service):
        """Test getting categories successfully"""
        mock_categories = ["smartphone", "laptop", "tablet"]
        mock_local_service.get_categories.return_value = mock_categories
        
        result = await product_service.get_categories()
        
        assert set(result) >= {"smartphone", "laptop", "tablet"}
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
        mock_products = [{"id": "P008", "name": "MacBook Pro 16-inch M3 Pro", "specifications": {"rating": 4.9}}]
        mock_local_service.get_top_rated_products.return_value = mock_products
        
        result = await product_service.get_top_rated_products(5)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("specifications" in p and p["specifications"].get("rating", 0) >= 4.5 for p in result)
        mock_local_service.get_top_rated_products.assert_called_once_with(5)
    
    @pytest.mark.asyncio
    async def test_get_best_selling_products(self, product_service, mock_local_service):
        """Test getting best selling products"""
        mock_products = [{"id": "P016", "name": "iPad Pro 11-inch M2", "specifications": {"sold": 1000}}]
        mock_local_service.get_best_selling_products.return_value = mock_products
        
        result = await product_service.get_best_selling_products(5)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("specifications" in p and "sold" in p["specifications"] for p in result)
        mock_local_service.get_best_selling_products.assert_called_once_with(5)
    
    def test_get_products_by_category(self, product_service, mock_local_service):
        """Test getting products by category"""
        mock_products = [{"id": "P001", "name": "iPhone 15 Pro Max", "category": "smartphone"}]
        mock_local_service.get_products_by_category.return_value = mock_products
        
        result = product_service.get_products_by_category("smartphone", 5)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(p["category"] == "smartphone" for p in result)
        mock_local_service.get_products_by_category.assert_called_once_with("smartphone")
    
    def test_get_all_products(self, product_service, mock_local_service):
        """Test getting all products"""
        mock_products = [
            {"id": "P001", "name": "iPhone 15 Pro Max"},
            {"id": "P002", "name": "iPhone 15 Pro"}
        ]
        mock_local_service.get_products.return_value = mock_products
        
        result = product_service.get_all_products(10)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("id" in p and "name" in p for p in result)
        mock_local_service.get_products.assert_called_once_with(10)
    
    def test_get_product_details(self, product_service, mock_local_service):
        """Test getting product details"""
        mock_product = {"id": "P001", "name": "iPhone 15 Pro Max", "price": 21999000}
        mock_local_service.get_product_details.return_value = mock_product
        
        result = product_service.get_product_details("P001")
        
        assert isinstance(result, dict)
        assert result["id"] == "P001"
        assert "name" in result
        mock_local_service.get_product_details.assert_called_once_with("P001")
    
    def test_get_brands(self, product_service, mock_local_service):
        """Test getting brands"""
        mock_brands = ["Apple", "Samsung", "Sony"]
        mock_local_service.get_brands.return_value = mock_brands
        
        result = product_service.get_brands()
        
        assert set(["Apple", "Samsung", "Sony"]).issubset(set(result))
        mock_local_service.get_brands.assert_called_once()
    
    def test_get_products_by_brand(self, product_service, mock_local_service):
        """Test getting products by brand"""
        mock_products = [{"id": "P001", "name": "iPhone 15 Pro Max", "brand": "Apple"}]
        mock_local_service.get_products_by_brand.return_value = mock_products
        
        result = product_service.get_products_by_brand("Apple", 5)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(p["brand"] == "Apple" for p in result)
        mock_local_service.get_products_by_brand.assert_called_once_with("Apple")

    @pytest.mark.asyncio
    async def test_smart_search_products(self, product_service, mock_local_service):
        """Test smart_search_products method"""
        mock_local_service.smart_search_products.return_value = (
            [{"id": "P001", "name": "MacBook Pro", "category": "laptop"}],
            "Berikut laptop terbaik berdasarkan rating"
        )
        
        # Test with category and budget
        products, message = await product_service.smart_search_products(
            keyword="laptop terbaik", 
            category="laptop", 
            max_price=50000000, 
            limit=3
        )
        assert len(products) > 0
        assert "laptop" in message.lower()
        assert "terbaik" in message.lower()

    @pytest.mark.asyncio
    async def test_smart_search_products_no_category(self, product_service, mock_local_service):
        """Test smart_search_products without category"""
        mock_local_service.smart_search_products.return_value = (
            [{"id": "P001", "name": "iPhone 15 Pro Max", "category": "smartphone"}],
            "Berikut produk terbaik berdasarkan rating"
        )
        
        products, message = await product_service.smart_search_products(
            keyword="produk terbaik", 
            limit=3
        )
        assert len(products) > 0
        assert "terbaik" in message.lower()

    @pytest.mark.asyncio
    async def test_smart_search_products_budget_only(self, product_service, mock_local_service):
        """Test smart_search_products with budget only"""
        mock_local_service.smart_search_products.return_value = (
            [{"id": "P001", "name": "iPhone 15", "price": 14999000}],
            "Berikut produk yang sesuai budget"
        )
        
        products, message = await product_service.smart_search_products(
            keyword="produk murah", 
            max_price=1000000, 
            limit=3
        )
        assert len(products) > 0
        assert "budget" in message.lower()

    @pytest.mark.asyncio
    async def test_smart_search_products_empty_result(self, product_service, mock_local_service):
        """Test smart_search_products with no matching products"""
        mock_local_service.smart_search_products.return_value = (
            [{"id": "P001", "name": "iPhone 15 Pro Max"}],
            "Berikut rekomendasi produk terpopuler"
        )
        
        products, message = await product_service.smart_search_products(
            keyword="produk tidak ada", 
            category="nonexistent", 
            max_price=100, 
            limit=3
        )
        assert len(products) > 0  # Should fallback to popular products
        assert "terpopuler" in message.lower() 