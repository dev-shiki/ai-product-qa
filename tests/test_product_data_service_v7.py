import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import logging

# Set up logging for tests to capture log messages
@pytest.fixture(autouse=True)
def setup_logging(caplog):
    caplog.set_level(logging.INFO)
    caplog.set_level(logging.ERROR)

# Import the class under test after setting up mocks for its dependencies
# This is crucial for patching modules correctly.
# We will mock LocalProductService from where it's imported in ProductDataService
# which is 'app.services.product_data_service.LocalProductService'
# So, we need to import ProductDataService *after* setting up mocks for its imports.

# Mock the LocalProductService globally for all tests in this file
@pytest.fixture
def mock_local_product_service():
    """
    Fixture to mock the LocalProductService dependency.
    """
    with patch('app.services.product_data_service.LocalProductService') as mock_service_class:
        mock_instance = MagicMock()
        # Define mock return values for methods that ProductDataService calls
        mock_instance.search_products.return_value = []
        mock_instance.get_products.return_value = []
        mock_instance.get_categories.return_value = []
        mock_instance.get_top_rated_products.return_value = []
        mock_instance.get_best_selling_products.return_value = []
        mock_instance.get_products_by_category.return_value = []
        mock_instance.get_product_details.return_value = None
        mock_instance.get_brands.return_value = []
        mock_instance.get_products_by_brand.return_value = []
        mock_instance.smart_search_products.return_value = ([], "No results.")

        mock_service_class.return_value = mock_instance
        yield mock_instance

# Mock asyncio.get_event_loop().run_in_executor
# This is called directly in ProductDataService, so we need to patch asyncio.
@pytest.fixture
def mock_run_in_executor(mocker):
    """
    Fixture to mock asyncio.get_event_loop().run_in_executor.
    It should return an awaitable.
    """
    mock_executor = MagicMock()
    mock_loop = MagicMock()
    mock_loop.run_in_executor.return_value = AsyncMock(return_value=[]) # Default empty list
    mock_executor.get_event_loop.return_value = mock_loop

    mocker.patch('asyncio.get_event_loop', return_value=mock_loop)
    return mock_loop.run_in_executor

# Import ProductDataService after all necessary patches are defined
from app.services.product_data_service import ProductDataService


@pytest.fixture
def product_data_service(mock_local_product_service):
    """
    Fixture to provide an instance of ProductDataService for tests.
    It ensures the LocalProductService is mocked.
    """
    service = ProductDataService()
    return service

