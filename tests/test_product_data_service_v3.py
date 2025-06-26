import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, patch

# Path to the module under test
from app.services.product_data_service import ProductDataService
# Path to the dependency (for reference, actual patching targets the import path)
from app.services.local_product_service import LocalProductService

# Sample data for mock returns
SAMPLE_PRODUCTS = [
    {"id": "p1", "name": "Laptop Pro", "price": 1200, "category": "Electronics", "brand": "TechCorp", "rating": 4.5, "sales": 100},
    {"id": "p2", "name": "Mechanical Keyboard", "price": 150, "category": "Electronics", "brand": "KeyMaster", "rating": 4.8, "sales": 200},
    {"id": "p3", "name": "Ergonomic Chair", "price": 400, "category": "Furniture", "brand": "ComfySeats", "rating": 4.2, "sales": 50},
    {"id": "p4", "name": "Smartphone X", "price": 800, "category": "Electronics", "brand": "GlobalTech", "rating": 4.7, "sales": 150},
    {"id": "p5", "name": "Designer Desk", "price": 300, "category": "Furniture", "brand": "ModernHome", "rating": 4.0, "sales": 30},
    {"id": "p6", "name": "Wireless Mouse", "price": 30, "category": "Electronics", "brand": "TechCorp", "rating": 4.3, "sales": 120},
    {"id": "p7", "name": "Python Book", "price": 50, "category": "Books", "brand": "CodeReads", "rating": 4.9, "sales": 80},
    {"id": "p8", "name": "Java Book", "price": 45, "category": "Books", "brand": "DevBooks", "rating": 4.1, "sales": 40},
    {"id": "p9", "name": "SQL Guide", "price": 35, "category": "Books", "brand": "DataLiteracy", "rating": 4.0, "sales": 20},
]
SAMPLE_CATEGORIES = ["Electronics", "Furniture", "Books"]
SAMPLE_BRANDS = ["TechCorp", "KeyMaster", "ComfySeats", "GlobalTech", "ModernHome", "CodeReads", "DevBooks", "DataLiteracy"]
SAMPLE_PRODUCT_DETAILS = {"id": "p1", "name": "Laptop Pro", "description": "Powerful laptop for professionals", "price": 1200}


@pytest.fixture
def mock_local_service(mocker):
    """
    Fixture to mock the LocalProductService dependency.
    Patches LocalProductService within the module ProductDataService imports it from,
    and configures default return values for its methods.
    """
    # Patch LocalProductService where it's imported in product_data_service.py
    mock_class = mocker.patch('app.services.product_data_service.LocalProductService')
    mock_instance = mock_class.return_value # This is the instance that ProductDataService uses
    
    # Configure default mock behaviors for LocalProductService methods
    mock_instance.search_products.return_value = SAMPLE_PRODUCTS
    mock_instance.get_products.return_value = SAMPLE_PRODUCTS
    mock_instance.get_categories.return_value = SAMPLE_CATEGORIES
    mock_instance.get_top_rated_products.return_value = sorted(SAMPLE_PRODUCTS, key=lambda x: x.get('rating', 0), reverse=True)
    mock_instance.get_best_selling_products.return_value = sorted(SAMPLE_PRODUCTS, key=lambda x: x.get('sales', 0), reverse=True)
    
    # Ensure get_products_by_category returns enough for slicing in SUT
    mock_instance.get_products_by_category.side_effect = \
        lambda category: [p for p in SAMPLE_PRODUCTS if p.get('category') == category]
    
    # Ensure get_products_by_brand returns enough for slicing in SUT
    mock_instance.get_products_by_brand.side_effect = \
        lambda brand: [p for p in SAMPLE_PRODUCTS if p.get('brand') == brand]
    
    mock_instance.get_product_details.side_effect = \
        lambda product_id: next((p for p in SAMPLE_PRODUCTS if p['id'] == product_id), None)
    
    mock_instance.get_brands.return_value = SAMPLE_BRANDS
    mock_instance.smart_search_products.return_value = (SAMPLE_PRODUCTS, "Smart search completed.")

    yield mock_instance

