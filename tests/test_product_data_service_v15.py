import pytest
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock

# Adjust import paths based on actual project structure
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService

# Configure logging for tests
logging.basicConfig(level=logging.INFO)

# Dummy data for testing
MOCK_PRODUCTS = [
    {"id": "1", "name": "Laptop Pro", "category": "Electronics", "price": 1200, "rating": 4.5, "brand": "TechCorp"},
    {"id": "2", "name": "Mouse Wireless", "category": "Electronics", "price": 25, "rating": 3.8, "brand": "Logi"},
    {"id": "3", "name": "Keyboard Mechanical", "category": "Electronics", "price": 75, "rating": 4.7, "brand": "Razer"},
    {"id": "4", "name": "Desk Chair Ergonomic", "category": "Furniture", "price": 300, "rating": 4.2, "brand": "ErgoOffice"},
    {"id": "5", "name": "Smartphone X", "category": "Electronics", "price": 800, "rating": 4.9, "brand": "GlobalTech"},
    {"id": "6", "name": "Coffee Table", "category": "Furniture", "price": 150, "rating": 3.5, "brand": "HomeDeco"},
]

MOCK_CATEGORIES = ["Electronics", "Furniture", "Books"]
MOCK_BRANDS = ["TechCorp", "Logi", "Razer", "ErgoOffice", "GlobalTech", "HomeDeco"]

@pytest.fixture
def mock_local_product_service(mocker):
    """
    Fixture to mock the LocalProductService.
    All methods of this mock should return data that's compatible with the service.
    For methods called via run_in_executor, the underlying mock method just needs
    to be a regular MagicMock, as run_in_executor executes it synchronously within a thread.
    """
    mock_service = mocker.MagicMock(spec=LocalProductService)

    # Configure mock returns for common methods
    mock_service.search_products.return_value = MOCK_PRODUCTS[:2] # Default for search
    mock_service.get_products.return_value = MOCK_PRODUCTS # Default for get_all_products / fallback
    mock_service.get_categories.return_value = MOCK_CATEGORIES
    mock_service.get_top_rated_products.return_value = [p for p in MOCK_PRODUCTS if p["rating"] > 4.0]
    mock_service.get_best_selling_products.return_value = MOCK_PRODUCTS[:3] # Example subset
    # For category/brand methods, the ProductDataService applies slicing, so the mock returns full list
    mock_service.get_products_by_category.side_effect = lambda cat: [p for p in MOCK_PRODUCTS if p["category"] == cat]
    mock_service.get_product_details.side_effect = lambda pid: next((p for p in MOCK_PRODUCTS if p["id"] == pid), None)
    mock_service.get_brands.return_value = MOCK_BRANDS
    mock_service.get_products_by_brand.side_effect = lambda brand: [p for p in MOCK_PRODUCTS if p["brand"] == brand]
    mock_service.smart_search_products.return_value = (MOCK_PRODUCTS[:1], "Found 1 product matching criteria.")

    # Patch LocalProductService during ProductDataService initialization
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_service)
    return mock_service

@pytest.fixture
def product_data_service(mock_local_product_service):
    """Fixture to provide an instance of ProductDataService with mocked dependencies."""
    service = ProductDataService()
    return service

@pytest.fixture(autouse=True)
def suppress_asyncio_get_event_loop_deprecation(mocker):
    """
    Suppresses the DeprecationWarning for asyncio.get_event_loop in Python 3.10+.
    This ensures tests run cleanly across different Python versions by patching
    get_event_loop to use get_running_loop if available.
    """
    if hasattr(asyncio, 'get_running_loop'):
        mocker.patch('asyncio.get_event_loop', new=asyncio.get_running_loop)