@pytest.mark.asyncio
class TestProductDataService:

    async def test_init(self, mock_local_product_service, caplog):
        """
        Test that ProductDataService initializes correctly and uses LocalProductService.
        """
        service = ProductDataService()
        assert service.local_service == mock_local_product_service
        mock_local_product_service.assert_called_once()
        assert "ProductDataService initialized with LocalProductService" in caplog.text

    async def test_search_products_success(self, product_data_service, mock_run_in_executor, caplog):
        """
        Test search_products method success case.
        """
        expected_products = [{"id": "1", "name": "Laptop A"}, {"id": "2", "name": "Laptop B"}]
        mock_run_in_executor.return_value = AsyncMock(return_value=expected_products)

        result = await product_data_service.search_products("laptop", limit=5)

        assert result == expected_products
        mock_run_in_executor.assert_called_once_with(None, product_data_service.local_service.search_products, "laptop", 5)
        assert "Searching products with keyword: laptop" in caplog.text
        assert "Found 2 products for keyword: laptop" in caplog.text

    async def test_search_products_error(self, product_data_service, mock_run_in_executor, caplog):
        """
        Test search_products method error case.
        """
        mock_run_in_executor.return_value = AsyncMock(side_effect=Exception("API error"))

        result = await product_data_service.search_products("invalid")

        assert result == []
        mock_run_in_executor.assert_called_once_with(None, product_data_service.local_service.search_products, "invalid", 10)
        assert "Error searching products: API error" in caplog.text
        assert "Searching products with keyword: invalid" in caplog.text # Should still log info before error

    async def test_get_products_by_search(self, product_data_service, mock_run_in_executor, caplog):
        """
        Test get_products when search keyword is provided.
        Should delegate to search_products.
        """
        expected_products = [{"id": "s1", "name": "Search Item"}]
        mock_run_in_executor.return_value = AsyncMock(return_value=expected_products)

        result = await product_data_service.get_products(search="item", limit=5)

        assert result == expected_products
        # Verify that search_products was called via run_in_executor
        mock_run_in_executor.assert_called_once_with(None, product_data_service.local_service.search_products, "item", 5)
        assert "Searching products with keyword: item" in caplog.text


    async def test_get_products_by_category(self, product_data_service, mock_local_product_service):
        """
        Test get_products when category is provided.
        Should delegate to get_products_by_category.
        """
        expected_products = [{"id": "c1", "name": "Category Item"}]
        mock_local_product_service.get_products_by_category.return_value = expected_products

        result = await product_data_service.get_products(category="electronics", limit=15)

        assert result == expected_products
        mock_local_product_service.get_products_by_category.assert_called_once_with("electronics")
        # Ensure it respects the limit by slicing
        assert len(result) <= 15

    async def test_get_products_all(self, product_data_service, mock_local_product_service):
        """
        Test get_products when no search or category is provided.
        Should delegate to get_all_products.
        """
        expected_products = [{"id": "a1", "name": "All Item"}]
        mock_local_product_service.get_products.return_value = expected_products

        result = await product_data_service.get_products(limit=10)

        assert result == expected_products
        mock_local_product_service.get_products.assert_called_once_with(10)

    async def test_get_products_error_fallback(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_products error scenario where it falls back to local_service.get_products.
        We'll make an internal call (e.g., search_products) fail to trigger the fallback.
        """
        # Mocking an internal method that get_products calls to raise an exception
        # Let's mock search_products within the service itself for this specific test
        # Note: This is an internal mock, not a dependency mock.
        with patch.object(product_data_service, 'search_products', side_effect=Exception("Internal search error")) as mock_search_products:
            expected_fallback_products = [{"id": "fb1", "name": "Fallback Product"}]
            mock_local_product_service.get_products.return_value = expected_fallback_products

            result = await product_data_service.get_products(search="error_test", limit=5)

            assert result == expected_fallback_products
            mock_search_products.assert_called_once_with("error_test", 5)
            mock_local_product_service.get_products.assert_called_once_with(5) # Called as fallback
            assert "Error getting products: Internal search error" in caplog.text

    async def test_get_categories_success(self, product_data_service, mock_local_product_service):
        """
        Test get_categories method success case.
        """
        expected_categories = ["Electronics", "Books"]
        mock_local_product_service.get_categories.return_value = expected_categories

        result = await product_data_service.get_categories()

        assert result == expected_categories
        mock_local_product_service.get_categories.assert_called_once()

    async def test_get_categories_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_categories method error case.
        """
        mock_local_product_service.get_categories.side_effect = Exception("Category fetch error")

        result = await product_data_service.get_categories()

        assert result == []
        mock_local_product_service.get_categories.assert_called_once()
        assert "Error getting categories: Category fetch error" in caplog.text

    async def test_get_top_rated_products_success(self, product_data_service, mock_local_product_service):
        """
        Test get_top_rated_products method success case.
        """
        expected_products = [{"id": "tr1", "rating": 5}]
        mock_local_product_service.get_top_rated_products.return_value = expected_products

        result = await product_data_service.get_top_rated_products(limit=3)

        assert result == expected_products
        mock_local_product_service.get_top_rated_products.assert_called_once_with(3)

    async def test_get_top_rated_products_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_top_rated_products method error case.
        """
        mock_local_product_service.get_top_rated_products.side_effect = Exception("Top rated error")

        result = await product_data_service.get_top_rated_products()

        assert result == []
        mock_local_product_service.get_top_rated_products.assert_called_once_with(10)
        assert "Error getting top rated products: Top rated error" in caplog.text

    async def test_get_best_selling_products_success(self, product_data_service, mock_local_product_service):
        """
        Test get_best_selling_products method success case.
        """
        expected_products = [{"id": "bs1", "sales": 100}]
        mock_local_product_service.get_best_selling_products.return_value = expected_products

        result = await product_data_service.get_best_selling_products(limit=2)

        assert result == expected_products
        mock_local_product_service.get_best_selling_products.assert_called_once_with(2)

    async def test_get_best_selling_products_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_best_selling_products method error case.
        """
        mock_local_product_service.get_best_selling_products.side_effect = Exception("Best selling error")

        result = await product_data_service.get_best_selling_products()

        assert result == []
        mock_local_product_service.get_best_selling_products.assert_called_once_with(10)
        assert "Error getting best selling products: Best selling error" in caplog.text

    def test_get_products_by_category_success(self, product_data_service, mock_local_product_service):
        """
        Test get_products_by_category method success case.
        Ensures limit is applied.
        """
        mock_local_product_service.get_products_by_category.return_value = [
            {"id": "cat1", "category": "books"},
            {"id": "cat2", "category": "books"},
            {"id": "cat3", "category": "books"},
            {"id": "cat4", "category": "books"},
        ]
        
        result = product_data_service.get_products_by_category("books", limit=2)
        
        assert len(result) == 2
        assert result == [{"id": "cat1", "category": "books"}, {"id": "cat2", "category": "books"}]
        mock_local_product_service.get_products_by_category.assert_called_once_with("books")

    def test_get_products_by_category_less_than_limit(self, product_data_service, mock_local_product_service):
        """
        Test get_products_by_category when fewer items than limit are returned.
        """
        mock_local_product_service.get_products_by_category.return_value = [
            {"id": "cat1", "category": "books"},
        ]
        
        result = product_data_service.get_products_by_category("books", limit=5)
        
        assert len(result) == 1
        assert result == [{"id": "cat1", "category": "books"}]

    def test_get_products_by_category_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_products_by_category method error case.
        """
        mock_local_product_service.get_products_by_category.side_effect = Exception("Category error")

        result = product_data_service.get_products_by_category("fiction")

        assert result == []
        mock_local_product_service.get_products_by_category.assert_called_once_with("fiction")
        assert "Error getting products by category: Category error" in caplog.text

    def test_get_all_products_success(self, product_data_service, mock_local_product_service):
        """
        Test get_all_products method success case.
        """
        expected_products = [{"id": "p1", "name": "Product 1"}, {"id": "p2", "name": "Product 2"}]
        mock_local_product_service.get_products.return_value = expected_products

        result = product_data_service.get_all_products(limit=2)

        assert result == expected_products
        mock_local_product_service.get_products.assert_called_once_with(2)

    def test_get_all_products_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_all_products method error case.
        """
        mock_local_product_service.get_products.side_effect = Exception("All products error")

        result = product_data_service.get_all_products()

        assert result == []
        mock_local_product_service.get_products.assert_called_once_with(20) # Default limit
        assert "Error getting all products: All products error" in caplog.text

    def test_get_product_details_success(self, product_data_service, mock_local_product_service):
        """
        Test get_product_details method success case.
        """
        expected_details = {"id": "xyz", "name": "Super Product", "price": 99.99}
        mock_local_product_service.get_product_details.return_value = expected_details

        result = product_data_service.get_product_details("xyz")

        assert result == expected_details
        mock_local_product_service.get_product_details.assert_called_once_with("xyz")

    def test_get_product_details_not_found(self, product_data_service, mock_local_product_service):
        """
        Test get_product_details when product is not found.
        """
        mock_local_product_service.get_product_details.return_value = None

        result = product_data_service.get_product_details("nonexistent_id")

        assert result is None
        mock_local_product_service.get_product_details.assert_called_once_with("nonexistent_id")

    def test_get_product_details_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_product_details method error case.
        """
        mock_local_product_service.get_product_details.side_effect = Exception("Details error")

        result = product_data_service.get_product_details("123")

        assert result is None
        mock_local_product_service.get_product_details.assert_called_once_with("123")
        assert "Error getting product details: Details error" in caplog.text

    def test_get_brands_success(self, product_data_service, mock_local_product_service):
        """
        Test get_brands method success case.
        """
        expected_brands = ["BrandA", "BrandB"]
        mock_local_product_service.get_brands.return_value = expected_brands

        result = product_data_service.get_brands()

        assert result == expected_brands
        mock_local_product_service.get_brands.assert_called_once()

    def test_get_brands_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_brands method error case.
        """
        mock_local_product_service.get_brands.side_effect = Exception("Brands error")

        result = product_data_service.get_brands()

        assert result == []
        mock_local_product_service.get_brands.assert_called_once()
        assert "Error getting brands: Brands error" in caplog.text

    def test_get_products_by_brand_success(self, product_data_service, mock_local_product_service):
        """
        Test get_products_by_brand method success case.
        Ensures limit is applied.
        """
        mock_local_product_service.get_products_by_brand.return_value = [
            {"id": "b1", "brand": "BrandX"},
            {"id": "b2", "brand": "BrandX"},
            {"id": "b3", "brand": "BrandX"},
        ]
        
        result = product_data_service.get_products_by_brand("BrandX", limit=2)
        
        assert len(result) == 2
        assert result == [{"id": "b1", "brand": "BrandX"}, {"id": "b2", "brand": "BrandX"}]
        mock_local_product_service.get_products_by_brand.assert_called_once_with("BrandX")

    def test_get_products_by_brand_less_than_limit(self, product_data_service, mock_local_product_service):
        """
        Test get_products_by_brand when fewer items than limit are returned.
        """
        mock_local_product_service.get_products_by_brand.return_value = [
            {"id": "b1", "brand": "BrandX"},
        ]
        
        result = product_data_service.get_products_by_brand("BrandX", limit=5)
        
        assert len(result) == 1
        assert result == [{"id": "b1", "brand": "BrandX"}]

    def test_get_products_by_brand_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_products_by_brand method error case.
        """
        mock_local_product_service.get_products_by_brand.side_effect = Exception("Brand products error")

        result = product_data_service.get_products_by_brand("BrandY")

        assert result == []
        mock_local_product_service.get_products_by_brand.assert_called_once_with("BrandY")
        assert "Error getting products by brand: Brand products error" in caplog.text

    async def test_smart_search_products_success(self, product_data_service, mock_run_in_executor):
        """
        Test smart_search_products method success case.
        """
        expected_products = [{"id": "ss1", "name": "Smart Search Result"}]
        expected_message = "Smart search completed."
        mock_run_in_executor.return_value = AsyncMock(return_value=(expected_products, expected_message))

        products, message = await product_data_service.smart_search_products(
            keyword="smart", category="tech", max_price=500, limit=2
        )

        assert products == expected_products
        assert message == expected_message
        mock_run_in_executor.assert_called_once_with(
            None, product_data_service.local_service.smart_search_products, "smart", "tech", 500, 2
        )

    async def test_smart_search_products_error(self, product_data_service, mock_run_in_executor):
        """
        Test smart_search_products method error case.
        The original method does not handle exceptions, so we expect it to propagate.
        """
        mock_run_in_executor.return_value = AsyncMock(side_effect=Exception("Smart search failed"))

        with pytest.raises(Exception, match="Smart search failed"):
            await product_data_service.smart_search_products(keyword="error")

        mock_run_in_executor.assert_called_once_with(
            None, product_data_service.local_service.smart_search_products, "error", None, None, 5
        )

    async def test_smart_search_products_defaults(self, product_data_service, mock_run_in_executor):
        """
        Test smart_search_products with default parameters.
        """
        expected_products = [{"id": "ssd1", "name": "Default Result"}]
        expected_message = "Default search."
        mock_run_in_executor.return_value = AsyncMock(return_value=(expected_products, expected_message))

        products, message = await product_data_service.smart_search_products()

        assert products == expected_products
        assert message == expected_message
        mock_run_in_executor.assert_called_once_with(
            None, product_data_service.local_service.smart_search_products, '', None, None, 5
        )