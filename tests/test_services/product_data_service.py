import logging
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# Define the path to the module under test for patching purposes
PRODUCT_DATA_SERVICE_MODULE = 'app.services.product_data_service'

# Define a mock specification for LocalProductService methods
# This helps ensure that methods called on the mock exist on the real object,
# preventing silent errors from typos in method names.
class MockLocalProductServiceSpec:
    """Specification for mocking LocalProductService methods."""
    def search_products(self, keyword: str, limit: int = 10): pass
    def get_products(self, limit: int = 20): pass
    def get_categories(self) -> list: pass
    def get_top_rated_products(self, limit: int = 10) -> list: pass
    def get_best_selling_products(self, limit: int = 10) -> list: pass
    def get_products_by_category(self, category: str) -> list: pass # ProductDataService applies limit by slicing
    def get_product_details(self, product_id: str): pass
    def get_brands(self) -> list: pass
    def get_products_by_brand(self, brand: str) -> list: pass # ProductDataService applies limit by slicing
    def smart_search_products(self, keyword: str = '', category: str = None, max_price: int = None, limit: int = 5): pass


@pytest.fixture
def mock_local_service(mocker):
    """
    Mocks the LocalProductService that ProductDataService uses.
    This fixture patches the imported LocalProductService within the target module.
    """
    # Patch `LocalProductService` as it's imported within `product_data_service.py`
    mock_lps = mocker.patch(
        f'{PRODUCT_DATA_SERVICE_MODULE}.LocalProductService',
        autospec=MockLocalProductServiceSpec # Use autospec to validate method calls
    ).return_value

    # Set default return values for the mock methods to prevent NoneType errors
    # for methods that are not specifically configured in a test.
    mock_lps.get_products_by_category.return_value = []
    mock_lps.get_products.return_value = []
    mock_lps.get_product_details.return_value = None
    mock_lps.get_brands.return_value = []
    mock_lps.get_products_by_brand.return_value = []
    mock_lps.get_categories.return_value = []
    mock_lps.get_top_rated_products.return_value = []
    mock_lps.get_best_selling_products.return_value = []
    mock_lps.search_products.return_value = []
    mock_lps.smart_search_products.return_value = ([], "")

    return mock_lps


@pytest.fixture
def product_data_service(mock_local_service):
    """
    Provides an instance of ProductDataService with its dependencies mocked.
    Import is done inside the fixture to ensure the patch is active when the class is defined.
    """
    # Import ProductDataService after LocalProductService has been patched
    from app.services.product_data_service import ProductDataService
    service = ProductDataService()
    # Assert that the service uses our mock
    assert service.local_service is mock_local_service
    return service


@pytest.fixture
def mock_run_in_executor(mocker):
    """
    Mocks asyncio.get_event_loop().run_in_executor to return an awaitable.
    This allows controlling the return value or side effect of the executor.
    """
    # Patch `asyncio.get_event_loop`
    mock_loop = mocker.patch(f'{PRODUCT_DATA_SERVICE_MODULE}.asyncio.get_event_loop').return_value
    
    # Create an AsyncMock for the return value of run_in_executor.
    # When `await mock_loop.run_in_executor(...)` is called, it will resolve to this mock's value.
    mock_executor_awaitable = AsyncMock()
    mock_loop.run_in_executor.return_value = mock_executor_awaitable
    
    # The fixture returns the AsyncMock itself, so tests can set its return_value or side_effect.
    return mock_executor_awaitable


# --- Test Cases for ProductDataService ---