class TestProductDataService:

    @pytest.mark.asyncio
    async def test_init(self, product_data_service, mock_local_product_service, caplog):
        """Test ProductDataService initialization and its logging."""
        # The product_data_service fixture already initializes it.
        # Check if LocalProductService was instantiated and assigned.
        assert product_data_service.local_service is mock_local_product_service
        
        # Re-initialize within caplog context to capture the log message
        with caplog.at_level('INFO'):
            _ = ProductDataService()
            assert "ProductDataService initialized with LocalProductService" in caplog.text

    @pytest.mark.asyncio
    async def test_search_products_success(self, product_data_service, mock_local_product_service, caplog):
        """Test search_products method success case, including logging."""
        keyword = "laptop"
        limit = 1
        mock_local_product_service.search_products.return_value = MOCK_PRODUCTS[:limit]

        with caplog.at_level('INFO'):
            products = await product_data_service.search_products(keyword, limit)

            assert products == MOCK_PRODUCTS[:limit]
            mock_local_product_service.search_products.assert_called_once_with(keyword, limit)
            assert f"Searching products with keyword: {keyword}" in caplog.text
            assert f"Found {len(products)} products for keyword: {keyword}" in caplog.text

    @pytest.mark.asyncio
    async def test_search_products_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test search_products method exception case, ensuring an empty list is returned and error logged."""
        keyword = "error_query"
        mock_local_product_service.search_products.side_effect = Exception("Mock search error")

        with caplog.at_level('ERROR'):
            products = await product_data_service.search_products(keyword)

            assert products == []
            mock_local_product_service.search_products.assert_called_once_with(keyword, 10) # default limit
            assert "Error searching products: Mock search error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_products_with_search(self, product_data_service, mock_local_product_service, mocker):
        """Test get_products when 'search' parameter is provided, ensuring it calls search_products."""
        search_keyword = "query"
        limit = 1
        expected_products = MOCK_PRODUCTS[:limit]

        # Mock the internal search_products call to isolate the test of get_products' logic
        mocker.patch.object(product_data_service, 'search_products', new=AsyncMock(return_value=expected_products))

        products = await product_data_service.get_products(search=search_keyword, limit=limit)

        assert products == expected_products
        product_data_service.search_products.assert_called_once_with(search_keyword, limit)
        product_data_service.get_products_by_category.assert_not_called()
        product_data_service.get_all_products.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_products_with_category(self, product_data_service, mock_local_product_service, mocker):
        """Test get_products when 'category' parameter is provided, ensuring it calls get_products_by_category."""
        category_name = "Electronics"
        limit = 2
        expected_products = [p for p in MOCK_PRODUCTS if p["category"] == category_name][:limit]

        # Mock the internal get_products_by_category call
        mocker.patch.object(product_data_service, 'get_products_by_category', return_value=expected_products)

        products = await product_data_service.get_products(category=category_name, limit=limit)

        assert products == expected_products
        product_data_service.get_products_by_category.assert_called_once_with(category_name, limit)
        product_data_service.search_products.assert_not_called()
        product_data_service.get_all_products.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_products_no_filters(self, product_data_service, mock_local_product_service, mocker):
        """Test get_products when no filters are provided, ensuring it calls get_all_products."""
        limit = 3
        expected_products = MOCK_PRODUCTS[:limit]

        # Mock the internal get_all_products call
        mocker.patch.object(product_data_service, 'get_all_products', return_value=expected_products)

        products = await product_data_service.get_products(limit=limit)

        assert products == expected_products
        product_data_service.get_all_products.assert_called_once_with(limit)
        product_data_service.search_products.assert_not_called()
        product_data_service.get_products_by_category.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_products_exception_fallback(self, product_data_service, mock_local_product_service, mocker, caplog):
        """
        Test get_products error handling: if a specific filter method fails,
        it should fall back to calling self.local_service.get_products(limit).
        """
        search_keyword = "error_query"
        fallback_products = MOCK_PRODUCTS[:1] # What local_service.get_products would return

        # Make the search branch raise an exception
        mocker.patch.object(product_data_service, 'search_products', new=AsyncMock(side_effect=Exception("Mock get_products error")))
        mock_local_product_service.get_products.return_value = fallback_products

        with caplog.at_level('ERROR'):
            products = await product_data_service.get_products(search=search_keyword, limit=5)

            assert products == fallback_products
            product_data_service.search_products.assert_called_once_with(search_keyword, 5)
            mock_local_product_service.get_products.assert_called_once_with(5) # Verify fallback call
            assert "Error getting products: Mock get_products error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service, mock_local_product_service, caplog):
        """Test get_categories method success case."""
        mock_local_product_service.get_categories.return_value = MOCK_CATEGORIES

        categories = await product_data_service.get_categories()

        assert categories == MOCK_CATEGORIES
        mock_local_product_service.get_categories.assert_called_once()
        assert "Error getting categories" not in caplog.text

    @pytest.mark.asyncio
    async def test_get_categories_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test get_categories method exception case, ensuring an empty list is returned and error logged."""
        mock_local_product_service.get_categories.side_effect = Exception("Mock categories error")

        with caplog.at_level('ERROR'):
            categories = await product_data_service.get_categories()

            assert categories == []
            mock_local_product_service.get_categories.assert_called_once()
            assert "Error getting categories: Mock categories error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service, mock_local_product_service, caplog):
        """Test get_top_rated_products method success case."""
        limit = 2
        expected_products = [p for p in MOCK_PRODUCTS if p["rating"] > 4.0][:limit]
        # The mock returns the full list, ProductDataService will slice it
        mock_local_product_service.get_top_rated_products.return_value = [p for p in MOCK_PRODUCTS if p["rating"] > 4.0] 

        products = await product_data_service.get_top_rated_products(limit)

        assert products == expected_products
        mock_local_product_service.get_top_rated_products.assert_called_once_with(limit)
        assert "Error getting top rated products" not in caplog.text

    @pytest.mark.asyncio
    async def test_get_top_rated_products_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test get_top_rated_products method exception case, ensuring an empty list is returned and error logged."""
        mock_local_product_service.get_top_rated_products.side_effect = Exception("Mock top rated error")

        with caplog.at_level('ERROR'):
            products = await product_data_service.get_top_rated_products()

            assert products == []
            mock_local_product_service.get_top_rated_products.assert_called_once_with(10) # default limit
            assert "Error getting top rated products: Mock top rated error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service, mock_local_product_service, caplog):
        """Test get_best_selling_products method success case."""
        limit = 3
        expected_products = MOCK_PRODUCTS[:limit]
        # The mock returns the full list, ProductDataService will slice it
        mock_local_product_service.get_best_selling_products.return_value = MOCK_PRODUCTS 

        products = await product_data_service.get_best_selling_products(limit)

        assert products == expected_products
        mock_local_product_service.get_best_selling_products.assert_called_once_with(limit)
        assert "Error getting best selling products" not in caplog.text

    @pytest.mark.asyncio
    async def test_get_best_selling_products_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test get_best_selling_products method exception case, ensuring an empty list is returned and error logged."""
        mock_local_product_service.get_best_selling_products.side_effect = Exception("Mock best selling error")

        with caplog.at_level('ERROR'):
            products = await product_data_service.get_best_selling_products()

            assert products == []
            mock_local_product_service.get_best_selling_products.assert_called_once_with(10) # default limit
            assert "Error getting best selling products: Mock best selling error" in caplog.text

    def test_get_products_by_category_success(self, product_data_service, mock_local_product_service, caplog):
        """Test get_products_by_category method success case."""
        category = "Electronics"
        limit = 2
        expected_products = [p for p in MOCK_PRODUCTS if p["category"] == category][:limit]
        # The mock should return the full list, as ProductDataService applies the [:limit]
        mock_local_product_service.get_products_by_category.return_value = [p for p in MOCK_PRODUCTS if p["category"] == category] 

        products = product_data_service.get_products_by_category(category, limit)

        assert products == expected_products
        mock_local_product_service.get_products_by_category.assert_called_once_with(category)
        assert "Error getting products by category" not in caplog.text

    def test_get_products_by_category_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test get_products_by_category method exception case, ensuring an empty list is returned and error logged."""
        category = "NonExistent"
        mock_local_product_service.get_products_by_category.side_effect = Exception("Mock category error")

        with caplog.at_level('ERROR'):
            products = product_data_service.get_products_by_category(category)

            assert products == []
            mock_local_product_service.get_products_by_category.assert_called_once_with(category)
            assert "Error getting products by category: Mock category error" in caplog.text

    def test_get_all_products_success(self, product_data_service, mock_local_product_service, caplog):
        """Test get_all_products method success case."""
        limit = 5
        expected_products = MOCK_PRODUCTS[:limit]
        # The mock should return the full list, as ProductDataService applies the [:limit]
        mock_local_product_service.get_products.return_value = MOCK_PRODUCTS

        products = product_data_service.get_all_products(limit)

        assert products == expected_products
        mock_local_product_service.get_products.assert_called_once_with(limit)
        assert "Error getting all products" not in caplog.text

    def test_get_all_products_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test get_all_products method exception case, ensuring an empty list is returned and error logged."""
        mock_local_product_service.get_products.side_effect = Exception("Mock all products error")

        with caplog.at_level('ERROR'):
            products = product_data_service.get_all_products()

            assert products == []
            mock_local_product_service.get_products.assert_called_once_with(20) # default limit
            assert "Error getting all products: Mock all products error" in caplog.text

    def test_get_product_details_success(self, product_data_service, mock_local_product_service, caplog):
        """Test get_product_details method success case."""
        product_id = "1"
        expected_product = MOCK_PRODUCTS[0]
        mock_local_product_service.get_product_details.return_value = expected_product

        details = product_data_service.get_product_details(product_id)

        assert details == expected_product
        mock_local_product_service.get_product_details.assert_called_once_with(product_id)
        assert "Error getting product details" not in caplog.text

    def test_get_product_details_not_found(self, product_data_service, mock_local_product_service, caplog):
        """Test get_product_details method when product is not found."""
        product_id = "999"
        mock_local_product_service.get_product_details.return_value = None

        details = product_data_service.get_product_details(product_id)

        assert details is None
        mock_local_product_service.get_product_details.assert_called_once_with(product_id)
        assert "Error getting product details" not in caplog.text # No error, just not found

    def test_get_product_details_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test get_product_details method exception case, ensuring None is returned and error logged."""
        product_id = "error_id"
        mock_local_product_service.get_product_details.side_effect = Exception("Mock details error")

        with caplog.at_level('ERROR'):
            details = product_data_service.get_product_details(product_id)

            assert details is None
            mock_local_product_service.get_product_details.assert_called_once_with(product_id)
            assert "Error getting product details: Mock details error" in caplog.text

    def test_get_brands_success(self, product_data_service, mock_local_product_service, caplog):
        """Test get_brands method success case."""
        mock_local_product_service.get_brands.return_value = MOCK_BRANDS

        brands = product_data_service.get_brands()

        assert brands == MOCK_BRANDS
        mock_local_product_service.get_brands.assert_called_once()
        assert "Error getting brands" not in caplog.text

    def test_get_brands_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test get_brands method exception case, ensuring an empty list is returned and error logged."""
        mock_local_product_service.get_brands.side_effect = Exception("Mock brands error")

        with caplog.at_level('ERROR'):
            brands = product_data_service.get_brands()

            assert brands == []
            mock_local_product_service.get_brands.assert_called_once()
            assert "Error getting brands: Mock brands error" in caplog.text

    def test_get_products_by_brand_success(self, product_data_service, mock_local_product_service, caplog):
        """Test get_products_by_brand method success case."""
        brand = "TechCorp"
        limit = 1
        expected_products = [p for p in MOCK_PRODUCTS if p["brand"] == brand][:limit]
        # The mock should return the full list, as ProductDataService applies the [:limit]
        mock_local_product_service.get_products_by_brand.return_value = [p for p in MOCK_PRODUCTS if p["brand"] == brand] 

        products = product_data_service.get_products_by_brand(brand, limit)

        assert products == expected_products
        mock_local_product_service.get_products_by_brand.assert_called_once_with(brand)
        assert "Error getting products by brand" not in caplog.text

    def test_get_products_by_brand_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test get_products_by_brand method exception case, ensuring an empty list is returned and error logged."""
        brand = "NonExistentBrand"
        mock_local_product_service.get_products_by_brand.side_effect = Exception("Mock brand error")

        with caplog.at_level('ERROR'):
            products = product_data_service.get_products_by_brand(brand)

            assert products == []
            mock_local_product_service.get_products_by_brand.assert_called_once_with(brand)
            assert "Error getting products by brand: Mock brand error" in caplog.text

    @pytest.mark.asyncio
    async def test_smart_search_products_success(self, product_data_service, mock_local_product_service):
        """Test smart_search_products method success case."""
        keyword = "smart"
        category = "Electronics"
        max_price = 1000
        limit = 1
        expected_products = MOCK_PRODUCTS[:1]
        expected_message = "Found 1 product matching criteria."

        mock_local_product_service.smart_search_products.return_value = (expected_products, expected_message)

        products, message = await product_data_service.smart_search_products(keyword, category, max_price, limit)

        assert products == expected_products
        assert message == expected_message
        mock_local_product_service.smart_search_products.assert_called_once_with(keyword, category, max_price, limit)

    @pytest.mark.asyncio
    async def test_smart_search_products_exception(self, product_data_service, mock_local_product_service):
        """
        Test smart_search_products method when an exception occurs.
        Since this method does not have a try-except, the exception should propagate.
        """
        mock_local_product_service.smart_search_products.side_effect = Exception("Smart search internal error")

        with pytest.raises(Exception, match="Smart search internal error"):
            # Call with default args to ensure coverage of the path
            await product_data_service.smart_search_products() 
        
        # Verify the underlying service method was called with default arguments
        mock_local_product_service.smart_search_products.assert_called_once_with('', None, None, 5)