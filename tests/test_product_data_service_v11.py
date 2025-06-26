import pytest
import asyncio
import logging
from unittest.mock import MagicMock, patch, AsyncMock

# Define fixtures for mocking LocalProductService and ProductDataService
# These are placed here for self-containment, but could also be in a conftest.py

@pytest.fixture
def mock_local_product_service_and_class():
    """Mocks the LocalProductService and provides both the mock class and instance."""
    with patch('app.services.product_data_service.LocalProductService') as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_class, mock_instance

@pytest.fixture
def product_data_service(mock_local_product_service_and_class):
    """Provides an instance of ProductDataService with a mocked LocalProductService."""
    _mock_class, mock_instance = mock_local_product_service_and_class
    from app.services.product_data_service import ProductDataService
    service = ProductDataService()
    # The __init__ method of ProductDataService will call LocalProductService()
    # which due to the patch will return our mock_instance.
    # So service.local_service will correctly be mock_instance.
    yield service

# Sample data for mocks
SAMPLE_PRODUCTS = [
    {"id": "1", "name": "Laptop Pro", "category": "Electronics", "price": 1200, "rating": 4.5, "brand": "TechCo", "is_bestseller": True},
    {"id": "2", "name": "Wireless Mouse", "category": "Electronics", "price": 25, "rating": 4.0, "brand": "TechCo", "is_bestseller": False},
    {"id": "3", "name": "Coffee Maker", "category": "Home Appliances", "price": 75, "rating": 4.2, "brand": "BrewGen", "is_bestseller": False},
    {"id": "4", "name": "Bluetooth Speaker", "category": "Audio", "price": 100, "rating": 4.8, "brand": "SoundBlast", "is_bestseller": True},
    {"id": "5", "name": "Desk Chair", "category": "Furniture", "price": 150, "rating": 3.9, "brand": "Comfort", "is_bestseller": False},
    {"id": "6", "name": "Gaming PC", "category": "Electronics", "price": 1800, "rating": 4.9, "brand": "GameX", "is_bestseller": True},
    {"id": "7", "name": "Keyboard", "category": "Electronics", "price": 50, "rating": 4.1, "brand": "TechCo", "is_bestseller": False},
]

SAMPLE_CATEGORIES = ["Electronics", "Home Appliances", "Audio", "Furniture"]
SAMPLE_BRANDS = ["TechCo", "BrewGen", "SoundBlast", "Comfort", "GameX"]


