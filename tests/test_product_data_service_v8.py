import pytest
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService # Import for patching target


# --- Mock Data ---
MOCK_PRODUCT_1 = {"id": "p1", "name": "Laptop Pro", "category": "Electronics", "brand": "TechCorp", "rating": 4.5, "price": 1200, "description": "Powerful laptop."}
MOCK_PRODUCT_2 = {"id": "p2", "name": "Gaming Mouse", "category": "Electronics", "brand": "GameGear", "rating": 4.0, "price": 75, "description": "Ergonomic gaming mouse."}
MOCK_PRODUCT_3 = {"id": "p3", "name": "The Great Novel", "category": "Books", "brand": "LiteraryPub", "rating": 4.8, "price": 25, "description": "Bestselling novel."}
MOCK_PRODUCT_4 = {"id": "p4", "name": "Smartphone X", "category": "Electronics", "brand": "TechCorp", "rating": 4.2, "price": 800, "description": "Next-gen smartphone."}
MOCK_PRODUCT_5 = {"id": "p5", "name": "Desk Lamp", "category": "Home Goods", "brand": "BrightCo", "rating": 3.9, "price": 50, "description": "Modern desk lamp."}

MOCK_ALL_PRODUCTS = [MOCK_PRODUCT_1, MOCK_PRODUCT_2, MOCK_PRODUCT_3, MOCK_PRODUCT_4, MOCK_PRODUCT_5]
MOCK_ELECTRONICS_PRODUCTS = [MOCK_PRODUCT_1, MOCK_PRODUCT_2, MOCK_PRODUCT_4]
MOCK_BOOK_PRODUCTS = [MOCK_PRODUCT_3]
MOCK_TECHCORP_PRODUCTS = [MOCK_PRODUCT_1, MOCK_PRODUCT_4]

MOCK_CATEGORIES = ["Electronics", "Books", "Home Goods"]
MOCK_BRANDS = ["TechCorp", "GameGear", "LiteraryPub", "BrightCo"]


# --- Pytest Fixtures ---
@pytest.fixture
def mock_local_product_service(mocker):
    """
    Fixture to mock LocalProductService.
    All methods of LocalProductService are mocked and their default return values set.
    """
    mock_service = mocker.MagicMock(spec=LocalProductService)

    # Configure default mock return values for methods
    mock_service.search_products.return_value = [MOCK_PRODUCT_1]
    mock_service.get_products.return_value = MOCK_ALL_PRODUCTS
    mock_service.get_categories.return_value = MOCK_CATEGORIES
    mock_service.get_top_rated_products.return_value = [MOCK_PRODUCT_3, MOCK_PRODUCT_1]
    mock_service.get_best_selling_products.return_value = [MOCK_PRODUCT_1, MOCK_PRODUCT_4]
    mock_service.get_products_by_category.return_value = MOCK_ELECTRONICS_PRODUCTS
    mock_service.get_product_details.return_value = MOCK_PRODUCT_1
    mock_service.get_brands.return_value = MOCK_BRANDS
    mock_service.get_products_by_brand.return_value = MOCK_TECHCORP_PRODUCTS
    mock_service.smart_search_products.return_value = ([MOCK_PRODUCT_1], "Smart search results")
    
    # Patch the LocalProductService class itself to return our mock instance
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_service)
    
    return mock_service

@pytest.fixture
def product_data_service(mock_local_product_service):
    """
    Fixture to provide an instance of ProductDataService with a mocked LocalProductService.
    """
    return ProductDataService()


