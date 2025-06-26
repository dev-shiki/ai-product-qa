import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
import logging

# Ensure the path is correct for importing the service
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService

@pytest.fixture
def mock_local_product_service():
    """
    Fixture to mock the LocalProductService class and its instance.
    Sets default return values for common methods to prevent errors
    if not explicitly set in a test.
    """
    with patch('app.services.product_data_service.LocalProductService') as mock_service_class:
        mock_instance = MagicMock(spec=LocalProductService)
        # Default mock return values
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

@pytest.fixture
def product_data_service(mock_local_product_service):
    """
    Fixture to provide an instance of ProductDataService with
    its LocalProductService dependency mocked.
    """
    return ProductDataService()

@pytest.fixture
def mock_run_in_executor(monkeypatch):
    """
    Mocks asyncio.get_event_loop().run_in_executor for async methods.
    It directly calls the target function (which will be a mock itself)
    and returns its result, bypassing actual thread pool execution.
    """
    mock_loop = MagicMock()
    
    async def _mock_executor_return(executor, func, *args, **kwargs):
        # We expect 'func' to be a mock from mock_local_product_service
        # Call it directly to get its configured return_value or side_effect
        return func(*args, **kwargs)

    mock_loop.run_in_executor.side_effect = _mock_executor_return

    mock_get_event_loop = MagicMock(return_value=mock_loop)
    monkeypatch.setattr(asyncio, 'get_event_loop', mock_get_event_loop)
    return mock_loop.run_in_executor

