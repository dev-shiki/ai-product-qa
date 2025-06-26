import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import logging

# Assuming the project structure allows direct import
# If running pytest from the project root, this should work.
# If running from a subdirectory (e.g., tests/), you might need to adjust sys.path
# or use a different import mechanism like:
# from ..app.services.product_data_service import ProductDataService
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService # Used for type hinting in mocks


@pytest.fixture
def mock_local_service(mocker):
    """
    Fixture to provide a mocked LocalProductService instance.
    All methods are mocked with default return values.
    """
    mock_service = mocker.MagicMock(spec=LocalProductService)
    # Configure default return values for LocalProductService methods
    mock_service.search_products.return_value = []
    mock_service.get_products.return_value = []
    mock_service.get_categories.return_value = []
    mock_service.get_top_rated_products.return_value = []
    mock_service.get_best_selling_products.return_value = []
    mock_service.get_products_by_category.return_value = []
    mock_service.get_product_details.return_value = None
    mock_service.get_brands.return_value = []
    mock_service.get_products_by_brand.return_value = []
    mock_service.smart_search_products.return_value = ([], "No message.") # Default for smart_search
    return mock_service

@pytest.fixture
def mock_asyncio_loop(mocker):
    """
    Fixture to mock asyncio.get_event_loop and its run_in_executor method.
    This allows controlling the behavior of asynchronous calls to synchronous methods.
    """
    mock_loop = mocker.MagicMock()
    # By default, run_in_executor returns an awaitable (AsyncMock) that resolves to None.
    # Specific tests will set its return_value for their needs.
    mock_loop.run_in_executor.return_value = AsyncMock() 
    mocker.patch("asyncio.get_event_loop", return_value=mock_loop)
    return mock_loop

@pytest.fixture
def product_data_service_instance(mock_local_service, mocker):
    """
    Fixture to provide a ProductDataService instance with its LocalProductService
    dependency replaced by a mock.
    """
    # Patch the LocalProductService class itself so that when ProductDataService
    # instantiates it in its __init__, it gets our mock.
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service)
    service = ProductDataService()
    return service

@pytest.fixture(autouse=True)
def cap_logging(mocker):
    """
    Fixture to mock the logger's error and info methods to capture log calls for assertions.
    `autouse=True` means this fixture is automatically applied to all tests.
    """
    mock_logger_error = mocker.patch('app.services.product_data_service.logger.error')
    mock_logger_info = mocker.patch('app.services.product_data_service.logger.info')
    return {'error': mock_logger_error, 'info': mock_logger_info}