class TestProductDataService:
    """Comprehensive test suite for ProductDataService."""

    @pytest.mark.asyncio
    async def test_init(self, mock_local_service, caplog):
        """Test ProductDataService initialization."""
        from app.services.product_data_service import ProductDataService
        with caplog.at_level(logging.INFO):
            service = ProductDataService()
            assert service.local_service is mock_local_service
            assert "ProductDataService initialized with LocalProductService" in caplog.text

    @pytest.mark.asyncio
    async def test_search_products_success(self, product_data_service, mock_run_in_executor, caplog):
        """Test search_products returns products successfully."""
        expected_products = [{"id": "1", "name": "Laptop", "price": 1200}]
        mock_run_in_executor.return_value = expected_products

        with caplog.at_level(logging.INFO):
            products = await product_data_service.search_products("laptop", limit=5)
            assert products == expected_products
            assert "Searching products with keyword: laptop" in caplog.text
            assert "Found 1 products for keyword: laptop" in caplog.text
        
        # Verify run_in_executor was called with the correct local_service method and arguments
        product_data_service.local_service.search_products.assert_called_once_with("laptop", 5)

    @pytest.mark.asyncio
    async def test_search_products_no_results(self, product_data_service, mock_run_in_executor, caplog):
        """Test search_products returns an empty list when no products are found."""
        mock_run_in_executor.return_value = []

        with caplog.at_level(logging.INFO):
            products = await product_data_service.search_products("nonexistent", limit=10)
            assert products == []
            assert "Found 0 products for keyword: nonexistent" in caplog.text
        
        product_data_service.local_service.search_products.assert_called_once_with("nonexistent", 10)

    @pytest.mark.asyncio
    async def test_search_products_exception(self, product_data_service, mock_run_in_executor, caplog):
        """Test search_products handles exceptions gracefully and logs an error."""
        mock_run_in_executor.side_effect = Exception("Local service error during search")

        with caplog.at_level(logging.ERROR):
            products = await product_data_service.search_products("error_case")
            assert products == []
            assert "Error searching products: Local service error during search" in caplog.text
        
        product_data_service.local_service.search_products.assert_called_once_with("error_case", 10)

    @pytest.mark.asyncio
    async def test_search_products_zero_limit(self, product_data_service, mock_run_in_executor, caplog):
        """Test search_products with limit=0 returns an empty list."""
        mock_run_in_executor.return_value = [] # The underlying service should return 0 items for limit 0

        with caplog.at_level(logging.INFO):
            products = await product_data_service.search_products("any", limit=0)
            assert products == []
            assert "Found 0 products for keyword: any" in caplog.text
        
        product_data_service.local_service.search_products.assert_called_once_with("any", 0)


    @pytest.mark.asyncio
    async def test_get_products_with_search(self, product_data_service, mock_run_in_executor):
        """Test get_products dispatches to search_products when 'search' keyword is present."""
        expected_products = [{"id": "s1", "name": "Search Result"}]
        # Mock the underlying call that search_products uses
        product_data_service.local_service.search_products.return_value = expected_products
        mock_run_in_executor.return_value = expected_products # Ensures the await in search_products gets the value
        
        products = await product_data_service.get_products(search="query", limit=5)
        assert products == expected_products
        # Verify that local_service.search_products was called via run_in_executor
        product_data_service.local_service.search_products.assert_called_once_with("query", 5)

    @pytest.mark.asyncio
    async def test_get_products_with_category(self, product_data_service):
        """Test get_products dispatches to get_products_by_category when 'category' is present."""
        expected_products = [{"id": "c1", "name": "Category Item"}]
        # This will be called by ProductDataService's get_products_by_category method, not directly by get_products
        product_data_service.local_service.get_products_by_category.return_value = expected_products
        
        products = await product_data_service.get_products(category="electronics", limit=10)
        assert products == expected_products
        # local_service's method is called by the ProductDataService's internal method
        product_data_service.local_service.get_products_by_category.assert_called_once_with("electronics")

    @pytest.mark.asyncio
    async def test_get_products_no_filters(self, product_data_service):
        """Test get_products dispatches to get_all_products when no filters are present."""
        expected_products = [{"id": "a1", "name": "All Item"}]
        # This will be called by ProductDataService's get_all_products method
        product_data_service.local_service.get_products.return_value = expected_products
        
        products = await product_data_service.get_products(limit=15)
        assert products == expected_products
        # local_service's method is called by the ProductDataService's internal method
        product_data_service.local_service.get_products.assert_called_once_with(15)

    @pytest.mark.asyncio
    async def test_get_products_search_precedence(self, product_data_service, mock_run_in_executor):
        """Test get_products prioritizes 'search' over 'category' if both are provided."""
        expected_products = [{"id": "s_prec", "name": "Search Precedence"}]
        product_data_service.local_service.search_products.return_value = expected_products
        mock_run_in_executor.return_value = expected_products

        products = await product_data_service.get_products(search="query", category="ignored", limit=5)
        assert products == expected_products
        product_data_service.local_service.search_products.assert_called_once_with("query", 5)
        product_data_service.local_service.get_products_by_category.assert_not_called() # Ensure category path was not taken

    @pytest.mark.asyncio
    async def test_get_products_exception_fallback(self, product_data_service, mock_run_in_executor, caplog):
        """Test get_products falls back to local_service.get_products on error in 'search' dispatch."""
        # Simulate an error in the search path to trigger the fallback
        mock_run_in_executor.side_effect = Exception("Search path failed")
        
        # Configure fallback method's return value
        fallback_products = [{"id": "fallback", "name": "Fallback Product"}]
        product_data_service.local_service.get_products.return_value = fallback_products

        with caplog.at_level(logging.ERROR):
            products = await product_data_service.get_products(search="err", limit=5)
            assert products == fallback_products
            assert "Error getting products: Search path failed" in caplog.text
        
        # Verify fallback call
        product_data_service.local_service.get_products.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_get_products_with_category_exception_fallback(self, product_data_service, mocker, caplog):
        """
        Test get_products falls back to local_service.get_products when
        get_products_by_category (called internally) raises an exception.
        """
        # Patch the internal method get_products_by_category to raise an exception
        mocker.patch.object(product_data_service, 'get_products_by_category', side_effect=Exception("Category processing failed"))
        
        # Configure fallback method's return value
        fallback_products = [{"id": "fallback_cat", "name": "Fallback Category Product"}]
        product_data_service.local_service.get_products.return_value = fallback_products

        with caplog.at_level(logging.ERROR):
            products = await product_data_service.get_products(category="error_cat", limit=7)
            assert products == fallback_products
            assert "Error getting products: Category processing failed" in caplog.text
        
        # Verify that get_products_by_category was attempted and then fallback occurred
        product_data_service.get_products_by_category.assert_called_once_with("error_cat", 7)
        product_data_service.local_service.get_products.assert_called_once_with(7)


    @pytest.mark.asyncio
    async def test_get_products_no_filters_exception_fallback(self, product_data_service, mocker, caplog):
        """
        Test get_products falls back to local_service.get_products when
        get_all_products (called internally) raises an exception.
        """
        # Patch the internal method get_all_products to raise an exception
        mocker.patch.object(product_data_service, 'get_all_products', side_effect=Exception("All products processing failed"))
        
        # Configure fallback method's return value
        fallback_products = [{"id": "fallback_all", "name": "Fallback All Product"}]
        product_data_service.local_service.get_products.return_value = fallback_products

        with caplog.at_level(logging.ERROR):
            products = await product_data_service.get_products(limit=12)
            assert products == fallback_products
            assert "Error getting products: All products processing failed" in caplog.text
        
        # Verify that get_all_products was attempted and then fallback occurred
        product_data_service.get_all_products.assert_called_once_with(12)
        product_data_service.local_service.get_products.assert_called_once_with(12)

    @pytest.mark.asyncio
    async def test_get_products_default_limit(self, product_data_service):
        """Test get_products uses default limit when no filters are specified."""
        expected_products = [{"id": "default", "name": "Default Limit Product"}]
        product_data_service.local_service.get_products.return_value = expected_products
        
        products = await product_data_service.get_products() # No limit specified
        assert products == expected_products
        product_data_service.local_service.get_products.assert_called_once_with(20) # Default limit is 20


    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service):
        """Test get_categories returns categories successfully."""
        expected_categories = ["Electronics", "Books", "Clothing"]
        product_data_service.local_service.get_categories.return_value = expected_categories
        
        categories = await product_data_service.get_categories()
        assert categories == expected_categories
        product_data_service.local_service.get_categories.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_categories_empty(self, product_data_service):
        """Test get_categories returns an empty list when no categories are available."""
        product_data_service.local_service.get_categories.return_value = []
        
        categories = await product_data_service.get_categories()
        assert categories == []
        product_data_service.local_service.get_categories.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_categories_exception(self, product_data_service, caplog):
        """Test get_categories handles exceptions gracefully."""
        product_data_service.local_service.get_categories.side_effect = Exception("Category service down")
        
        with caplog.at_level(logging.ERROR):
            categories = await product_data_service.get_categories()
            assert categories == []
            assert "Error getting categories: Category service down" in caplog.text
        
        product_data_service.local_service.get_categories.assert_called_once()


    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service):
        """Test get_top_rated_products returns products successfully."""
        expected_products = [{"id": "t1", "name": "Top Product", "rating": 5.0}]
        product_data_service.local_service.get_top_rated_products.return_value = expected_products
        
        products = await product_data_service.get_top_rated_products(limit=2)
        assert products == expected_products
        product_data_service.local_service.get_top_rated_products.assert_called_once_with(2)

    @pytest.mark.asyncio
    async def test_get_top_rated_products_empty(self, product_data_service):
        """Test get_top_rated_products returns empty list when no products are found."""
        product_data_service.local_service.get_top_rated_products.return_value = []
        products = await product_data_service.get_top_rated_products(limit=5)
        assert products == []
        product_data_service.local_service.get_top_rated_products.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_get_top_rated_products_zero_limit(self, product_data_service):
        """Test get_top_rated_products with limit=0 returns empty list."""
        product_data_service.local_service.get_top_rated_products.return_value = [] # The underlying service should return 0 for limit 0
        products = await product_data_service.get_top_rated_products(limit=0)
        assert products == []
        product_data_service.local_service.get_top_rated_products.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_get_top_rated_products_exception(self, product_data_service, caplog):
        """Test get_top_rated_products handles exceptions gracefully."""
        product_data_service.local_service.get_top_rated_products.side_effect = Exception("Top rated service error")
        
        with caplog.at_level(logging.ERROR):
            products = await product_data_service.get_top_rated_products()
            assert products == []
            assert "Error getting top rated products: Top rated service error" in caplog.text
        
        product_data_service.local_service.get_top_rated_products.assert_called_once_with(10)


    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service):
        """Test get_best_selling_products returns products successfully."""
        expected_products = [{"id": "b1", "name": "Best Seller", "sales": 1000}]
        product_data_service.local_service.get_best_selling_products.return_value = expected_products
        
        products = await product_data_service.get_best_selling_products(limit=3)
        assert products == expected_products
        product_data_service.local_service.get_best_selling_products.assert_called_once_with(3)

    @pytest.mark.asyncio
    async def test_get_best_selling_products_empty(self, product_data_service):
        """Test get_best_selling_products returns empty list when no products are found."""
        product_data_service.local_service.get_best_selling_products.return_value = []
        products = await product_data_service.get_best_selling_products(limit=5)
        assert products == []
        product_data_service.local_service.get_best_selling_products.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_get_best_selling_products_zero_limit(self, product_data_service):
        """Test get_best_selling_products with limit=0 returns empty list."""
        product_data_service.local_service.get_best_selling_products.return_value = [] # The underlying service should return 0 for limit 0
        products = await product_data_service.get_best_selling_products(limit=0)
        assert products == []
        product_data_service.local_service.get_best_selling_products.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_get_best_selling_products_exception(self, product_data_service, caplog):
        """Test get_best_selling_products handles exceptions gracefully."""
        product_data_service.local_service.get_best_selling_products.side_effect = Exception("Best selling service error")
        
        with caplog.at_level(logging.ERROR):
            products = await product_data_service.get_best_selling_products()
            assert products == []
            assert "Error getting best selling products: Best selling service error" in caplog.text
        
        product_data_service.local_service.get_best_selling_products.assert_called_once_with(10)


    def test_get_products_by_category_success(self, product_data_service):
        """Test get_products_by_category returns products and applies limit."""
        # Simulate more products than limit to test slicing
        all_cat_products = [{"id": "c1"}, {"id": "c2"}, {"id": "c3"}, {"id": "c4"}]
        product_data_service.local_service.get_products_by_category.return_value = all_cat_products
        
        products = product_data_service.get_products_by_category("electronics", limit=2)
        assert products == [{"id": "c1"}, {"id": "c2"}]
        # local_service.get_products_by_category does not take limit directly
        product_data_service.local_service.get_products_by_category.assert_called_once_with("electronics")

    def test_get_products_by_category_limit_exceeds_available(self, product_data_service):
        """Test get_products_by_category returns all available products if limit exceeds them."""
        all_cat_products = [{"id": "c1"}, {"id": "c2"}]
        product_data_service.local_service.get_products_by_category.return_value = all_cat_products
        
        products = product_data_service.get_products_by_category("electronics", limit=10) # Limit is 10, but only 2 available
        assert products == all_cat_products
        product_data_service.local_service.get_products_by_category.assert_called_once_with("electronics")

    def test_get_products_by_category_zero_limit(self, product_data_service):
        """Test get_products_by_category with limit=0 returns an empty list."""
        product_data_service.local_service.get_products_by_category.return_value = [{"id": "c1"}] # Even if products exist
        
        products = product_data_service.get_products_by_category("electronics", limit=0)
        assert products == []
        product_data_service.local_service.get_products_by_category.assert_called_once_with("electronics")


    def test_get_products_by_category_no_results(self, product_data_service):
        """Test get_products_by_category returns empty list if no results."""
        product_data_service.local_service.get_products_by_category.return_value = []
        
        products = product_data_service.get_products_by_category("unknown_category")
        assert products == []
        product_data_service.local_service.get_products_by_category.assert_called_once_with("unknown_category")

    def test_get_products_by_category_exception(self, product_data_service, caplog):
        """Test get_products_by_category handles exceptions gracefully."""
        product_data_service.local_service.get_products_by_category.side_effect = Exception("Category DB error")
        
        with caplog.at_level(logging.ERROR):
            products = product_data_service.get_products_by_category("failed_cat")
            assert products == []
            assert "Error getting products by category: Category DB error" in caplog.text
        
        product_data_service.local_service.get_products_by_category.assert_called_once_with("failed_cat")


    def test_get_all_products_success(self, product_data_service):
        """Test get_all_products returns products and passes limit to local service."""
        # local_service.get_products takes limit directly
        expected_products_for_limit = [{"id": "a1"}, {"id": "a2"}]
        product_data_service.local_service.get_products.return_value = expected_products_for_limit
        
        products = product_data_service.get_all_products(limit=2)
        assert products == expected_products_for_limit
        product_data_service.local_service.get_products.assert_called_once_with(2)

    def test_get_all_products_default_limit(self, product_data_service):
        """Test get_all_products uses default limit."""
        expected_products = [{"id": "a1", "name": "Default All Product"}]
        product_data_service.local_service.get_products.return_value = expected_products
        
        products = product_data_service.get_all_products() # No limit specified
        assert products == expected_products
        product_data_service.local_service.get_products.assert_called_once_with(20) # Default limit is 20

    def test_get_all_products_no_results(self, product_data_service):
        """Test get_all_products returns empty list if no results."""
        product_data_service.local_service.get_products.return_value = []
        
        products = product_data_service.get_all_products()
        assert products == []
        product_data_service.local_service.get_products.assert_called_once_with(20)

    def test_get_all_products_zero_limit(self, product_data_service):
        """Test get_all_products with limit=0 returns empty list."""
        product_data_service.local_service.get_products.return_value = [] # Underlying service would return 0 for limit 0
        products = product_data_service.get_all_products(limit=0)
        assert products == []
        product_data_service.local_service.get_products.assert_called_once_with(0)


    def test_get_all_products_exception(self, product_data_service, caplog):
        """Test get_all_products handles exceptions gracefully."""
        product_data_service.local_service.get_products.side_effect = Exception("All products DB error")
        
        with caplog.at_level(logging.ERROR):
            products = product_data_service.get_all_products()
            assert products == []
            assert "Error getting all products: All products DB error" in caplog.text
        
        product_data_service.local_service.get_products.assert_called_once_with(20)


    def test_get_product_details_success(self, product_data_service):
        """Test get_product_details returns product details."""
        expected_details = {"id": "p123", "name": "Widget X", "description": "A fine widget."}
        product_data_service.local_service.get_product_details.return_value = expected_details
        
        details = product_data_service.get_product_details("p123")
        assert details == expected_details
        product_data_service.local_service.get_product_details.assert_called_once_with("p123")

    def test_get_product_details_not_found(self, product_data_service):
        """Test get_product_details returns None if product not found."""
        product_data_service.local_service.get_product_details.return_value = None
        
        details = product_data_service.get_product_details("nonexistent")
        assert details is None
        product_data_service.local_service.get_product_details.assert_called_once_with("nonexistent")

    def test_get_product_details_exception(self, product_data_service, caplog):
        """Test get_product_details handles exceptions gracefully."""
        product_data_service.local_service.get_product_details.side_effect = Exception("Details service error")
        
        with caplog.at_level(logging.ERROR):
            details = product_data_service.get_product_details("error_id")
            assert details is None
            assert "Error getting product details: Details service error" in caplog.text
        
        product_data_service.local_service.get_product_details.assert_called_once_with("error_id")


    def test_get_brands_success(self, product_data_service):
        """Test get_brands returns list of brands."""
        expected_brands = ["Brand A", "Brand B", "Brand C"]
        product_data_service.local_service.get_brands.return_value = expected_brands
        
        brands = product_data_service.get_brands()
        assert brands == expected_brands
        product_data_service.local_service.get_brands.assert_called_once()

    def test_get_brands_empty(self, product_data_service):
        """Test get_brands returns empty list when no brands are available."""
        product_data_service.local_service.get_brands.return_value = []
        
        brands = product_data_service.get_brands()
        assert brands == []
        product_data_service.local_service.get_brands.assert_called_once()

    def test_get_brands_exception(self, product_data_service, caplog):
        """Test get_brands handles exceptions gracefully."""
        product_data_service.local_service.get_brands.side_effect = Exception("Brand service error")
        
        with caplog.at_level(logging.ERROR):
            brands = product_data_service.get_brands()
            assert brands == []
            assert "Error getting brands: Brand service error" in caplog.text
        
        product_data_service.local_service.get_brands.assert_called_once()


    def test_get_products_by_brand_success(self, product_data_service):
        """Test get_products_by_brand returns products and applies limit."""
        all_brand_products = [{"id": "br1"}, {"id": "br2"}, {"id": "br3"}, {"id": "br4"}]
        product_data_service.local_service.get_products_by_brand.return_value = all_brand_products
        
        products = product_data_service.get_products_by_brand("brandx", limit=2)
        assert products == [{"id": "br1"}, {"id": "br2"}]
        # local_service.get_products_by_brand does not take limit directly
        product_data_service.local_service.get_products_by_brand.assert_called_once_with("brandx")

    def test_get_products_by_brand_limit_exceeds_available(self, product_data_service):
        """Test get_products_by_brand returns all available products if limit exceeds them."""
        all_brand_products = [{"id": "br1"}, {"id": "br2"}]
        product_data_service.local_service.get_products_by_brand.return_value = all_brand_products
        
        products = product_data_service.get_products_by_brand("brandx", limit=10)
        assert products == all_brand_products
        product_data_service.local_service.get_products_by_brand.assert_called_once_with("brandx")

    def test_get_products_by_brand_zero_limit(self, product_data_service):
        """Test get_products_by_brand with limit=0 returns an empty list."""
        product_data_service.local_service.get_products_by_brand.return_value = [{"id": "br1"}] # Even if products exist
        
        products = product_data_service.get_products_by_brand("brandx", limit=0)
        assert products == []
        product_data_service.local_service.get_products_by_brand.assert_called_once_with("brandx")

    def test_get_products_by_brand_no_results(self, product_data_service):
        """Test get_products_by_brand returns empty list if no results."""
        product_data_service.local_service.get_products_by_brand.return_value = []
        
        products = product_data_service.get_products_by_brand("unknown_brand")
        assert products == []
        product_data_service.local_service.get_products_by_brand.assert_called_once_with("unknown_brand")

    def test_get_products_by_brand_exception(self, product_data_service, caplog):
        """Test get_products_by_brand handles exceptions gracefully."""
        product_data_service.local_service.get_products_by_brand.side_effect = Exception("Brand DB error")
        
        with caplog.at_level(logging.ERROR):
            products = product_data_service.get_products_by_brand("failed_brand")
            assert products == []
            assert "Error getting products by brand: Brand DB error" in caplog.text
        
        product_data_service.local_service.get_products_by_brand.assert_called_once_with("failed_brand")


    @pytest.mark.asyncio
    async def test_smart_search_products_success(self, product_data_service, mock_run_in_executor):
        """Test smart_search_products returns products and message successfully."""
        expected_products = [{"id": "s_s1", "name": "Smart Item"}]
        expected_message = "Smart search completed."
        mock_run_executor_result = (expected_products, expected_message)
        mock_run_in_executor.return_value = mock_run_executor_result # What the await resolves to

        products, message = await product_data_service.smart_search_products(
            keyword="smart", category="books", max_price=50, limit=3
        )
        assert products == expected_products
        assert message == expected_message
        
        product_data_service.local_service.smart_search_products.assert_called_once_with(
            "smart", "books", 50, 3
        )

    @pytest.mark.asyncio
    async def test_smart_search_products_default_args(self, product_data_service, mock_run_in_executor):
        """Test smart_search_products uses default arguments correctly."""
        expected_products = [{"id": "s_s_def", "name": "Default Search"}]
        expected_message = "Default search."
        mock_run_executor_result = (expected_products, expected_message)
        mock_run_in_executor.return_value = mock_run_executor_result

        products, message = await product_data_service.smart_search_products() # No args
        assert products == expected_products
        assert message == expected_message
        
        # Verify that the local service method was called with default values
        product_data_service.local_service.smart_search_products.assert_called_once_with(
            '', None, None, 5
        )
    
    @pytest.mark.asyncio
    async def test_smart_search_products_zero_limit(self, product_data_service, mock_run_in_executor):
        """Test smart_search_products with limit=0."""
        expected_products = []
        expected_message = "No results due to limit 0."
        mock_run_executor_result = (expected_products, expected_message)
        mock_run_in_executor.return_value = mock_run_executor_result

        products, message = await product_data_service.smart_search_products(limit=0)
        assert products == expected_products
        assert message == expected_message
        product_data_service.local_service.smart_search_products.assert_called_once_with('', None, None, 0)


    @pytest.mark.asyncio
    async def test_smart_search_products_exception(self, product_data_service, mock_run_in_executor):
        """Test smart_search_products propagates exceptions as it has no try-except."""
        mock_run_in_executor.side_effect = Exception("Smart search internal error")

        with pytest.raises(Exception, match="Smart search internal error"):
            await product_data_service.smart_search_products("fail_keyword")

        # Verify that the local service method was still attempted to be called
        product_data_service.local_service.smart_search_products.assert_called_once_with("fail_keyword", None, None, 5)