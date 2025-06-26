import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# Adjust import path based on your project structure
# Assuming tests are run from the project root or similar setup where 'app' is importable
from app.services.product_data_service import ProductDataService
# LocalProductService is imported within ProductDataService, so we need its module path for patching
from app.services import local_product_service 

@pytest.fixture
def mock_local_product_service(mocker):
    """
    Mocks the LocalProductService class that ProductDataService depends on.
    When ProductDataService tries to instantiate LocalProductService(), it will
    instead get this mock object.
    """
    # Patch the LocalProductService class in the module where ProductDataService imports it
    # We use autospec=True to ensure the mock has the same methods as the original class
    mock_service_instance = mocker.patch('app.services.product_data_service.LocalProductService', autospec=True).return_value
    return mock_service_instance

@pytest.fixture
def product_data_service(mock_local_product_service):
    """
    Provides an instance of ProductDataService with its LocalProductService dependency mocked.
    """
    service = ProductDataService()
    return service

@pytest.fixture(autouse=True)
def mock_logger(mocker):
    """
    Mocks the logger used in ProductDataService to prevent console output
    during tests and allow inspection of log calls.
    """
    return mocker.patch('app.services.product_data_service.logger')

class TestProductDataService:
    """Comprehensive test suite for ProductDataService."""

    def test_init_success(self, mock_local_product_service, mock_logger):
        """
        Test that ProductDataService initializes correctly and
        instantiates LocalProductService.
        """
        service = ProductDataService()
        mock_local_product_service.assert_called_once() # Ensure LocalProductService() was called
        assert isinstance(service.local_service, MagicMock) # Verify it's our mock
        mock_logger.info.assert_called_with("ProductDataService initialized with LocalProductService")

    @pytest.mark.asyncio
    async def test_search_products_success(self, product_data_service, mock_local_product_service, mocker):
        """
        Test search_products method for successful product retrieval
        via run_in_executor.
        """
        keyword = "laptop"
        limit = 5
        expected_products = [{"id": "L1", "name": "Gaming Laptop", "price": 1200}]

        # Mock asyncio.get_event_loop and its run_in_executor method
        mock_loop = mocker.AsyncMock()
        mocker.patch('asyncio.get_event_loop', return_value=mock_loop)

        # Set the return value for local_service.search_products *when it's called by run_in_executor*
        mock_local_product_service.search_products.return_value = expected_products
        # Set the return value for run_in_executor itself, as this is what the await will yield
        mock_loop.run_in_executor.return_value = expected_products

        result = await product_data_service.search_products(keyword, limit)

        assert result == expected_products
        mock_local_product_service.search_products.assert_called_once_with(keyword, limit)
        mock_loop.run_in_executor.assert_called_once_with(
            None, mock_local_product_service.search_products, keyword, limit
        )
        product_data_service.logger.info.assert_any_call(f"Searching products with keyword: {keyword}")
        product_data_service.logger.info.assert_any_call(f"Found {len(expected_products)} products for keyword: {keyword}")

    @pytest.mark.asyncio
    async def test_search_products_error(self, product_data_service, mock_local_product_service, mocker):
        """
        Test search_products method's error handling, ensuring it returns an empty list
        and logs the error.
        """
        keyword = "error_test"
        limit = 5
        error_message = "Mocked search failure"

        mock_loop = mocker.AsyncMock()
        mocker.patch('asyncio.get_event_loop', return_value=mock_loop)

        # Simulate an exception from the underlying local service method
        mock_local_product_service.search_products.side_effect = Exception(error_message)
        # The run_in_executor mock must also raise this exception for the await to catch it
        mock_loop.run_in_executor.side_effect = Exception(error_message)

        result = await product_data_service.search_products(keyword, limit)

        assert result == []
        mock_local_product_service.search_products.assert_called_once_with(keyword, limit)
        mock_loop.run_in_executor.assert_called_once_with(
            None, mock_local_product_service.search_products, keyword, limit
        )
        product_data_service.logger.error.assert_called_once_with(f"Error searching products: {error_message}")

    @pytest.mark.asyncio
    async def test_get_products_with_search_parameter(self, product_data_service, mocker):
        """
        Test get_products method when 'search' parameter is provided,
        ensuring it delegates to search_products.
        """
        # Patch the internal search_products method to control its behavior
        mock_search_products = mocker.patch.object(product_data_service, 'search_products', new_callable=AsyncMock)
        expected_products = [{"id": "s1", "name": "Search Result 1"}]
        mock_search_products.return_value = expected_products

        result = await product_data_service.get_products(search="query_term", limit=8)

        assert result == expected_products
        mock_search_products.assert_called_once_with("query_term", 8)
        # Ensure other branches were not taken
        mocker.patch.object(product_data_service, 'get_products_by_category', side_effect=AssertionError("Should not call get_products_by_category"))
        mocker.patch.object(product_data_service, 'get_all_products', side_effect=AssertionError("Should not call get_all_products"))

    @pytest.mark.asyncio
    async def test_get_products_with_category_parameter(self, product_data_service, mocker):
        """
        Test get_products method when 'category' parameter is provided (and no search),
        ensuring it delegates to get_products_by_category.
        """
        mock_get_products_by_category = mocker.patch.object(product_data_service, 'get_products_by_category')
        expected_products = [{"id": "c1", "name": "Category Item 1"}]
        mock_get_products_by_category.return_value = expected_products

        result = await product_data_service.get_products(category="electronics", limit=15)

        assert result == expected_products
        mock_get_products_by_category.assert_called_once_with("electronics", 15)
        # Ensure other branches were not taken
        mocker.patch.object(product_data_service, 'search_products', side_effect=AssertionError("Should not call search_products"))
        mocker.patch.object(product_data_service, 'get_all_products', side_effect=AssertionError("Should not call get_all_products"))

    @pytest.mark.asyncio
    async def test_get_products_no_filter_parameters(self, product_data_service, mocker):
        """
        Test get_products method when no filter parameters are provided,
        ensuring it delegates to get_all_products.
        """
        mock_get_all_products = mocker.patch.object(product_data_service, 'get_all_products')
        expected_products = [{"id": "a1", "name": "All Product 1"}]
        mock_get_all_products.return_value = expected_products

        result = await product_data_service.get_products(limit=10) # Default limit for this method is 20, but we pass 10

        assert result == expected_products
        mock_get_all_products.assert_called_once_with(10)
        # Ensure other branches were not taken
        mocker.patch.object(product_data_service, 'search_products', side_effect=AssertionError("Should not call search_products"))
        mocker.patch.object(product_data_service, 'get_products_by_category', side_effect=AssertionError("Should not call get_products_by_category"))

    @pytest.mark.asyncio
    async def test_get_products_error_fallback(self, product_data_service, mock_local_product_service, mocker):
        """
        Test get_products method's error handling, ensuring it falls back to
        local_service.get_products if an internal method (e.g., get_all_products) fails.
        """
        # Simulate an exception in one of the internal delegated calls (e.g., get_all_products)
        mocker.patch.object(product_data_service, 'get_all_products', side_effect=Exception("Simulated internal error"))

        expected_fallback_products = [{"id": "fb1", "name": "Fallback Product"}]
        mock_local_product_service.get_products.return_value = expected_fallback_products

        result = await product_data_service.get_products(limit=12)

        assert result == expected_fallback_products
        mock_local_product_service.get_products.assert_called_once_with(12)
        product_data_service.logger.error.assert_called_once() # Check that an error was logged

    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service, mock_local_product_service):
        """Test get_categories method for successful retrieval."""
        expected_categories = ["Books", "Electronics", "Clothing"]
        mock_local_product_service.get_categories.return_value = expected_categories
        result = await product_data_service.get_categories()
        assert result == expected_categories
        mock_local_product_service.get_categories.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_categories_error(self, product_data_service, mock_local_product_service):
        """Test get_categories method's error handling."""
        error_message = "Category service unavailable"
        mock_local_product_service.get_categories.side_effect = Exception(error_message)
        result = await product_data_service.get_categories()
        assert result == []
        product_data_service.logger.error.assert_called_once_with(f"Error getting categories: {error_message}")

    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service, mock_local_product_service):
        """Test get_top_rated_products method for successful retrieval."""
        expected_products = [{"id": "tr1", "name": "Top Rated Item", "rating": 4.9}]
        mock_local_product_service.get_top_rated_products.return_value = expected_products
        result = await product_data_service.get_top_rated_products(limit=3)
        assert result == expected_products
        mock_local_product_service.get_top_rated_products.assert_called_once_with(3)

    @pytest.mark.asyncio
    async def test_get_top_rated_products_error(self, product_data_service, mock_local_product_service):
        """Test get_top_rated_products method's error handling."""
        error_message = "DB read error for top rated"
        mock_local_product_service.get_top_rated_products.side_effect = Exception(error_message)
        result = await product_data_service.get_top_rated_products(limit=5)
        assert result == []
        product_data_service.logger.error.assert_called_once_with(f"Error getting top rated products: {error_message}")

    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service, mock_local_product_service):
        """Test get_best_selling_products method for successful retrieval."""
        expected_products = [{"id": "bs1", "name": "Best Seller", "sales": 1500}]
        mock_local_product_service.get_best_selling_products.return_value = expected_products
        result = await product_data_service.get_best_selling_products(limit=7)
        assert result == expected_products
        mock_local_product_service.get_best_selling_products.assert_called_once_with(7)

    @pytest.mark.asyncio
    async def test_get_best_selling_products_error(self, product_data_service, mock_local_product_service):
        """Test get_best_selling_products method's error handling."""
        error_message = "Sales data unreachable"
        mock_local_product_service.get_best_selling_products.side_effect = Exception(error_message)
        result = await product_data_service.get_best_selling_products(limit=10)
        assert result == []
        product_data_service.logger.error.assert_called_once_with(f"Error getting best selling products: {error_message}")

    def test_get_products_by_category_success_with_limit(self, product_data_service, mock_local_product_service):
        """
        Test get_products_by_category method for successful retrieval
        and correct application of limit.
        """
        category = "Electronics"
        all_products_in_category = [
            {"id": "e1", "name": "Laptop"}, {"id": "e2", "name": "Mouse"},
            {"id": "e3", "name": "Keyboard"}, {"id": "e4", "name": "Monitor"},
        ]
        mock_local_product_service.get_products_by_category.return_value = all_products_in_category

        # Test with limit < actual products
        result = product_data_service.get_products_by_category(category, limit=2)
        assert result == [{"id": "e1", "name": "Laptop"}, {"id": "e2", "name": "Mouse"}]
        mock_local_product_service.get_products_by_category.assert_called_once_with(category)
        mock_local_product_service.get_products_by_category.reset_mock() # Reset mock for next call

        # Test with limit > actual products (should return all available)
        result = product_data_service.get_products_by_category(category, limit=10)
        assert result == all_products_in_category
        mock_local_product_service.get_products_by_category.assert_called_once_with(category)

    def test_get_products_by_category_no_products(self, product_data_service, mock_local_product_service):
        """
        Test get_products_by_category when no products are found for the given category.
        """
        category = "NonExistent"
        mock_local_product_service.get_products_by_category.return_value = []
        result = product_data_service.get_products_by_category(category, limit=5)
        assert result == []
        mock_local_product_service.get_products_by_category.assert_called_once_with(category)

    def test_get_products_by_category_error(self, product_data_service, mock_local_product_service):
        """Test get_products_by_category method's error handling."""
        error_message = "Category filter failed"
        mock_local_product_service.get_products_by_category.side_effect = Exception(error_message)
        result = product_data_service.get_products_by_category("Books", limit=10)
        assert result == []
        product_data_service.logger.error.assert_called_once_with(f"Error getting products by category: {error_message}")

    def test_get_all_products_success(self, product_data_service, mock_local_product_service):
        """
        Test get_all_products method for successful retrieval
        and correct passing of limit to the local service.
        """
        all_products_data = [
            {"id": "p1", "name": "Prod 1"}, {"id": "p2", "name": "Prod 2"},
            {"id": "p3", "name": "Prod 3"}, {"id": "p4", "name": "Prod 4"}
        ]
        # local_service.get_products directly accepts the limit
        mock_local_product_service.get_products.return_value = all_products_data[:2] # Simulate local service returning 2 products for limit=2

        # Test with custom limit
        result = product_data_service.get_all_products(limit=2)
        assert result == all_products_data[:2]
        mock_local_product_service.get_products.assert_called_once_with(2)
        mock_local_product_service.get_products.reset_mock()

        # Test with default limit (20)
        mock_local_product_service.get_products.return_value = all_products_data # Simulate local service returning all for default limit
        result = product_data_service.get_all_products()
        assert result == all_products_data
        mock_local_product_service.get_products.assert_called_once_with(20)

    def test_get_all_products_no_products(self, product_data_service, mock_local_product_service):
        """Test get_all_products when no products are returned by the local service."""
        mock_local_product_service.get_products.return_value = []
        result = product_data_service.get_all_products(limit=5)
        assert result == []
        mock_local_product_service.get_products.assert_called_once_with(5)

    def test_get_all_products_error(self, product_data_service, mock_local_product_service):
        """Test get_all_products method's error handling."""
        error_message = "Failed to retrieve all products"
        mock_local_product_service.get_products.side_effect = Exception(error_message)
        result = product_data_service.get_all_products(limit=10)
        assert result == []
        product_data_service.logger.error.assert_called_once_with(f"Error getting all products: {error_message}")

    def test_get_product_details_success_found(self, product_data_service, mock_local_product_service):
        """Test get_product_details when the product is found."""
        product_id = "abc-123"
        expected_details = {"id": product_id, "name": "Cool Gadget", "price": 199.99}
        mock_local_product_service.get_product_details.return_value = expected_details
        result = product_data_service.get_product_details(product_id)
        assert result == expected_details
        mock_local_product_service.get_product_details.assert_called_once_with(product_id)

    def test_get_product_details_success_not_found(self, product_data_service, mock_local_product_service):
        """Test get_product_details when the product is not found (returns None)."""
        product_id = "non-existent-id"
        mock_local_product_service.get_product_details.return_value = None
        result = product_data_service.get_product_details(product_id)
        assert result is None
        mock_local_product_service.get_product_details.assert_called_once_with(product_id)

    def test_get_product_details_error(self, product_data_service, mock_local_product_service):
        """Test get_product_details method's error handling."""
        error_message = "Details lookup failed"
        mock_local_product_service.get_product_details.side_effect = Exception(error_message)
        result = product_data_service.get_product_details("error-id")
        assert result is None
        product_data_service.logger.error.assert_called_once_with(f"Error getting product details: {error_message}")

    def test_get_brands_success(self, product_data_service, mock_local_product_service):
        """Test get_brands method for successful retrieval."""
        expected_brands = ["Nike", "Adidas", "Puma"]
        mock_local_product_service.get_brands.return_value = expected_brands
        result = product_data_service.get_brands()
        assert result == expected_brands
        mock_local_product_service.get_brands.assert_called_once()

    def test_get_brands_error(self, product_data_service, mock_local_product_service):
        """Test get_brands method's error handling."""
        error_message = "Brand list unavailable"
        mock_local_product_service.get_brands.side_effect = Exception(error_message)
        result = product_data_service.get_brands()
        assert result == []
        product_data_service.logger.error.assert_called_once_with(f"Error getting brands: {error_message}")

    def test_get_products_by_brand_success_with_limit(self, product_data_service, mock_local_product_service):
        """
        Test get_products_by_brand method for successful retrieval
        and correct application of limit.
        """
        brand = "Sony"
        all_products_by_brand = [
            {"id": "sny1", "name": "Sony TV"}, {"id": "sny2", "name": "Sony Headphone"},
            {"id": "sny3", "name": "Sony Camera"}, {"id": "sny4", "name": "Sony PlayStation"},
        ]
        mock_local_product_service.get_products_by_brand.return_value = all_products_by_brand

        # Test with limit < actual products
        result = product_data_service.get_products_by_brand(brand, limit=2)
        assert result == [{"id": "sny1", "name": "Sony TV"}, {"id": "sny2", "name": "Sony Headphone"}]
        mock_local_product_service.get_products_by_brand.assert_called_once_with(brand)
        mock_local_product_service.get_products_by_brand.reset_mock()

        # Test with limit > actual products (should return all available)
        result = product_data_service.get_products_by_brand(brand, limit=10)
        assert result == all_products_by_brand
        mock_local_product_service.get_products_by_brand.assert_called_once_with(brand)

    def test_get_products_by_brand_no_products(self, product_data_service, mock_local_product_service):
        """Test get_products_by_brand when no products are found for the given brand."""
        brand = "NonExistentBrand"
        mock_local_product_service.get_products_by_brand.return_value = []
        result = product_data_service.get_products_by_brand(brand, limit=5)
        assert result == []
        mock_local_product_service.get_products_by_brand.assert_called_once_with(brand)

    def test_get_products_by_brand_error(self, product_data_service, mock_local_product_service):
        """Test get_products_by_brand method's error handling."""
        error_message = "Brand filter service failed"
        mock_local_product_service.get_products_by_brand.side_effect = Exception(error_message)
        result = product_data_service.get_products_by_brand("Xiaomi", limit=10)
        assert result == []
        product_data_service.logger.error.assert_called_once_with(f"Error getting products by brand: {error_message}")

    @pytest.mark.asyncio
    async def test_smart_search_products_success(self, product_data_service, mock_local_product_service, mocker):
        """
        Test smart_search_products method for successful execution,
        ensuring correct arguments are passed and results are returned.
        """
        keyword = "smartwatch"
        category = "wearables"
        max_price = 300
        limit = 2
        expected_products = [{"id": "ss1", "name": "Smart Watch X"}]
        expected_message = "Smart search found 1 result."

        mock_loop = mocker.AsyncMock()
        mocker.patch('asyncio.get_event_loop', return_value=mock_loop)

        # The actual method being executed in the executor
        mock_local_product_service.smart_search_products.return_value = (expected_products, expected_message)
        # The value that run_in_executor should return when awaited
        mock_loop.run_in_executor.return_value = (expected_products, expected_message)

        products, message = await product_data_service.smart_search_products(keyword, category, max_price, limit)

        assert products == expected_products
        assert message == expected_message
        mock_local_product_service.smart_search_products.assert_called_once_with(keyword, category, max_price, limit)
        mock_loop.run_in_executor.assert_called_once_with(
            None, mock_local_product_service.smart_search_products, keyword, category, max_price, limit
        )

    @pytest.mark.asyncio
    async def test_smart_search_products_default_params(self, product_data_service, mock_local_product_service, mocker):
        """
        Test smart_search_products with its default parameters,
        ensuring the defaults are correctly passed to the local service.
        """
        expected_products = [{"id": "def1", "name": "Default Product"}]
        expected_message = "Default search completed."

        mock_loop = mocker.AsyncMock()
        mocker.patch('asyncio.get_event_loop', return_value=mock_loop)
        mock_local_product_service.smart_search_products.return_value = (expected_products, expected_message)
        mock_loop.run_in_executor.return_value = (expected_products, expected_message)

        products, message = await product_data_service.smart_search_products() # Call with defaults

        assert products == expected_products
        assert message == expected_message
        # Check that default arguments are passed correctly: keyword='', category=None, max_price=None, limit=5
        mock_local_product_service.smart_search_products.assert_called_once_with('', None, None, 5)
        mock_loop.run_in_executor.assert_called_once_with(
            None, mock_local_product_service.smart_search_products, '', None, None, 5
        )

    @pytest.mark.asyncio
    async def test_smart_search_products_exception_propagation(self, product_data_service, mock_local_product_service, mocker):
        """
        Test that exceptions raised by local_service.smart_search_products
        propagate through smart_search_products as it lacks specific error handling.
        """
        error_message = "Underlying smart search service error"

        mock_loop = mocker.AsyncMock()
        mocker.patch('asyncio.get_event_loop', return_value=mock_loop)

        # The actual method being executed in the executor raises an exception
        mock_local_product_service.smart_search_products.side_effect = Exception(error_message)
        # The run_in_executor mock must also raise this exception for the await to catch it
        mock_loop.run_in_executor.side_effect = Exception(error_message)

        with pytest.raises(Exception) as excinfo:
            await product_data_service.smart_search_products("fail_search")

        assert str(excinfo.value) == error_message
        mock_local_product_service.smart_search_products.assert_called_once_with("fail_search", None, None, 5)
        mock_loop.run_in_executor.assert_called_once()