class TestProductDataService:
    """
    Comprehensive test suite for the ProductDataService class.
    Aims for high test coverage including success, edge, and error cases.
    """

    @pytest.mark.asyncio
    async def test_init_success(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test ProductDataService initialization.
        Verifies that LocalProductService is instantiated and an info log is made.
        """
        assert product_data_service_instance.local_service == mock_local_service
        cap_logging['info'].assert_called_with("ProductDataService initialized with LocalProductService")

    @pytest.mark.asyncio
    async def test_search_products_success(self, product_data_service_instance, mock_local_service, mock_asyncio_loop, cap_logging):
        """
        Test search_products method for successful product retrieval.
        Verifies the correct call to run_in_executor and returned products.
        """
        expected_products = [{"id": "1", "name": "Laptop XYZ", "price": 1200}]
        # Configure the awaitable returned by run_in_executor to resolve to our expected products
        mock_asyncio_loop.run_in_executor.return_value.return_value = expected_products
        
        keyword = "laptop"
        limit = 5
        products = await product_data_service_instance.search_products(keyword, limit)
        
        assert products == expected_products
        mock_asyncio_loop.run_in_executor.assert_called_once_with(None, mock_local_service.search_products, keyword, limit)
        cap_logging['info'].assert_any_call(f"Searching products with keyword: {keyword}")
        cap_logging['info'].assert_any_call(f"Found {len(expected_products)} products for keyword: {keyword}")
        cap_logging['error'].assert_not_called()

    @pytest.mark.asyncio
    async def test_search_products_no_results(self, product_data_service_instance, mock_local_service, mock_asyncio_loop, cap_logging):
        """
        Test search_products when no products are found for the keyword.
        """
        mock_asyncio_loop.run_in_executor.return_value.return_value = []
        
        keyword = "nonexistent"
        products = await product_data_service_instance.search_products(keyword)
        
        assert products == []
        mock_asyncio_loop.run_in_executor.assert_called_once_with(None, mock_local_service.search_products, keyword, 10) # default limit
        cap_logging['info'].assert_any_call(f"Found 0 products for keyword: {keyword}")
        cap_logging['error'].assert_not_called()

    @pytest.mark.asyncio
    async def test_search_products_exception(self, product_data_service_instance, mock_local_service, mock_asyncio_loop, cap_logging):
        """
        Test search_products method when an exception occurs during execution.
        Verifies an empty list is returned and an error is logged.
        """
        mock_asyncio_loop.run_in_executor.return_value.side_effect = Exception("Test search error")
        
        keyword = "error_query"
        products = await product_data_service_instance.search_products(keyword)
        
        assert products == []
        mock_asyncio_loop.run_in_executor.assert_called_once()
        cap_logging['error'].assert_called_once_with(f"Error searching products: Test search error")
        cap_logging['info'].assert_any_call(f"Searching products with keyword: {keyword}")


    @pytest.mark.asyncio
    async def test_get_products_search_path(self, product_data_service_instance, mocker):
        """
        Test get_products method when the 'search' parameter is provided.
        Verifies that search_products is called.
        """
        # Patch the internal call to search_products
        mocker.patch.object(product_data_service_instance, 'search_products', new_callable=AsyncMock)
        expected_products = [{"id": "2", "name": "Tablet ABC"}]
        product_data_service_instance.search_products.return_value = expected_products
        
        limit = 10
        search_keyword = "tablet"
        products = await product_data_service_instance.get_products(limit=limit, search=search_keyword)
        
        assert products == expected_products
        product_data_service_instance.search_products.assert_called_once_with(search_keyword, limit)
        # Ensure other paths are not taken
        product_data_service_instance.get_products_by_category.assert_not_called()
        product_data_service_instance.get_all_products.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_products_category_path(self, product_data_service_instance, mocker):
        """
        Test get_products method when the 'category' parameter is provided.
        Verifies that get_products_by_category is called.
        """
        mocker.patch.object(product_data_service_instance, 'get_products_by_category')
        expected_products = [{"id": "3", "name": "TV XYZ", "category": "electronics"}]
        product_data_service_instance.get_products_by_category.return_value = expected_products
        
        limit = 15
        category_name = "electronics"
        products = await product_data_service_instance.get_products(limit=limit, category=category_name)
        
        assert products == expected_products
        product_data_service_instance.get_products_by_category.assert_called_once_with(category_name, limit)
        # Ensure other paths are not taken
        product_data_service_instance.search_products.assert_not_called()
        product_data_service_instance.get_all_products.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_products_all_path(self, product_data_service_instance, mocker):
        """
        Test get_products method when no specific filter (search/category) is provided.
        Verifies that get_all_products is called.
        """
        mocker.patch.object(product_data_service_instance, 'get_all_products')
        expected_products = [{"id": "4", "name": "Chair ABC"}]
        product_data_service_instance.get_all_products.return_value = expected_products
        
        limit = 25
        products = await product_data_service_instance.get_products(limit=limit)
        
        assert products == expected_products
        product_data_service_instance.get_all_products.assert_called_once_with(limit)
        # Ensure other paths are not taken
        product_data_service_instance.search_products.assert_not_called()
        product_data_service_instance.get_products_by_category.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_products_exception_fallback(self, product_data_service_instance, mock_local_service, mocker, cap_logging):
        """
        Test get_products method error handling.
        Verifies that an internal exception is caught, logged, and it falls back to local_service.get_products.
        """
        # Make one of the internal calls (e.g., get_all_products) raise an exception
        mocker.patch.object(product_data_service_instance, 'get_all_products', side_effect=Exception("Internal test error"))
        
        fallback_products = [{"id": "5", "name": "Fallback Item"}]
        mock_local_service.get_products.return_value = fallback_products
        
        limit = 10
        products = await product_data_service_instance.get_products(limit=limit)
        
        assert products == fallback_products
        product_data_service_instance.get_all_products.assert_called_once_with(limit) # Verify the initial call that failed
        mock_local_service.get_products.assert_called_once_with(limit) # Verify the fallback call
        cap_logging['error'].assert_called_once_with("Error getting products: Internal test error")

    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test get_categories method for successful retrieval.
        """
        expected_categories = ["Electronics", "Books", "Home & Garden"]
        mock_local_service.get_categories.return_value = expected_categories
        
        categories = await product_data_service_instance.get_categories()
        
        assert categories == expected_categories
        mock_local_service.get_categories.assert_called_once()
        cap_logging['error'].assert_not_called()

    @pytest.mark.asyncio
    async def test_get_categories_exception(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test get_categories method when an exception occurs.
        Verifies an empty list is returned and an error is logged.
        """
        mock_local_service.get_categories.side_effect = Exception("Category retrieval error")
        
        categories = await product_data_service_instance.get_categories()
        
        assert categories == []
        mock_local_service.get_categories.assert_called_once()
        cap_logging['error'].assert_called_once_with("Error getting categories: Category retrieval error")

    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test get_top_rated_products method for successful retrieval.
        """
        expected_products = [{"id": "6", "name": "High Rated Product", "rating": 4.9}]
        mock_local_service.get_top_rated_products.return_value = expected_products
        
        limit = 5
        products = await product_data_service_instance.get_top_rated_products(limit)
        
        assert products == expected_products
        mock_local_service.get_top_rated_products.assert_called_once_with(limit)
        cap_logging['error'].assert_not_called()

    @pytest.mark.asyncio
    async def test_get_top_rated_products_exception(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test get_top_rated_products method when an exception occurs.
        Verifies an empty list is returned and an error is logged.
        """
        mock_local_service.get_top_rated_products.side_effect = Exception("Top rated product error")
        
        products = await product_data_service_instance.get_top_rated_products()
        
        assert products == []
        mock_local_service.get_top_rated_products.assert_called_once()
        cap_logging['error'].assert_called_once_with("Error getting top rated products: Top rated product error")

    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test get_best_selling_products method for successful retrieval.
        """
        expected_products = [{"id": "7", "name": "Best Seller", "sales": 1500}]
        mock_local_service.get_best_selling_products.return_value = expected_products
        
        limit = 3
        products = await product_data_service_instance.get_best_selling_products(limit)
        
        assert products == expected_products
        mock_local_service.get_best_selling_products.assert_called_once_with(limit)
        cap_logging['error'].assert_not_called()

    @pytest.mark.asyncio
    async def test_get_best_selling_products_exception(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test get_best_selling_products method when an exception occurs.
        Verifies an empty list is returned and an error is logged.
        """
        mock_local_service.get_best_selling_products.side_effect = Exception("Best selling product error")
        
        products = await product_data_service_instance.get_best_selling_products()
        
        assert products == []
        mock_local_service.get_best_selling_products.assert_called_once()
        cap_logging['error'].assert_called_once_with("Error getting best selling products: Best selling product error")

    def test_get_products_by_category_success_with_limit(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test get_products_by_category method for successful retrieval with a limit.
        Verifies that LocalProductService is called without limit, and the result is sliced.
        """
        all_products_in_category = [
            {"id": "8", "name": "Book A", "category": "books"}, 
            {"id": "9", "name": "Book B", "category": "books"}, 
            {"id": "10", "name": "Book C", "category": "books"}
        ]
        mock_local_service.get_products_by_category.return_value = all_products_in_category
        
        category = "books"
        limit = 2
        products = product_data_service_instance.get_products_by_category(category, limit)
        
        assert products == all_products_in_category[:limit]
        mock_local_service.get_products_by_category.assert_called_once_with(category) 
        cap_logging['error'].assert_not_called()

    def test_get_products_by_category_limit_exceeds_available(self, product_data_service_instance, mock_local_service):
        """
        Test get_products_by_category when the requested limit is greater than available products.
        Verifies all available products are returned.
        """
        all_products_in_category = [{"id": "8", "name": "Book A", "category": "books"}]
        mock_local_service.get_products_by_category.return_value = all_products_in_category
        
        category = "books"
        limit = 5 # Request more than available
        products = product_data_service_instance.get_products_by_category(category, limit)
        
        assert products == all_products_in_category
        mock_local_service.get_products_by_category.assert_called_once_with(category)

    def test_get_products_by_category_no_products(self, product_data_service_instance, mock_local_service):
        """
        Test get_products_by_category when no products are found for the category.
        """
        mock_local_service.get_products_by_category.return_value = []
        
        category = "empty_cat"
        limit = 5
        products = product_data_service_instance.get_products_by_category(category, limit)
        
        assert products == []
        mock_local_service.get_products_by_category.assert_called_once_with(category)

    def test_get_products_by_category_exception(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test get_products_by_category method when an exception occurs.
        Verifies an empty list is returned and an error is logged.
        """
        mock_local_service.get_products_by_category.side_effect = Exception("Category search error")
        
        products = product_data_service_instance.get_products_by_category("error_cat")
        
        assert products == []
        mock_local_service.get_products_by_category.assert_called_once()
        cap_logging['error'].assert_called_once_with("Error getting products by category: Category search error")

    def test_get_all_products_success(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test get_all_products method for successful retrieval.
        """
        expected_products = [{"id": "11", "name": "All Product 1"}, {"id": "12", "name": "All Product 2"}]
        mock_local_service.get_products.return_value = expected_products
        
        limit = 20
        products = product_data_service_instance.get_all_products(limit)
        
        assert products == expected_products
        mock_local_service.get_products.assert_called_once_with(limit)
        cap_logging['error'].assert_not_called()

    def test_get_all_products_exception(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test get_all_products method when an exception occurs.
        Verifies an empty list is returned and an error is logged.
        """
        mock_local_service.get_products.side_effect = Exception("All products retrieval error")
        
        products = product_data_service_instance.get_all_products()
        
        assert products == []
        mock_local_service.get_products.assert_called_once()
        cap_logging['error'].assert_called_once_with("Error getting all products: All products retrieval error")

    def test_get_product_details_found(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test get_product_details method when a product is found by ID.
        """
        expected_details = {"id": "p1", "name": "Product A", "price": 100, "description": "Details about A"}
        mock_local_service.get_product_details.return_value = expected_details
        
        product_id = "p1"
        details = product_data_service_instance.get_product_details(product_id)
        
        assert details == expected_details
        mock_local_service.get_product_details.assert_called_once_with(product_id)
        cap_logging['error'].assert_not_called()

    def test_get_product_details_not_found(self, product_data_service_instance, mock_local_service):
        """
        Test get_product_details method when a product is not found (returns None).
        """
        mock_local_service.get_product_details.return_value = None
        
        product_id = "nonexistent_id"
        details = product_data_service_instance.get_product_details(product_id)
        
        assert details is None
        mock_local_service.get_product_details.assert_called_once_with(product_id)

    def test_get_product_details_exception(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test get_product_details method when an exception occurs.
        Verifies None is returned and an error is logged.
        """
        mock_local_service.get_product_details.side_effect = Exception("Product details error")
        
        details = product_data_service_instance.get_product_details("error_id")
        
        assert details is None
        mock_local_service.get_product_details.assert_called_once()
        cap_logging['error'].assert_called_once_with("Error getting product details: Product details error")

    def test_get_brands_success(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test get_brands method for successful retrieval.
        """
        expected_brands = ["BrandX", "BrandY", "BrandZ"]
        mock_local_service.get_brands.return_value = expected_brands
        
        brands = product_data_service_instance.get_brands()
        
        assert brands == expected_brands
        mock_local_service.get_brands.assert_called_once()
        cap_logging['error'].assert_not_called()

    def test_get_brands_exception(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test get_brands method when an exception occurs.
        Verifies an empty list is returned and an error is logged.
        """
        mock_local_service.get_brands.side_effect = Exception("Brands retrieval error")
        
        brands = product_data_service_instance.get_brands()
        
        assert brands == []
        mock_local_service.get_brands.assert_called_once()
        cap_logging['error'].assert_called_once_with("Error getting brands: Brands retrieval error")

    def test_get_products_by_brand_success_with_limit(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test get_products_by_brand method for successful retrieval with a limit.
        Verifies that LocalProductService is called without limit, and the result is sliced.
        """
        all_products_in_brand = [
            {"id": "b1", "name": "BrandX Phone", "brand": "BrandX"}, 
            {"id": "b2", "name": "BrandX Laptop", "brand": "BrandX"}, 
            {"id": "b3", "name": "BrandX Watch", "brand": "BrandX"}
        ]
        mock_local_service.get_products_by_brand.return_value = all_products_in_brand
        
        brand = "BrandX"
        limit = 2
        products = product_data_service_instance.get_products_by_brand(brand, limit)
        
        assert products == all_products_in_brand[:limit]
        mock_local_service.get_products_by_brand.assert_called_once_with(brand)
        cap_logging['error'].assert_not_called()

    def test_get_products_by_brand_limit_exceeds_available(self, product_data_service_instance, mock_local_service):
        """
        Test get_products_by_brand when the requested limit is greater than available products.
        Verifies all available products are returned.
        """
        all_products_in_brand = [{"id": "b1", "name": "BrandX Phone", "brand": "BrandX"}]
        mock_local_service.get_products_by_brand.return_value = all_products_in_brand
        
        brand = "BrandX"
        limit = 5 # Request more than available
        products = product_data_service_instance.get_products_by_brand(brand, limit)
        
        assert products == all_products_in_brand
        mock_local_service.get_products_by_brand.assert_called_once_with(brand)

    def test_get_products_by_brand_no_products(self, product_data_service_instance, mock_local_service):
        """
        Test get_products_by_brand when no products are found for the brand.
        """
        mock_local_service.get_products_by_brand.return_value = []
        
        brand = "empty_brand"
        limit = 5
        products = product_data_service_instance.get_products_by_brand(brand, limit)
        
        assert products == []
        mock_local_service.get_products_by_brand.assert_called_once_with(brand)

    def test_get_products_by_brand_exception(self, product_data_service_instance, mock_local_service, cap_logging):
        """
        Test get_products_by_brand method when an exception occurs.
        Verifies an empty list is returned and an error is logged.
        """
        mock_local_service.get_products_by_brand.side_effect = Exception("Brand search error")
        
        products = product_data_service_instance.get_products_by_brand("error_brand")
        
        assert products == []
        mock_local_service.get_products_by_brand.assert_called_once()
        cap_logging['error'].assert_called_once_with("Error getting products by brand: Brand search error")

    @pytest.mark.asyncio
    async def test_smart_search_products_success_full_params(self, product_data_service_instance, mock_local_service, mock_asyncio_loop):
        """
        Test smart_search_products method for successful retrieval with all parameters.
        Verifies the correct call to run_in_executor and returned data.
        """
        expected_products = [{"id": "s1", "name": "Smart Speaker"}]
        expected_message = "Found 1 smart product matching criteria."
        
        # Configure the awaitable returned by run_in_executor
        mock_asyncio_loop.run_in_executor.return_value.return_value = (expected_products, expected_message)
        
        keyword = "smart"
        category = "electronics"
        max_price = 500
        limit = 1
        
        products, message = await product_data_service_instance.smart_search_products(
            keyword=keyword, category=category, max_price=max_price, limit=limit
        )
        
        assert products == expected_products
        assert message == expected_message
        
        mock_asyncio_loop.run_in_executor.assert_called_once_with(
            None, mock_local_service.smart_search_products, keyword, category, max_price, limit
        )

    @pytest.mark.asyncio
    async def test_smart_search_products_success_default_params(self, product_data_service_instance, mock_local_service, mock_asyncio_loop):
        """
        Test smart_search_products with default parameters.
        Verifies that default parameters are correctly passed to the underlying service.
        """
        mock_asyncio_loop.run_in_executor.return_value.return_value = ([], "No products found.")
        
        products, message = await product_data_service_instance.smart_search_products() # Call with defaults
        
        assert products == []
        assert message == "No products found."
        
        # Verify default parameters are passed: keyword='', category=None, max_price=None, limit=5
        mock_asyncio_loop.run_in_executor.assert_called_once_with(
            None, mock_local_service.smart_search_products, '', None, None, 5
        )

    @pytest.mark.asyncio
    async def test_smart_search_products_exception_propagation(self, product_data_service_instance, mock_local_service, mock_asyncio_loop):
        """
        Test smart_search_products method when an exception occurs in the executor.
        The original `ProductDataService` implementation for `smart_search_products`
        does not handle exceptions internally; they are propagated upwards.
        This test verifies that propagation behavior.
        """
        mock_asyncio_loop.run_in_executor.return_value.side_effect = Exception("Smart search executor error")
        
        keyword = "error_search"
        
        with pytest.raises(Exception) as excinfo:
            await product_data_service_instance.smart_search_products(keyword=keyword)
        
        assert "Smart search executor error" in str(excinfo.value)
        mock_asyncio_loop.run_in_executor.assert_called_once_with(
            None, mock_local_service.smart_search_products, keyword, None, None, 5 # default params included
        )