import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# No need to import LocalProductService directly here, as it's mocked via its import path
# from app.services.local_product_service import LocalProductService
from app.services.product_data_service import ProductDataService


# Mock data to be returned by the mocked LocalProductService methods
MOCK_PRODUCTS = [
    {"id": "1", "name": "Laptop Pro", "category": "Electronics", "price": 1200, "rating": 4.5, "brand": "TechCorp"},
    {"id": "2", "name": "Mechanical Keyboard", "category": "Electronics", "price": 75, "rating": 4.0, "brand": "GadgetCo"},
    {"id": "3", "name": "Ergonomic Mouse", "category": "Electronics", "price": 25, "rating": 3.8, "brand": "GadgetCo"},
    {"id": "4", "name": "Summer T-Shirt", "category": "Apparel", "price": 20, "rating": 4.2, "brand": "Fashionista"},
    {"id": "5", "name": "Slim Fit Jeans", "category": "Apparel", "price": 50, "rating": 4.7, "brand": "Fashionista"},
    {"id": "6", "name": "Gaming PC", "category": "Electronics", "price": 2500, "rating": 4.9, "brand": "TechCorp"},
]

MOCK_CATEGORIES = ["Electronics", "Apparel", "HomeGoods"]
MOCK_BRANDS = ["TechCorp", "GadgetCo", "Fashionista", "HomeComfort"]

@pytest.fixture
def mock_local_product_service_class():
    """
    Fixture to mock the LocalProductService class.
    It patches the class itself, allowing us to inspect its instantiation and control
    the methods of its mock instance.
    """
    with patch('app.services.product_data_service.LocalProductService') as MockLocalService:
        # This is the mock instance that LocalProductService() will return
        mock_instance = MockLocalService.return_value
        
        # Configure return values for all methods called by ProductDataService
        mock_instance.search_products.return_value = MOCK_PRODUCTS
        mock_instance.get_products.return_value = MOCK_PRODUCTS # Used by get_all_products and get_products fallback
        mock_instance.get_categories.return_value = MOCK_CATEGORIES
        # Simulate top-rated/best-selling by taking a sorted subset of MOCK_PRODUCTS
        mock_instance.get_top_rated_products.return_value = sorted(MOCK_PRODUCTS, key=lambda p: p['rating'], reverse=True)[:2] 
        mock_instance.get_best_selling_products.return_value = sorted(MOCK_PRODUCTS, key=lambda p: p['price'], reverse=True)[:2] 
        
        # Return all electronics for category calls, so ProductDataService can apply limit if needed
        mock_instance.get_products_by_category.return_value = [p for p in MOCK_PRODUCTS if p["category"] == "Electronics"]
        
        # Configure get_product_details to simulate lookup by ID
        mock_instance.get_product_details.side_effect = lambda product_id: next((p for p in MOCK_PRODUCTS if p["id"] == product_id), None)
        mock_instance.get_brands.return_value = MOCK_BRANDS
        
        # Return all GadgetCo products for brand calls, so ProductDataService can apply limit if needed
        mock_instance.get_products_by_brand.return_value = [p for p in MOCK_PRODUCTS if p["brand"] == "GadgetCo"]
        
        # smart_search_products returns a tuple of (products, message)
        mock_instance.smart_search_products.return_value = (MOCK_PRODUCTS[:2], "Smart search completed with some results.")
        
        yield MockLocalService # Yield the mock class to check its instantiation

@pytest.fixture
def product_data_service(mock_local_product_service_class):
    """
    Fixture to provide a ProductDataService instance for each test.
    This also ensures the LocalProductService mock is set up before the ProductDataService is initialized.
    """
    service = ProductDataService()
    return service

