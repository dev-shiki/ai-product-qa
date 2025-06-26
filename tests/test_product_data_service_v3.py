import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

# Assuming app is in the Python path for imports
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService

# --- Fixtures ---

@pytest.fixture
def mock_local_product_service(mocker):
    """
    Mocks the LocalProductService class and its instance.
    This ensures that ProductDataService uses our mock.
    """
    # Create a mock instance with spec to ensure methods exist and are callable
    mock_instance = mocker.MagicMock(spec=LocalProductService)
    # Patch the class itself so that when ProductDataService is initialized,
    # it receives our mock instance instead of a real LocalProductService.
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_instance)
    return mock_instance

@pytest.fixture
def product_data_service(mock_local_product_service):
    """
    Provides an instance of ProductDataService with a mocked LocalProductService.
    """
    return ProductDataService()

@pytest.fixture(autouse=True)
def mock_asyncio_run_in_executor(mocker):
    """
    Mocks asyncio.get_event_loop().run_in_executor.

    This fixture ensures that calls to `run_in_executor` (which wraps
    synchronous calls into an async context) are handled.
    It simulates the behavior by directly calling the passed `func` and
    returning its result as an awaitable. This allows testing both
    the parameters passed to `run_in_executor` and the ultimate call
    to the underlying `LocalProductService` method.
    """
    # Mock the return value of asyncio.get_event_loop()
    mock_loop_instance = MagicMock()
    mocker.patch("asyncio.get_event_loop", return_value=mock_loop_instance)

    # Define the side effect for run_in_executor:
    # It takes the 'func' and '*args', calls the 'func' directly,
    # and returns the result. Since it's an async mock, awaiting it will
    # directly yield this result.
    async def _mock_run_in_executor(executor, func, *args, **kwargs):
        return func(*args, **kwargs)

    # Set this async mock as the side effect of run_in_executor
    mock_executor_method = AsyncMock(side_effect=_mock_run_in_executor)
    mock_loop_instance.run_in_executor = mock_executor_method

    # Return the mock object for `run_in_executor` so tests can make assertions on it
    return mock_executor_method

@pytest.fixture
def caplog_debug(caplog):
    """
    Fixture to set the logging level to DEBUG for the duration of tests
    and capture log messages.
    """
    caplog.set_level(logging.DEBUG)
    return caplog

# --- Test Cases ---

