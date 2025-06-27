import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import logging

# Assuming the path from the root of the project
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService

# Configure logging for tests to capture messages
@pytest.fixture(autouse=True)
def setup_logging(caplog):
    """Fixture to set logging level for the service and capture logs for assertions."""
    # Set the specific logger used by ProductDataService to INFO to capture its messages
    logging.getLogger('app.services.product_data_service').setLevel(logging.INFO)
    # Set caplog's level to DEBUG to capture all messages flowing through it
    caplog.set_level(logging.DEBUG) 

@pytest.fixture
def mock_local_service():
    """Mocks the LocalProductService, the primary data source for ProductDataService."""
    # Using MagicMock with spec ensures that the mock adheres to the real interface,
    # catching typos or calls to non-existent methods.
    return MagicMock(spec=LocalProductService)

@pytest.fixture
def product_data_service(mock_local_service, mocker):
    """
    Fixture that provides an instance of ProductDataService with its dependencies mocked.
    It patches `LocalProductService` and `asyncio.get_event_loop().run_in_executor`
    to control their behavior during tests.
    """
    # 1. Patch `LocalProductService`'s constructor so that when ProductDataService
    # instantiates `LocalProductService`, it receives our mock instead.
    mocker.patch(
        'app.services.product_data_service.LocalProductService',
        return_value=mock_local_service
    )

    # Initialize the ProductDataService. It will now use our `mock_local_service`.
    service = ProductDataService()

    # 2. Patch `asyncio.get_event_loop().run_in_executor` for async methods.
    # The `import asyncio` is inside the methods, but because it imports the global
    # `asyncio` module, patching `asyncio.get_event_loop` at the module level works.
    mock_loop = MagicMock()
    # `run_in_executor` itself returns a Future, which `await`s. An AsyncMock
    # directly simulates this behavior for easy configuration of return values.
    mock_loop.run_in_executor = AsyncMock() 
    mocker.patch('asyncio.get_event_loop', return_value=mock_loop)
    
    # Store the `run_in_executor` mock on the service instance for easy access
    # and configuration within individual test cases.
    service._mock_run_in_executor = mock_loop.run_in_executor
    
    return service

# --- Test ProductDataService Initialization ---
class TestProductDataServiceInit:
    """Tests for the ProductDataService __init__ method."""

    def test_init_success(self, product_data_service, mock_local_service, caplog):
        """
        Test that ProductDataService initializes correctly, sets its `local_service`
        attribute to the mocked service, and logs the correct initialization message.
        """
        assert product_data_service.local_service is mock_local_service
        # Verify the specific log message indicating successful initialization.
        assert "ProductDataService initialized with LocalProductService" in [record.message for record in caplog.records]
        # Ensure no methods on the mock local_service were called during initialization.
        assert not mock_local_service.called

# --- Test search_products method ---
class TestSearchProducts:
    """Tests for the async `search_products` method."""

    @pytest.mark.asyncio
    async def test_search_products_success(self, product_data_service, caplog):
        """
        Test successful product search.
        Verifies correct return value, log messages, and that `run_in_executor`
        was called with the appropriate arguments.
        """
        expected_products = [
            {"id": "p1", "name": "Laptop Pro", "price": 1200}, 
            {"id": "p2", "name": "Wireless Mouse", "price": 25}
        ]
        
        # Configure the `_mock_run_in_executor` to return the expected products.
        product_data_service._mock_run_in_executor.return_value = expected_products

        keyword = "electronics"
        limit = 5
        result = await product_data_service.search_products(keyword, limit)
        
        assert result == expected_products
        # Verify that `run_in_executor` was called exactly once with the correct arguments.
        product_data_service._mock_run_in_executor.assert_called_once_with(
            None, product_data_service.local_service.search_products, keyword, limit
        )
        # Verify specific log messages were captured.
        assert f"Searching products with keyword: {keyword}" in [record.message for record in caplog.records]
        assert f"Found {len(expected_products)} products for keyword: {keyword}" in [record.message for record in caplog.records]

    @pytest.mark.asyncio
    async def test_search_products_no_results(self, product_data_service, caplog):
        """
        Test product search returns an empty list when no products match the keyword.
        Verifies logging for zero results found.
        """
        product_data_service._mock_run_in_executor.return_value = []
        
        keyword = "nonexistent_item"
        limit = 10
        result = await product_data_service.search_products(keyword, limit)
        
        assert result == []
        product_data_service._mock_run_in_executor.assert_called_once_with(
            None, product_data_service.local_service.search_products, keyword, limit
        )
        assert f"Searching products with keyword: {keyword}" in [record.message for record in caplog.records]
        assert f"Found 0 products for keyword: {keyword}" in [record.message for record in caplog.records]

    @pytest.mark.asyncio
    async def test_search_products_exception(self, product_data_service, caplog):
        """
        Test product search handles exceptions gracefully by returning an empty list
        and logging an error message.
        """
        mock_error_message = "Mock search service connectivity error"
        product_data_service._mock_run_in_executor.side_effect = Exception(mock_error_message)
        
        keyword = "error_query"
        limit = 5
        result = await product_data_service.search_products(keyword, limit)
        
        assert result == []
        product_data_service._mock_run_in_executor.assert_called_once_with(
            None, product_data_service.local_service.search_products, keyword, limit
        )
        assert f"Error searching products: {mock_error_message}" in [record.message for record in caplog.records]

