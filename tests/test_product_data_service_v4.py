import pytest
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock, patch

# Adjust the import path based on your project structure
# Assuming the test file is test_services/product_data_service.py
# and the source file is app/services/product_data_service.py
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService # Imported for patching target

# Configure logging to capture logs during tests
# pytest's caplog fixture handles this automatically without needing global config.

@pytest.fixture
def sample_products():
    """Provides a sample list of product dictionaries for mock returns."""
    return [
        {"id": "1", "name": "Laptop Pro", "category": "Electronics", "price": 1200, "rating": 4.5, "brand": "BrandA"},
        {"id": "2", "name": "Wireless Mouse", "category": "Electronics", "price": 25, "rating": 4.0, "brand": "BrandB"},
        {"id": "3", "name": "Mechanical Keyboard", "category": "Electronics", "price": 75, "rating": 4.2, "brand": "BrandA"},
        {"id": "4", "name": "Ergonomic Desk", "category": "Furniture", "price": 300, "rating": 3.8, "brand": "BrandC"},
        {"id": "5", "name": "Office Chair", "category": "Furniture", "price": 150, "rating": 4.7, "brand": "BrandB"},
        {"id": "6", "name": "Ultra HD Monitor", "category": "Electronics", "price": 300, "rating": 4.1, "brand": "BrandA"},
        {"id": "7", "name": "Journal Notebook", "category": "Stationery", "price": 10, "rating": 3.5, "brand": "BrandC"},
        {"id": "8", "name": "Gel Pen Set", "category": "Stationery", "price": 2, "rating": 3.0, "brand": "BrandA"},
    ]

@pytest.fixture
def sample_categories():
    """Provides a sample list of categories."""
    return ["Electronics", "Furniture", "Stationery"]

@pytest.fixture
def sample_brands():
    """Provides a sample list of brands."""
    return ["BrandA", "BrandB", "BrandC"]

@pytest.fixture
def mock_local_service(mocker):
    """
    Mocks the LocalProductService class that ProductDataService depends on.
    This ensures that ProductDataService operates in isolation from actual external service calls.
    """
    # The patch target is the path where LocalProductService is imported *into*
    # the ProductDataService module.
    mock_local_service_class = mocker.patch('app.services.product_data_service.LocalProductService')
    # Configure default return values for common methods on the mocked instance
    mock_local_service_instance = mock_local_service_class.return_value
    mock_local_service_instance.get_products.return_value = []
    mock_local_service_instance.search_products.return_value = []
    mock_local_service_instance.get_categories.return_value = []
    mock_local_service_instance.get_top_rated_products.return_value = []
    mock_local_service_instance.get_best_selling_products.return_value = []
    mock_local_service_instance.get_products_by_category.return_value = []
    mock_local_service_instance.get_brands.return_value = []
    mock_local_service_instance.get_products_by_brand.return_value = []
    mock_local_service_instance.get_product_details.return_value = None
    mock_local_service_instance.smart_search_products.return_value = ([], "No message")
    return mock_local_service_instance # Return the mocked instance for direct configuration in tests

@pytest.fixture
def product_data_service(mock_local_service):
    """Provides an instance of ProductDataService with its dependencies mocked."""
    return ProductDataService()

@pytest.fixture
def mock_run_in_executor(mocker):
    """
    Mocks asyncio.get_event_loop().run_in_executor for async methods that use it.
    This allows controlling the return value and behavior of the executor.
    """
    # Create a mock for the event loop
    mock_loop = MagicMock()
    # Create an AsyncMock for the run_in_executor method, as it's awaited
    mock_executor = AsyncMock()
    mock_loop.run_in_executor.return_value = mock_executor

    # Patch the asyncio.get_event_loop function globally
    mocker.patch("asyncio.get_event_loop", return_value=mock_loop)
    return mock_executor # Return the mock of run_in_executor itself for individual test configuration