# --- Test Class ---
@pytest.mark.asyncio
class TestProductDataService:

    async def test_init(self, product_data_service, mock_local_product_service, caplog):
        """
        Test ProductDataService initialization.
        Ensures LocalProductService is instantiated and a successful log message is emitted.
        """
        # Re-initialize to capture init logs within the caplog context
        with caplog.at_level(logging.INFO):
            service = ProductDataService()
            assert isinstance(service, ProductDataService)
            # Assert that LocalProductService was instantiated
            mock_local_product_service.assert_called_once()
            # Assert the initialization log message
            assert "ProductDataService initialized with LocalProductService" in caplog.text

    async def test_search_products_success(self, product_data_service, mock_local_product_service):
        """
        Test successful product search.
        Verifies the correct method of LocalProductService is called and returns expected data.
        """
        keyword = "laptop"
        limit = 5
        expected_products = [MOCK_PRODUCT_1]
        mock_local_product_service.search_products.return_value = expected_products

        products = await product_data_service.search_products(keyword, limit)

        mock_local_product_service.search_products.assert_called_once_with(keyword, limit)
        assert products == expected_products
        assert len(products) == 1

    async def test_search_products_no_results(self, product_data_service, mock_local_product_service):
        """
        Test product search with no results found.
        Ensures an empty list is returned.
        """
        keyword = "nonexistent"
        limit = 5
        mock_local_product_service.search_products.return_value = []

        products = await product_data_service.search_products(keyword, limit)

        mock_local_product_service.search_products.assert_called_once_with(keyword, limit)
        assert products == []
        assert len(products) == 0

    async def test_search_products_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test product search when LocalProductService raises an exception.
        Should catch the exception, log an error, and return an empty list.
        """
        keyword = "error_test"
        limit = 5
        mock_local_product_service.search_products.side_effect = Exception("Service unavailable")

        with caplog.at_level(logging.ERROR):
            products = await product_data_service.search_products(keyword, limit)

            mock_local_product_service.search_products.assert_called_once_with(keyword, limit)
            assert products == []
            assert "Error searching products: Service unavailable" in caplog.text

    async def test_get_products_with_search_filter(self, product_data_service, mocker):
        """
        Test get_products method when a 'search' keyword is provided.
        It should delegate to the internal search_products method.
        """
        mock_search = mocker.patch.object(product_data_service, 'search_products', new_callable=AsyncMock)
        mock_search.return_value = [MOCK_PRODUCT_1]

        products = await product_data_service.get_products(search="laptop", limit=5)

        mock_search.assert_called_once_with("laptop", 5)
        assert products == [MOCK_PRODUCT_1]

    async def test_get_products_with_category_filter(self, product_data_service, mocker):
        """
        Test get_products method when a 'category' is provided.
        It should delegate to the internal get_products_by_category method.
        """
        mock_get_by_category = mocker.patch.object(product_data_service, 'get_products_by_category')
        mock_get_by_category.return_value = MOCK_ELECTRONICS_PRODUCTS

        products = await product_data_service.get_products(category="Electronics", limit=10)

        mock_get_by_category.assert_called_once_with("Electronics", 10)
        assert products == MOCK_ELECTRONICS_PRODUCTS

    async def test_get_products_without_filters(self, product_data_service, mocker):
        """
        Test get_products method when no 'search' or 'category' filters are provided.
        It should delegate to the internal get_all_products method.
        """
        mock_get_all = mocker.patch.object(product_data_service, 'get_all_products')
        mock_get_all.return_value = MOCK_ALL_PRODUCTS[:2]

        products = await product_data_service.get_products(limit=2)

        mock_get_all.assert_called_once_with(2)
        assert products == MOCK_ALL_PRODUCTS[:2]

    async def test_get_products_exception_fallback(self, product_data_service, mock_local_product_service, mocker, caplog):
        """
        Test get_products when an internal method (e.g., get_all_products) raises an exception.
        Should log an error and fall back to calling local_service.get_products.
        """
        # Simulate an exception in one of the internal calls
        mocker.patch.object(product_data_service, 'get_all_products', side_effect=Exception("Internal processing error"))
        # Configure the fallback return value for local_service.get_products
        mock_local_product_service.get_products.return_value = [MOCK_PRODUCT_3]

        with caplog.at_level(logging.ERROR):
            products = await product_data_service.get_products(limit=5)

            assert "Error getting products: Internal processing error" in caplog.text
            # Assert that the fallback method was called
            mock_local_product_service.get_products.assert_called_once_with(5)
            assert products == [MOCK_PRODUCT_3]

    async def test_get_categories_success(self, product_data_service, mock_local_product_service):
        """
        Test successful retrieval of categories.
        """
        mock_local_product_service.get_categories.return_value = MOCK_CATEGORIES
        categories = await product_data_service.get_categories()
        mock_local_product_service.get_categories.assert_called_once()
        assert categories == MOCK_CATEGORIES

    async def test_get_categories_no_results(self, product_data_service, mock_local_product_service):
        """
        Test retrieval of categories when no categories are available.
        """
        mock_local_product_service.get_categories.return_value = []
        categories = await product_data_service.get_categories()
        mock_local_product_service.get_categories.assert_called_once()
        assert categories == []

    async def test_get_categories_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test retrieval of categories when LocalProductService raises an exception.
        Should return an empty list and log an error.
        """
        mock_local_product_service.get_categories.side_effect = Exception("Category service down")
        with caplog.at_level(logging.ERROR):
            categories = await product_data_service.get_categories()
            assert categories == []
            assert "Error getting categories: Category service down" in caplog.text

    async def test_get_top_rated_products_success(self, product_data_service, mock_local_product_service):
        """
        Test successful retrieval of top rated products.
        """
        expected_products = [MOCK_PRODUCT_3, MOCK_PRODUCT_1]
        mock_local_product_service.get_top_rated_products.return_value = expected_products
        products = await product_data_service.get_top_rated_products(limit=2)
        mock_local_product_service.get_top_rated_products.assert_called_once_with(2)
        assert products == expected_products

    async def test_get_top_rated_products_no_results(self, product_data_service, mock_local_product_service):
        """
        Test retrieval of top rated products when no results are available.
        """
        mock_local_product_service.get_top_rated_products.return_value = []
        products = await product_data_service.get_top_rated_products(limit=5)
        assert products == []

    async def test_get_top_rated_products_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test retrieval of top rated products when LocalProductService raises an exception.
        Should return an empty list and log an error.
        """
        mock_local_product_service.get_top_rated_products.side_effect = Exception("Rating service error")
        with caplog.at_level(logging.ERROR):
            products = await product_data_service.get_top_rated_products(limit=5)
            assert products == []
            assert "Error getting top rated products: Rating service error" in caplog.text

    async def test_get_best_selling_products_success(self, product_data_service, mock_local_product_service):
        """
        Test successful retrieval of best selling products.
        """
        expected_products = [MOCK_PRODUCT_1, MOCK_PRODUCT_4]
        mock_local_product_service.get_best_selling_products.return_value = expected_products
        products = await product_data_service.get_best_selling_products(limit=2)
        mock_local_product_service.get_best_selling_products.assert_called_once_with(2)
        assert products == expected_products

    async def test_get_best_selling_products_no_results(self, product_data_service, mock_local_product_service):
        """
        Test retrieval of best selling products when no results are available.
        """
        mock_local_product_service.get_best_selling_products.return_value = []
        products = await product_data_service.get_best_selling_products(limit=5)
        assert products == []

    async def test_get_best_selling_products_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test retrieval of best selling products when LocalProductService raises an exception.
        Should return an empty list and log an error.
        """
        mock_local_product_service.get_best_selling_products.side_effect = Exception("Selling service error")
        with caplog.at_level(logging.ERROR):
            products = await product_data_service.get_best_selling_products(limit=5)
            assert products == []
            assert "Error getting best selling products: Selling service error" in caplog.text

    def test_get_products_by_category_success_with_limit(self, product_data_service, mock_local_product_service):
        """
        Test successful retrieval of products by category, respecting the limit.
        """
        mock_local_product_service.get_products_by_category.return_value = MOCK_ELECTRONICS_PRODUCTS # 3 products
        
        products = product_data_service.get_products_by_category("Electronics", limit=2)
        
        mock_local_product_service.get_products_by_category.assert_called_once_with("Electronics")
        assert products == [MOCK_PRODUCT_1, MOCK_PRODUCT_2] # Limited to 2

    def test_get_products_by_category_success_full_results(self, product_data_service, mock_local_product_service):
        """
        Test successful retrieval of products by category when limit is greater than available.
        """
        mock_local_product_service.get_products_by_category.return_value = MOCK_BOOK_PRODUCTS # 1 product
        products = product_data_service.get_products_by_category("Books", limit=5)
        assert products == MOCK_BOOK_PRODUCTS # All 1 product returned

    def test_get_products_by_category_no_results(self, product_data_service, mock_local_product_service):
        """
        Test retrieval of products by category with no results for the given category.
        """
        mock_local_product_service.get_products_by_category.return_value = []
        products = product_data_service.get_products_by_category("NonExistentCategory", limit=10)
        assert products == []

    def test_get_products_by_category_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test retrieval of products by category when LocalProductService raises an exception.
        Should return an empty list and log an error.
        """
        mock_local_product_service.get_products_by_category.side_effect = Exception("Category filter error")
        with caplog.at_level(logging.ERROR):
            products = product_data_service.get_products_by_category("ErrorCat", limit=10)
            assert products == []
            assert "Error getting products by category: Category filter error" in caplog.text

    def test_get_all_products_success_with_limit(self, product_data_service, mock_local_product_service):
        """
        Test successful retrieval of all products, passing the limit to the local service.
        """
        # Reset mock to configure for this specific test
        mock_local_product_service.get_products.reset_mock() 
        # Simulate local service returning products up to the requested limit
        mock_local_product_service.get_products.return_value = MOCK_ALL_PRODUCTS[:2]
        
        products = product_data_service.get_all_products(limit=2)
        
        mock_local_product_service.get_products.assert_called_once_with(2)
        assert products == MOCK_ALL_PRODUCTS[:2]

    def test_get_all_products_success_full_results(self, product_data_service, mock_local_product_service):
        """
        Test successful retrieval of all products when limit is greater than total products.
        """
        mock_local_product_service.get_products.reset_mock()
        mock_local_product_service.get_products.return_value = MOCK_ALL_PRODUCTS
        products = product_data_service.get_all_products(limit=10) # Request more than available
        
        mock_local_product_service.get_products.assert_called_once_with(10)
        assert products == MOCK_ALL_PRODUCTS

    def test_get_all_products_no_results(self, product_data_service, mock_local_product_service):
        """
        Test retrieval of all products when no products are available.
        """
        mock_local_product_service.get_products.return_value = []
        products = product_data_service.get_all_products(limit=10)
        assert products == []

    def test_get_all_products_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test retrieval of all products when LocalProductService raises an exception.
        Should return an empty list and log an error.
        """
        mock_local_product_service.get_products.side_effect = Exception("All products error")
        with caplog.at_level(logging.ERROR):
            products = product_data_service.get_all_products(limit=10)
            assert products == []
            assert "Error getting all products: All products error" in caplog.text

    def test_get_product_details_success(self, product_data_service, mock_local_product_service):
        """
        Test successful retrieval of product details by ID.
        """
        product_id = "p1"
        mock_local_product_service.get_product_details.return_value = MOCK_PRODUCT_1
        details = product_data_service.get_product_details(product_id)
        mock_local_product_service.get_product_details.assert_called_once_with(product_id)
        assert details == MOCK_PRODUCT_1

    def test_get_product_details_not_found(self, product_data_service, mock_local_product_service):
        """
        Test retrieval of product details for a non-existent ID.
        Should return None.
        """
        product_id = "non_existent_id"
        mock_local_product_service.get_product_details.return_value = None
        details = product_data_service.get_product_details(product_id)
        assert details is None

    def test_get_product_details_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test retrieval of product details when LocalProductService raises an exception.
        Should return None and log an error.
        """
        product_id = "error_id"
        mock_local_product_service.get_product_details.side_effect = Exception("Details service error")
        with caplog.at_level(logging.ERROR):
            details = product_data_service.get_product_details(product_id)
            assert details is None
            assert "Error getting product details: Details service error" in caplog.text

    def test_get_brands_success(self, product_data_service, mock_local_product_service):
        """
        Test successful retrieval of available brands.
        """
        mock_local_product_service.get_brands.return_value = MOCK_BRANDS
        brands = product_data_service.get_brands()
        mock_local_product_service.get_brands.assert_called_once()
        assert brands == MOCK_BRANDS

    def test_get_brands_no_results(self, product_data_service, mock_local_product_service):
        """
        Test retrieval of brands when no brands are available.
        """
        mock_local_product_service.get_brands.return_value = []
        brands = product_data_service.get_brands()
        assert brands == []

    def test_get_brands_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test retrieval of brands when LocalProductService raises an exception.
        Should return an empty list and log an error.
        """
        mock_local_product_service.get_brands.side_effect = Exception("Brands service down")
        with caplog.at_level(logging.ERROR):
            brands = product_data_service.get_brands()
            assert brands == []
            assert "Error getting brands: Brands service down" in caplog.text

    def test_get_products_by_brand_success_with_limit(self, product_data_service, mock_local_product_service):
        """
        Test successful retrieval of products by brand, respecting the limit.
        """
        mock_local_product_service.get_products_by_brand.return_value = MOCK_TECHCORP_PRODUCTS # 2 products
        
        products = product_data_service.get_products_by_brand("TechCorp", limit=1)
        
        mock_local_product_service.get_products_by_brand.assert_called_once_with("TechCorp")
        assert products == [MOCK_PRODUCT_1] # Limited to 1

    def test_get_products_by_brand_success_full_results(self, product_data_service, mock_local_product_service):
        """
        Test successful retrieval of products by brand when limit is greater than available.
        """
        mock_local_product_service.get_products_by_brand.return_value = MOCK_TECHCORP_PRODUCTS
        products = product_data_service.get_products_by_brand("TechCorp", limit=5)
        assert products == MOCK_TECHCORP_PRODUCTS # All 2 products returned

    def test_get_products_by_brand_no_results(self, product_data_service, mock_local_product_service):
        """
        Test retrieval of products by brand with no results for the given brand.
        """
        mock_local_product_service.get_products_by_brand.return_value = []
        products = product_data_service.get_products_by_brand("NonExistentBrand", limit=10)
        assert products == []

    def test_get_products_by_brand_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test retrieval of products by brand when LocalProductService raises an exception.
        Should return an empty list and log an error.
        """
        mock_local_product_service.get_products_by_brand.side_effect = Exception("Brand filter error")
        with caplog.at_level(logging.ERROR):
            products = product_data_service.get_products_by_brand("ErrorBrand", limit=10)
            assert products == []
            assert "Error getting products by brand: Brand filter error" in caplog.text

    async def test_smart_search_products_success(self, product_data_service, mock_local_product_service):
        """
        Test successful smart search with various parameters.
        Verifies correct delegation to LocalProductService and returns its output.
        """
        keyword = "smart"
        category = "Electronics"
        max_price = 500
        limit = 2
        expected_products = [MOCK_PRODUCT_2, MOCK_PRODUCT_4]
        expected_message = "Smart search completed."
        
        mock_local_product_service.smart_search_products.return_value = (expected_products, expected_message)

        products, message = await product_data_service.smart_search_products(
            keyword=keyword, category=category, max_price=max_price, limit=limit
        )

        mock_local_product_service.smart_search_products.assert_called_once_with(
            keyword, category, max_price, limit
        )
        assert products == expected_products
        assert message == expected_message

    async def test_smart_search_products_no_results(self, product_data_service, mock_local_product_service):
        """
        Test smart search when no products are found.
        """
        keyword = "empty search"
        mock_local_product_service.smart_search_products.return_value = ([], "No results found for your query.")

        products, message = await product_data_service.smart_search_products(keyword=keyword)

        assert products == []
        assert message == "No results found for your query."

    async def test_smart_search_products_exception(self, product_data_service, mock_local_product_service):
        """
        Test smart search when LocalProductService raises an exception.
        The ProductDataService does NOT handle exceptions for this method,
        so the test expects the exception to propagate.
        """
        mock_local_product_service.smart_search_products.side_effect = Exception("Smart search backend error")

        with pytest.raises(Exception, match="Smart search backend error"):
            await product_data_service.smart_search_products(keyword="error")

        mock_local_product_service.smart_search_products.assert_called_once()