# --- Test get_products method ---
class TestGetProducts:
    """Tests for the async `get_products` method, which contains conditional logic
    delegating to other methods based on provided filters."""

    @pytest.mark.asyncio
    async def test_get_products_with_search_keyword(self, product_data_service, mocker):
        """
        Test `get_products` delegates to `search_products` when a 'search' keyword is provided.
        Ensures the correct internal method is called with proper arguments.
        """
        # Mock the internal `search_products` method to control its behavior directly.
        mock_search_products = mocker.patch.object(product_data_service, 'search_products', new_callable=AsyncMock)
        expected_products = [{"id": "s1", "name": "Filtered by Search"}]
        mock_search_products.return_value = expected_products

        search_query = "filtered_item"
        limit = 5
        result = await product_data_service.get_products(limit=limit, search=search_query)
        
        assert result == expected_products
        mock_search_products.assert_called_once_with(search_query, limit)
        # Crucially, `_mock_run_in_executor` should *not* be called directly by `get_products`
        # in this path, as `search_products` handles its own executor interaction.
        product_data_service._mock_run_in_executor.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_products_with_category(self, product_data_service, mocker):
        """
        Test `get_products` delegates to `get_products_by_category` when a 'category' is provided.
        Ensures the correct internal method is called with proper arguments.
        """
        # Mock the internal `get_products_by_category` method.
        mock_get_by_category = mocker.patch.object(product_data_service, 'get_products_by_category')
        expected_products = [{"id": "c1", "name": "Category Product"}]
        mock_get_by_category.return_value = expected_products

        category_name = "home_appliances"
        limit = 15
        result = await product_data_service.get_products(limit=limit, category=category_name)
        
        assert result == expected_products
        mock_get_by_category.assert_called_once_with(category_name, limit)
        # This branch calls a synchronous method, so `_mock_run_in_executor` should not be called.
        product_data_service._mock_run_in_executor.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_products_without_filters(self, product_data_service, mocker):
        """
        Test `get_products` delegates to `get_all_products` when no filters
        (neither 'search' nor 'category') are provided.
        Ensures the correct internal method is called with proper arguments.
        """
        # Mock the internal `get_all_products` method.
        mock_get_all = mocker.patch.object(product_data_service, 'get_all_products')
        expected_products = [{"id": "a1", "name": "All Products Item"}]
        mock_get_all.return_value = expected_products

        limit = 25
        result = await product_data_service.get_products(limit=limit) # No search or category specified
        
        assert result == expected_products
        mock_get_all.assert_called_once_with(limit)
        # This branch calls a synchronous method, so `_mock_run_in_executor` should not be called.
        product_data_service._mock_run_in_executor.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_products_exception_fallback(self, product_data_service, mock_local_service, caplog, mocker):
        """
        Test `get_products` handles exceptions that occur within its internal logic
        branches (e.g., in `get_all_products`) and falls back to calling
        `local_service.get_products` directly, logging the error.
        """
        # Simulate an exception in the code path that would be taken (e.g., `get_all_products`).
        mock_internal_error_message = "Simulated internal error during product retrieval"
        mocker.patch.object(
            product_data_service, 'get_all_products', side_effect=Exception(mock_internal_error_message)
        )

        # Set up the expected fallback return value from `mock_local_service.get_products`.
        fallback_products = [{"id": "fallback1", "name": "Fallback Product"}]
        mock_local_service.get_products.return_value = fallback_products

        limit = 10
        # Call `get_products` without filters, triggering the `get_all_products` path.
        result = await product_data_service.get_products(limit=limit) 
        
        assert result == fallback_products
        # Verify that `mock_local_service.get_products` was called as the fallback.
        mock_local_service.get_products.assert_called_once_with(limit)
        # Verify that the error was logged.
        assert f"Error getting products: {mock_internal_error_message}" in [record.message for record in caplog.records]
        # Ensure that `_mock_run_in_executor` was not involved in this specific fallback path.
        product_data_service._mock_run_in_executor.assert_not_called()

