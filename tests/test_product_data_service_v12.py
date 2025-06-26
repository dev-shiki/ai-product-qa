import logging
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

# Import the service to be tested
from app.services.product_data_service import ProductDataService

# --- Dummy Data ---
MOCK_PRODUCT_1 = {"id": "1", "name": "Laptop Pro", "price": 1200, "category": "Electronics", "rating": 4.5, "brand": "BrandX"}
MOCK_PRODUCT_2 = {"id": "2", "name": "Mechanical Keyboard", "price": 150, "category": "Electronics", "rating": 4.8, "brand": "BrandY"}
MOCK_PRODUCT_3 = {"id": "3", "name": "Wireless Mouse", "price": 50, "category": "Electronics", "rating": 4.2, "brand": "BrandX"}
MOCK_PRODUCT_4 = {"id": "4", "name": "Office Chair", "price": 300, "category": "Furniture", "rating": 4.0, "brand": "BrandZ"}
MOCK_PRODUCT_5 = {"id": "5", "name": "Desk Lamp", "price": 75, "category": "Home Decor", "rating": 3.9, "brand": "BrandA"}
MOCK_PRODUCT_6 = {"id": "6", "name": "Monitor", "price": 400, "category": "Electronics", "rating": 4.1, "brand": "BrandX"}

MOCK_PRODUCTS = [MOCK_PRODUCT_1, MOCK_PRODUCT_2, MOCK_PRODUCT_3, MOCK_PRODUCT_4, MOCK_PRODUCT_5, MOCK_PRODUCT_6]
MOCK_CATEGORIES = ["Electronics", "Furniture", "Home Decor"]
MOCK_BRANDS = ["BrandX", "BrandY", "BrandZ", "BrandA"]

# --- Fixtures ---

@pytest.fixture
def mock_local_service(mocker):
    """
    Fixture to mock LocalProductService, which ProductDataService depends on.
    All methods are mocked with their default success returns.
    Individual tests can override these returns or set side_effects.
    """
    # Patch LocalProductService wherever it's imported in product_data_service module
    mock_service_instance = mocker.patch('app.services.product_data_service.LocalProductService', autospec=True).return_value
    
    # Configure default successful return values for all methods
    # For methods called via run_in_executor, the mock return value should be the actual data,
    # as run_in_executor handles the awaitable wrapper around the sync call.
    mock_service_instance.search_products.return_value = MOCK_PRODUCTS
    mock_service_instance.get_categories.return_value = MOCK_CATEGORIES
    mock_service_instance.get_top_rated_products.return_value = MOCK_PRODUCTS
    mock_service_instance.get_best_selling_products.return_value = MOCK_PRODUCTS
    mock_service_instance.get_products_by_category.return_value = MOCK_PRODUCTS
    mock_service_instance.get_products.return_value = MOCK_PRODUCTS # Used by get_all_products and get_products fallback
    mock_service_instance.get_product_details.return_value = MOCK_PRODUCT_1
    mock_service_instance.get_brands.return_value = MOCK_BRANDS
    mock_service_instance.get_products_by_brand.return_value = MOCK_PRODUCTS
    mock_service_instance.smart_search_products.return_value = (MOCK_PRODUCTS, "Smart search completed.")

    return mock_service_instance

@pytest.fixture
def product_data_service(mock_local_service):
    """Fixture to provide an instance of ProductDataService with a mocked LocalProductService."""
    return ProductDataService()

@pytest.fixture(autouse=True)
def cap_log(mocker):
    """Fixture to capture log messages and prevent them from appearing during tests."""
    # Capture the logger used in ProductDataService
    mock_logger = mocker.patch('app.services.product_data_service.logger')
    return mock_logger

# --- Tests ---