class TestProductDataService:
    """
    Comprehensive test suite for the ProductDataService class.
    """

    @pytest.mark.asyncio
    async def test_init(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test that ProductDataService initializes LocalProductService correctly
        and logs the initialization.
        """
        # product_data_service fixture already initializes the service
        # Verify LocalProductService was instantiated once
        mock_local_product_service.assert_called_once()
        # Verify the local_service attribute is our mock
        assert isinstance(product_data_service.local_service, MagicMock)
        # Verify the initialization log message
        assert "ProductDataService initialized with LocalProductService" in caplog_debug.text

    @pytest.mark.asyncio
    async def test_search_products_success(self, product_data_service, mock_local_product_service, mock_asyncio_run_in_executor, caplog_debug):
        """
        Test search_products method for successful product retrieval
        with default and custom limits.
        """
        expected_products = [{"id": "1", "name": "Laptop"}, {"id": "2", "name": "Keyboard"}]
        # Configure the mock of local_service.search_products, which is called by run_in_executor
        mock_local_product_service.search_products.return_value = expected_products

        keyword = "laptop"
        limit = 5
        products = await product_data_service.search_products(keyword, limit)

        assert products == expected_products
        # Check that run_in_executor was called with the correct function and arguments
        mock_asyncio_run_in_executor.assert_called_once_with(
            None, mock_local_product_service.search_products, keyword, limit
        )
        # Check that the underlying local service method was called by run_in_executor
        mock_local_product_service.search_products.assert_called_once_with(keyword, limit)
        # Check log messages
        assert f"Searching products with keyword: {keyword}" in caplog_debug.text
        assert f"Found {len(expected_products)} products for keyword: {keyword}" in caplog_debug.text
        assert "Error searching products" not in caplog_debug.text # Ensure no error logged

        # Test with default limit
        mock_local_product_service.search_products.reset_mock()
        mock_asyncio_run_in_executor.reset_mock()
        caplog_debug.clear()

        await product_data_service.search_products(keyword)
        mock_local_product_service.search_products.assert_called_once_with(keyword, 10) # Default limit

    @pytest.mark.asyncio
    async def test_search_products_error(self, product_data_service, mock_local_product_service, mock_asyncio_run_in_executor, caplog_debug):
        """
        Test search_products method handles errors gracefully by returning an empty list
        and logging the error.
        """
        error_message = "Search failed due to network error"
        mock_local_product_service.search_products.side_effect = Exception(error_message)

        products = await product_data_service.search_products("error_keyword")

        assert products == []
        # run_in_executor should still be called, but the underlying function raises
        mock_asyncio_run_in_executor.assert_called_once()
        mock_local_product_service.search_products.assert_called_once_with("error_keyword", 10) # Default limit
        # Check error log message
        assert f"Error searching products: {error_message}" in caplog_debug.text
        assert f"Searching products with keyword: error_keyword" in caplog_debug.text # Log before error

    @pytest.mark.asyncio
    async def test_get_products_with_search(self, product_data_service, mock_local_product_service, mocker):
        """
        Test get_products when a search keyword is provided.
        It should internally call search_products with correct arguments.
        """
        expected_products = [{"id": "3", "name": "Mouse"}]
        # Mock search_products directly on the service instance because get_products calls it internally.
        # This prevents the need to configure mock_asyncio_run_in_executor for this internal call.
        mock_search_products = mocker.patch.object(
            product_data_service, 'search_products', new_callable=AsyncMock, return_value=expected_products
        )

        products = await product_data_service.get_products(limit=5, search="mouse")

        assert products == expected_products
        mock_search_products.assert_called_once_with("mouse", 5)
        # Ensure other internal methods are NOT called
        mock_local_product_service.get_products.assert_not_called() # Not fallback or get_all_products
        mocker.patch.object(product_data_service, 'get_products_by_category').assert_not_called() # Not category
        mocker.patch.object(product_data_service, 'get_all_products').assert_not_called() # Not all products

    @pytest.mark.asyncio
    async def test_get_products_with_category(self, product_data_service, mock_local_product_service, mocker):
        """
        Test get_products when a category is provided (and no search).
        It should internally call get_products_by_category.
        """
        expected_products = [{"id": "4", "name": "TV", "category": "electronics"}]
        mock_get_products_by_category = mocker.patch.object(
            product_data_service, 'get_products_by_category', return_value=expected_products
        )

        products = await product_data_service.get_products(limit=10, category="electronics")

        assert products == expected_products
        mock_get_products_by_category.assert_called_once_with("electronics", 10)
        # Ensure other internal methods are NOT called
        mock_local_product_service.get_products.assert_not_called()
        mocker.patch.object(product_data_service, 'search_products').assert_not_called()
        mocker.patch.object(product_data_service, 'get_all_products').assert_not_called()

    @pytest.mark.asyncio
    async def test_get_products_no_filter(self, product_data_service, mock_local_product_service, mocker):
        """
        Test get_products when no search or category is provided.
        It should internally call get_all_products.
        """
        expected_products = [{"id": "5", "name": "Book"}]
        mock_get_all_products = mocker.patch.object(
            product_data_service, 'get_all_products', return_value=expected_products
        )

        products = await product_data_service.get_products(limit=15)

        assert products == expected_products
        mock_get_all_products.assert_called_once_with(15)
        # Ensure other internal methods are NOT called
        mock_local_product_service.get_products.assert_not_called()
        mocker.patch.object(product_data_service, 'search_products').assert_not_called()
        mocker.patch.object(product_data_service, 'get_products_by_category').assert_not_called()

    @pytest.mark.asyncio
    async def test_get_products_error_fallback(self, product_data_service, mock_local_product_service, mocker, caplog_debug):
        """
        Test get_products error handling fallback.
        If an internal method call fails, it should catch the exception,
        log it, and then call local_service.get_products as a fallback.
        """
        fallback_products = [{"id": "6", "name": "Fallback Item"}]
        # Configure the fallback result from LocalProductService
        mock_local_product_service.get_products.return_value = fallback_products

        # Simulate an internal method (e.g., get_all_products) raising an error
        error_message = "Simulated internal error for get_all_products"
        mocker.patch.object(
            product_data_service, 'get_all_products', side_effect=Exception(error_message)
        )

        products = await product_data_service.get_products(limit=5)

        assert products == fallback_products
        # Verify the fallback call to LocalProductService
        mock_local_product_service.get_products.assert_called_once_with(5)
        # Verify the error log message
        assert f"Error getting products: {error_message}" in caplog_debug.text

    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_categories for successful retrieval.
        """
        expected_categories = ["Electronics", "Books", "Clothes"]
        mock_local_product_service.get_categories.return_value = expected_categories

        categories = await product_data_service.get_categories()

        assert categories == expected_categories
        mock_local_product_service.get_categories.assert_called_once()
        assert "Error getting categories" not in caplog_debug.text

    @pytest.mark.asyncio
    async def test_get_categories_error(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_categories handles errors gracefully by returning an empty list
        and logging the error.
        """
        error_message = "Category retrieval failed"
        mock_local_product_service.get_categories.side_effect = Exception(error_message)

        categories = await product_data_service.get_categories()

        assert categories == []
        mock_local_product_service.get_categories.assert_called_once()
        assert f"Error getting categories: {error_message}" in caplog_debug.text

    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_top_rated_products for successful retrieval.
        """
        expected_products = [{"id": "7", "name": "Top Product", "rating": 5.0}]
        mock_local_product_service.get_top_rated_products.return_value = expected_products

        products = await product_data_service.get_top_rated_products(limit=5)

        assert products == expected_products
        mock_local_product_service.get_top_rated_products.assert_called_once_with(5)
        assert "Error getting top rated products" not in caplog_debug.text

        # Test with default limit
        mock_local_product_service.get_top_rated_products.reset_mock()
        caplog_debug.clear()
        await product_data_service.get_top_rated_products()
        mock_local_product_service.get_top_rated_products.assert_called_once_with(10)


    @pytest.mark.asyncio
    async def test_get_top_rated_products_error(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_top_rated_products handles errors gracefully by returning an empty list
        and logging the error.
        """
        error_message = "Top rated product error"
        mock_local_product_service.get_top_rated_products.side_effect = Exception(error_message)

        products = await product_data_service.get_top_rated_products()

        assert products == []
        mock_local_product_service.get_top_rated_products.assert_called_once_with(10) # Default limit
        assert f"Error getting top rated products: {error_message}" in caplog_debug.text

    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_best_selling_products for successful retrieval.
        """
        expected_products = [{"id": "8", "name": "Best Seller", "sales_count": 1000}]
        mock_local_product_service.get_best_selling_products.return_value = expected_products

        products = await product_data_service.get_best_selling_products(limit=3)

        assert products == expected_products
        mock_local_product_service.get_best_selling_products.assert_called_once_with(3)
        assert "Error getting best selling products" not in caplog_debug.text

        # Test with default limit
        mock_local_product_service.get_best_selling_products.reset_mock()
        caplog_debug.clear()
        await product_data_service.get_best_selling_products()
        mock_local_product_service.get_best_selling_products.assert_called_once_with(10)


    @pytest.mark.asyncio
    async def test_get_best_selling_products_error(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_best_selling_products handles errors gracefully by returning an empty list
        and logging the error.
        """
        error_message = "Best selling product error"
        mock_local_product_service.get_best_selling_products.side_effect = Exception(error_message)

        products = await product_data_service.get_best_selling_products()

        assert products == []
        mock_local_product_service.get_best_selling_products.assert_called_once_with(10) # Default limit
        assert f"Error getting best selling products: {error_message}" in caplog_debug.text

    def test_get_products_by_category_success(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_products_by_category for successful retrieval and limit application.
        The LocalProductService returns all items for the category, and ProductDataService
        applies the limit by slicing.
        """
        all_products = [
            {"id": "9", "category": "Electronics"},
            {"id": "10", "category": "Electronics"},
            {"id": "11", "category": "Electronics"}
        ]
        mock_local_product_service.get_products_by_category.return_value = all_products

        # Test with limit smaller than available products
        products = product_data_service.get_products_by_category("Electronics", limit=2)
        assert products == all_products[:2] # Check limit slicing applied by ProductDataService
        mock_local_product_service.get_products_by_category.assert_called_once_with("Electronics") # Local service gets all

        mock_local_product_service.get_products_by_category.reset_mock()
        caplog_debug.clear()

        # Test with limit greater than available products
        products_no_limit = product_data_service.get_products_by_category("Electronics", limit=5)
        assert products_no_limit == all_products # Limit greater than available, returns all
        mock_local_product_service.get_products_by_category.assert_called_once_with("Electronics")

        assert "Error getting products by category" not in caplog_debug.text

        # Test with default limit
        mock_local_product_service.get_products_by_category.reset_mock()
        caplog_debug.clear()
        product_data_service.get_products_by_category("Electronics")
        mock_local_product_service.get_products_by_category.assert_called_once_with("Electronics")
        # Default limit is 10, if 3 products, it should return all 3.
        assert product_data_service.get_products_by_category("Electronics") == all_products


    def test_get_products_by_category_error(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_products_by_category handles errors gracefully by returning an empty list
        and logging the error.
        """
        error_message = "Category search failed"
        mock_local_product_service.get_products_by_category.side_effect = Exception(error_message)

        products = product_data_service.get_products_by_category("NonExistentCategory")

        assert products == []
        mock_local_product_service.get_products_by_category.assert_called_once_with("NonExistentCategory")
        assert f"Error getting products by category: {error_message}" in caplog_debug.text

    def test_get_all_products_success(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_all_products for successful retrieval.
        """
        expected_products = [{"id": "12", "name": "Product A"}, {"id": "13", "name": "Product B"}]
        mock_local_product_service.get_products.return_value = expected_products

        products = product_data_service.get_all_products(limit=2)

        assert products == expected_products # Local service returns limited products
        mock_local_product_service.get_products.assert_called_once_with(2)
        assert "Error getting all products" not in caplog_debug.text

        # Test with default limit
        mock_local_product_service.get_products.reset_mock()
        caplog_debug.clear()
        product_data_service.get_all_products()
        mock_local_product_service.get_products.assert_called_once_with(20)

    def test_get_all_products_error(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_all_products handles errors gracefully by returning an empty list
        and logging the error.
        """
        error_message = "All products retrieval failed"
        mock_local_product_service.get_products.side_effect = Exception(error_message)

        products = product_data_service.get_all_products()

        assert products == []
        mock_local_product_service.get_products.assert_called_once_with(20) # Default limit
        assert f"Error getting all products: {error_message}" in caplog_debug.text

    def test_get_product_details_success(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_product_details for successful retrieval.
        """
        expected_details = {"id": "prod123", "name": "Gadget X", "description": "Cool device"}
        mock_local_product_service.get_product_details.return_value = expected_details

        details = product_data_service.get_product_details("prod123")

        assert details == expected_details
        mock_local_product_service.get_product_details.assert_called_once_with("prod123")
        assert "Error getting product details" not in caplog_debug.text

    def test_get_product_details_not_found(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_product_details when the product is not found (LocalProductService returns None).
        """
        mock_local_product_service.get_product_details.return_value = None

        details = product_data_service.get_product_details("nonexistent_id")

        assert details is None
        mock_local_product_service.get_product_details.assert_called_once_with("nonexistent_id")
        assert "Error getting product details" not in caplog_debug.text # No error logged if explicitly None

    def test_get_product_details_error(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_product_details handles errors gracefully by returning None
        and logging the error.
        """
        error_message = "Database connection error"
        mock_local_product_service.get_product_details.side_effect = Exception(error_message)

        details = product_data_service.get_product_details("error_id")

        assert details is None
        mock_local_product_service.get_product_details.assert_called_once_with("error_id")
        assert f"Error getting product details: {error_message}" in caplog_debug.text

    def test_get_brands_success(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_brands for successful retrieval.
        """
        expected_brands = ["BrandA", "BrandB", "BrandC"]
        mock_local_product_service.get_brands.return_value = expected_brands

        brands = product_data_service.get_brands()

        assert brands == expected_brands
        mock_local_product_service.get_brands.assert_called_once()
        assert "Error getting brands" not in caplog_debug.text

    def test_get_brands_error(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_brands handles errors gracefully by returning an empty list
        and logging the error.
        """
        error_message = "Brand data inaccessible"
        mock_local_product_service.get_brands.side_effect = Exception(error_message)

        brands = product_data_service.get_brands()

        assert brands == []
        mock_local_product_service.get_brands.assert_called_once()
        assert f"Error getting brands: {error_message}" in caplog_debug.text

    def test_get_products_by_brand_success(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_products_by_brand for successful retrieval and limit application.
        Similar to get_products_by_category, LocalProductService returns all items,
        and ProductDataService applies the limit by slicing.
        """
        all_products = [
            {"id": "14", "brand": "BrandX"},
            {"id": "15", "brand": "BrandX"},
            {"id": "16", "brand": "BrandX"},
            {"id": "17", "brand": "BrandX"}
        ]
        mock_local_product_service.get_products_by_brand.return_value = all_products

        # Test with limit smaller than available products
        products = product_data_service.get_products_by_brand("BrandX", limit=2)
        assert products == all_products[:2] # Check limit slicing applied by ProductDataService
        mock_local_product_service.get_products_by_brand.assert_called_once_with("BrandX") # Local service gets all

        mock_local_product_service.get_products_by_brand.reset_mock()
        caplog_debug.clear()

        # Test with limit greater than available products
        products_no_limit = product_data_service.get_products_by_brand("BrandX", limit=5)
        assert products_no_limit == all_products # Limit greater than available, returns all
        mock_local_product_service.get_products_by_brand.assert_called_once_with("BrandX")

        assert "Error getting products by brand" not in caplog_debug.text

        # Test with default limit
        mock_local_product_service.get_products_by_brand.reset_mock()
        caplog_debug.clear()
        product_data_service.get_products_by_brand("BrandX")
        mock_local_product_service.get_products_by_brand.assert_called_once_with("BrandX")
        assert product_data_service.get_products_by_brand("BrandX") == all_products # Should return all 4 due to default limit 10

    def test_get_products_by_brand_error(self, product_data_service, mock_local_product_service, caplog_debug):
        """
        Test get_products_by_brand handles errors gracefully by returning an empty list
        and logging the error.
        """
        error_message = "Brand search failed"
        mock_local_product_service.get_products_by_brand.side_effect = Exception(error_message)

        products = product_data_service.get_products_by_brand("NonExistentBrand")

        assert products == []
        mock_local_product_service.get_products_by_brand.assert_called_once_with("NonExistentBrand")
        assert f"Error getting products by brand: {error_message}" in caplog_debug.text

    @pytest.mark.asyncio
    async def test_smart_search_products_success(self, product_data_service, mock_local_product_service, mock_asyncio_run_in_executor, caplog_debug):
        """
        Test smart_search_products for successful retrieval.
        This method does not have its own try-except, so success means direct return.
        """
        expected_products = [{"id": "18", "name": "Smart Speaker"}]
        expected_message = "Smart search completed."
        # Configure the mock of local_service.smart_search_products, which is called by run_in_executor
        mock_local_product_service.smart_search_products.return_value = (expected_products, expected_message)

        products, message = await product_data_service.smart_search_products(
            keyword="smart", category="electronics", max_price=100, limit=2
        )

        assert products == expected_products
        assert message == expected_message
        # Verify run_in_executor was called with correct parameters
        mock_asyncio_run_in_executor.assert_called_once_with(
            None,
            mock_local_product_service.smart_search_products,
            "smart", "electronics", 100, 2
        )
        # Verify the underlying local service method was called
        mock_local_product_service.smart_search_products.assert_called_once_with(
            "smart", "electronics", 100, 2
        )
        assert "Error" not in caplog_debug.text # No try-except in smart_search_products, so no log on success

        # Test with default arguments
        mock_local_product_service.smart_search_products.reset_mock()
        mock_asyncio_run_in_executor.reset_mock()
        caplog_debug.clear()

        default_products = [{"id": "19"}]
        default_message = "Default search"
        mock_local_product_service.smart_search_products.return_value = (default_products, default_message)
        
        products, message = await product_data_service.smart_search_products()
        assert products == default_products
        assert message == default_message
        mock_local_product_service.smart_search_products.assert_called_once_with("", None, None, 5)


    @pytest.mark.asyncio
    async def test_smart_search_products_error_propagation(self, product_data_service, mock_local_product_service, mock_asyncio_run_in_executor):
        """
        Test smart_search_products propagates exceptions as it does not have
        its own try-except block.
        """
        error_message = "Simulated smart search internal error"
        mock_local_product_service.smart_search_products.side_effect = Exception(error_message)

        with pytest.raises(Exception, match=error_message):
            await product_data_service.smart_search_products("fail_keyword")

        # Verify run_in_executor was called
        mock_asyncio_run_in_executor.assert_called_once()
        # Verify the underlying local service method was called
        mock_local_product_service.smart_search_products.assert_called_once_with("fail_keyword", None, None, 5) # Default args