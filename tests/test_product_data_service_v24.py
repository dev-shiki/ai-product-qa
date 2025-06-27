import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

# Adjust path for imports. Assuming project root is two levels up from this test file.
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.insert(0, project_root)

# Import the class under test and its dependency
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService # Used for isinstance check in init test

# --- Fixtures ---

@pytest.fixture
def mock_local_service():
    """
    Mocks the LocalProductService dependency.
    This mock will be used for all tests to isolate ProductDataService logic.
    """
    with patch('app.services.product_data_service.LocalProductService') as MockLocalProductServiceClass:
        # Create an instance of the mock class to return from the patch
        # This instance's methods (e.g., search_products) will be MagicMocks by default
        mock_instance = MockLocalProductServiceClass.return_value
        yield mock_instance

@pytest.fixture
def product_data_service(mock_local_service):
    """
    Provides an instance of ProductDataService with its LocalProductService
    dependency mocked.
    """
    service = ProductDataService()
    # Ensure the internal local_service attribute truly points to our mock
    # This is important for methods that directly call self.local_service.method()
    service.local_service = mock_local_service
    return service

@pytest.fixture
def sample_products():
    """Provides consistent sample product data for tests."""
    return [
        {"id": "1", "name": "Laptop Pro", "price": 1200, "category": "Electronics", "rating": 4.5, "brand": "TechBrand"},
        {"id": "2", "name": "Mechanical Keyboard", "price": 150, "category": "Electronics", "rating": 4.8, "brand": "KeyMaster"},
        {"id": "3", "name": "Ergonomic Desk Chair", "price": 300, "category": "Furniture", "rating": 4.2, "brand": "SitWell"},
        {"id": "4", "name": "Wireless Mouse", "price": 50, "category": "Electronics", "rating": 4.0, "brand": "TechBrand"},
        {"id": "5", "name": "Gaming Headset", "price": 100, "category": "Accessories", "rating": 4.7, "brand": "AudioPro"},
    ]

@pytest.fixture
def sample_categories():
    """Provides consistent sample category data for tests."""
    return ["Electronics", "Furniture", "Accessories", "Books"]

@pytest.fixture
def sample_brands():
    """Provides consistent sample brand data for tests."""
    return ["TechBrand", "KeyMaster", "SitWell", "AudioPro"]

# --- Test Cases ---

