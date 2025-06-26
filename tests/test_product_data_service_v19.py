import pytest
from unittest.mock import MagicMock
import asyncio
import logging

# Import the actual classes from their expected paths
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService

# Configure the logger for testing to capture messages
# The logger in the service file is named after its module path
logger = logging.getLogger('app.services.product_data_service')
logger.setLevel(logging.INFO)  # Ensure info and error logs are captured during tests

@pytest.fixture
def mock_local_product_service(mocker):
    """
    Fixture to mock LocalProductService instance created by ProductDataService.
    We patch the LocalProductService class definition at the module level where
    ProductDataService imports it, so any instance created by ProductDataService
    will be our mock.
    """
    mock_instance = MagicMock(spec=LocalProductService)
    # The patch target is the path where LocalProductService is *imported* within product_data_service.py
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_instance)
    return mock_instance

@pytest.fixture
def product_data_service(mock_local_product_service):
    """
    Fixture to provide an instance of ProductDataService with mocked LocalProductService.
    """
    return ProductDataService()

@pytest.mark.asyncio
class TestProductDataService:
    """
    Comprehensive test suite for ProductDataService.
    Aims for high coverage by testing all methods,
    including success, no results/not found, and error scenarios.
    Proper mocking of LocalProductService is used to isolate testing.
    """

    async def test_init(self, product_data_service, mock_local_product_service, caplog):
        """
        Test ProductDataService initialization.
        Verifies that LocalProductService is instantiated and logging occurs.
        """
        # Re-initialize the service within the test to capture its specific init logs
        # Ensure caplog captures from the correct logger
        with caplog.at_level(logging.INFO, logger='app.services.product_data_service'):
            service = ProductDataService()
            assert isinstance(service.local_service, MagicMock)
            assert service.local_service is mock_local_product_service
            assert "ProductDataService initialized with LocalProductService" in caplog.text

    async def test_search_products_success(self, product_data_service, mock_local_product_service, caplog):
        """
        Test search_products method with successful product retrieval.
        Verifies correct parameters, return value, and info logging.
        """
        expected_products = [{"id": "1", "name": "Laptop", "price": 1200}, {"id": "2", "name": "Tablet", "price": 500}]
        mock_local_product_service.search_products.return_value = expected_products

        with caplog.at_level(logging.INFO, logger='app.services.product_data_service'):
            products = await product_data_service.search_products("tech", limit=2)

            mock_local_product_service.search_products.assert_called_once_with("tech", 2)
            assert products == expected_products
            assert f"Searching products with keyword: tech" in caplog.text
            assert f"Found {len(expected_products)} products for keyword: tech" in caplog.text

    async def test_search_products_no_results(self, product_data_service, mock_local_product_service, caplog):
        """
        Test search_products method when no results are found.
        Verifies empty list return and appropriate logging.
        """
        mock_local_product_service.search_products.return_value = []

        with caplog.at_level(logging.INFO, logger='app.services.product_data_service'):
            products = await product_data_service.search_products("nonexistent_keyword")

            mock_local_product_service.search_products.assert_called_once_with("nonexistent_keyword", 10)
            assert products == []
            assert "Found 0 products for keyword: nonexistent_keyword" in caplog.text

    async def test_search_products_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test search_products method when an error occurs during local service call.
        Verifies empty list return and error logging.
        """
        mock_local_product_service.search_products.side_effect = Exception("Simulated service error")

        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            products = await product_data_service.search_products("error_keyword")

            mock_local_product_service.search_products.assert_called_once_with("error_keyword", 10)
            assert products == []
            assert "Error searching products: Simulated service error" in caplog.text


    @pytest.mark.parametrize("search_keyword, category_name, expected_method_name", [
        ("search_term", None, "search_products"),
        (None, "electronics", "get_products_by_category"),
        (None, None, "get_all_products"),
    ])
    async def test_get_products_delegation(self, product_data_service, mocker, search_keyword, category_name, expected_method_name):
        """
        Test get_products method delegates to the correct internal method
        based on provided parameters (search, category, or default to all).
        Mocks internal methods to verify call paths.
        """
        # Patch internal methods of ProductDataService itself
        mock_search = mocker.patch.object(product_data_service, 'search_products', return_value=[{"id": "s"}])
        mock_get_by_category = mocker.patch.object(product_data_service, 'get_products_by_category', return_value=[{"id": "c"}])
        mock_get_all = mocker.patch.object(product_data_service, 'get_all_products', return_value=[{"id": "a"}])

        result_limit = 5
        result = await product_data_service.get_products(limit=result_limit, category=category_name, search=search_keyword)

        if expected_method_name == "search_products":
            mock_search.assert_called_once_with(search_keyword, result_limit)
            assert result == [{"id": "s"}]
            mock_get_by_category.assert_not_called()
            mock_get_all.assert_not_called()
        elif expected_method_name == "get_products_by_category":
            mock_get_by_category.assert_called_once_with(category_name, result_limit)
            assert result == [{"id": "c"}]
            mock_search.assert_not_called()
            mock_get_all.assert_not_called()
        else: # expected_method_name == "get_all_products"
            mock_get_all.assert_called_once_with(result_limit)
            assert result == [{"id": "a"}]
            mock_search.assert_not_called()
            mock_get_by_category.assert_not_called()

    async def test_get_products_error_fallback(self, product_data_service, mock_local_product_service, caplog, mocker):
        """
        Test get_products method error handling fallback.
        If an internal method call fails, it should log an error and call
        self.local_service.get_products as a fallback.
        """
        # Make one of the delegated methods raise an error (e.g., get_all_products)
        mocker.patch.object(product_data_service, 'get_all_products', side_effect=ValueError("Internal delegation error"))

        # Configure the fallback behavior of mock_local_product_service.get_products (the sync method)
        expected_fallback_products = [{"id": "fallback_prod", "name": "Fallback Item"}]
        mock_local_product_service.get_products.return_value = expected_fallback_products

        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            products = await product_data_service.get_products(limit=15)

            assert products == expected_fallback_products
            mock_local_product_service.get_products.assert_called_once_with(15)
            assert "Error getting products: Internal delegation error" in caplog.text


    async def test_get_categories_success(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_categories method with successful retrieval.
        """
        expected_categories = ["Electronics", "Books", "Clothing"]
        mock_local_product_service.get_categories.return_value = expected_categories
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'): # Assert no error logs
            categories = await product_data_service.get_categories()
            
            mock_local_product_service.get_categories.assert_called_once()
            assert categories == expected_categories
            assert "Error getting categories" not in caplog.text

    async def test_get_categories_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_categories method error handling.
        Verifies empty list return and error logging.
        """
        mock_local_product_service.get_categories.side_effect = Exception("Category service unreachable")
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            categories = await product_data_service.get_categories()
            
            mock_local_product_service.get_categories.assert_called_once()
            assert categories == []
            assert "Error getting categories: Category service unreachable" in caplog.text

    async def test_get_top_rated_products_success(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_top_rated_products method with successful retrieval.
        """
        expected_products = [{"id": "tr1", "rating": 5, "name": "Highly Rated"}]
        mock_local_product_service.get_top_rated_products.return_value = expected_products
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            products = await product_data_service.get_top_rated_products(limit=5)
            
            mock_local_product_service.get_top_rated_products.assert_called_once_with(5)
            assert products == expected_products
            assert "Error getting top rated products" not in caplog.text

    async def test_get_top_rated_products_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_top_rated_products method error handling.
        Verifies empty list return and error logging.
        """
        mock_local_product_service.get_top_rated_products.side_effect = Exception("TRP fetch failed")
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            products = await product_data_service.get_top_rated_products()
            
            mock_local_product_service.get_top_rated_products.assert_called_once_with(10) # default limit
            assert products == []
            assert "Error getting top rated products: TRP fetch failed" in caplog.text

    async def test_get_best_selling_products_success(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_best_selling_products method with successful retrieval.
        """
        expected_products = [{"id": "bs1", "sales": 1000, "name": "Bestseller"}]
        mock_local_product_service.get_best_selling_products.return_value = expected_products
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            products = await product_data_service.get_best_selling_products(limit=5)
            
            mock_local_product_service.get_best_selling_products.assert_called_once_with(5)
            assert products == expected_products
            assert "Error getting best selling products" not in caplog.text

    async def test_get_best_selling_products_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_best_selling_products method error handling.
        Verifies empty list return and error logging.
        """
        mock_local_product_service.get_best_selling_products.side_effect = Exception("BSP fetch failed")
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            products = await product_data_service.get_best_selling_products()
            
            mock_local_product_service.get_best_selling_products.assert_called_once_with(10) # default limit
            assert products == []
            assert "Error getting best selling products: BSP fetch failed" in caplog.text

    def test_get_products_by_category_success_with_limit(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_products_by_category method with successful retrieval and limit slicing.
        """
        # Return more products than the limit to test slicing
        all_products = [{"id": "c1p1"}, {"id": "c1p2"}, {"id": "c1p3"}, {"id": "c1p4"}]
        mock_local_product_service.get_products_by_category.return_value = all_products
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            products = product_data_service.get_products_by_category("Electronics", limit=2)
            
            mock_local_product_service.get_products_by_category.assert_called_once_with("Electronics")
            assert products == [{"id": "c1p1"}, {"id": "c1p2"}] # Check limit slicing
            assert "Error getting products by category" not in caplog.text

    def test_get_products_by_category_success_no_limit_applied(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_products_by_category method when the returned products are fewer than the default limit.
        """
        # Return fewer products than default limit (10) to ensure slicing doesn't cut valid results
        all_products = [{"id": "c1p1"}, {"id": "c1p2"}]
        mock_local_product_service.get_products_by_category.return_value = all_products
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            products = product_data_service.get_products_by_category("Electronics") # Uses default limit 10
            
            mock_local_product_service.get_products_by_category.assert_called_once_with("Electronics")
            assert products == all_products
            assert "Error getting products by category" not in caplog.text

    def test_get_products_by_category_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_products_by_category method error handling.
        Verifies empty list return and error logging.
        """
        mock_local_product_service.get_products_by_category.side_effect = Exception("Category search failed")
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            products = product_data_service.get_products_by_category("Fashion")
            
            mock_local_product_service.get_products_by_category.assert_called_once_with("Fashion")
            assert products == []
            assert "Error getting products by category: Category search failed" in caplog.text

    def test_get_all_products_success(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_all_products method with successful retrieval.
        """
        expected_products = [{"id": "p1", "name": "Product A"}, {"id": "p2", "name": "Product B"}]
        mock_local_product_service.get_products.return_value = expected_products
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            products = product_data_service.get_all_products(limit=2)
            
            mock_local_product_service.get_products.assert_called_once_with(2)
            assert products == expected_products
            assert "Error getting all products" not in caplog.text

    def test_get_all_products_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_all_products method error handling.
        Verifies empty list return and error logging.
        """
        mock_local_product_service.get_products.side_effect = Exception("All products fetch error")
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            products = product_data_service.get_all_products() # Uses default limit 20
            
            mock_local_product_service.get_products.assert_called_once_with(20)
            assert products == []
            assert "Error getting all products: All products fetch error" in caplog.text

    def test_get_product_details_success(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_product_details method with successful retrieval.
        """
        expected_detail = {"id": "p123", "name": "Test Product", "description": "A description"}
        mock_local_product_service.get_product_details.return_value = expected_detail
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            details = product_data_service.get_product_details("p123")
            
            mock_local_product_service.get_product_details.assert_called_once_with("p123")
            assert details == expected_detail
            assert "Error getting product details" not in caplog.text

    def test_get_product_details_not_found(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_product_details method when product is not found.
        Verifies None return.
        """
        mock_local_product_service.get_product_details.return_value = None
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            details = product_data_service.get_product_details("nonexistent_id")
            
            mock_local_product_service.get_product_details.assert_called_once_with("nonexistent_id")
            assert details is None
            assert "Error getting product details" not in caplog.text

    def test_get_product_details_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_product_details method error handling.
        Verifies None return and error logging.
        """
        mock_local_product_service.get_product_details.side_effect = Exception("Details fetch failed")
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            details = product_data_service.get_product_details("error_id")
            
            mock_local_product_service.get_product_details.assert_called_once_with("error_id")
            assert details is None
            assert "Error getting product details: Details fetch failed" in caplog.text

    def test_get_brands_success(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_brands method with successful retrieval.
        """
        expected_brands = ["BrandA", "BrandB", "BrandC"]
        mock_local_product_service.get_brands.return_value = expected_brands
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            brands = product_data_service.get_brands()
            
            mock_local_product_service.get_brands.assert_called_once()
            assert brands == expected_brands
            assert "Error getting brands" not in caplog.text

    def test_get_brands_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_brands method error handling.
        Verifies empty list return and error logging.
        """
        mock_local_product_service.get_brands.side_effect = Exception("Brands fetch failed")
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            brands = product_data_service.get_brands()
            
            mock_local_product_service.get_brands.assert_called_once()
            assert brands == []
            assert "Error getting brands: Brands fetch failed" in caplog.text

    def test_get_products_by_brand_success_with_limit(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_products_by_brand method with successful retrieval and limit slicing.
        """
        # Return more products than the limit to test slicing
        all_products = [{"id": "b1p1"}, {"id": "b1p2"}, {"id": "b1p3"}, {"id": "b1p4"}]
        mock_local_product_service.get_products_by_brand.return_value = all_products
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            products = product_data_service.get_products_by_brand("BrandX", limit=2)
            
            mock_local_product_service.get_products_by_brand.assert_called_once_with("BrandX")
            assert products == [{"id": "b1p1"}, {"id": "b1p2"}] # Check limit slicing
            assert "Error getting products by brand" not in caplog.text

    def test_get_products_by_brand_success_no_limit_applied(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_products_by_brand method when the returned products are fewer than the default limit.
        """
        # Return fewer products than default limit (10) to ensure slicing doesn't cut valid results
        all_products = [{"id": "b1p1"}, {"id": "b1p2"}]
        mock_local_product_service.get_products_by_brand.return_value = all_products
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            products = product_data_service.get_products_by_brand("BrandX") # Uses default limit 10
            
            mock_local_product_service.get_products_by_brand.assert_called_once_with("BrandX")
            assert products == all_products
            assert "Error getting products by brand" not in caplog.text

    def test_get_products_by_brand_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_products_by_brand method error handling.
        Verifies empty list return and error logging.
        """
        mock_local_product_service.get_products_by_brand.side_effect = Exception("Brand search failed")
        
        with caplog.at_level(logging.ERROR, logger='app.services.product_data_service'):
            products = product_data_service.get_products_by_brand("BrandY")
            
            mock_local_product_service.get_products_by_brand.assert_called_once_with("BrandY")
            assert products == []
            assert "Error getting products by brand: Brand search failed" in caplog.text

    async def test_smart_search_products_success(self, product_data_service, mock_local_product_service):
        """
        Test smart_search_products method with successful search.
        Verifies correct parameters, return value (products and message).
        """
        expected_products = [{"id": "s1", "name": "Smart Gadget"}, {"id": "s2", "name": "Smart Watch"}]
        expected_message = "Search completed successfully with 2 results."
        mock_local_product_service.smart_search_products.return_value = (expected_products, expected_message)

        products, message = await product_data_service.smart_search_products(
            keyword="smart", category="electronics", max_price=1000, limit=3
        )

        mock_local_product_service.smart_search_products.assert_called_once_with(
            "smart", "electronics", 1000, 3
        )
        assert products == expected_products
        assert message == expected_message

    async def test_smart_search_products_default_params(self, product_data_service, mock_local_product_service):
        """
        Test smart_search_products method with default parameters.
        """
        mock_local_product_service.smart_search_products.return_value = ([], "No products found for default search.")

        products, message = await product_data_service.smart_search_products()

        mock_local_product_service.smart_search_products.assert_called_once_with(
            '', None, None, 5
        )
        assert products == []
        assert message == "No products found for default search."

    async def test_smart_search_products_error_propagates(self, product_data_service, mock_local_product_service):
        """
        Test smart_search_products method when an error occurs.
        This method does NOT have a try-except, so the exception should propagate.
        """
        mock_local_product_service.smart_search_products.side_effect = RuntimeError("Local smart search failed")

        with pytest.raises(RuntimeError, match="Local smart search failed"):
            await product_data_service.smart_search_products("error_case")

        mock_local_product_service.smart_search_products.assert_called_once_with("error_case", None, None, 5)