# --- Test async methods (direct calls to local_service with error handling) ---
class TestDirectAsyncMethods:
    """Tests for async methods that directly call `local_service` methods and include
    their own `try-except` blocks for error handling."""

    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service, mock_local_service, caplog):
        """Test `get_categories` successfully retrieves and returns a list of categories."""
        expected_categories = ["Electronics", "Clothing", "Home & Garden"]
        mock_local_service.get_categories.return_value = expected_categories
        
        result = await product_data_service.get_categories()
        
        assert result == expected_categories
        mock_local_service.get_categories.assert_called_once()
        assert "Error getting categories" not in [record.message for record in caplog.records]

    @pytest.mark.asyncio
    async def test_get_categories_empty(self, product_data_service, mock_local_service, caplog):
        """Test `get_categories` returns an empty list if no categories are available."""
        mock_local_service.get_categories.return_value = []
        result = await product_data_service.get_categories()
        assert result == []
        mock_local_service.get_categories.assert_called_once()
        assert "Error getting categories" not in [record.message for record in caplog.records]


    @pytest.mark.asyncio
    async def test_get_categories_exception(self, product_data_service, mock_local_service, caplog):
        """Test `get_categories` handles exceptions by returning an empty list and logging an error."""
        mock_error_message = "Category service connection refused"
        mock_local_service.get_categories.side_effect = Exception(mock_error_message)
        
        result = await product_data_service.get_categories()
        
        assert result == []
        mock_local_service.get_categories.assert_called_once()
        assert f"Error getting categories: {mock_error_message}" in [record.message for record in caplog.records]

    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service, mock_local_service, caplog):
        """Test `get_top_rated_products` successfully retrieves and returns products."""
        expected_products = [{"id": "tr1", "rating": 5.0}, {"id": "tr2", "rating": 4.8}]
        mock_local_service.get_top_rated_products.return_value = expected_products
        
        limit = 3
        result = await product_data_service.get_top_rated_products(limit=limit)
        
        assert result == expected_products
        mock_local_service.get_top_rated_products.assert_called_once_with(limit)
        assert "Error getting top rated products" not in [record.message for record in caplog.records]

    @pytest.mark.asyncio
    async def test_get_top_rated_products_exception(self, product_data_service, mock_local_service, caplog):
        """Test `get_top_rated_products` handles exceptions by returning an empty list and logging an error."""
        mock_error_message = "Top rated service read timeout"
        mock_local_service.get_top_rated_products.side_effect = Exception(mock_error_message)
        
        result = await product_data_service.get_top_rated_products() # Tests default limit (10)
        
        assert result == []
        mock_local_service.get_top_rated_products.assert_called_once_with(10)
        assert f"Error getting top rated products: {mock_error_message}" in [record.message for record in caplog.records]

    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service, mock_local_service, caplog):
        """Test `get_best_selling_products` successfully retrieves and returns products."""
        expected_products = [{"id": "bs1", "sales_count": 1000}, {"id": "bs2", "sales_count": 800}]
        mock_local_service.get_best_selling_products.return_value = expected_products
        
        limit = 2
        result = await product_data_service.get_best_selling_products(limit=limit)
        
        assert result == expected_products
        mock_local_service.get_best_selling_products.assert_called_once_with(limit)
        assert "Error getting best selling products" not in [record.message for record in caplog.records]

    @pytest.mark.asyncio
    async def test_get_best_selling_products_exception(self, product_data_service, mock_local_service, caplog):
        """Test `get_best_selling_products` handles exceptions by returning an empty list and logging an error."""
        mock_error_message = "Best selling service internal server error"
        mock_local_service.get_best_selling_products.side_effect = Exception(mock_error_message)
        
        result = await product_data_service.get_best_selling_products() # Tests default limit (10)
        
        assert result == []
        mock_local_service.get_best_selling_products.assert_called_once_with(10)
        assert f"Error getting best selling products: {mock_error_message}" in [record.message for record in caplog.records]