@pytest.mark.asyncio # Marks all tests in this class to run with pytest-asyncio
class TestProductDataService:
    """Comprehensive test suite for ProductDataService."""

    async def test_init(self, product_data_service, mock_local_service, caplog):
        """
        Test that ProductDataService initializes correctly by creating a LocalProductService instance
        and logs the initialization.
        """
        with caplog.at_level(logging.INFO):
            # product_data_service is already initialized by the fixture.
            # We just need to assert its state and the side-effects.
            assert isinstance(product_data_service.local_service, MagicMock)
            mock_local_service.assert_called_once_with() # Ensure LocalProductService constructor was called
            assert "ProductDataService initialized with LocalProductService" in caplog.text

    async def test_search_products_success(self, product_data_service, mock_run_in_executor, sample_products, caplog):
        """
        Test search_products returns products successfully via run_in_executor.
        Covers default limit and custom limit.
        """
        mock_run_in_executor.return_value = sample_products[:2]
        keyword = "laptop"
        limit = 2
        with caplog.at_level(logging.INFO):
            result = await product_data_service.search_products(keyword, limit)

            mock_run_in_executor.assert_awaited_once_with(None, product_data_service.local_service.search_products, keyword, limit)
            assert result == sample_products[:2]
            assert f"Searching products with keyword: {keyword}" in caplog.text
            assert f"Found {len(sample_products[:2])} products for keyword: {keyword}" in caplog.text

    async def test_search_products_no_results(self, product_data_service, mock_run_in_executor, caplog):
        """Test search_products returns an empty list when no products match."""
        mock_run_in_executor.return_value = []
        keyword = "nonexistent"
        with caplog.at_level(logging.INFO):
            result = await product_data_service.search_products(keyword)

            mock_run_in_executor.assert_awaited_once_with(None, product_data_service.local_service.search_products, keyword, 10) # Default limit
            assert result == []
            assert f"Found 0 products for keyword: {keyword}" in caplog.text

    async def test_search_products_exception(self, product_data_service, mock_run_in_executor, caplog):
        """Test search_products handles exceptions gracefully and returns an empty list."""
        mock_run_in_executor.side_effect = Exception("Simulated search failure")
        keyword = "error_test"
        with caplog.at_level(logging.ERROR):
            result = await product_data_service.search_products(keyword)

            mock_run_in_executor.assert_awaited_once_with(None, product_data_service.local_service.search_products, keyword, 10)
            assert result == []
            assert "Error searching products: Simulated search failure" in caplog.text

    # --- Test get_products (complex branching logic) ---

    async def test_get_products_with_search_parameter(self, product_data_service, mock_run_in_executor, sample_products):
        """
        Test get_products delegates to search_products when the 'search' parameter is provided.
        """
        mock_run_in_executor.return_value = sample_products[:1] # Mock result for search_products
        result = await product_data_service.get_products(search="laptop", limit=1)

        mock_run_in_executor.assert_awaited_once_with(None, product_data_service.local_service.search_products, "laptop", 1)
        assert result == sample_products[:1]

    async def test_get_products_with_category_parameter(self, product_data_service, mock_local_service, sample_products):
        """
        Test get_products delegates to get_products_by_category when the 'category' parameter is provided
        and 'search' is None.
        """
        # Ensure only Electronics products are returned by the mock for a specific category
        electronics_products = [p for p in sample_products if p["category"] == "Electronics"]
        mock_local_service.get_products_by_category.return_value = electronics_products
        result = await product_data_service.get_products(category="Electronics", limit=2)

        mock_local_service.get_products_by_category.assert_called_once_with("Electronics")
        # ProductDataService.get_products_by_category applies slicing locally
        assert result == electronics_products[:2]
        assert len(result) == 2

    async def test_get_products_all_products_default_case(self, product_data_service, mock_local_service, sample_products):
        """
        Test get_products delegates to get_all_products when no 'search' or 'category' filters are provided.
        """
        mock_local_service.get_products.return_value = sample_products
        result = await product_data_service.get_products(limit=3)

        mock_local_service.get_products.assert_called_once_with(3)
        assert result == sample_products[:3] # get_all_products calls local_service.get_products with limit
        assert len(result) == 3

    async def test_get_products_search_takes_precedence_over_category(self, product_data_service, mock_run_in_executor, mock_local_service, sample_products):
        """
        Test that if both 'search' and 'category' are provided to get_products, 'search' takes precedence.
        """
        mock_run_in_executor.return_value = sample_products[:1] # This should be the called path
        # Configure mock_local_service for category, but it should not be called
        mock_local_service.get_products_by_category.return_value = sample_products

        result = await product_data_service.get_products(search="monitor", category="Electronics", limit=1)

        mock_run_in_executor.assert_awaited_once_with(None, product_data_service.local_service.search_products, "monitor", 1)
        mock_local_service.get_products_by_category.assert_not_called()
        mock_local_service.get_products.assert_not_called() # get_all_products path should not be taken
        assert result == sample_products[:1]

    async def test_get_products_exception_fallback(self, product_data_service, mock_local_service, caplog):
        """
        Test get_products' top-level exception handling. If an unexpected error occurs in a
        called internal method that is *not* caught by that method's own try/except,
        get_products should catch it and fall back to local_service.get_products().
        """
        # To simulate an unhandled exception hitting the top-level get_products try/except,
        # we can temporarily patch one of its internal helper methods to raise an error
        # that is not handled by the helper itself (though in this code, all helpers have try/except).
        # We will make `get_all_products` (which `get_products` calls) raise an error before its own
        # internal try-except. This is a bit of a stretch but covers the line.

        # Store original method to restore later
        original_get_all_products = product_data_service.get_all_products

        # Temporarily replace get_all_products with a mock that raises an error
        async def mock_get_all_products_raise_error(*args, **kwargs):
            raise ValueError("Simulated unexpected error in get_all_products")

        product_data_service.get_all_products = mock_get_all_products_raise_error

        # Configure the fallback behavior of mock_local_service.get_products
        mock_local_service.get_products.return_value = [{"id": "fallback_product", "name": "Fallback"}]

        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_products(limit=5)
            assert result == [{"id": "fallback_product", "name": "Fallback"}]
            mock_local_service.get_products.assert_called_once_with(5) # Fallback was called
            assert "Error getting products: Simulated unexpected error in get_all_products" in caplog.text

        # Restore the original method
        product_data_service.get_all_products = original_get_all_products

    # --- Test simple async methods with success and error via parametrization ---

    @pytest.mark.parametrize("method_name, mock_return_data, expected_log_prefix", [
        ("get_categories", ["Electronics", "Furniture"], "Error getting categories"),
        ("get_top_rated_products", [{"id": "tp1", "name": "Top Product"}], "Error getting top rated products"),
        ("get_best_selling_products", [{"id": "bs1", "name": "Best Seller"}], "Error getting best selling products"),
    ])
    async def test_async_method_success(self, product_data_service, mock_local_service, method_name, mock_return_data):
        """Test successful execution for various async methods."""
        # Dynamically set the return value for the mocked local_service method
        getattr(mock_local_service, method_name).return_value = mock_return_data
        result = await getattr(product_data_service, method_name)() # Call the method on the service
        getattr(mock_local_service, method_name).assert_called_once()
        assert result == mock_return_data

    @pytest.mark.parametrize("method_name, expected_log_prefix", [
        ("get_categories", "Error getting categories"),
        ("get_top_rated_products", "Error getting top rated products"),
        ("get_best_selling_products", "Error getting best selling products"),
    ])
    async def test_async_method_exception(self, product_data_service, mock_local_service, method_name, expected_log_prefix, caplog):
        """Test exception handling for various async methods; they should return an empty list."""
        getattr(mock_local_service, method_name).side_effect = Exception("Service unavailable")
        with caplog.at_level(logging.ERROR):
            result = await getattr(product_data_service, method_name)()
            getattr(mock_local_service, method_name).assert_called_once()
            assert result == [] # All these methods return [] on error
            assert f"{expected_log_prefix}: Service unavailable" in caplog.text

    # --- Test synchronous methods with success and error ---

    def test_get_products_by_category_success(self, product_data_service, mock_local_service, sample_products):
        """Test get_products_by_category returns filtered products, respecting limit."""
        # Filter sample products to simulate category-specific data
        electronics_products = [p for p in sample_products if p["category"] == "Electronics"]
        mock_local_service.get_products_by_category.return_value = electronics_products
        result = product_data_service.get_products_by_category("Electronics", limit=2)
        mock_local_service.get_products_by_category.assert_called_once_with("Electronics")
        assert result == electronics_products[:2]
        assert len(result) == 2

    def test_get_products_by_category_no_results(self, product_data_service, mock_local_service):
        """Test get_products_by_category returns empty list if no products found for category."""
        mock_local_service.get_products_by_category.return_value = []
        result = product_data_service.get_products_by_category("NonExistentCategory")
        mock_local_service.get_products_by_category.assert_called_once_with("NonExistentCategory")
        assert result == []

    def test_get_products_by_category_exception(self, product_data_service, mock_local_service, caplog):
        """Test get_products_by_category handles exceptions gracefully and returns empty list."""
        mock_local_service.get_products_by_category.side_effect = Exception("Category search failed")
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_products_by_category("ErrorCategory")
            mock_local_service.get_products_by_category.assert_called_once_with("ErrorCategory")
            assert result == []
            assert "Error getting products by category: Category search failed" in caplog.text

    def test_get_all_products_success(self, product_data_service, mock_local_service, sample_products):
        """Test get_all_products returns all products, respecting limit."""
        mock_local_service.get_products.return_value = sample_products
        result = product_data_service.get_all_products(limit=3)
        mock_local_service.get_products.assert_called_once_with(3)
        assert result == sample_products[:3]
        assert len(result) == 3

    def test_get_all_products_no_products(self, product_data_service, mock_local_service):
        """Test get_all_products returns empty list when no products are available."""
        mock_local_service.get_products.return_value = []
        result = product_data_service.get_all_products(limit=5)
        mock_local_service.get_products.assert_called_once_with(5)
        assert result == []

    def test_get_all_products_exception(self, product_data_service, mock_local_service, caplog):
        """Test get_all_products handles exceptions gracefully and returns empty list."""
        mock_local_service.get_products.side_effect = Exception("Failed to get all products")
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_all_products(limit=5)
            mock_local_service.get_products.assert_called_once_with(5)
            assert result == []
            assert "Error getting all products: Failed to get all products" in caplog.text

    def test_get_product_details_found(self, product_data_service, mock_local_service, sample_products):
        """Test get_product_details returns product details when product is found."""
        mock_local_service.get_product_details.return_value = sample_products[0]
        product_id = "1"
        result = product_data_service.get_product_details(product_id)
        mock_local_service.get_product_details.assert_called_once_with(product_id)
        assert result == sample_products[0]

    def test_get_product_details_not_found(self, product_data_service, mock_local_service):
        """Test get_product_details returns None when product is not found."""
        mock_local_service.get_product_details.return_value = None
        product_id = "nonexistent_id"
        result = product_data_service.get_product_details(product_id)
        mock_local_service.get_product_details.assert_called_once_with(product_id)
        assert result is None

    def test_get_product_details_exception(self, product_data_service, mock_local_service, caplog):
        """Test get_product_details handles exceptions gracefully and returns None."""
        mock_local_service.get_product_details.side_effect = Exception("Details service error")
        product_id = "error_id"
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_product_details(product_id)
            mock_local_service.get_product_details.assert_called_once_with(product_id)
            assert result is None
            assert "Error getting product details: Details service error" in caplog.text

    def test_get_brands_success(self, product_data_service, mock_local_service, sample_brands):
        """Test get_brands returns a list of available brands."""
        mock_local_service.get_brands.return_value = sample_brands
        result = product_data_service.get_brands()
        mock_local_service.get_brands.assert_called_once()
        assert result == sample_brands

    def test_get_brands_exception(self, product_data_service, mock_local_service, caplog):
        """Test get_brands handles exceptions gracefully and returns an empty list."""
        mock_local_service.get_brands.side_effect = Exception("Brands service error")
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_brands()
            mock_local_service.get_brands.assert_called_once()
            assert result == []
            assert "Error getting brands: Brands service error" in caplog.text

    def test_get_products_by_brand_success(self, product_data_service, mock_local_service, sample_products):
        """Test get_products_by_brand returns filtered products by brand, respecting limit."""
        # Simulate products for 'BrandA'
        brand_a_products = [p for p in sample_products if p["brand"] == "BrandA"]
        mock_local_service.get_products_by_brand.return_value = brand_a_products
        result = product_data_service.get_products_by_brand("BrandA", limit=2)
        mock_local_service.get_products_by_brand.assert_called_once_with("BrandA")
        assert result == brand_a_products[:2]
        assert len(result) == 2

    def test_get_products_by_brand_no_results(self, product_data_service, mock_local_service):
        """Test get_products_by_brand returns empty list if no products found for brand."""
        mock_local_service.get_products_by_brand.return_value = []
        result = product_data_service.get_products_by_brand("NonExistentBrand")
        mock_local_service.get_products_by_brand.assert_called_once_with("NonExistentBrand")
        assert result == []

    def test_get_products_by_brand_exception(self, product_data_service, mock_local_service, caplog):
        """Test get_products_by_brand handles exceptions gracefully and returns empty list."""
        mock_local_service.get_products_by_brand.side_effect = Exception("Brand search failed")
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_products_by_brand("ErrorBrand")
            mock_local_service.get_products_by_brand.assert_called_once_with("ErrorBrand")
            assert result == []
            assert "Error getting products by brand: Brand search failed" in caplog.text

    # --- Test smart_search_products ---

    async def test_smart_search_products_success(self, product_data_service, mock_run_in_executor, sample_products):
        """Test smart_search_products returns products and message from local_service."""
        mock_run_in_executor.return_value = (sample_products[:1], "Found 1 product with smart search")
        keyword, category, max_price, limit = "smart", "Electronics", 500, 1
        products, message = await product_data_service.smart_search_products(keyword, category, max_price, limit)

        mock_run_in_executor.assert_awaited_once_with(
            None, product_data_service.local_service.smart_search_products, keyword, category, max_price, limit
        )
        assert products == sample_products[:1]
        assert message == "Found 1 product with smart search"

    async def test_smart_search_products_no_results(self, product_data_service, mock_run_in_executor):
        """Test smart_search_products returns empty products and message when no results."""
        mock_run_in_executor.return_value = ([], "No products found for criteria")
        products, message = await product_data_service.smart_search_products(keyword="none", category=None, max_price=None, limit=5)

        assert products == []
        assert message == "No products found for criteria"
        mock_run_in_executor.assert_awaited_once_with(
            None, product_data_service.local_service.smart_search_products, "none", None, None, 5
        )

    async def test_smart_search_products_exception(self, product_data_service, mock_run_in_executor):
        """
        Test smart_search_products passes exceptions through, as it does not have its own try-except.
        """
        mock_run_in_executor.side_effect = ConnectionError("Cannot connect to local service for smart search")

        with pytest.raises(ConnectionError, match="Cannot connect to local service for smart search"):
            await product_data_service.smart_search_products("error_keyword")

        mock_run_in_executor.assert_awaited_once()