class TestProductDataService:

    @pytest.mark.asyncio
    async def test_init_sets_local_service(self, mock_local_service):
        """
        Verify that ProductDataService initializes correctly by setting its
        local_service attribute to an instance of LocalProductService (or its mock).
        """
        service = ProductDataService()
        assert isinstance(service.local_service, MagicMock) # It's a mock instance
        mock_local_service.assert_called_once() # Ensure the LocalProductService constructor was called

    @pytest.mark.asyncio
    async def test_search_products_success(self, product_data_service, mock_local_service, sample_products):
        """
        Test that search_products successfully retrieves and returns product data
        from the local service.
        """
        mock_local_service.search_products.return_value = sample_products[:2]
        keyword = "laptop"
        limit = 2
        result = await product_data_service.search_products(keyword, limit)
        assert result == sample_products[:2]
        mock_local_service.search_products.assert_called_once_with(keyword, limit)

    @pytest.mark.asyncio
    async def test_search_products_empty_results(self, product_data_service, mock_local_service):
        """
        Test that search_products returns an empty list when the local service
        finds no products.
        """
        mock_local_service.search_products.return_value = []
        result = await product_data_service.search_products("nonexistent", 10)
        assert result == []
        mock_local_service.search_products.assert_called_once_with("nonexistent", 10)

    @pytest.mark.asyncio
    async def test_search_products_exception_handling(self, product_data_service, mock_local_service, caplog):
        """
        Test that search_products gracefully handles exceptions from the local
        service and returns an empty list, logging the error.
        """
        mock_local_service.search_products.side_effect = Exception("Search service unavailable")
        with caplog.at_level(logging.ERROR):
            result = await product_data_service.search_products("error_keyword", 5)
            assert result == []
            assert "Error searching products: Search service unavailable" in caplog.text
        mock_local_service.search_products.assert_called_once_with("error_keyword", 5)

    @pytest.mark.asyncio
    async def test_get_products_with_search_filter(self, product_data_service, sample_products):
        """
        Test that get_products delegates to search_products when a 'search'
        keyword is provided.
        """
        # Mock search_products directly on the service instance to control its behavior
        # and verify it's called, avoiding deep mocking of run_in_executor for this test.
        product_data_service.search_products = AsyncMock(return_value=sample_products[:1])
        result = await product_data_service.get_products(search="Laptop", limit=1)
        assert result == sample_products[:1]
        product_data_service.search_products.assert_called_once_with("Laptop", 1)
        # Ensure other filtering methods were not called
        assert not isinstance(product_data_service.get_products_by_category, MagicMock) or not product_data_service.get_products_by_category.called
        assert not isinstance(product_data_service.get_all_products, MagicMock) or not product_data_service.get_all_products.called

    @pytest.mark.asyncio
    async def test_get_products_with_category_filter(self, product_data_service, sample_products):
        """
        Test that get_products delegates to get_products_by_category when a 'category'
        is provided and 'search' is not.
        """
        product_data_service.get_products_by_category = MagicMock(return_value=sample_products[2:3])
        result = await product_data_service.get_products(category="Furniture", limit=1)
        assert result == sample_products[2:3]
        product_data_service.get_products_by_category.assert_called_once_with("Furniture", 1)
        # Ensure other filtering methods were not called
        assert not isinstance(product_data_service.search_products, AsyncMock) or not product_data_service.search_products.called
        assert not isinstance(product_data_service.get_all_products, MagicMock) or not product_data_service.get_all_products.called

    @pytest.mark.asyncio
    async def test_get_products_without_filters(self, product_data_service, sample_products):
        """
        Test that get_products delegates to get_all_products when neither 'search'
        nor 'category' filters are provided.
        """
        product_data_service.get_all_products = MagicMock(return_value=sample_products)
        result = await product_data_service.get_products(limit=5)
        assert result == sample_products
        product_data_service.get_all_products.assert_called_once_with(5)
        # Ensure other filtering methods were not called
        assert not isinstance(product_data_service.search_products, AsyncMock) or not product_data_service.search_products.called
        assert not isinstance(product_data_service.get_products_by_category, MagicMock) or not product_data_service.get_products_by_category.called

    @pytest.mark.asyncio
    async def test_get_products_exception_handling_and_fallback(self, product_data_service, mock_local_service, sample_products, caplog):
        """
        Test that get_products handles exceptions from its internal calls (e.g., search_products)
        and falls back to calling local_service.get_products.
        """
        # Simulate an error in the 'search' path
        product_data_service.search_products = AsyncMock(side_effect=Exception("Simulated search error"))
        # Mock the fallback method
        mock_local_service.get_products.return_value = sample_products
        
        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_products(search="failing_search", limit=10)
            assert result == sample_products # Should return results from fallback
            assert "Error getting products: Simulated search error" in caplog.text
        
        product_data_service.search_products.assert_called_once_with("failing_search", 10)
        mock_local_service.get_products.assert_called_once_with(10) # Verify fallback call

    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service, mock_local_service, sample_categories):
        """Test that get_categories returns the list of categories on success."""
        mock_local_service.get_categories.return_value = sample_categories
        result = await product_data_service.get_categories()
        assert result == sample_categories
        mock_local_service.get_categories.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_categories_empty(self, product_data_service, mock_local_service):
        """Test that get_categories returns an empty list when no categories are found."""
        mock_local_service.get_categories.return_value = []
        result = await product_data_service.get_categories()
        assert result == []
        mock_local_service.get_categories.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_categories_exception_handling(self, product_data_service, mock_local_service, caplog):
        """
        Test that get_categories handles exceptions from the local service and
        returns an empty list, logging the error.
        """
        mock_local_service.get_categories.side_effect = Exception("Category service unreachable")
        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_categories()
            assert result == []
            assert "Error getting categories: Category service unreachable" in caplog.text
        mock_local_service.get_categories.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service, mock_local_service, sample_products):
        """Test that get_top_rated_products returns top-rated products."""
        mock_local_service.get_top_rated_products.return_value = sorted(sample_products, key=lambda x: x['rating'], reverse=True)[:3]
        result = await product_data_service.get_top_rated_products(limit=3)
        assert len(result) == 3
        assert result[0]['name'] == "Mechanical Keyboard" # Highest rated
        mock_local_service.get_top_rated_products.assert_called_once_with(3)

    @pytest.mark.asyncio
    async def test_get_top_rated_products_empty(self, product_data_service, mock_local_service):
        """Test that get_top_rated_products returns an empty list when none are found."""
        mock_local_service.get_top_rated_products.return_value = []
        result = await product_data_service.get_top_rated_products(limit=5)
        assert result == []
        mock_local_service.get_top_rated_products.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_get_top_rated_products_exception_handling(self, product_data_service, mock_local_service, caplog):
        """
        Test that get_top_rated_products handles exceptions from the local service
        and returns an empty list, logging the error.
        """
        mock_local_service.get_top_rated_products.side_effect = Exception("Top rated service error")
        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_top_rated_products(limit=5)
            assert result == []
            assert "Error getting top rated products: Top rated service error" in caplog.text
        mock_local_service.get_top_rated_products.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service, mock_local_service, sample_products):
        """Test that get_best_selling_products returns best-selling products."""
        mock_local_service.get_best_selling_products.return_value = sample_products[::2] # Example best selling
        result = await product_data_service.get_best_selling_products(limit=3)
        assert len(result) == 3
        assert result == sample_products[::2]
        mock_local_service.get_best_selling_products.assert_called_once_with(3)

    @pytest.mark.asyncio
    async def test_get_best_selling_products_empty(self, product_data_service, mock_local_service):
        """Test that get_best_selling_products returns an empty list when none are found."""
        mock_local_service.get_best_selling_products.return_value = []
        result = await product_data_service.get_best_selling_products(limit=5)
        assert result == []
        mock_local_service.get_best_selling_products.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_get_best_selling_products_exception_handling(self, product_data_service, mock_local_service, caplog):
        """
        Test that get_best_selling_products handles exceptions from the local service
        and returns an empty list, logging the error.
        """
        mock_local_service.get_best_selling_products.side_effect = Exception("Best selling service error")
        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_best_selling_products(limit=5)
            assert result == []
            assert "Error getting best selling products: Best selling service error" in caplog.text
        mock_local_service.get_best_selling_products.assert_called_once_with(5)

    def test_get_products_by_category_success(self, product_data_service, mock_local_service, sample_products):
        """
        Test that get_products_by_category returns products filtered by category
        and respects the limit.
        """
        mock_local_service.get_products_by_category.return_value = [
            p for p in sample_products if p["category"] == "Electronics"
        ]
        category = "Electronics"
        limit = 2
        result = product_data_service.get_products_by_category(category, limit)
        assert len(result) == limit
        assert all(p["category"] == category for p in result)
        mock_local_service.get_products_by_category.assert_called_once_with(category) # Local service method does not take limit

    def test_get_products_by_category_empty(self, product_data_service, mock_local_service):
        """Test that get_products_by_category returns an empty list if no products match."""
        mock_local_service.get_products_by_category.return_value = []
        result = product_data_service.get_products_by_category("NonExistentCategory", 10)
        assert result == []
        mock_local_service.get_products_by_category.assert_called_once_with("NonExistentCategory")

    def test_get_products_by_category_exception_handling(self, product_data_service, mock_local_service, caplog):
        """
        Test that get_products_by_category handles exceptions from the local service
        and returns an empty list, logging the error.
        """
        mock_local_service.get_products_by_category.side_effect = Exception("Category lookup failed")
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_products_by_category("ErrorCategory", 5)
            assert result == []
            assert "Error getting products by category: Category lookup failed" in caplog.text
        mock_local_service.get_products_by_category.assert_called_once_with("ErrorCategory")

    def test_get_all_products_success(self, product_data_service, mock_local_service, sample_products):
        """Test that get_all_products returns all products up to the specified limit."""
        mock_local_service.get_products.return_value = sample_products
        limit = 3
        result = product_data_service.get_all_products(limit)
        assert result == sample_products[:limit]
        mock_local_service.get_products.assert_called_once_with(limit)

    def test_get_all_products_empty(self, product_data_service, mock_local_service):
        """Test that get_all_products returns an empty list when no products are available."""
        mock_local_service.get_products.return_value = []
        result = product_data_service.get_all_products(10)
        assert result == []
        mock_local_service.get_products.assert_called_once_with(10)

    def test_get_all_products_exception_handling(self, product_data_service, mock_local_service, caplog):
        """
        Test that get_all_products handles exceptions from the local service and
        returns an empty list, logging the error.
        """
        mock_local_service.get_products.side_effect = Exception("All products retrieve failed")
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_all_products(10)
            assert result == []
            assert "Error getting all products: All products retrieve failed" in caplog.text
        mock_local_service.get_products.assert_called_once_with(10)

    def test_get_product_details_found(self, product_data_service, mock_local_service, sample_products):
        """Test that get_product_details returns the product dictionary when found."""
        product_id = "1"
        mock_local_service.get_product_details.return_value = sample_products[0]
        result = product_data_service.get_product_details(product_id)
        assert result == sample_products[0]
        mock_local_service.get_product_details.assert_called_once_with(product_id)

    def test_get_product_details_not_found(self, product_data_service, mock_local_service):
        """Test that get_product_details returns None when the product is not found."""
        product_id = "999"
        mock_local_service.get_product_details.return_value = None
        result = product_data_service.get_product_details(product_id)
        assert result is None
        mock_local_service.get_product_details.assert_called_once_with(product_id)

    def test_get_product_details_exception_handling(self, product_data_service, mock_local_service, caplog):
        """
        Test that get_product_details handles exceptions from the local service and
        returns None, logging the error.
        """
        product_id = "error_id"
        mock_local_service.get_product_details.side_effect = Exception("Details service error")
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_product_details(product_id)
            assert result is None
            assert "Error getting product details: Details service error" in caplog.text
        mock_local_service.get_product_details.assert_called_once_with(product_id)

    def test_get_brands_success(self, product_data_service, mock_local_service, sample_brands):
        """Test that get_brands returns the list of brands on success."""
        mock_local_service.get_brands.return_value = sample_brands
        result = product_data_service.get_brands()
        assert result == sample_brands
        mock_local_service.get_brands.assert_called_once()

    def test_get_brands_empty(self, product_data_service, mock_local_service):
        """Test that get_brands returns an empty list when no brands are found."""
        mock_local_service.get_brands.return_value = []
        result = product_data_service.get_brands()
        assert result == []
        mock_local_service.get_brands.assert_called_once()

    def test_get_brands_exception_handling(self, product_data_service, mock_local_service, caplog):
        """
        Test that get_brands handles exceptions from the local service and
        returns an empty list, logging the error.
        """
        mock_local_service.get_brands.side_effect = Exception("Brands service unavailable")
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_brands()
            assert result == []
            assert "Error getting brands: Brands service unavailable" in caplog.text
        mock_local_service.get_brands.assert_called_once()

    def test_get_products_by_brand_success(self, product_data_service, mock_local_service, sample_products):
        """
        Test that get_products_by_brand returns products filtered by brand
        and respects the limit.
        """
        mock_local_service.get_products_by_brand.return_value = [
            p for p in sample_products if p.get("brand") == "TechBrand"
        ]
        brand = "TechBrand"
        limit = 1
        result = product_data_service.get_products_by_brand(brand, limit)
        assert len(result) == limit
        assert all(p.get("brand") == brand for p in result)
        mock_local_service.get_products_by_brand.assert_called_once_with(brand) # Local service method does not take limit

    def test_get_products_by_brand_empty(self, product_data_service, mock_local_service):
        """Test that get_products_by_brand returns an empty list if no products match."""
        mock_local_service.get_products_by_brand.return_value = []
        result = product_data_service.get_products_by_brand("NonExistentBrand", 10)
        assert result == []
        mock_local_service.get_products_by_brand.assert_called_once_with("NonExistentBrand")

    def test_get_products_by_brand_exception_handling(self, product_data_service, mock_local_service, caplog):
        """
        Test that get_products_by_brand handles exceptions from the local service
        and returns an empty list, logging the error.
        """
        mock_local_service.get_products_by_brand.side_effect = Exception("Brand lookup failed")
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_products_by_brand("ErrorBrand", 5)
            assert result == []
            assert "Error getting products by brand: Brand lookup failed" in caplog.text
        mock_local_service.get_products_by_brand.assert_called_once_with("ErrorBrand")

    @pytest.mark.asyncio
    async def test_smart_search_products_success(self, product_data_service, mock_local_service, sample_products):
        """
        Test that smart_search_products successfully performs a hybrid search
        and returns products and a message.
        """
        mock_local_service.smart_search_products.return_value = (sample_products[:2], "2 matching products found.")
        
        keyword = "smart"
        category = "Electronics"
        max_price = 1000
        limit = 2
        
        products, message = await product_data_service.smart_search_products(keyword, category, max_price, limit)
        
        assert products == sample_products[:2]
        assert message == "2 matching products found."
        mock_local_service.smart_search_products.assert_called_once_with(keyword, category, max_price, limit)

    @pytest.mark.asyncio
    async def test_smart_search_products_no_results(self, product_data_service, mock_local_service):
        """Test that smart_search_products returns empty results and an appropriate message."""
        mock_local_service.smart_search_products.return_value = ([], "No products match criteria.")
        products, message = await product_data_service.smart_search_products("nonexistent")
        assert products == []
        assert message == "No products match criteria."
        mock_local_service.smart_search_products.assert_called_once_with("nonexistent", None, None, 5) # Test default limit

    @pytest.mark.asyncio
    async def test_smart_search_products_exception_propagation(self, product_data_service, mock_local_service):
        """
        Test that smart_search_products propagates exceptions from the local service,
        as it does not have its own try-except block.
        """
        mock_local_service.smart_search_products.side_effect = Exception("Smart search backend error")
        
        with pytest.raises(Exception) as exc_info:
            await product_data_service.smart_search_products("error")
        assert "Smart search backend error" in str(exc_info.value)
        mock_local_service.smart_search_products.assert_called_once_with("error", None, None, 5)

    @pytest.mark.asyncio
    async def test_smart_search_products_default_parameters(self, product_data_service, mock_local_service):
        """
        Test that smart_search_products correctly uses its default parameters
        when no arguments are provided.
        """
        mock_local_service.smart_search_products.return_value = ([], "Default search executed.")
        await product_data_service.smart_search_products()
        mock_local_service.smart_search_products.assert_called_once_with('', None, None, 5)