# --- Test synchronous methods ---
class TestSynchronousMethods:
    """Tests for synchronous methods that call `local_service` methods and include
    their own `try-except` blocks for error handling."""

    def test_get_products_by_category_success_with_limit(self, product_data_service, mock_local_service, caplog):
        """
        Test `get_products_by_category` returns products and correctly applies the limit
        by slicing the result from `local_service`.
        """
        mock_local_service.get_products_by_category.return_value = [
            {"id": "cat_p1"}, {"id": "cat_p2"}, {"id": "cat_p3"}, {"id": "cat_p4"}
        ]
        
        category = "kitchenware"
        limit = 2
        result = product_data_service.get_products_by_category(category, limit)
        
        assert result == [{"id": "cat_p1"}, {"id": "cat_p2"}]
        mock_local_service.get_products_by_category.assert_called_once_with(category)
        assert "Error getting products by category" not in [record.message for record in caplog.records]

    def test_get_products_by_category_success_no_limit_exceeded(self, product_data_service, mock_local_service, caplog):
        """
        Test `get_products_by_category` returns all available products when the actual
        number of products is less than the specified or default limit.
        """
        mock_local_service.get_products_by_category.return_value = [
            {"id": "cat_p1"}, {"id": "cat_p2"}, {"id": "cat_p3"}
        ]
        
        category = "books"
        result = product_data_service.get_products_by_category(category) # Default limit is 10
        
        assert result == [{"id": "cat_p1"}, {"id": "cat_p2"}, {"id": "cat_p3"}] 
        mock_local_service.get_products_by_category.assert_called_once_with(category)
        assert "Error getting products by category" not in [record.message for record in caplog.records]

    def test_get_products_by_category_empty(self, product_data_service, mock_local_service, caplog):
        """Test `get_products_by_category` returns an empty list if no products are found for the category."""
        mock_local_service.get_products_by_category.return_value = []
        
        category = "nonexistent_category"
        result = product_data_service.get_products_by_category(category)
        
        assert result == []
        mock_local_service.get_products_by_category.assert_called_once_with(category)
        assert "Error getting products by category" not in [record.message for record in caplog.records]

    def test_get_products_by_category_exception(self, product_data_service, mock_local_service, caplog):
        """Test `get_products_by_category` handles exceptions by returning an empty list and logging an error."""
        mock_error_message = "Category filter service error"
        mock_local_service.get_products_by_category.side_effect = Exception(mock_error_message)
        
        category = "bad_category"
        result = product_data_service.get_products_by_category(category)
        
        assert result == []
        mock_local_service.get_products_by_category.assert_called_once_with(category)
        assert f"Error getting products by category: {mock_error_message}" in [record.message for record in caplog.records]

    def test_get_all_products_success_with_limit(self, product_data_service, mock_local_service, caplog):
        """
        Test `get_all_products` returns products and correctly applies the limit.
        """
        mock_local_service.get_products.return_value = [
            {"id": "p1"}, {"id": "p2"}, {"id": "p3"}, {"id": "p4"}, {"id": "p5"}, {"id": "p6"}
        ]
        
        limit = 3
        result = product_data_service.get_all_products(limit=limit)
        
        assert result == [{"id": "p1"}, {"id": "p2"}, {"id": "p3"}]
        mock_local_service.get_products.assert_called_once_with(limit)
        assert "Error getting all products" not in [record.message for record in caplog.records]

    def test_get_all_products_success_no_limit_exceeded(self, product_data_service, mock_local_service, caplog):
        """
        Test `get_all_products` returns all available products when the actual number
        of products is less than the specified or default limit.
        """
        mock_local_service.get_products.return_value = [
            {"id": "p1"}, {"id": "p2"}, {"id": "p3"}
        ]
        
        result = product_data_service.get_all_products() # Default limit 20
        
        assert result == [{"id": "p1"}, {"id": "p2"}, {"id": "p3"}]
        mock_local_service.get_products.assert_called_once_with(20)
        assert "Error getting all products" not in [record.message for record in caplog.records]

    def test_get_all_products_empty(self, product_data_service, mock_local_service, caplog):
        """Test `get_all_products` returns an empty list if no products are found."""
        mock_local_service.get_products.return_value = []
        
        result = product_data_service.get_all_products()
        
        assert result == []
        mock_local_service.get_products.assert_called_once_with(20)
        assert "Error getting all products" not in [record.message for record in caplog.records]

    def test_get_all_products_exception(self, product_data_service, mock_local_service, caplog):
        """Test `get_all_products` handles exceptions by returning an empty list and logging an error."""
        mock_error_message = "All products fetch error"
        mock_local_service.get_products.side_effect = Exception(mock_error_message)
        
        result = product_data_service.get_all_products()
        
        assert result == []
        mock_local_service.get_products.assert_called_once_with(20)
        assert f"Error getting all products: {mock_error_message}" in [record.message for record in caplog.records]

    def test_get_product_details_success(self, product_data_service, mock_local_service, caplog):
        """Test `get_product_details` successfully retrieves and returns product details for a given ID."""
        expected_details = {"id": "prod_123", "name": "Detail Product X", "price": 99.99}
        mock_local_service.get_product_details.return_value = expected_details
        
        product_id = "prod_123"
        result = product_data_service.get_product_details(product_id)
        
        assert result == expected_details
        mock_local_service.get_product_details.assert_called_once_with(product_id)
        assert "Error getting product details" not in [record.message for record in caplog.records]

    def test_get_product_details_not_found(self, product_data_service, mock_local_service, caplog):
        """Test `get_product_details` returns None if the product ID is not found."""
        mock_local_service.get_product_details.return_value = None
        
        product_id = "non_existent_id_999"
        result = product_data_service.get_product_details(product_id)
        
        assert result is None
        mock_local_service.get_product_details.assert_called_once_with(product_id)
        assert "Error getting product details" not in [record.message for record in caplog.records]

    def test_get_product_details_exception(self, product_data_service, mock_local_service, caplog):
        """Test `get_product_details` handles exceptions by returning None and logging an error."""
        mock_error_message = "Product details service database error"
        mock_local_service.get_product_details.side_effect = Exception(mock_error_message)
        
        product_id = "bad_id_abc"
        result = product_data_service.get_product_details(product_id)
        
        assert result is None
        mock_local_service.get_product_details.assert_called_once_with(product_id)
        assert f"Error getting product details: {mock_error_message}" in [record.message for record in caplog.records]

    def test_get_brands_success(self, product_data_service, mock_local_service, caplog):
        """Test `get_brands` successfully retrieves and returns a list of available brands."""
        expected_brands = ["BrandA", "BrandB", "BrandC"]
        mock_local_service.get_brands.return_value = expected_brands
        
        result = product_data_service.get_brands()
        
        assert result == expected_brands
        mock_local_service.get_brands.assert_called_once()
        assert "Error getting brands" not in [record.message for record in caplog.records]

    def test_get_brands_empty(self, product_data_service, mock_local_service, caplog):
        """Test `get_brands` returns an empty list if no brands are available."""
        mock_local_service.get_brands.return_value = []
        result = product_data_service.get_brands()
        assert result == []
        mock_local_service.get_brands.assert_called_once()
        assert "Error getting brands" not in [record.message for record in caplog.records]

    def test_get_brands_exception(self, product_data_service, mock_local_service, caplog):
        """Test `get_brands` handles exceptions by returning an empty list and logging an error."""
        mock_error_message = "Brands service API failure"
        mock_local_service.get_brands.side_effect = Exception(mock_error_message)
        
        result = product_data_service.get_brands()
        
        assert result == []
        mock_local_service.get_brands.assert_called_once()
        assert f"Error getting brands: {mock_error_message}" in [record.message for record in caplog.records]

    def test_get_products_by_brand_success_with_limit(self, product_data_service, mock_local_service, caplog):
        """
        Test `get_products_by_brand` returns products and correctly applies the limit.
        """
        mock_local_service.get_products_by_brand.return_value = [
            {"id": "b1"}, {"id": "b2"}, {"id": "b3"}, {"id": "b4"}
        ]
        
        brand = "LuxuryBrand"
        limit = 2
        result = product_data_service.get_products_by_brand(brand, limit)
        
        assert result == [{"id": "b1"}, {"id": "b2"}]
        mock_local_service.get_products_by_brand.assert_called_once_with(brand)
        assert "Error getting products by brand" not in [record.message for record in caplog.records]

    def test_get_products_by_brand_success_no_limit_exceeded(self, product_data_service, mock_local_service, caplog):
        """
        Test `get_products_by_brand` returns all available products when the actual number
        of products is less than the specified or default limit.
        """
        mock_local_service.get_products_by_brand.return_value = [
            {"id": "b1"}, {"id": "b2"}, {"id": "b3"}
        ]
        
        brand = "EcoFriendly"
        result = product_data_service.get_products_by_brand(brand) # Default limit 10
        
        assert result == [{"id": "b1"}, {"id": "b2"}, {"id": "b3"}]
        mock_local_service.get_products_by_brand.assert_called_once_with(brand)
        assert "Error getting products by brand" not in [record.message for record in caplog.records]

    def test_get_products_by_brand_empty(self, product_data_service, mock_local_service, caplog):
        """Test `get_products_by_brand` returns an empty list if no products are found for the brand."""
        mock_local_service.get_products_by_brand.return_value = []
        
        brand = "nonexistent_brand"
        result = product_data_service.get_products_by_brand(brand)
        
        assert result == []
        mock_local_service.get_products_by_brand.assert_called_once_with(brand)
        assert "Error getting products by brand" not in [record.message for record in caplog.records]

    def test_get_products_by_brand_exception(self, product_data_service, mock_local_service, caplog):
        """Test `get_products_by_brand` handles exceptions by returning an empty list and logging an error."""
        mock_error_message = "Brand filter service connection lost"
        mock_local_service.get_products_by_brand.side_effect = Exception(mock_error_message)
        
        brand = "bad_brand"
        result = product_data_service.get_products_by_brand(brand)
        
        assert result == []
        mock_local_service.get_products_by_brand.assert_called_once_with(brand)
        assert f"Error getting products by brand: {mock_error_message}" in [record.message for record in caplog.records]