class TestProductDataService:
    """Comprehensive test suite for ProductDataService."""

    @pytest.mark.asyncio # Not strictly needed for sync test but doesn't hurt.
    async def test_init(self, mock_local_product_service_and_class, caplog):
        """
        Test ProductDataService initialization.
        Verifies that LocalProductService is instantiated and a log message is emitted.
        """
        mock_class, mock_instance = mock_local_product_service_and_class
        
        # Reset mocks before instantiating ProductDataService to ensure fresh state for this test
        mock_class.reset_mock()
        mock_instance.reset_mock()

        from app.services.product_data_service import ProductDataService
        with caplog.at_level(logging.INFO):
            service = ProductDataService()
            
            # Assert that the service's local_service attribute is the mock instance
            assert service.local_service is mock_instance
            
            # Assert that LocalProductService's constructor was called once
            mock_class.assert_called_once_with()
            
            # Assert the initialization log message
            assert "ProductDataService initialized with LocalProductService" in caplog.text

    @pytest.mark.asyncio
    async def test_search_products_success(self, product_data_service, mock_local_product_service_and_class):
        """Test successful product search with keyword and limit."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        expected_products = [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]]
        mock_local_service.search_products.return_value = expected_products
        
        keyword = "laptop"
        limit = 5
        result = await product_data_service.search_products(keyword, limit)
        
        mock_local_service.search_products.assert_called_once_with(keyword, limit)
        assert result == expected_products
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_search_products_no_results(self, product_data_service, mock_local_product_service_and_class):
        """Test product search returning no results."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.search_products.return_value = []
        
        result = await product_data_service.search_products("nonexistent", 10)
        
        assert result == []
        mock_local_service.search_products.assert_called_once_with("nonexistent", 10)

    @pytest.mark.asyncio
    async def test_search_products_exception(self, product_data_service, mock_local_product_service_and_class, caplog):
        """Test product search raising an exception, ensuring an empty list is returned and error is logged."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.search_products.side_effect = Exception("Search service unavailable")
        
        with caplog.at_level(logging.ERROR):
            result = await product_data_service.search_products("error", 10)
            
            assert result == []
            assert "Error searching products: Search service unavailable" in caplog.text
            mock_local_service.search_products.assert_called_once_with("error", 10)

    @pytest.mark.asyncio
    async def test_get_products_with_search_filter(self, product_data_service, mocker):
        """Test get_products when a search keyword is provided."""
        mock_search_products = mocker.patch.object(product_data_service, 'search_products', new_callable=AsyncMock)
        mock_search_products.return_value = [SAMPLE_PRODUCTS[0]]
        
        result = await product_data_service.get_products(limit=5, search="laptop")
        
        mock_search_products.assert_called_once_with("laptop", 5)
        assert result == [SAMPLE_PRODUCTS[0]]

    @pytest.mark.asyncio
    async def test_get_products_with_category_filter(self, product_data_service, mocker):
        """Test get_products when a category is provided."""
        mock_get_products_by_category = mocker.patch.object(product_data_service, 'get_products_by_category')
        mock_get_products_by_category.return_value = [SAMPLE_PRODUCTS[2]]
        
        result = await product_data_service.get_products(limit=5, category="Home Appliances")
        
        mock_get_products_by_category.assert_called_once_with("Home Appliances", 5)
        assert result == [SAMPLE_PRODUCTS[2]]

    @pytest.mark.asyncio
    async def test_get_products_without_filters(self, product_data_service, mocker):
        """Test get_products when no filters are provided, ensuring it calls get_all_products."""
        mock_get_all_products = mocker.patch.object(product_data_service, 'get_all_products')
        mock_get_all_products.return_value = SAMPLE_PRODUCTS
        
        result = await product_data_service.get_products(limit=5)
        
        mock_get_all_products.assert_called_once_with(5)
        assert result == SAMPLE_PRODUCTS

    @pytest.mark.asyncio
    async def test_get_products_exception_fallback(self, product_data_service, mock_local_product_service_and_class, mocker, caplog):
        """
        Test get_products' exception handling, ensuring it logs the error
        and falls back to local_service.get_products.
        """
        _mock_class, mock_local_service = mock_local_product_service_and_class
        
        # Mock an internal method called by get_products to raise an exception
        mocker.patch.object(product_data_service, 'search_products', side_effect=Exception("Internal search error"))
        
        # Mock the fallback method on the actual local_service mock
        mock_local_service.get_products.return_value = [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]]

        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_products(limit=10, search="something")
            
            assert result == [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]]
            assert "Error getting products: Internal search error" in caplog.text
            # Verify the fallback method was called with the correct limit
            mock_local_service.get_products.assert_called_once_with(10)

    @pytest.mark.asyncio
    async def test_get_products_exception_fallback_get_category(self, product_data_service, mock_local_product_service_and_class, mocker, caplog):
        """
        Test get_products' exception handling, ensuring it logs the error
        and falls back to local_service.get_products when category path fails.
        """
        _mock_class, mock_local_service = mock_local_product_service_and_class
        
        # Mock an internal method called by get_products to raise an exception
        mocker.patch.object(product_data_service, 'get_products_by_category', side_effect=Exception("Internal category error"))
        
        # Mock the fallback method on the actual local_service mock
        mock_local_service.get_products.return_value = [SAMPLE_PRODUCTS[2], SAMPLE_PRODUCTS[3]]

        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_products(limit=10, category="electronics")
            
            assert result == [SAMPLE_PRODUCTS[2], SAMPLE_PRODUCTS[3]]
            assert "Error getting products: Internal category error" in caplog.text
            # Verify the fallback method was called with the correct limit
            mock_local_service.get_products.assert_called_once_with(10)
            
    @pytest.mark.asyncio
    async def test_get_products_exception_fallback_get_all(self, product_data_service, mock_local_product_service_and_class, mocker, caplog):
        """
        Test get_products' exception handling, ensuring it logs the error
        and falls back to local_service.get_products when get_all_products path fails.
        """
        _mock_class, mock_local_service = mock_local_product_service_and_class
        
        # Mock an internal method called by get_products to raise an exception
        mocker.patch.object(product_data_service, 'get_all_products', side_effect=Exception("Internal all products error"))
        
        # Mock the fallback method on the actual local_service mock
        mock_local_service.get_products.return_value = [SAMPLE_PRODUCTS[4], SAMPLE_PRODUCTS[5]]

        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_products(limit=10)
            
            assert result == [SAMPLE_PRODUCTS[4], SAMPLE_PRODUCTS[5]]
            assert "Error getting products: Internal all products error" in caplog.text
            # Verify the fallback method was called with the correct limit
            mock_local_service.get_products.assert_called_once_with(10)

    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service, mock_local_product_service_and_class):
        """Test successful retrieval of categories."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.get_categories.return_value = SAMPLE_CATEGORIES
        
        result = await product_data_service.get_categories()
        
        assert result == SAMPLE_CATEGORIES
        mock_local_service.get_categories.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_categories_exception(self, product_data_service, mock_local_product_service_and_class, caplog):
        """Test get_categories raising an exception, ensuring an empty list is returned and error is logged."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.get_categories.side_effect = Exception("Category service error")
        
        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_categories()
            
            assert result == []
            assert "Error getting categories: Category service error" in caplog.text
            mock_local_service.get_categories.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service, mock_local_product_service_and_class):
        """Test successful retrieval of top rated products."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        expected_products = [SAMPLE_PRODUCTS[3], SAMPLE_PRODUCTS[5]] # Products with high rating
        mock_local_service.get_top_rated_products.return_value = expected_products
        
        result = await product_data_service.get_top_rated_products(limit=2)
        
        assert result == expected_products
        mock_local_service.get_top_rated_products.assert_called_once_with(2)

    @pytest.mark.asyncio
    async def test_get_top_rated_products_exception(self, product_data_service, mock_local_product_service_and_class, caplog):
        """Test get_top_rated_products raising an exception, ensuring an empty list is returned and error is logged."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.get_top_rated_products.side_effect = Exception("Top rated error")
        
        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_top_rated_products(limit=5)
            
            assert result == []
            assert "Error getting top rated products: Top rated error" in caplog.text
            mock_local_service.get_top_rated_products.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service, mock_local_product_service_and_class):
        """Test successful retrieval of best selling products."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        expected_products = [SAMPLE_PRODUCTS[5], SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[3]] # Products marked bestseller
        mock_local_service.get_best_selling_products.return_value = expected_products
        
        result = await product_data_service.get_best_selling_products(limit=2)
        
        assert result == expected_products[:2] # Check limit application
        mock_local_service.get_best_selling_products.assert_called_once_with(2)

    @pytest.mark.asyncio
    async def test_get_best_selling_products_exception(self, product_data_service, mock_local_product_service_and_class, caplog):
        """Test get_best_selling_products raising an exception, ensuring an empty list is returned and error is logged."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.get_best_selling_products.side_effect = Exception("Best selling error")
        
        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_best_selling_products(limit=5)
            
            assert result == []
            assert "Error getting best selling products: Best selling error" in caplog.text
            mock_local_service.get_best_selling_products.assert_called_once_with(5)

    def test_get_products_by_category_success(self, product_data_service, mock_local_product_service_and_class):
        """
        Test successful retrieval of products by category,
        ensuring the limit is applied by ProductDataService.
        """
        _mock_class, mock_local_service = mock_local_product_service_and_class
        # Mock local service to return more than the limit to test slicing
        mock_local_service.get_products_by_category.return_value = [
            SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1], SAMPLE_PRODUCTS[6]
        ] # 3 electronics
        
        result = product_data_service.get_products_by_category("Electronics", 2)
        
        assert result == [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]] # Expect only 2 due to limit
        # The underlying local service method doesn't take a limit
        mock_local_service.get_products_by_category.assert_called_once_with("Electronics")

    def test_get_products_by_category_no_results(self, product_data_service, mock_local_product_service_and_class):
        """Test get_products_by_category with no matching products."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.get_products_by_category.return_value = []
        
        result = product_data_service.get_products_by_category("NonExistent", 5)
        
        assert result == []
        mock_local_service.get_products_by_category.assert_called_once_with("NonExistent")

    def test_get_products_by_category_exception(self, product_data_service, mock_local_product_service_and_class, caplog):
        """Test get_products_by_category raising an exception, ensuring an empty list is returned and error is logged."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.get_products_by_category.side_effect = Exception("Category filter error")
        
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_products_by_category("ErrorCategory", 5)
            
            assert result == []
            assert "Error getting products by category: Category filter error" in caplog.text
            mock_local_service.get_products_by_category.assert_called_once_with("ErrorCategory")

    def test_get_all_products_success(self, product_data_service, mock_local_product_service_and_class):
        """Test successful retrieval of all products, ensuring the limit is passed to local service."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.get_products.return_value = SAMPLE_PRODUCTS # Assume local service returns all and handles limit
        
        result = product_data_service.get_all_products(limit=3)
        
        # ProductDataService's get_all_products just passes the limit to local_service.get_products
        # and returns the result. The LocalProductService mock returns the sliced list.
        assert result == SAMPLE_PRODUCTS[:3]
        mock_local_service.get_products.assert_called_once_with(3)

    def test_get_all_products_exception(self, product_data_service, mock_local_product_service_and_class, caplog):
        """Test get_all_products raising an exception, ensuring an empty list is returned and error is logged."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.get_products.side_effect = Exception("All products error")
        
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_all_products(limit=10)
            
            assert result == []
            assert "Error getting all products: All products error" in caplog.text
            mock_local_service.get_products.assert_called_once_with(10)

    def test_get_product_details_success(self, product_data_service, mock_local_product_service_and_class):
        """Test successful retrieval of product details by ID."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.get_product_details.return_value = SAMPLE_PRODUCTS[0]
        
        result = product_data_service.get_product_details("1")
        
        assert result == SAMPLE_PRODUCTS[0]
        mock_local_service.get_product_details.assert_called_once_with("1")

    def test_get_product_details_not_found(self, product_data_service, mock_local_product_service_and_class):
        """Test get_product_details for a non-existent product, expecting None."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.get_product_details.return_value = None
        
        result = product_data_service.get_product_details("nonexistent")
        
        assert result is None
        mock_local_service.get_product_details.assert_called_once_with("nonexistent")

    def test_get_product_details_exception(self, product_data_service, mock_local_product_service_and_class, caplog):
        """Test get_product_details raising an exception, ensuring None is returned and error is logged."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.get_product_details.side_effect = Exception("Details fetch error")
        
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_product_details("error_id")
            
            assert result is None
            assert "Error getting product details: Details fetch error" in caplog.text
            mock_local_service.get_product_details.assert_called_once_with("error_id")

    def test_get_brands_success(self, product_data_service, mock_local_product_service_and_class):
        """Test successful retrieval of available brands."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.get_brands.return_value = SAMPLE_BRANDS
        
        result = product_data_service.get_brands()
        
        assert result == SAMPLE_BRANDS
        mock_local_service.get_brands.assert_called_once()

    def test_get_brands_exception(self, product_data_service, mock_local_product_service_and_class, caplog):
        """Test get_brands raising an exception, ensuring an empty list is returned and error is logged."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.get_brands.side_effect = Exception("Brand service error")
        
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_brands()
            
            assert result == []
            assert "Error getting brands: Brand service error" in caplog.text
            mock_local_service.get_brands.assert_called_once()

    def test_get_products_by_brand_success(self, product_data_service, mock_local_product_service_and_class):
        """
        Test successful retrieval of products by brand,
        ensuring the limit is applied by ProductDataService.
        """
        _mock_class, mock_local_service = mock_local_product_service_and_class
        # Mock local service to return more than the limit to test slicing
        mock_local_service.get_products_by_brand.return_value = [
            SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1], SAMPLE_PRODUCTS[6]
        ] # 3 TechCo products
        
        result = product_data_service.get_products_by_brand("TechCo", 2)
        
        assert result == [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]] # Expect only 2 due to limit
        # The underlying local service method doesn't take a limit
        mock_local_service.get_products_by_brand.assert_called_once_with("TechCo")

    def test_get_products_by_brand_no_results(self, product_data_service, mock_local_product_service_and_class):
        """Test get_products_by_brand with no matching products."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.get_products_by_brand.return_value = []
        
        result = product_data_service.get_products_by_brand("NonExistentBrand", 5)
        
        assert result == []
        mock_local_service.get_products_by_brand.assert_called_once_with("NonExistentBrand")

    def test_get_products_by_brand_exception(self, product_data_service, mock_local_product_service_and_class, caplog):
        """Test get_products_by_brand raising an exception, ensuring an empty list is returned and error is logged."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.get_products_by_brand.side_effect = Exception("Brand filter error")
        
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_products_by_brand("ErrorBrand", 5)
            
            assert result == []
            assert "Error getting products by brand: Brand filter error" in caplog.text
            mock_local_service.get_products_by_brand.assert_called_once_with("ErrorBrand")

    @pytest.mark.asyncio
    async def test_smart_search_products_success_all_params(self, product_data_service, mock_local_product_service_and_class):
        """Test successful smart search when all parameters are specified."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.smart_search_products.return_value = ([SAMPLE_PRODUCTS[0]], "Found specific laptop")
        
        products, message = await product_data_service.smart_search_products(
            keyword="laptop", category="Electronics", max_price=1500, limit=1
        )
        
        assert products == [SAMPLE_PRODUCTS[0]]
        assert message == "Found specific laptop"
        mock_local_service.smart_search_products.assert_called_once_with(
            "laptop", "Electronics", 1500, 1
        )

    @pytest.mark.asyncio
    async def test_smart_search_products_success_keyword_only(self, product_data_service, mock_local_product_service_and_class):
        """Test successful smart search with only a keyword."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.smart_search_products.return_value = ([SAMPLE_PRODUCTS[1]], "Found wireless mouse")
        
        products, message = await product_data_service.smart_search_products(keyword="mouse")
        
        assert products == [SAMPLE_PRODUCTS[1]]
        assert message == "Found wireless mouse"
        mock_local_service.smart_search_products.assert_called_once_with("mouse", None, None, 5) # Default limit is 5

    @pytest.mark.asyncio
    async def test_smart_search_products_success_no_params(self, product_data_service, mock_local_product_service_and_class):
        """Test successful smart search with no parameters (defaults used)."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.smart_search_products.return_value = ([], "No products found")
        
        products, message = await product_data_service.smart_search_products()
        
        assert products == []
        assert message == "No products found"
        mock_local_service.smart_search_products.assert_called_once_with('', None, None, 5)

    @pytest.mark.asyncio
    async def test_smart_search_products_exception(self, product_data_service, mock_local_product_service_and_class):
        """Test smart_search_products raising an exception, ensuring it propagates."""
        _mock_class, mock_local_service = mock_local_product_service_and_class
        mock_local_service.smart_search_products.side_effect = Exception("Smart search internal error")
        
        # This method does not have its own try-except, so the exception should propagate
        with pytest.raises(Exception, match="Smart search internal error"):
            await product_data_service.smart_search_products(keyword="error_case")
        
        mock_local_service.smart_search_products.assert_called_once_with("error_case", None, None, 5)