class TestProductDataService:

    @pytest.mark.asyncio
    async def test_init(self, mock_local_service, cap_log):
        """Test ProductDataService initialization."""
        # ProductDataService initializes LocalProductService in its __init__
        service = ProductDataService()
        
        # Verify that LocalProductService was instantiated
        mock_local_service.assert_called_once() 
        # Ensure the `local_service` attribute is indeed the mocked instance
        assert isinstance(service.local_service, Mock) 
        # Verify that an info log message was emitted
        cap_log.info.assert_called_once_with("ProductDataService initialized with LocalProductService")

    @pytest.mark.asyncio
    async def test_search_products_success(self, product_data_service, mock_local_service, cap_log):
        """Test search_products with successful results."""
        keyword = "laptop"
        limit = 2
        # Configure mock to return specific limited products
        mock_local_service.search_products.return_value = MOCK_PRODUCTS[:limit]
        
        products = await product_data_service.search_products(keyword, limit)
        
        # Assert the underlying local service method was called correctly
        mock_local_service.search_products.assert_called_once_with(keyword, limit)
        # Assert the correct products are returned
        assert products == MOCK_PRODUCTS[:limit]
        # Assert logging calls
        cap_log.info.assert_any_call(f"Searching products with keyword: {keyword}")
        cap_log.info.assert_any_call(f"Found {len(products)} products for keyword: {keyword}")
        cap_log.error.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_products_no_results(self, product_data_service, mock_local_service, cap_log):
        """Test search_products when no results are found."""
        keyword = "xyz"
        mock_local_service.search_products.return_value = []
        
        products = await product_data_service.search_products(keyword)
        
        mock_local_service.search_products.assert_called_once_with(keyword, 10) # default limit
        assert products == []
        cap_log.info.assert_any_call(f"Searching products with keyword: {keyword}")
        cap_log.info.assert_any_call(f"Found 0 products for keyword: {keyword}")
        cap_log.error.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_products_error(self, product_data_service, mock_local_service, cap_log):
        """Test search_products when an error occurs."""
        keyword = "error"
        mock_local_service.search_products.side_effect = Exception("Network error")
        
        products = await product_data_service.search_products(keyword)
        
        mock_local_service.search_products.assert_called_once_with(keyword, 10)
        assert products == []
        cap_log.error.assert_called_once_with("Error searching products: Network error")
        cap_log.info.assert_called_once() # Only the initial info message before error

    @pytest.mark.asyncio
    async def test_get_products_with_search(self, product_data_service, mocker, mock_local_service):
        """Test get_products when search keyword is provided, verifying it calls search_products."""
        # Patch the internal search_products call of product_data_service to control its behavior
        mock_search_products = mocker.patch.object(product_data_service, 'search_products', new_callable=AsyncMock, return_value=MOCK_PRODUCTS[:1])
        
        products = await product_data_service.get_products(search="keyboard", limit=1)
        
        mock_search_products.assert_called_once_with("keyboard", 1)
        # Ensure that fallback or other branches were not called
        mock_local_service.get_products.assert_not_called() 
        product_data_service.get_products_by_category.assert_not_called()
        product_data_service.get_all_products.assert_not_called()
        assert products == MOCK_PRODUCTS[:1]

    @pytest.mark.asyncio
    async def test_get_products_with_category(self, product_data_service, mocker, mock_local_service):
        """Test get_products when category is provided, verifying it calls get_products_by_category."""
        # Patch the internal get_products_by_category call of product_data_service
        mock_get_products_by_category = mocker.patch.object(product_data_service, 'get_products_by_category', return_value=MOCK_PRODUCTS[:2])

        products = await product_data_service.get_products(category="Electronics", limit=2)

        mock_get_products_by_category.assert_called_once_with("Electronics", 2)
        # Ensure that fallback or other branches were not called
        mock_local_service.get_products.assert_not_called()
        product_data_service.search_products.assert_not_called()
        product_data_service.get_all_products.assert_not_called()
        assert products == MOCK_PRODUCTS[:2]

    @pytest.mark.asyncio
    async def test_get_products_default(self, product_data_service, mocker, mock_local_service):
        """Test get_products with no search/category, verifying it calls get_all_products."""
        # Patch the internal get_all_products call of product_data_service
        mock_get_all_products = mocker.patch.object(product_data_service, 'get_all_products', return_value=MOCK_PRODUCTS[:3])
        
        products = await product_data_service.get_products(limit=3)
        
        mock_get_all_products.assert_called_once_with(3)
        # Ensure that fallback or other branches were not called
        mock_local_service.get_products.assert_not_called()
        product_data_service.search_products.assert_not_called()
        product_data_service.get_products_by_category.assert_not_called()
        assert products == MOCK_PRODUCTS[:3]

    @pytest.mark.asyncio
    async def test_get_products_error_fallback(self, product_data_service, mocker, mock_local_service, cap_log):
        """Test get_products error handling and fallback to local_service.get_products."""
        # Simulate an error in one of the internal calls (e.g., search_products)
        mocker.patch.object(product_data_service, 'search_products', new_callable=AsyncMock, side_effect=Exception("Search failed"))
        # Ensure other internal calls are not made
        mocker.patch.object(product_data_service, 'get_products_by_category', return_value=[])
        mocker.patch.object(product_data_service, 'get_all_products', return_value=[])
        
        # Configure fallback return from mock_local_service
        mock_local_service.get_products.return_value = MOCK_PRODUCTS[:1] 
        
        products = await product_data_service.get_products(search="failed", limit=1)
        
        product_data_service.search_products.assert_called_once() # The failing method was called
        # Assert the fallback method on local_service was called
        mock_local_service.get_products.assert_called_once_with(1) 
        cap_log.error.assert_called_once_with("Error getting products: Search failed")
        assert products == MOCK_PRODUCTS[:1] # Products returned from fallback

    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service, mock_local_service, cap_log):
        """Test get_categories with successful results."""
        mock_local_service.get_categories.return_value = MOCK_CATEGORIES
        
        categories = await product_data_service.get_categories()
        
        mock_local_service.get_categories.assert_called_once()
        assert categories == MOCK_CATEGORIES
        cap_log.error.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_categories_error(self, product_data_service, mock_local_service, cap_log):
        """Test get_categories when an error occurs."""
        mock_local_service.get_categories.side_effect = Exception("Category DB down")
        
        categories = await product_data_service.get_categories()
        
        mock_local_service.get_categories.assert_called_once()
        assert categories == []
        cap_log.error.assert_called_once_with("Error getting categories: Category DB down")

    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service, mock_local_service, cap_log):
        """Test get_top_rated_products with successful results."""
        mock_local_service.get_top_rated_products.return_value = MOCK_PRODUCTS[:2]
        
        products = await product_data_service.get_top_rated_products(limit=2)
        
        mock_local_service.get_top_rated_products.assert_called_once_with(2)
        assert products == MOCK_PRODUCTS[:2]
        cap_log.error.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_top_rated_products_error(self, product_data_service, mock_local_service, cap_log):
        """Test get_top_rated_products when an error occurs."""
        mock_local_service.get_top_rated_products.side_effect = Exception("Rating service error")
        
        products = await product_data_service.get_top_rated_products()
        
        mock_local_service.get_top_rated_products.assert_called_once_with(10) # default limit
        assert products == []
        cap_log.error.assert_called_once_with("Error getting top rated products: Rating service error")

    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service, mock_local_service, cap_log):
        """Test get_best_selling_products with successful results."""
        mock_local_service.get_best_selling_products.return_value = MOCK_PRODUCTS[:3]
        
        products = await product_data_service.get_best_selling_products(limit=3)
        
        mock_local_service.get_best_selling_products.assert_called_once_with(3)
        assert products == MOCK_PRODUCTS[:3]
        cap_log.error.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_best_selling_products_error(self, product_data_service, mock_local_service, cap_log):
        """Test get_best_selling_products when an error occurs."""
        mock_local_service.get_best_selling_products.side_effect = Exception("Sales data error")
        
        products = await product_data_service.get_best_selling_products()
        
        mock_local_service.get_best_selling_products.assert_called_once_with(10)
        assert products == []
        cap_log.error.assert_called_once_with("Error getting best selling products: Sales data error")

    def test_get_products_by_category_success_with_limit(self, product_data_service, mock_local_service, cap_log):
        """Test get_products_by_category with successful results and limit applied."""
        # Mock the underlying service to return more products than the test limit
        mock_local_service.get_products_by_category.return_value = [MOCK_PRODUCT_1, MOCK_PRODUCT_2, MOCK_PRODUCT_3]
        
        products = product_data_service.get_products_by_category("Electronics", limit=2)
        
        # The mock is called without the limit, as slicing happens in ProductDataService
        mock_local_service.get_products_by_category.assert_called_once_with("Electronics")
        assert products == [MOCK_PRODUCT_1, MOCK_PRODUCT_2] # Slicing applied
        cap_log.error.assert_not_called()

    def test_get_products_by_category_limit_exceeds_available(self, product_data_service, mock_local_service):
        """Test get_products_by_category when limit exceeds available products."""
        mock_local_service.get_products_by_category.return_value = [MOCK_PRODUCT_1, MOCK_PRODUCT_2]
        
        products = product_data_service.get_products_by_category("Electronics", limit=5)
        
        assert products == [MOCK_PRODUCT_1, MOCK_PRODUCT_2] # All available products returned

    def test_get_products_by_category_no_results(self, product_data_service, mock_local_service):
        """Test get_products_by_category when no products are found."""
        mock_local_service.get_products_by_category.return_value = []
        
        products = product_data_service.get_products_by_category("NonExistentCategory")
        
        assert products == []

    def test_get_products_by_category_error(self, product_data_service, mock_local_service, cap_log):
        """Test get_products_by_category when an error occurs."""
        mock_local_service.get_products_by_category.side_effect = Exception("DB error")
        
        products = product_data_service.get_products_by_category("Electronics")
        
        mock_local_service.get_products_by_category.assert_called_once_with("Electronics")
        assert products == []
        cap_log.error.assert_called_once_with("Error getting products by category: DB error")

    def test_get_all_products_success(self, product_data_service, mock_local_service, cap_log):
        """Test get_all_products with successful results."""
        mock_local_service.get_products.return_value = MOCK_PRODUCTS # Mock returns full list
        
        products = product_data_service.get_all_products(limit=5)
        
        # The limit is passed directly to local_service.get_products
        mock_local_service.get_products.assert_called_once_with(5)
        assert products == MOCK_PRODUCTS # The returned list from mock matches the expectation, assuming mock adheres to limit
        cap_log.error.assert_not_called()

    def test_get_all_products_error(self, product_data_service, mock_local_service, cap_log):
        """Test get_all_products when an error occurs."""
        mock_local_service.get_products.side_effect = Exception("All products error")
        
        products = product_data_service.get_all_products()
        
        mock_local_service.get_products.assert_called_once_with(20) # default limit
        assert products == []
        cap_log.error.assert_called_once_with("Error getting all products: All products error")

    def test_get_product_details_success(self, product_data_service, mock_local_service, cap_log):
        """Test get_product_details with successful result."""
        mock_local_service.get_product_details.return_value = MOCK_PRODUCT_1
        
        product = product_data_service.get_product_details("1")
        
        mock_local_service.get_product_details.assert_called_once_with("1")
        assert product == MOCK_PRODUCT_1
        cap_log.error.assert_not_called()

    def test_get_product_details_not_found(self, product_data_service, mock_local_service, cap_log):
        """Test get_product_details when product is not found."""
        mock_local_service.get_product_details.return_value = None
        
        product = product_data_service.get_product_details("999")
        
        mock_local_service.get_product_details.assert_called_once_with("999")
        assert product is None
        cap_log.error.assert_not_called()

    def test_get_product_details_error(self, product_data_service, mock_local_service, cap_log):
        """Test get_product_details when an error occurs."""
        mock_local_service.get_product_details.side_effect = Exception("Detail fetch error")
        
        product = product_data_service.get_product_details("1")
        
        mock_local_service.get_product_details.assert_called_once_with("1")
        assert product is None
        cap_log.error.assert_called_once_with("Error getting product details: Detail fetch error")

    def test_get_brands_success(self, product_data_service, mock_local_service, cap_log):
        """Test get_brands with successful results."""
        mock_local_service.get_brands.return_value = MOCK_BRANDS
        
        brands = product_data_service.get_brands()
        
        mock_local_service.get_brands.assert_called_once()
        assert brands == MOCK_BRANDS
        cap_log.error.assert_not_called()

    def test_get_brands_error(self, product_data_service, mock_local_service, cap_log):
        """Test get_brands when an error occurs."""
        mock_local_service.get_brands.side_effect = Exception("Brand service error")
        
        brands = product_data_service.get_brands()
        
        mock_local_service.get_brands.assert_called_once()
        assert brands == []
        cap_log.error.assert_called_once_with("Error getting brands: Brand service error")

    def test_get_products_by_brand_success_with_limit(self, product_data_service, mock_local_service, cap_log):
        """Test get_products_by_brand with successful results and limit applied."""
        # Mock the underlying service to return more products than the test limit
        mock_local_service.get_products_by_brand.return_value = [MOCK_PRODUCT_1, MOCK_PRODUCT_3, MOCK_PRODUCT_6] # All BrandX products
        
        products = product_data_service.get_products_by_brand("BrandX", limit=2)
        
        # The mock is called without the limit, as slicing happens in ProductDataService
        mock_local_service.get_products_by_brand.assert_called_once_with("BrandX")
        assert products == [MOCK_PRODUCT_1, MOCK_PRODUCT_3] # Slicing applied
        cap_log.error.assert_not_called()

    def test_get_products_by_brand_limit_exceeds_available(self, product_data_service, mock_local_service):
        """Test get_products_by_brand when limit exceeds available products."""
        mock_local_service.get_products_by_brand.return_value = [MOCK_PRODUCT_1, MOCK_PRODUCT_3]
        
        products = product_data_service.get_products_by_brand("BrandX", limit=5)
        
        assert products == [MOCK_PRODUCT_1, MOCK_PRODUCT_3] # All available products returned

    def test_get_products_by_brand_no_results(self, product_data_service, mock_local_service):
        """Test get_products_by_brand when no products are found for the brand."""
        mock_local_service.get_products_by_brand.return_value = []
        
        products = product_data_service.get_products_by_brand("NonExistentBrand")
        
        assert products == []

    def test_get_products_by_brand_error(self, product_data_service, mock_local_service, cap_log):
        """Test get_products_by_brand when an error occurs."""
        mock_local_service.get_products_by_brand.side_effect = Exception("Brand DB error")
        
        products = product_data_service.get_products_by_brand("BrandX")
        
        mock_local_service.get_products_by_brand.assert_called_once_with("BrandX")
        assert products == []
        cap_log.error.assert_called_once_with("Error getting products by brand: Brand DB error")

    @pytest.mark.asyncio
    async def test_smart_search_products_success_with_all_args(self, product_data_service, mock_local_service):
        """Test smart_search_products with all arguments provided and success."""
        expected_products = MOCK_PRODUCTS[:1]
        expected_message = "Found 1 product matching criteria."
        mock_local_service.smart_search_products.return_value = (expected_products, expected_message)

        keyword = "laptop"
        category = "Electronics"
        max_price = 1500
        limit = 5

        products, message = await product_data_service.smart_search_products(
            keyword=keyword, category=category, max_price=max_price, limit=limit
        )
        
        mock_local_service.smart_search_products.assert_called_once_with(
            keyword, category, max_price, limit
        )
        assert products == expected_products
        assert message == expected_message

    @pytest.mark.asyncio
    async def test_smart_search_products_no_args_success(self, product_data_service, mock_local_service):
        """Test smart_search_products with no arguments (default values)."""
        expected_products = MOCK_PRODUCTS[:5]
        expected_message = "All products found."
        mock_local_service.smart_search_products.return_value = (expected_products, expected_message)

        products, message = await product_data_service.smart_search_products()
        
        # Assert default arguments are passed correctly
        mock_local_service.smart_search_products.assert_called_once_with('', None, None, 5) 
        assert products == expected_products
        assert message == expected_message
        
    @pytest.mark.asyncio
    async def test_smart_search_products_error_propagation(self, product_data_service, mock_local_service):
        """Test smart_search_products error propagation (original method lacks try-except)."""
        mock_local_service.smart_search_products.side_effect = Exception("Smart search internal error")
        
        with pytest.raises(Exception) as excinfo:
            await product_data_service.smart_search_products(keyword="fail")
            
        assert "Smart search internal error" in str(excinfo.value)
        mock_local_service.smart_search_products.assert_called_once()