# --- Test smart_search_products method ---
class TestSmartSearchProducts:
    """Tests for the async `smart_search_products` method."""

    @pytest.mark.asyncio
    async def test_smart_search_products_success(self, product_data_service, caplog):
        """
        Test successful smart search, verifying both the returned products and message.
        """
        expected_products = [{"id": "ss1", "name": "Smart Speaker"}]
        expected_message = "Smart search completed successfully."
        
        # Configure `_mock_run_in_executor` to return the tuple (products, message).
        product_data_service._mock_run_in_executor.return_value = (expected_products, expected_message)

        keyword = "smart_device"
        category = "electronics"
        max_price = 100
        limit = 2
        products, message = await product_data_service.smart_search_products(
            keyword=keyword, category=category, max_price=max_price, limit=limit
        )
        
        assert products == expected_products
        assert message == expected_message
        # Verify `run_in_executor` was called with all parameters correctly.
        product_data_service._mock_run_in_executor.assert_called_once_with(
            None, product_data_service.local_service.smart_search_products, keyword, category, max_price, limit
        )
        # The `smart_search_products` method itself does not have a `try-except`,
        # so ensure no error logs originating from this method appear.
        assert "Error" not in [record.levelname for record in caplog.records]

    @pytest.mark.asyncio
    async def test_smart_search_products_no_results(self, product_data_service, caplog):
        """
        Test smart search returns no products and an appropriate message.
        Verifies default parameter values are passed correctly.
        """
        expected_products = []
        expected_message = "No products found matching criteria."
        
        product_data_service._mock_run_in_executor.return_value = (expected_products, expected_message)

        keyword = "no_match_query"
        # Test with default optional parameters (category=None, max_price=None, limit=5)
        products, message = await product_data_service.smart_search_products(keyword=keyword)
        
        assert products == expected_products
        assert message == expected_message
        product_data_service._mock_run_in_executor.assert_called_once_with(
            None, product_data_service.local_service.smart_search_products, keyword, None, None, 5
        )
        assert "Error" not in [record.levelname for record in caplog.records]

    @pytest.mark.asyncio
    async def test_smart_search_products_exception_propagates(self, product_data_service):
        """
        Test `smart_search_products` propagates exceptions from the underlying `local_service`
        call, as it does not contain its own `try-except` block.
        """
        mock_error_message = "Smart search internal error during executor execution"
        product_data_service._mock_run_in_executor.side_effect = Exception(mock_error_message)
        
        with pytest.raises(Exception, match=mock_error_message):
            await product_data_service.smart_search_products("error_keyword")
        
        # Verify that the call to `run_in_executor` was made before the exception propagated.
        product_data_service._mock_run_in_executor.assert_called_once_with(
            None, product_data_service.local_service.smart_search_products, "error_keyword", None, None, 5
        )