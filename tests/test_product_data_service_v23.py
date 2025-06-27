import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
import logging

# Assuming the path for the module under test
from app.services.product_data_service import ProductDataService

# Fixture to set up logging and capture messages
@pytest.fixture(autouse=True)
def setup_logging(caplog):
    """Configures logging to capture all INFO and ERROR messages during tests."""
    caplog.set_level(logging.INFO)
    yield

@pytest.fixture
def mock_local_service(mocker):
    """
    Fixture to mock the LocalProductService class.
    Mocks the class itself, so any instantiation of LocalProductService
    within ProductDataService will return this mock object.
    """
    mock_service_instance = mocker.Mock()
    
    # Set default return values for common methods
    mock_service_instance.search_products.return_value = []
    mock_service_instance.get_products.return_value = []
    mock_service_instance.get_categories.return_value = []
    mock_service_instance.get_top_rated_products.return_value = []
    mock_service_instance.get_best_selling_products.return_value = []
    mock_service_instance.get_products_by_category.return_value = []
    mock_service_instance.get_product_details.return_value = None
    mock_service_instance.get_brands.return_value = []
    mock_service_instance.get_products_by_brand.return_value = []
    mock_service_instance.smart_search_products.return_value = ([], "No results.")

    # Patch the LocalProductService class to return our mock instance
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_service_instance)
    
    return mock_service_instance # Return the mock instance that ProductDataService will use

@pytest.fixture
def product_data_service(mock_local_service):
    """Fixture to provide a ProductDataService instance with its dependencies mocked."""
    return ProductDataService()