@pytest.fixture
async def product_data_service(mock_local_service):
    """
    Fixture to provide an instance of ProductDataService with mocked dependencies.
    """
    service = ProductDataService()
    # Assert that the LocalProductService instance was correctly assigned from the mock
    assert service.local_service is mock_local_service
    return service

@pytest.fixture
def mock_run_in_executor(mocker):
    """
    Fixture to mock asyncio.get_event_loop().run_in_executor.
    This allows controlling the return value and side effects of async operations
    that are offloaded to a thread pool within the ProductDataService.
    """
    mock_loop = mocker.patch('asyncio.get_event_loop').return_value
    mock_future = AsyncMock() # This is the awaitable (mock Future) that run_in_executor returns
    mock_loop.run_in_executor.return_value = mock_future
    yield mock_future


class TestProductDataService:
    """
    Comprehensive test suite for ProductDataService, ensuring high test coverage
    for all methods, including success and error scenarios, and proper mocking.
    """

    @pytest.mark.asyncio
    async def test_search_products_success(self, product_data_service, mock_local_service, mock_run_in_executor):
        """
        Test successful product search.
        Verifies correct interaction with LocalProductService via run_in_executor.
        """
        expected_products = [{"id": "s1", "name": "Search Result Product"}]
        mock_run_in_executor.return_value = expected_products

        keyword = "keyboard"
        limit = 5
        result = await product_data_service.search_products(keyword, limit)

        assert result == expected_products
        # Verify get_event_loop was called to get the loop
        asyncio.get_event_loop.assert_called_once()
        # Verify run_in_executor was called with the correct callable and arguments
        asyncio.get_event_loop.return_value.run_in_executor.assert_called_once_with(
            None, mock_local_service.search_products, keyword, limit
        )
        # Ensure the underlying sync method (mock_local_service.search_products) was not called directly by the service,
        # as it should be called by the executor.
        mock_local_service.search_products.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_products_error(self, product_data_service, mock_local_service, mock_run_in_executor, caplog):
        """
        Test product search error handling.
        Ensures an empty list is returned and an error is logged on exception from the executor.
        """
        mock_run_in_executor.side_effect = Exception("Simulated search executor error")

        keyword = "error_test"
        limit = 5
        with caplog.at_level(logging.ERROR):
            result = await product_data_service.search_products(keyword, limit)

        assert result == []
        assert "Error searching products: Simulated search executor error" in caplog.text
        asyncio.get_event_loop.return_value.run_in_executor.assert_called_once_with(
            None, mock_local_service.search_products, keyword, limit
        )
        mock_local_service.search_products.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_products_with_search(self, product_data_service, mock_local_service, mock_run_in_executor):
        """
        Test get_products when 'search' parameter is provided.
        It should delegate the call to the internal search_products method.
        """
        expected_products = [{"id": "gs1", "name": "Get Search Result"}]
        mock_run_in_executor.return_value = expected_products # This controls ProductDataService.search_products' return

        search_keyword = "query"
        limit_val = 15
        result = await product_data_service.get_products(limit=limit_val, search=search_keyword)

        assert result == expected_products
        # Verify that run_in_executor was called via product_data_service.search_products
        asyncio.get_event_loop.return_value.run_in_executor.assert_called_once_with(
            None, mock_local_service.search_products, search_keyword, limit_val
        )
        mock_local_service.get_products_by_category.assert_not_called()
        mock_local_service.get_products.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_products_with_category(self, product_data_service, mock_local_service):
        """
        Test get_products when 'category' parameter is provided.
        It should delegate the call to the internal get_products_by_category method.
        """
        # Mock returns from local_service and then ensure slicing is applied by SUT
        mock_local_service.get_products_by_category.return_value = \
            [p for p in SAMPLE_PRODUCTS if p['category'] == 'Electronics'] # Returns 3 products

        category_name = "Electronics"
        limit_val = 2
        result = await product_data_service.get_products(limit=limit_val, category=category_name)

        # The SUT (ProductDataService) applies the [:limit] slicing itself
        assert len(result) == limit_val
        assert result == [p for p in SAMPLE_PRODUCTS if p['category'] == 'Electronics'][:limit_val]
        mock_local_service.get_products_by_category.assert_called_once_with(category_name)

        mock_local_service.search_products.assert_not_called()
        mock_local_service.get_products.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_products_without_filters(self, product_data_service, mock_local_service):
        """
        Test get_products when no filters (search or category) are provided.
        It should delegate the call to the internal get_all_products method.
        """
        expected_products = SAMPLE_PRODUCTS[:10] # Default limit for get_all_products/get_products
        mock_local_service.get_products.return_value = expected_products # get_all_products uses this internally

        limit_val = 20
        result = await product_data_service.get_products(limit=limit_val)

        assert result == expected_products # The mock is set to return this
        mock_local_service.get_products.assert_called_once_with(limit_val)
        mock_local_service.search_products.assert_not_called()
        mock_local_service.get_products_by_category.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_products_error_fallback(self, product_data_service, mock_local_service, mocker, caplog):
        """
        Test get_products error handling.
        Ensures a fallback to local_service.get_products on internal exception
        (e.g., if any of the delegated methods like search_products, get_products_by_category,
        or get_all_products raise an exception).
        """
        # We need to mock one of the branches within get_products to raise an error.
        # Let's make get_products_by_category (which is an internal method of SUT) fail.
        mocker.patch.object(product_data_service, 'get_products_by_category', side_effect=Exception("Internal category processing error"))

        fallback_products = [{"id": "fb1", "name": "Fallback Product"}]
        mock_local_service.get_products.return_value = fallback_products # This is the expected fallback call result

        with caplog.at_level(logging.ERROR):
            # Call get_products with a category to trigger the failing branch
            result = await product_data_service.get_products(category="nonexistent_category", limit=5)

        assert result == fallback_products
        assert "Error getting products: Internal category processing error" in caplog.text
        # Verify that the failing internal method was called
        product_data_service.get_products_by_category.assert_called_once_with("nonexistent_category", 5)
        # Verify that the fallback method on local_service was called
        mock_local_service.get_products.assert_called_once_with(5) # Uses the limit from the get_products call

    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service, mock_local_service):
        """Test successful retrieval of categories."""
        expected_categories = ["Electronics", "Books"]
        mock_local_service.get_categories.return_value = expected_categories
        result = await product_data_service.get_categories()
        assert result == expected_categories
        mock_local_service.get_categories.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_categories_error(self, product_data_service, mock_local_service, caplog):
        """Test error handling for get_categories."""
        mock_local_service.get_categories.side_effect = Exception("Category service error")
        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_categories()
        assert result == []
        assert "Error getting categories: Category service error" in caplog.text
        mock_local_service.get_categories.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service, mock_local_service):
        """Test successful retrieval of top-rated products."""
        expected_products = [{"id": "tr1", "rating": 5.0}]
        mock_local_service.get_top_rated_products.return_value = expected_products
        limit = 3
        result = await product_data_service.get_top_rated_products(limit)
        assert result == expected_products
        mock_local_service.get_top_rated_products.assert_called_once_with(limit)

    @pytest.mark.asyncio
    async def test_get_top_rated_products_error(self, product_data_service, mock_local_service, caplog):
        """Test error handling for get_top_rated_products."""
        mock_local_service.get_top_rated_products.side_effect = Exception("Top rated error")
        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_top_rated_products()
        assert result == []
        assert "Error getting top rated products: Top rated error" in caplog.text
        mock_local_service.get_top_rated_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service, mock_local_service):
        """Test successful retrieval of best-selling products."""
        expected_products = [{"id": "bs1", "sales": 1000}]
        mock_local_service.get_best_selling_products.return_value = expected_products
        limit = 3
        result = await product_data_service.get_best_selling_products(limit)
        assert result == expected_products
        mock_local_service.get_best_selling_products.assert_called_once_with(limit)

    @pytest.mark.asyncio
    async def test_get_best_selling_products_error(self, product_data_service, mock_local_service, caplog):
        """Test error handling for get_best_selling_products."""
        mock_local_service.get_best_selling_products.side_effect = Exception("Best selling error")
        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_best_selling_products()
        assert result == []
        assert "Error getting best selling products: Best selling error" in caplog.text
        mock_local_service.get_best_selling_products.assert_called_once()

    def test_get_products_by_category_success(self, product_data_service, mock_local_service):
        """
        Test successful retrieval of products by category, including limit slicing.
        The SUT applies the limit slicing after getting all products for that category.
        """
        # The mock is configured via side_effect to filter SAMPLE_PRODUCTS
        category = "Books"
        limit = 2
        # Expected products before slicing by SUT: 3 products matching 'Books'
        expected_full_list = [p for p in SAMPLE_PRODUCTS if p.get('category') == category]

        result = product_data_service.get_products_by_category(category, limit)

        assert len(result) == limit
        assert result == expected_full_list[:limit]
        # Verify that local_service was called without the limit (SUT applies slicing)
        mock_local_service.get_products_by_category.assert_called_once_with(category)

    def test_get_products_by_category_limit_exceeded(self, product_data_service, mock_local_service):
        """
        Test get_products_by_category when requested limit is higher than available products.
        SUT should return all available products without error.
        """
        # The mock is configured via side_effect to filter SAMPLE_PRODUCTS
        category = "Furniture" # Has 2 products in SAMPLE_PRODUCTS
        limit = 5 # Requesting more than available
        expected_full_list = [p for p in SAMPLE_PRODUCTS if p.get('category') == category]

        result = product_data_service.get_products_by_category(category, limit)

        assert len(result) == len(expected_full_list)
        assert result == expected_full_list
        mock_local_service.get_products_by_category.assert_called_once_with(category)

    def test_get_products_by_category_error(self, product_data_service, mock_local_service, caplog):
        """Test error handling for get_products_by_category."""
        mock_local_service.get_products_by_category.side_effect = Exception("Local category filter error")
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_products_by_category("Fashion")
        assert result == []
        assert "Error getting products by category: Local category filter error" in caplog.text
        mock_local_service.get_products_by_category.assert_called_once_with("Fashion")

    def test_get_all_products_success(self, product_data_service, mock_local_service):
        """Test successful retrieval of all products, respecting the limit."""
        expected_products_subset = SAMPLE_PRODUCTS[:5]
        # get_all_products internally calls local_service.get_products with the limit
        mock_local_service.get_products.return_value = expected_products_subset

        limit = 5
        result = product_data_service.get_all_products(limit)

        assert result == expected_products_subset
        mock_local_service.get_products.assert_called_once_with(limit)

    def test_get_all_products_error(self, product_data_service, mock_local_service, caplog):
        """Test error handling for get_all_products."""
        mock_local_service.get_products.side_effect = Exception("Local get all error")
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_all_products()
        assert result == []
        assert "Error getting all products: Local get all error" in caplog.text
        mock_local_service.get_products.assert_called_once()

    def test_get_product_details_found(self, product_data_service, mock_local_service):
        """Test successful retrieval of product details for an existing product."""
        expected_details = SAMPLE_PRODUCT_DETAILS
        # Mock is configured via side_effect to return specific product details by ID
        product_id = "p1"
        result = product_data_service.get_product_details(product_id)
        assert result == expected_details
        mock_local_service.get_product_details.assert_called_once_with(product_id)

    def test_get_product_details_not_found(self, product_data_service, mock_local_service):
        """Test retrieval of product details for a non-existing product."""
        mock_local_service.get_product_details.return_value = None # Explicitly set for not found case
        product_id = "nonexistent_id"
        result = product_data_service.get_product_details(product_id)
        assert result is None
        mock_local_service.get_product_details.assert_called_once_with(product_id)

    def test_get_product_details_error(self, product_data_service, mock_local_service, caplog):
        """Test error handling for get_product_details."""
        mock_local_service.get_product_details.side_effect = Exception("Details service error")
        product_id = "error_id"
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_product_details(product_id)
        assert result is None
        assert "Error getting product details: Details service error" in caplog.text
        mock_local_service.get_product_details.assert_called_once_with(product_id)

    def test_get_brands_success(self, product_data_service, mock_local_service):
        """Test successful retrieval of brands."""
        expected_brands = ["TechCorp", "KeyMaster"]
        mock_local_service.get_brands.return_value = expected_brands
        result = product_data_service.get_brands()
        assert result == expected_brands
        mock_local_service.get_brands.assert_called_once()

    def test_get_brands_error(self, product_data_service, mock_local_service, caplog):
        """Test error handling for get_brands."""
        mock_local_service.get_brands.side_effect = Exception("Brands service error")
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_brands()
        assert result == []
        assert "Error getting brands: Brands service error" in caplog.text
        mock_local_service.get_brands.assert_called_once()

    def test_get_products_by_brand_success(self, product_data_service, mock_local_service):
        """
        Test successful retrieval of products by brand, including limit slicing.
        The SUT applies the limit slicing after getting all products for that brand.
        """
        # The mock is configured via side_effect to filter SAMPLE_PRODUCTS
        brand = "TechCorp" # Has 2 products in SAMPLE_PRODUCTS
        limit = 1
        expected_full_list = [p for p in SAMPLE_PRODUCTS if p.get('brand') == brand]

        result = product_data_service.get_products_by_brand(brand, limit)

        assert len(result) == limit
        assert result == expected_full_list[:limit]
        # Verify that local_service was called without the limit (SUT applies slicing)
        mock_local_service.get_products_by_brand.assert_called_once_with(brand)

    def test_get_products_by_brand_limit_exceeded(self, product_data_service, mock_local_service):
        """
        Test get_products_by_brand when requested limit is higher than available products.
        SUT should return all available products without error.
        """
        # The mock is configured via side_effect to filter SAMPLE_PRODUCTS
        brand = "KeyMaster" # Has 1 product in SAMPLE_PRODUCTS
        limit = 5 # Requesting more than available
        expected_full_list = [p for p in SAMPLE_PRODUCTS if p.get('brand') == brand]

        result = product_data_service.get_products_by_brand(brand, limit)

        assert len(result) == len(expected_full_list)
        assert result == expected_full_list
        mock_local_service.get_products_by_brand.assert_called_once_with(brand)

    def test_get_products_by_brand_error(self, product_data_service, mock_local_service, caplog):
        """Test error handling for get_products_by_brand."""
        mock_local_service.get_products_by_brand.side_effect = Exception("Local brand filter error")
        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_products_by_brand("NonExistentBrand")
        assert result == []
        assert "Error getting products by brand: Local brand filter error" in caplog.text
        mock_local_service.get_products_by_brand.assert_called_once_with("NonExistentBrand")

    @pytest.mark.asyncio
    async def test_smart_search_products_success(self, product_data_service, mock_local_service, mock_run_in_executor):
        """
        Test successful smart search.
        Verifies correct interaction with LocalProductService via run_in_executor
        and correct return of products and message tuple.
        """
        expected_products = [{"id": "ss1", "name": "Smart Search Item"}]
        expected_message = "Smart search completed with results."
        mock_run_in_executor.return_value = (expected_products, expected_message)

        keyword = "smart"
        category = "Electronics"
        max_price = 500
        limit = 2
        products, message = await product_data_service.smart_search_products(keyword, category, max_price, limit)

        assert products == expected_products
        assert message == expected_message
        asyncio.get_event_loop.assert_called_once()
        asyncio.get_event_loop.return_value.run_in_executor.assert_called_once_with(
            None, mock_local_service.smart_search_products, keyword, category, max_price, limit
        )
        mock_local_service.smart_search_products.assert_not_called()

    @pytest.mark.asyncio
    async def test_smart_search_products_error_propagation(self, product_data_service, mock_local_service, mock_run_in_executor):
        """
        Test that errors occurring during smart_search_products execution (e.g., from the executor)
        propagate up, as the service does not explicitly catch exceptions for this specific call.
        """
        mock_run_in_executor.side_effect = Exception("Smart search executor failure")

        with pytest.raises(Exception, match="Smart search executor failure"):
            await product_data_service.smart_search_products(keyword="fail_me", category="any")

        asyncio.get_event_loop.return_value.run_in_executor.assert_called_once()
        mock_local_service.smart_search_products.assert_not_called()