@pytest.mark.asyncio # Marks all tests in this class to be run with pytest-asyncio
class TestProductDataService:

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mock_local_product_service_class, product_data_service):
        """
        Autouse fixture to get references to the mock class and its instance.
        `product_data_service` fixture ensures `ProductDataService` is initialized
        and thus `LocalProductService()` is called, populating `mock_local_product_service_class.return_value`.
        """
        self.mock_local_product_service_class = mock_local_product_service_class
        self.mock_local_service_instance = mock_local_product_service_class.return_value
        self.service = product_data_service # Store the service instance for convenience

    async def test_init(self):
        """
        Test ProductDataService initialization.
        Ensures LocalProductService is instantiated and assigned correctly, and logs info.
        """
        # Check if LocalProductService class was instantiated exactly once
        self.mock_local_product_service_class.assert_called_once()
        # Check if the `local_service` attribute of ProductDataService points to our mocked instance
        assert self.service.local_service is self.mock_local_service_instance
        # Optionally check info log for initialization
        with patch('app.services.product_data_service.logger.info') as mock_logger_info:
             # Re-initialize to trigger init logic and logger call for this specific test
             # We create a new instance to cleanly test the __init__ behavior
             _ = ProductDataService()
             mock_logger_info.assert_called_once_with("ProductDataService initialized with LocalProductService")


    @patch('asyncio.get_event_loop')
    async def test_search_products_success(self, mock_get_event_loop):
        """
        Test `search_products` method for a successful search.
        Mocks `asyncio.get_event_loop().run_in_executor` to return predefined products
        and verifies logging.
        """
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop
        # Configure run_in_executor to return a Future that resolves with products
        future = asyncio.Future()
        future.set_result(MOCK_PRODUCTS[:2]) # Simulate finding 2 products
        mock_loop.run_in_executor.return_value = future

        keyword = "laptop"
        limit = 2
        
        with patch('app.services.product_data_service.logger.info') as mock_logger_info:
            products = await self.service.search_products(keyword, limit)

            assert products == MOCK_PRODUCTS[:2]
            mock_get_event_loop.assert_called_once()
            # Verify run_in_executor was called with the correct arguments
            mock_loop.run_in_executor.assert_called_once_with(
                None, self.mock_local_service_instance.search_products, keyword, limit
            )
            # Ensure the underlying local_service.search_products was NOT called directly (it's called by executor)
            self.mock_local_service_instance.search_products.assert_not_called()
            # Verify log messages
            mock_logger_info.assert_any_call(f"Searching products with keyword: {keyword}")
            mock_logger_info.assert_any_call(f"Found {len(MOCK_PRODUCTS[:2])} products for keyword: {keyword}")


    @patch('asyncio.get_event_loop')
    async def test_search_products_no_results(self, mock_get_event_loop):
        """
        Test `search_products` when no matching products are found.
        Ensures an empty list is returned and verifies logging.
        """
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop
        future = asyncio.Future()
        future.set_result([]) # Simulate no results
        mock_loop.run_in_executor.return_value = future

        keyword = "nonexistent"
        with patch('app.services.product_data_service.logger.info') as mock_logger_info:
            products = await self.service.search_products(keyword)

            assert products == []
            mock_loop.run_in_executor.assert_called_once()
            mock_logger_info.assert_any_call(f"Searching products with keyword: {keyword}")
            mock_logger_info.assert_any_call(f"Found 0 products for keyword: {keyword}")

    @patch('asyncio.get_event_loop')
    async def test_search_products_error(self, mock_get_event_loop):
        """
        Test `search_products` when an exception occurs during the search operation.
        Ensures an empty list is returned and the error is logged.
        """
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop
        
        # Simulate an exception from run_in_executor
        mock_loop.run_in_executor.side_effect = Exception("Simulated search error")

        # Capture log output to verify error logging
        with patch('app.services.product_data_service.logger.error') as mock_logger_error:
            keyword = "error_test"
            products = await self.service.search_products(keyword)

            assert products == []
            mock_loop.run_in_executor.assert_called_once()
            # Verify the error message logged
            mock_logger_error.assert_called_once_with(f"Error searching products: Simulated search error")

    async def test_get_products_with_search(self):
        """
        Test `get_products` when a search keyword is provided.
        It should delegate to `search_products` with the correct arguments.
        """
        # Temporarily replace the actual search_products method with an AsyncMock
        original_search_products = self.service.search_products
        self.service.search_products = AsyncMock(return_value=MOCK_PRODUCTS[:1]) # Simulate 1 product found
        
        search_keyword = "query"
        limit = 5 # Custom limit
        products = await self.service.get_products(limit=limit, search=search_keyword)

        assert products == MOCK_PRODUCTS[:1]
        self.service.search_products.assert_called_once_with(search_keyword, limit)
        self.service.search_products = original_search_products # Restore original for other tests

    async def test_get_products_with_category(self):
        """
        Test `get_products` when a category is provided (and no search keyword).
        It should delegate to `get_products_by_category` with the correct arguments.
        """
        # Temporarily replace the actual get_products_by_category method with a MagicMock
        original_get_products_by_category = self.service.get_products_by_category
        mock_category_products = [p for p in MOCK_PRODUCTS if p["category"] == "Apparel"]
        self.service.get_products_by_category = MagicMock(return_value=mock_category_products)

        category = "Apparel"
        limit = 15 # Custom limit
        products = await self.service.get_products(limit=limit, category=category)

        assert products == mock_category_products
        self.service.get_products_by_category.assert_called_once_with(category, limit)
        self.service.get_products_by_category = original_get_products_by_category # Restore original

    async def test_get_products_no_filters(self):
        """
        Test `get_products` when no filters (search or category) are provided.
        It should delegate to `get_all_products` with the correct limit.
        """
        # Temporarily replace the actual get_all_products method with a MagicMock
        original_get_all_products = self.service.get_all_products
        self.service.get_all_products = MagicMock(return_value=MOCK_PRODUCTS[:3]) # Simulate 3 products
        
        limit = 10 # Default limit
        products = await self.service.get_products(limit=limit)

        assert products == MOCK_PRODUCTS[:3]
        self.service.get_all_products.assert_called_once_with(limit)
        self.service.get_all_products = original_get_all_products # Restore original

    async def test_get_products_error_fallback(self):
        """
        Test `get_products` error handling. If an internal delegated call fails, it should
        catch the exception, log it, and fall back to `local_service.get_products`.
        """
        # Temporarily make one of the internal delegation methods raise an exception
        # We'll mock `get_all_products` to simulate an error in the default path
        original_get_all_products = self.service.get_all_products
        self.service.get_all_products = MagicMock(side_effect=Exception("Simulated internal error in get_all_products"))

        with patch('app.services.product_data_service.logger.error') as mock_logger_error:
            limit_val = 25 # Custom limit
            products = await self.service.get_products(limit=limit_val)

            # Ensure the fallback to local_service.get_products was called with the correct limit
            self.mock_local_service_instance.get_products.assert_called_once_with(limit_val)
            # The returned products should be what the fallback `local_service.get_products` mock returns
            assert products == self.mock_local_service_instance.get_products.return_value 
            
            mock_logger_error.assert_called_once()
            assert "Error getting products: Simulated internal error in get_all_products" in mock_logger_error.call_args[0][0]
        
        self.service.get_all_products = original_get_all_products # Restore original

    async def test_get_categories_success(self):
        """Test `get_categories` with successful retrieval."""
        categories = await self.service.get_categories()
        assert categories == MOCK_CATEGORIES
        self.mock_local_service_instance.get_categories.assert_called_once()

    async def test_get_categories_error(self):
        """Test `get_categories` when an error occurs in the underlying service, ensuring empty list and log."""
        self.mock_local_service_instance.get_categories.side_effect = Exception("Category service unavailable")
        with patch('app.services.product_data_service.logger.error') as mock_logger_error:
            categories = await self.service.get_categories()
            assert categories == []
            mock_logger_error.assert_called_once_with("Error getting categories: Category service unavailable")

    async def test_get_top_rated_products_success(self):
        """Test `get_top_rated_products` with successful retrieval and correct limit applied."""
        limit_val = 5
        products = await self.service.get_top_rated_products(limit_val)
        # Asserts against the specific return value configured in the mock fixture
        assert products == sorted(MOCK_PRODUCTS, key=lambda p: p['rating'], reverse=True)[:2] 
        self.mock_local_service_instance.get_top_rated_products.assert_called_once_with(limit_val)

    async def test_get_top_rated_products_error(self):
        """Test `get_top_rated_products` when an error occurs, ensuring empty list and log."""
        self.mock_local_service_instance.get_top_rated_products.side_effect = Exception("Top rated service error")
        with patch('app.services.product_data_service.logger.error') as mock_logger_error:
            products = await self.service.get_top_rated_products()
            assert products == []
            mock_logger_error.assert_called_once_with("Error getting top rated products: Top rated service error")

    async def test_get_best_selling_products_success(self):
        """Test `get_best_selling_products` with successful retrieval and correct limit applied."""
        limit_val = 7
        products = await self.service.get_best_selling_products(limit_val)
        # Asserts against the specific return value configured in the mock fixture
        assert products == sorted(MOCK_PRODUCTS, key=lambda p: p['price'], reverse=True)[:2] 
        self.mock_local_service_instance.get_best_selling_products.assert_called_once_with(limit_val)

    async def test_get_best_selling_products_error(self):
        """Test `get_best_selling_products` when an error occurs, ensuring empty list and log."""
        self.mock_local_service_instance.get_best_selling_products.side_effect = Exception("Best selling service error")
        with patch('app.services.product_data_service.logger.error') as mock_logger_error:
            products = await self.service.get_best_selling_products()
            assert products == []
            mock_logger_error.assert_called_once_with("Error getting best selling products: Best selling service error")

    def test_get_products_by_category_success(self):
        """
        Test `get_products_by_category` with successful retrieval and correct application of limit.
        """
        category = "Electronics"
        limit = 2
        # Mock returns all 4 electronics products, so service should slice to 2
        self.mock_local_service_instance.get_products_by_category.return_value = [
            p for p in MOCK_PRODUCTS if p["category"] == category
        ]
        expected_products = self.mock_local_service_instance.get_products_by_category.return_value[:limit]
        
        products = self.service.get_products_by_category(category, limit)
        assert products == expected_products
        self.mock_local_service_instance.get_products_by_category.assert_called_once_with(category)

    def test_get_products_by_category_no_results(self):
        """Test `get_products_by_category` when no products match the category, ensuring empty list."""
        self.mock_local_service_instance.get_products_by_category.return_value = []
        products = self.service.get_products_by_category("NonExistentCategory")
        assert products == []
        self.mock_local_service_instance.get_products_by_category.assert_called_once_with("NonExistentCategory")

    def test_get_products_by_category_error(self):
        """Test `get_products_by_category` when an error occurs, ensuring empty list and log."""
        self.mock_local_service_instance.get_products_by_category.side_effect = Exception("Category filter error")
        with patch('app.services.product_data_service.logger.error') as mock_logger_error:
            products = self.service.get_products_by_category("Electronics")
            assert products == []
            mock_logger_error.assert_called_once_with("Error getting products by category: Category filter error")

    def test_get_all_products_success(self):
        """
        Test `get_all_products` with successful retrieval and correct application of limit.
        """
        limit_val = 3
        # Mock returns all products, so service should slice
        self.mock_local_service_instance.get_products.return_value = MOCK_PRODUCTS
        
        products = self.service.get_all_products(limit_val)
        assert products == MOCK_PRODUCTS[:limit_val]
        # Note: LocalProductService's get_products method, as called by this method,
        # does not receive a limit, but ProductDataService *then* applies its own limit slice on the result.
        # However, the source code shows get_products(limit) is passed directly to local_service.get_products(limit).
        # So the `assert_called_once_with(limit_val)` is correct.
        self.mock_local_service_instance.get_products.assert_called_once_with(limit_val) 

    def test_get_all_products_error(self):
        """Test `get_all_products` when an error occurs, ensuring empty list and log."""
        self.mock_local_service_instance.get_products.side_effect = Exception("All products service error")
        with patch('app.services.product_data_service.logger.error') as mock_logger_error:
            products = self.service.get_all_products()
            assert products == []
            mock_logger_error.assert_called_once_with("Error getting all products: All products service error")

    def test_get_product_details_success(self):
        """Test `get_product_details` with successful retrieval."""
        product_id = "1"
        expected_details = next((p for p in MOCK_PRODUCTS if p["id"] == product_id), None)
        product_details = self.service.get_product_details(product_id)
        assert product_details == expected_details
        self.mock_local_service_instance.get_product_details.assert_called_once_with(product_id)

    def test_get_product_details_not_found(self):
        """Test `get_product_details` when product with given ID is not found, ensuring None."""
        product_id = "nonexistent_id"
        # The side_effect lambda configured in the fixture will return None for this ID
        product_details = self.service.get_product_details(product_id)
        assert product_details is None
        self.mock_local_service_instance.get_product_details.assert_called_once_with(product_id)

    def test_get_product_details_error(self):
        """Test `get_product_details` when an error occurs, ensuring None and log."""
        self.mock_local_service_instance.get_product_details.side_effect = Exception("Details service error")
        with patch('app.services.product_data_service.logger.error') as mock_logger_error:
            product_details = self.service.get_product_details("123")
            assert product_details is None
            mock_logger_error.assert_called_once_with("Error getting product details: Details service error")

    def test_get_brands_success(self):
        """Test `get_brands` with successful retrieval."""
        brands = self.service.get_brands()
        assert brands == MOCK_BRANDS
        self.mock_local_service_instance.get_brands.assert_called_once()

    def test_get_brands_error(self):
        """Test `get_brands` when an error occurs, ensuring empty list and log."""
        self.mock_local_service_instance.get_brands.side_effect = Exception("Brands service error")
        with patch('app.services.product_data_service.logger.error') as mock_logger_error:
            brands = self.service.get_brands()
            assert brands == []
            mock_logger_error.assert_called_once_with("Error getting brands: Brands service error")

    def test_get_products_by_brand_success(self):
        """
        Test `get_products_by_brand` with successful retrieval and correct application of limit.
        """
        brand = "GadgetCo"
        limit = 1
        # Mock returns all 'GadgetCo' products, so service should slice to 1
        self.mock_local_service_instance.get_products_by_brand.return_value = [
            p for p in MOCK_PRODUCTS if p["brand"] == brand
        ]
        expected_products = self.mock_local_service_instance.get_products_by_brand.return_value[:limit]
        
        products = self.service.get_products_by_brand(brand, limit)
        assert products == expected_products
        self.mock_local_service_instance.get_products_by_brand.assert_called_once_with(brand)

    def test_get_products_by_brand_no_results(self):
        """Test `get_products_by_brand` when no products match the brand, ensuring empty list."""
        self.mock_local_service_instance.get_products_by_brand.return_value = []
        products = self.service.get_products_by_brand("NonExistentBrand")
        assert products == []
        self.mock_local_service_instance.get_products_by_brand.assert_called_once_with("NonExistentBrand")

    def test_get_products_by_brand_error(self):
        """Test `get_products_by_brand` when an error occurs, ensuring empty list and log."""
        self.mock_local_service_instance.get_products_by_brand.side_effect = Exception("Brand filter error")
        with patch('app.services.product_data_service.logger.error') as mock_logger_error:
            products = self.service.get_products_by_brand("GadgetCo")
            assert products == []
            mock_logger_error.assert_called_once_with("Error getting products by brand: Brand filter error")

    @patch('asyncio.get_event_loop')
    async def test_smart_search_products_success(self, mock_get_event_loop):
        """
        Test `smart_search_products` with successful execution.
        Mocks `asyncio.get_event_loop().run_in_executor` to return a tuple.
        """
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop
        
        expected_result = (MOCK_PRODUCTS[:1], "Smart search found one result.")
        future = asyncio.Future()
        future.set_result(expected_result)
        mock_loop.run_in_executor.return_value = future

        keyword = "smartwatch"
        category = "Electronics"
        max_price = 500
        limit = 1
        
        products, message = await self.service.smart_search_products(keyword, category, max_price, limit)

        assert products == expected_result[0]
        assert message == expected_result[1]
        mock_get_event_loop.assert_called_once()
        # Verify run_in_executor was called with the correct arguments
        mock_loop.run_in_executor.assert_called_once_with(
            None, self.mock_local_service_instance.smart_search_products, keyword, category, max_price, limit
        )
        self.mock_local_service_instance.smart_search_products.assert_not_called() # Confirms it was called via executor

    @patch('asyncio.get_event_loop')
    async def test_smart_search_products_error_propagation(self, mock_get_event_loop):
        """
        Test `smart_search_products` error handling.
        The original method does not have a try-except block, so exceptions should propagate.
        """
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop
        
        # Simulate an exception from run_in_executor
        mock_loop.run_in_executor.side_effect = Exception("Simulated smart search executor error")

        with pytest.raises(Exception) as excinfo:
            await self.service.smart_search_products("fail_test")
        
        assert "Simulated smart search executor error" in str(excinfo.value)
        mock_loop.run_in_executor.assert_called_once_with(
            None, self.mock_local_service_instance.smart_search_products, "fail_test", None, None, 5
        )