@pytest.mark.asyncio
class TestProductDataService:
    """
    Comprehensive test suite for the ProductDataService class,
    covering success, edge, and error cases for all its methods.
    """

    async def test_init(self, mock_local_service, caplog):
        """
        Test ProductDataService initialization.
        Ensures LocalProductService is instantiated and a log message is recorded.
        """
        service = ProductDataService()
        mock_local_service.assert_called_once()
        assert service.local_service is mock_local_service
        assert "ProductDataService initialized with LocalProductService" in caplog.text

    async def test_search_products_success(self, product_data_service, mock_local_service, caplog):
        """Test search_products returns data successfully."""
        expected_products = [{"id": "1", "name": "Product A", "price": 10.0}]
        mock_local_service.search_products.return_value = expected_products
        
        products = await product_data_service.search_products("test_keyword", limit=5)
        
        mock_local_service.search_products.assert_called_once_with("test_keyword", 5)
        assert products == expected_products
        assert f"Found {len(expected_products)} products for keyword: test_keyword" in caplog.text
        assert caplog.records[-1].levelname == "INFO"

    async def test_search_products_no_results(self, product_data_service, mock_local_service, caplog):
        """Test search_products returns an empty list when no results are found."""
        mock_local_service.search_products.return_value = []
        
        products = await product_data_service.search_products("nonexistent_keyword")
        
        mock_local_service.search_products.assert_called_once_with("nonexistent_keyword", 10) # Default limit
        assert products == []
        assert "Found 0 products for keyword: nonexistent_keyword" in caplog.text
        assert caplog.records[-1].levelname == "INFO"

    async def test_search_products_exception(self, product_data_service, mock_local_service, caplog):
        """Test search_products handles exceptions from LocalProductService and returns an empty list."""
        mock_local_service.search_products.side_effect = Exception("Mocked search error")
        
        products = await product_data_service.search_products("error_keyword")
        
        mock_local_service.search_products.assert_called_once_with("error_keyword", 10)
        assert products == []
        assert "Error searching products: Mocked search error" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

    async def test_get_products_with_search_param(self, product_data_service, mock_local_service, mocker):
        """
        Test get_products delegates to search_products when 'search' parameter is provided.
        Mocks the internal call to self.search_products.
        """
        expected_products = [{"id": "2", "name": "Search Result"}]
        mocker.patch.object(product_data_service, 'search_products', AsyncMock(return_value=expected_products))
        
        products = await product_data_service.get_products(search="query", limit=7)
        
        product_data_service.search_products.assert_called_once_with("query", 7)
        assert products == expected_products
        mock_local_service.get_products.assert_not_called() # Ensure fallback is not called

    async def test_get_products_with_search_param_error_fallback(self, product_data_service, mock_local_service, mocker, caplog):
        """
        Test get_products falls back to local_service.get_products if search_products fails.
        """
        mocker.patch.object(product_data_service, 'search_products', AsyncMock(side_effect=Exception("Search failed internally")))
        fallback_products = [{"id": "fallback", "name": "Fallback Prod"}]
        mock_local_service.get_products.return_value = fallback_products

        products = await product_data_service.get_products(search="query", limit=5)
        
        product_data_service.search_products.assert_called_once_with("query", 5)
        mock_local_service.get_products.assert_called_once_with(5)
        assert products == fallback_products
        assert "Error getting products: Search failed internally" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

    async def test_get_products_with_category_param(self, product_data_service, mock_local_service, mocker):
        """
        Test get_products delegates to get_products_by_category when 'category' parameter is provided
        (and 'search' is None).
        """
        expected_products = [{"id": "3", "name": "Category Prod"}]
        mocker.patch.object(product_data_service, 'get_products_by_category', Mock(return_value=expected_products))
        
        products = await product_data_service.get_products(category="electronics", limit=8)
        
        product_data_service.get_products_by_category.assert_called_once_with("electronics", 8)
        assert products == expected_products
        mock_local_service.get_products.assert_not_called() # Ensure fallback is not called

    async def test_get_products_with_category_param_error_fallback(self, product_data_service, mock_local_service, mocker, caplog):
        """
        Test get_products falls back to local_service.get_products if get_products_by_category fails.
        """
        mocker.patch.object(product_data_service, 'get_products_by_category', Mock(side_effect=Exception("Category failed internally")))
        fallback_products = [{"id": "fallback_cat", "name": "Fallback Cat Prod"}]
        mock_local_service.get_products.return_value = fallback_products

        products = await product_data_service.get_products(category="electronics", limit=12)
        
        product_data_service.get_products_by_category.assert_called_once_with("electronics", 12)
        mock_local_service.get_products.assert_called_once_with(12)
        assert products == fallback_products
        assert "Error getting products: Category failed internally" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

    async def test_get_products_default(self, product_data_service, mock_local_service, mocker):
        """
        Test get_products delegates to get_all_products when neither 'search' nor 'category' is provided.
        """
        expected_products = [{"id": "4", "name": "All Products"}]
        mocker.patch.object(product_data_service, 'get_all_products', Mock(return_value=expected_products))
        
        products = await product_data_service.get_products(limit=15)
        
        product_data_service.get_all_products.assert_called_once_with(15)
        assert products == expected_products
        mock_local_service.get_products.assert_not_called() # Ensure fallback is not called

    async def test_get_products_default_error_fallback(self, product_data_service, mock_local_service, mocker, caplog):
        """
        Test get_products falls back to local_service.get_products if get_all_products fails.
        """
        mocker.patch.object(product_data_service, 'get_all_products', Mock(side_effect=Exception("All products failed internally")))
        fallback_products = [{"id": "fallback_all", "name": "Fallback All Prod"}]
        mock_local_service.get_products.return_value = fallback_products

        products = await product_data_service.get_products(limit=20)
        
        product_data_service.get_all_products.assert_called_once_with(20)
        mock_local_service.get_products.assert_called_once_with(20)
        assert products == fallback_products
        assert "Error getting products: All products failed internally" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

    async def test_get_categories_success(self, product_data_service, mock_local_service, caplog):
        """Test get_categories returns data successfully."""
        expected_categories = ["Electronics", "Books", "Home"]
        mock_local_service.get_categories.return_value = expected_categories
        
        categories = await product_data_service.get_categories()
        
        mock_local_service.get_categories.assert_called_once()
        assert categories == expected_categories
        assert caplog.records[-1].levelname == "INFO"

    async def test_get_categories_no_results(self, product_data_service, mock_local_service, caplog):
        """Test get_categories returns an empty list when no categories are found."""
        mock_local_service.get_categories.return_value = []
        
        categories = await product_data_service.get_categories()
        
        mock_local_service.get_categories.assert_called_once()
        assert categories == []
        assert caplog.records[-1].levelname == "INFO"

    async def test_get_categories_exception(self, product_data_service, mock_local_service, caplog):
        """Test get_categories handles exceptions and returns an empty list."""
        mock_local_service.get_categories.side_effect = Exception("Category fetch error")
        
        categories = await product_data_service.get_categories()
        
        mock_local_service.get_categories.assert_called_once()
        assert categories == []
        assert "Error getting categories: Category fetch error" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

    async def test_get_top_rated_products_success(self, product_data_service, mock_local_service):
        """Test get_top_rated_products returns data successfully."""
        expected_products = [{"id": "5", "rating": 4.9}, {"id": "6", "rating": 4.8}]
        mock_local_service.get_top_rated_products.return_value = expected_products
        
        products = await product_data_service.get_top_rated_products(limit=2)
        
        mock_local_service.get_top_rated_products.assert_called_once_with(2)
        assert products == expected_products

    async def test_get_top_rated_products_exception(self, product_data_service, mock_local_service, caplog):
        """Test get_top_rated_products handles exceptions and returns an empty list."""
        mock_local_service.get_top_rated_products.side_effect = Exception("Top rated fetch failed")
        
        products = await product_data_service.get_top_rated_products()
        
        assert products == []
        assert "Error getting top rated products: Top rated fetch failed" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

    async def test_get_best_selling_products_success(self, product_data_service, mock_local_service):
        """Test get_best_selling_products returns data successfully."""
        expected_products = [{"id": "7", "sales_count": 1000}, {"id": "8", "sales_count": 900}]
        mock_local_service.get_best_selling_products.return_value = expected_products
        
        products = await product_data_service.get_best_selling_products(limit=2)
        
        mock_local_service.get_best_selling_products.assert_called_once_with(2)
        assert products == expected_products

    async def test_get_best_selling_products_exception(self, product_data_service, mock_local_service, caplog):
        """Test get_best_selling_products handles exceptions and returns an empty list."""
        mock_local_service.get_best_selling_products.side_effect = Exception("Best selling fetch failed")
        
        products = await product_data_service.get_best_selling_products()
        
        assert products == []
        assert "Error getting best selling products: Best selling fetch failed" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

    def test_get_products_by_category_success_with_limit(self, product_data_service, mock_local_service):
        """Test get_products_by_category returns sliced data based on limit."""
        all_products_in_category = [
            {"id": "C1", "category": "books"}, 
            {"id": "C2", "category": "books"}, 
            {"id": "C3", "category": "books"}
        ]
        mock_local_service.get_products_by_category.return_value = all_products_in_category
        
        products = product_data_service.get_products_by_category("books", limit=2)
        
        mock_local_service.get_products_by_category.assert_called_once_with("books")
        assert products == [{"id": "C1", "category": "books"}, {"id": "C2", "category": "books"}]
        assert len(products) == 2

    def test_get_products_by_category_success_no_limit_applied(self, product_data_service, mock_local_service):
        """Test get_products_by_category returns all available if limit is higher than count."""
        all_products_in_category = [
            {"id": "C1", "category": "books"}, 
            {"id": "C2", "category": "books"}
        ]
        mock_local_service.get_products_by_category.return_value = all_products_in_category
        
        products = product_data_service.get_products_by_category("books", limit=10) # Default limit is 10
        
        mock_local_service.get_products_by_category.assert_called_once_with("books")
        assert products == all_products_in_category
        assert len(products) == 2

    def test_get_products_by_category_no_results(self, product_data_service, mock_local_service):
        """Test get_products_by_category returns empty list when no products found for category."""
        mock_local_service.get_products_by_category.return_value = []
        
        products = product_data_service.get_products_by_category("non_existent_category")
        
        assert products == []

    def test_get_products_by_category_exception(self, product_data_service, mock_local_service, caplog):
        """Test get_products_by_category handles exceptions and returns an empty list."""
        mock_local_service.get_products_by_category.side_effect = Exception("Category products fetch failed")
        
        products = product_data_service.get_products_by_category("error_category")
        
        assert products == []
        assert "Error getting products by category: Category products fetch failed" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

    def test_get_all_products_success(self, product_data_service, mock_local_service):
        """Test get_all_products returns data successfully, passing limit to local service."""
        expected_products = [{"id": "A1"}, {"id": "A2"}, {"id": "A3"}]
        mock_local_service.get_products.return_value = expected_products
        
        products = product_data_service.get_all_products(limit=3)
        
        mock_local_service.get_products.assert_called_once_with(3)
        assert products == expected_products

    def test_get_all_products_exception(self, product_data_service, mock_local_service, caplog):
        """Test get_all_products handles exceptions and returns an empty list."""
        mock_local_service.get_products.side_effect = Exception("All products fetch failed")
        
        products = product_data_service.get_all_products()
        
        assert products == []
        assert "Error getting all products: All products fetch failed" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

    def test_get_product_details_success(self, product_data_service, mock_local_service):
        """Test get_product_details returns details for a valid ID."""
        expected_details = {"id": "P123", "name": "Specific Product", "price": 99.99}
        mock_local_service.get_product_details.return_value = expected_details
        
        details = product_data_service.get_product_details("P123")
        
        mock_local_service.get_product_details.assert_called_once_with("P123")
        assert details == expected_details

    def test_get_product_details_not_found(self, product_data_service, mock_local_service):
        """Test get_product_details returns None if product is not found."""
        mock_local_service.get_product_details.return_value = None # This is the default mock behavior
        
        details = product_data_service.get_product_details("NonExistentID")
        
        mock_local_service.get_product_details.assert_called_once_with("NonExistentID")
        assert details is None

    def test_get_product_details_exception(self, product_data_service, mock_local_service, caplog):
        """Test get_product_details handles exceptions and returns None."""
        mock_local_service.get_product_details.side_effect = Exception("Details fetch error")
        
        details = product_data_service.get_product_details("ErrorID")
        
        assert details is None
        assert "Error getting product details: Details fetch error" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

    def test_get_brands_success(self, product_data_service, mock_local_service):
        """Test get_brands returns data successfully."""
        expected_brands = ["BrandX", "BrandY", "BrandZ"]
        mock_local_service.get_brands.return_value = expected_brands
        
        brands = product_data_service.get_brands()
        
        mock_local_service.get_brands.assert_called_once()
        assert brands == expected_brands

    def test_get_brands_no_results(self, product_data_service, mock_local_service):
        """Test get_brands returns empty list when no brands found."""
        mock_local_service.get_brands.return_value = []
        
        brands = product_data_service.get_brands()
        
        assert brands == []

    def test_get_brands_exception(self, product_data_service, mock_local_service, caplog):
        """Test get_brands handles exceptions and returns an empty list."""
        mock_local_service.get_brands.side_effect = Exception("Brands fetch error")
        
        brands = product_data_service.get_brands()
        
        assert brands == []
        assert "Error getting brands: Brands fetch error" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

    def test_get_products_by_brand_success_with_limit(self, product_data_service, mock_local_service):
        """Test get_products_by_brand returns sliced data based on limit."""
        all_products_by_brand = [
            {"id": "B1", "brand": "BrandA"}, 
            {"id": "B2", "brand": "BrandA"}, 
            {"id": "B3", "brand": "BrandA"}
        ]
        mock_local_service.get_products_by_brand.return_value = all_products_by_brand
        
        products = product_data_service.get_products_by_brand("BrandA", limit=2)
        
        mock_local_service.get_products_by_brand.assert_called_once_with("BrandA")
        assert products == [{"id": "B1", "brand": "BrandA"}, {"id": "B2", "brand": "BrandA"}]
        assert len(products) == 2

    def test_get_products_by_brand_success_no_limit_applied(self, product_data_service, mock_local_service):
        """Test get_products_by_brand returns all available if limit is higher than count."""
        all_products_by_brand = [
            {"id": "B1", "brand": "BrandA"}, 
            {"id": "B2", "brand": "BrandA"}
        ]
        mock_local_service.get_products_by_brand.return_value = all_products_by_brand
        
        products = product_data_service.get_products_by_brand("BrandA", limit=10) # Default limit is 10
        
        mock_local_service.get_products_by_brand.assert_called_once_with("BrandA")
        assert products == all_products_by_brand
        assert len(products) == 2

    def test_get_products_by_brand_no_results(self, product_data_service, mock_local_service):
        """Test get_products_by_brand returns empty list when no products found for brand."""
        mock_local_service.get_products_by_brand.return_value = []
        
        products = product_data_service.get_products_by_brand("non_existent_brand")
        
        assert products == []

    def test_get_products_by_brand_exception(self, product_data_service, mock_local_service, caplog):
        """Test get_products_by_brand handles exceptions and returns an empty list."""
        mock_local_service.get_products_by_brand.side_effect = Exception("Brand products fetch failed")
        
        products = product_data_service.get_products_by_brand("error_brand")
        
        assert products == []
        assert "Error getting products by brand: Brand products fetch failed" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

    async def test_smart_search_products_success_default_params(self, product_data_service, mock_local_service):
        """Test smart_search_products with default parameters."""
        expected_products = [{"id": "S1", "name": "Smart Product"}]
        expected_message = "Smart search completed."
        mock_local_service.smart_search_products.return_value = (expected_products, expected_message)
        
        products, message = await product_data_service.smart_search_products(keyword="smart")
        
        mock_local_service.smart_search_products.assert_called_once_with("smart", None, None, 5)
        assert products == expected_products
        assert message == expected_message

    async def test_smart_search_products_success_all_params(self, product_data_service, mock_local_service):
        """Test smart_search_products with all parameters provided."""
        expected_products = [{"id": "S2", "name": "Specific Smart"}]
        expected_message = "Specific search results."
        mock_local_service.smart_search_products.return_value = (expected_products, expected_message)
        
        products, message = await product_data_service.smart_search_products(
            keyword="specific", category="tools", max_price=50, limit=1
        )
        
        mock_local_service.smart_search_products.assert_called_once_with("specific", "tools", 50, 1)
        assert products == expected_products
        assert message == expected_message

    async def test_smart_search_products_no_results(self, product_data_service, mock_local_service):
        """Test smart_search_products returns no results."""
        mock_local_service.smart_search_products.return_value = ([], "No results for 'no match'.")
        
        products, message = await product_data_service.smart_search_products(keyword="no match")
        
        assert products == []
        assert message == "No results for 'no match'."

    async def test_smart_search_products_exception(self, product_data_service, mock_local_service):
        """
        Test smart_search_products propagates exceptions as it does not contain its own try-except block.
        """
        mock_local_service.smart_search_products.side_effect = Exception("Smart search internal error")
        
        with pytest.raises(Exception, match="Smart search internal error"):
            await product_data_service.smart_search_products(keyword="error")
        
        mock_local_service.smart_search_products.assert_called_once_with("error", None, None, 5)