class TestProductDataService:
    """
    Comprehensive test suite for the ProductDataService class,
    aiming for high coverage by testing all methods, their branches,
    and error handling.
    """

    @pytest.mark.asyncio
    async def test_init(self, mock_local_product_service, caplog):
        """
        Test ProductDataService initialization.
        Verifies that LocalProductService is instantiated and
        the correct log message is emitted.
        """
        with caplog.at_level(logging.INFO):
            service = ProductDataService()
            mock_local_product_service.assert_called_once()
            assert isinstance(service.local_service, MagicMock)
            assert "ProductDataService initialized with LocalProductService" in caplog.text

    @pytest.mark.asyncio
    async def test_search_products_success(self, product_data_service, mock_local_product_service, mock_run_in_executor, caplog):
        """
        Test `search_products` method for a successful search.
        Ensures the underlying local service is called correctly and
        the expected products are returned.
        """
        expected_products = [{"id": "1", "name": "Test Laptop", "price": 1200}]
        mock_local_product_service.search_products.return_value = expected_products

        with caplog.at_level(logging.INFO):
            products = await product_data_service.search_products("laptop", 1)

            mock_local_product_service.search_products.assert_called_once_with("laptop", 1)
            mock_run_in_executor.assert_called_once()
            assert products == expected_products
            assert "Searching products with keyword: laptop" in caplog.text
            assert "Found 1 products for keyword: laptop" in caplog.text

    @pytest.mark.asyncio
    async def test_search_products_error(self, product_data_service, mock_local_product_service, mock_run_in_executor, caplog):
        """
        Test `search_products` method when an error occurs in the underlying service.
        Verifies that an empty list is returned and an error is logged.
        """
        mock_local_product_service.search_products.side_effect = Exception("Service search failed")

        with caplog.at_level(logging.ERROR):
            products = await product_data_service.search_products("error_query", 5)

            mock_local_product_service.search_products.assert_called_once_with("error_query", 5)
            assert products == []
            assert "Error searching products: Service search failed" in caplog.text

    @pytest.mark.asyncio
    async def test_get_products_with_search(self, product_data_service, mock_local_product_service):
        """
        Test `get_products` when a 'search' keyword is provided.
        Ensures it correctly delegates to `search_products`.
        """
        expected_products = [{"id": "s1", "name": "Searched Item"}]
        mock_local_product_service.search_products.return_value = expected_products
        
        products = await product_data_service.get_products(search="query", limit=5)
        
        mock_local_product_service.search_products.assert_called_once_with("query", 5)
        assert products == expected_products

    @pytest.mark.asyncio
    async def test_get_products_with_category(self, product_data_service, mock_local_product_service):
        """
        Test `get_products` when a 'category' is provided (and no 'search').
        Ensures it correctly delegates to `get_products_by_category`.
        """
        expected_products = [{"id": "c1", "name": "Category Item"}]
        mock_local_product_service.get_products_by_category.return_value = expected_products
        
        products = await product_data_service.get_products(category="electronics", limit=10)
        
        mock_local_product_service.get_products_by_category.assert_called_once_with("electronics")
        mock_local_product_service.get_products_by_category.return_value = expected_products[:10] # ProductDataService implicitly limits
        assert products == expected_products # My mock returns the full list, service applies [:limit] inside get_products_by_category logic.

    @pytest.mark.asyncio
    async def test_get_products_all_products_fallback(self, product_data_service, mock_local_product_service):
        """
        Test `get_products` when neither 'search' nor 'category' is provided.
        Ensures it correctly delegates to `get_all_products`.
        """
        expected_products = [{"id": "a1", "name": "All Product"}]
        mock_local_product_service.get_products.return_value = expected_products # This is for get_all_products, not the fallback
        
        products = await product_data_service.get_products(limit=15)
        
        mock_local_product_service.get_products.assert_called_once_with(15) # This is called by get_all_products
        assert products == expected_products

    @pytest.mark.asyncio
    async def test_get_products_empty_search_or_category_calls_all_products(self, product_data_service, mock_local_product_service):
        """
        Test `get_products` with empty string for search or category,
        which should fall back to `get_all_products`.
        """
        mock_local_product_service.get_products.return_value = [{"id": "all_fallback"}]
        
        # Test empty string for search
        products_s = await product_data_service.get_products(search="", limit=5)
        mock_local_product_service.search_products.assert_not_called()
        mock_local_product_service.get_products.assert_called_once_with(5)
        assert products_s == [{"id": "all_fallback"}]
        
        mock_local_product_service.get_products.reset_mock() # Reset mock call count

        # Test empty string for category
        products_c = await product_data_service.get_products(category="", limit=5)
        mock_local_product_service.get_products_by_category.assert_not_called()
        mock_local_product_service.get_products.assert_called_once_with(5)
        assert products_c == [{"id": "all_fallback"}]

    @pytest.mark.asyncio
    async def test_get_products_error_fallback(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_products` error handling. If an internal call (e.g., search_products)
        raises an exception, it should log and fallback to `local_service.get_products`.
        """
        # Mocking an internal method to raise an error
        # We need to temporarily replace the _actual_ method on the service instance
        # to simulate an error _within_ the service's logic, not from the mock_local_product_service
        original_search_products = product_data_service.search_products
        product_data_service.search_products = AsyncMock(side_effect=Exception("Simulated internal error"))

        mock_local_product_service.get_products.return_value = [{"id": "fallback_product"}]

        with caplog.at_level(logging.ERROR):
            products = await product_data_service.get_products(search="error_trigger", limit=7)

            product_data_service.search_products.assert_called_once_with("error_trigger", 7)
            mock_local_product_service.get_products.assert_called_once_with(7) # Fallback call
            assert products == [{"id": "fallback_product"}]
            assert "Error getting products: Simulated internal error" in caplog.text
        
        product_data_service.search_products = original_search_products # Restore original

    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service, mock_local_product_service):
        """
        Test `get_categories` method success case.
        """
        mock_local_product_service.get_categories.return_value = ["Electronics", "Books"]
        categories = await product_data_service.get_categories()
        mock_local_product_service.get_categories.assert_called_once()
        assert categories == ["Electronics", "Books"]

    @pytest.mark.asyncio
    async def test_get_categories_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_categories` method error case.
        """
        mock_local_product_service.get_categories.side_effect = Exception("Category fetch error")
        with caplog.at_level(logging.ERROR):
            categories = await product_data_service.get_categories()
            mock_local_product_service.get_categories.assert_called_once()
            assert categories == []
            assert "Error getting categories: Category fetch error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service, mock_local_product_service):
        """
        Test `get_top_rated_products` method success case.
        """
        expected_products = [{"id": "tr1", "rating": 5.0}]
        mock_local_product_service.get_top_rated_products.return_value = expected_products
        products = await product_data_service.get_top_rated_products(limit=3)
        mock_local_product_service.get_top_rated_products.assert_called_once_with(3)
        assert products == expected_products

    @pytest.mark.asyncio
    async def test_get_top_rated_products_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_top_rated_products` method error case.
        """
        mock_local_product_service.get_top_rated_products.side_effect = Exception("Top rated error")
        with caplog.at_level(logging.ERROR):
            products = await product_data_service.get_top_rated_products(limit=3)
            mock_local_product_service.get_top_rated_products.assert_called_once_with(3)
            assert products == []
            assert "Error getting top rated products: Top rated error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service, mock_local_product_service):
        """
        Test `get_best_selling_products` method success case.
        """
        expected_products = [{"id": "bs1", "sales": 1000}]
        mock_local_product_service.get_best_selling_products.return_value = expected_products
        products = await product_data_service.get_best_selling_products(limit=3)
        mock_local_product_service.get_best_selling_products.assert_called_once_with(3)
        assert products == expected_products

    @pytest.mark.asyncio
    async def test_get_best_selling_products_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_best_selling_products` method error case.
        """
        mock_local_product_service.get_best_selling_products.side_effect = Exception("Best selling error")
        with caplog.at_level(logging.ERROR):
            products = await product_data_service.get_best_selling_products(limit=3)
            mock_local_product_service.get_best_selling_products.assert_called_once_with(3)
            assert products == []
            assert "Error getting best selling products: Best selling error" in caplog.text

    def test_get_products_by_category_success(self, product_data_service, mock_local_product_service):
        """
        Test `get_products_by_category` method success case, ensuring limit is applied.
        """
        mock_products_from_service = [
            {"id": "cat_1"}, {"id": "cat_2"}, {"id": "cat_3"}, {"id": "cat_4"}
        ]
        mock_local_product_service.get_products_by_category.return_value = mock_products_from_service
        
        products = product_data_service.get_products_by_category("electronics", 2)
        
        mock_local_product_service.get_products_by_category.assert_called_once_with("electronics")
        assert products == [{"id": "cat_1"}, {"id": "cat_2"}] # Service applies [:limit]
        assert len(products) == 2

    def test_get_products_by_category_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_products_by_category` method error case.
        """
        mock_local_product_service.get_products_by_category.side_effect = Exception("Category search error")
        with caplog.at_level(logging.ERROR):
            products = product_data_service.get_products_by_category("electronics", 2)
            mock_local_product_service.get_products_by_category.assert_called_once_with("electronics")
            assert products == []
            assert "Error getting products by category: Category search error" in caplog.text

    def test_get_all_products_success(self, product_data_service, mock_local_product_service):
        """
        Test `get_all_products` method success case.
        """
        expected_products = [{"id": "all_1"}, {"id": "all_2", "id": "all_3"}]
        mock_local_product_service.get_products.return_value = expected_products # No slicing here in ProductDataService
        
        products = product_data_service.get_all_products(limit=2)
        
        mock_local_product_service.get_products.assert_called_once_with(2)
        assert products == expected_products

    def test_get_all_products_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_all_products` method error case.
        """
        mock_local_product_service.get_products.side_effect = Exception("All products error")
        with caplog.at_level(logging.ERROR):
            products = product_data_service.get_all_products(limit=5)
            mock_local_product_service.get_products.assert_called_once_with(5)
            assert products == []
            assert "Error getting all products: All products error" in caplog.text

    def test_get_product_details_success(self, product_data_service, mock_local_product_service):
        """
        Test `get_product_details` method success case.
        """
        expected_product = {"id": "p1", "name": "Detail Product", "description": "Desc"}
        mock_local_product_service.get_product_details.return_value = expected_product
        product = product_data_service.get_product_details("p1")
        mock_local_product_service.get_product_details.assert_called_once_with("p1")
        assert product == expected_product

    def test_get_product_details_not_found(self, product_data_service, mock_local_product_service):
        """
        Test `get_product_details` method when product is not found (returns None).
        """
        mock_local_product_service.get_product_details.return_value = None
        product = product_data_service.get_product_details("non_existent_id")
        mock_local_product_service.get_product_details.assert_called_once_with("non_existent_id")
        assert product is None

    def test_get_product_details_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_product_details` method error case.
        """
        mock_local_product_service.get_product_details.side_effect = Exception("Details fetch error")
        with caplog.at_level(logging.ERROR):
            product = product_data_service.get_product_details("error_id")
            mock_local_product_service.get_product_details.assert_called_once_with("error_id")
            assert product is None
            assert "Error getting product details: Details fetch error" in caplog.text

    def test_get_brands_success(self, product_data_service, mock_local_product_service):
        """
        Test `get_brands` method success case.
        """
        expected_brands = ["BrandX", "BrandY"]
        mock_local_product_service.get_brands.return_value = expected_brands
        brands = product_data_service.get_brands()
        mock_local_product_service.get_brands.assert_called_once()
        assert brands == expected_brands

    def test_get_brands_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_brands` method error case.
        """
        mock_local_product_service.get_brands.side_effect = Exception("Brands fetch error")
        with caplog.at_level(logging.ERROR):
            brands = product_data_service.get_brands()
            mock_local_product_service.get_brands.assert_called_once()
            assert brands == []
            assert "Error getting brands: Brands fetch error" in caplog.text

    def test_get_products_by_brand_success(self, product_data_service, mock_local_product_service):
        """
        Test `get_products_by_brand` method success case, ensuring limit is applied.
        """
        mock_products_from_service = [
            {"id": "brand_1"}, {"id": "brand_2"}, {"id": "brand_3"}, {"id": "brand_4"}
        ]
        mock_local_product_service.get_products_by_brand.return_value = mock_products_from_service
        
        products = product_data_service.get_products_by_brand("Adidas", 2)
        
        mock_local_product_service.get_products_by_brand.assert_called_once_with("Adidas")
        assert products == [{"id": "brand_1"}, {"id": "brand_2"}] # Service applies [:limit]
        assert len(products) == 2

    def test_get_products_by_brand_error(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_products_by_brand` method error case.
        """
        mock_local_product_service.get_products_by_brand.side_effect = Exception("Brand search error")
        with caplog.at_level(logging.ERROR):
            products = product_data_service.get_products_by_brand("Adidas", 2)
            mock_local_product_service.get_products_by_brand.assert_called_once_with("Adidas")
            assert products == []
            assert "Error getting products by brand: Brand search error" in caplog.text

    @pytest.mark.asyncio
    async def test_smart_search_products_success(self, product_data_service, mock_local_product_service, mock_run_in_executor):
        """
        Test `smart_search_products` method success case.
        """
        expected_products = [{"id": "ss1", "name": "Smart Gadget"}]
        expected_message = "Search completed successfully."
        mock_local_product_service.smart_search_products.return_value = (expected_products, expected_message)

        products, message = await product_data_service.smart_search_products(
            keyword="gadget", category="tech", max_price=500, limit=1
        )

        mock_local_product_service.smart_search_products.assert_called_once_with(
            "gadget", "tech", 500, 1
        )
        mock_run_in_executor.assert_called_once()
        assert products == expected_products
        assert message == expected_message

    @pytest.mark.asyncio
    async def test_smart_search_products_error_propagation(self, product_data_service, mock_local_product_service, mock_run_in_executor):
        """
        Test `smart_search_products` method when an error occurs.
        Since the method itself does not handle exceptions, the error should propagate.
        """
        mock_local_product_service.smart_search_products.side_effect = RuntimeError("Smart search service failed")

        with pytest.raises(RuntimeError, match="Smart search service failed"):
            await product_data_service.smart_search_products(keyword="faulty")
        
        mock_local_product_service.smart_search_products.assert_called_once_with(
            "faulty", None, None, 5 # default values
        )
        mock_run_in_executor.assert_called_once()