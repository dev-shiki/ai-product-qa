import pytest
import asyncio
import logging
from unittest.mock import MagicMock, patch, AsyncMock

# Adjust the import path as necessary based on your project structure
# Assuming the tests are run from the project root or configured correctly for module imports
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService

# --- Fixtures ---

@pytest.fixture
def mock_local_service(mocker):
    """
    Mocks LocalProductService and returns the mock object.
    Sets default return values for all methods to ensure predictable behavior
    and avoid AttributeError if a method is called unexpectedly.
    """
    mock = mocker.MagicMock(spec=LocalProductService)
    mock.get_products.return_value = []
    mock.search_products.return_value = []
    mock.get_categories.return_value = []
    mock.get_top_rated_products.return_value = []
    mock.get_best_selling_products.return_value = []
    mock.get_products_by_category.return_value = []
    mock.get_product_details.return_value = None
    mock.get_brands.return_value = []
    mock.get_products_by_brand.return_value = []
    # smart_search_products returns a tuple (list, string)
    mock.smart_search_products.return_value = ([], "No results.")
    return mock

@pytest.fixture
def product_data_service(mocker, mock_local_service):
    """
    Fixture that provides an instance of ProductDataService
    with LocalProductService mocked out.
    """
    # Patch LocalProductService where it's imported in product_data_service.py
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service)
    service = ProductDataService()
    return service

# --- Tests ---

class TestProductDataService:

    def test_init(self, product_data_service, mock_local_service, caplog):
        """
        Test the initialization of ProductDataService.
        Ensures LocalProductService is correctly assigned and an info log is generated.
        """
        # The product_data_service fixture already initializes the service
        assert product_data_service.local_service is mock_local_service
        with caplog.at_level(logging.INFO):
            # Check if the log message from initialization is present
            assert "ProductDataService initialized with LocalProductService" in caplog.text

    @pytest.mark.asyncio
    async def test_search_products_success(self, product_data_service, mock_local_service, caplog):
        """
        Test successful product search using a keyword and limit.
        Ensures correct arguments are passed and results are returned, with info logs.
        """
        mock_products = [
            {"id": "1", "name": "Laptop X", "price": 1200},
            {"id": "2", "name": "Laptop Y", "price": 1500}
        ]
        mock_local_service.search_products.return_value = mock_products

        with caplog.at_level(logging.INFO):
            result = await product_data_service.search_products("laptop", limit=2)

            assert result == mock_products
            mock_local_service.search_products.assert_called_once_with("laptop", 2)
            assert f"Searching products with keyword: laptop" in caplog.text
            assert f"Found {len(mock_products)} products for keyword: laptop" in caplog.text

    @pytest.mark.asyncio
    async def test_search_products_no_results(self, product_data_service, mock_local_service):
        """
        Test product search when no products match the keyword.
        Ensures an empty list is returned.
        """
        mock_local_service.search_products.return_value = []
        result = await product_data_service.search_products("nonexistent", limit=5)
        assert result == []
        mock_local_service.search_products.assert_called_once_with("nonexistent", 5)

    @pytest.mark.asyncio
    async def test_search_products_error(self, product_data_service, mock_local_service, caplog):
        """
        Test product search when an underlying error occurs in LocalProductService.
        Ensures an empty list is returned and an error message is logged.
        """
        mock_local_service.search_products.side_effect = Exception("Simulated network error during search")

        with caplog.at_level(logging.ERROR):
            result = await product_data_service.search_products("error_test", limit=10)

            assert result == []
            mock_local_service.search_products.assert_called_once_with("error_test", 10)
            assert "Error searching products: Simulated network error during search" in caplog.text

    @pytest.mark.asyncio
    async def test_get_products_with_search_filter(self, product_data_service, mock_local_service):
        """
        Test get_products when 'search' parameter is provided.
        Ensures that it delegates to search_products with correct arguments.
        """
        mock_products_from_search = [{"id": "s1", "name": "Search Item"}]
        # Mock what product_data_service.search_products (which uses mock_local_service.search_products) returns
        mock_local_service.search_products.return_value = mock_products_from_search

        result = await product_data_service.get_products(search="query", limit=5)

        assert result == mock_products_from_search
        mock_local_service.search_products.assert_called_once_with("query", 5)
        # Verify that other paths were not taken
        mock_local_service.get_products_by_category.assert_not_called()
        mock_local_service.get_products.assert_not_called() # For get_all_products path


    @pytest.mark.asyncio
    async def test_get_products_with_category_filter(self, product_data_service, mock_local_service):
        """
        Test get_products when 'category' parameter is provided (and search is None).
        Ensures it delegates to get_products_by_category and applies the limit.
        """
        # Return more items than limit to test the slicing logic within ProductDataService
        mock_products_long = [{"id": f"c{i}", "category": "electronics"} for i in range(15)]
        mock_local_service.get_products_by_category.return_value = mock_products_long

        result = await product_data_service.get_products(category="electronics", limit=10)

        assert len(result) == 10
        assert result == mock_products_long[:10]
        mock_local_service.get_products_by_category.assert_called_once_with("electronics")
        # Verify that other paths were not taken
        mock_local_service.search_products.assert_not_called()
        mock_local_service.get_products.assert_not_called() # For get_all_products path

    @pytest.mark.asyncio
    async def test_get_products_with_no_filters(self, product_data_service, mock_local_service):
        """
        Test get_products when neither 'search' nor 'category' filters are provided.
        Ensures it delegates to get_all_products and applies the limit.
        """
        # Return more items than limit to test the limit application within ProductDataService
        mock_products_long = [{"id": f"a{i}", "name": "Product"} for i in range(25)]
        mock_local_service.get_products.return_value = mock_products_long # get_all_products uses local_service.get_products

        result = await product_data_service.get_products(limit=20)

        assert len(result) == 20
        assert result == mock_products_long[:20]
        mock_local_service.get_products.assert_called_once_with(20) # get_all_products passes limit
        # Verify that other paths were not taken
        mock_local_service.search_products.assert_not_called()
        mock_local_service.get_products_by_category.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_products_error_fallback(self, product_data_service, mock_local_service, caplog):
        """
        Test get_products error handling. If an error occurs in any of the internal
        delegated calls (search, category, or all), it should fall back to
        local_service.get_products and log the error.
        """
        # Simulate an error in the search path for get_products
        mock_local_service.search_products.side_effect = Exception("Simulated internal search error")
        
        # This will be the return value for the fallback call: self.local_service.get_products(limit)
        fallback_products = [{"id": "fb1", "name": "Fallback Product"}]
        mock_local_service.get_products.return_value = fallback_products

        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_products(search="error_trigger", limit=15)
            
            assert result == fallback_products
            mock_local_service.search_products.assert_called_once_with("error_trigger", 15)
            mock_local_service.get_products.assert_called_once_with(15) # Fallback call
            assert "Error getting products: Simulated internal search error" in caplog.text


    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service, mock_local_service, caplog):
        """
        Test successful retrieval of available product categories.
        """
        mock_categories = ["Electronics", "Books", "Clothing", "Home & Kitchen"]
        mock_local_service.get_categories.return_value = mock_categories

        result = await product_data_service.get_categories()

        assert result == mock_categories
        mock_local_service.get_categories.assert_called_once()
        assert "Error getting categories" not in caplog.text # Ensure no error logged

    @pytest.mark.asyncio
    async def test_get_categories_error(self, product_data_service, mock_local_service, caplog):
        """
        Test get_categories when an error occurs in LocalProductService.
        Ensures an empty list is returned and an error message is logged.
        """
        mock_local_service.get_categories.side_effect = Exception("Category fetch API error")

        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_categories()

            assert result == []
            mock_local_service.get_categories.assert_called_once()
            assert "Error getting categories: Category fetch API error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service, mock_local_service, caplog):
        """
        Test successful retrieval of top-rated products.
        """
        mock_products = [{"id": "tr1", "rating": 5, "name": "Highly Rated"}]
        mock_local_service.get_top_rated_products.return_value = mock_products

        result = await product_data_service.get_top_rated_products(limit=5)

        assert result == mock_products
        mock_local_service.get_top_rated_products.assert_called_once_with(5)
        assert "Error getting top rated products" not in caplog.text

    @pytest.mark.asyncio
    async def test_get_top_rated_products_error(self, product_data_service, mock_local_service, caplog):
        """
        Test get_top_rated_products when an error occurs.
        Ensures an empty list is returned and error is logged.
        """
        mock_local_service.get_top_rated_products.side_effect = Exception("Top rated service error")

        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_top_rated_products(limit=5)

            assert result == []
            mock_local_service.get_top_rated_products.assert_called_once_with(5)
            assert "Error getting top rated products: Top rated service error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service, mock_local_service, caplog):
        """
        Test successful retrieval of best-selling products.
        """
        mock_products = [{"id": "bs1", "sales": 1000, "name": "Best Seller"}]
        mock_local_service.get_best_selling_products.return_value = mock_products

        result = await product_data_service.get_best_selling_products(limit=5)

        assert result == mock_products
        mock_local_service.get_best_selling_products.assert_called_once_with(5)
        assert "Error getting best selling products" not in caplog.text

    @pytest.mark.asyncio
    async def test_get_best_selling_products_error(self, product_data_service, mock_local_service, caplog):
        """
        Test get_best_selling_products when an error occurs.
        Ensures an empty list is returned and error is logged.
        """
        mock_local_service.get_best_selling_products.side_effect = Exception("Best selling service error")

        with caplog.at_level(logging.ERROR):
            result = await product_data_service.get_best_selling_products(limit=5)

            assert result == []
            mock_local_service.get_best_selling_products.assert_called_once_with(5)
            assert "Error getting best selling products: Best selling service error" in caplog.text

    def test_get_products_by_category_success(self, product_data_service, mock_local_service, caplog):
        """
        Test successful retrieval of products by category, respecting the limit.
        """
        # Return more items than limit to verify slicing
        mock_products_long = [{"id": f"c{i}", "category": "books"} for i in range(15)]
        mock_local_service.get_products_by_category.return_value = mock_products_long

        result = product_data_service.get_products_by_category("books", limit=10)

        assert len(result) == 10
        assert result == mock_products_long[:10]
        mock_local_service.get_products_by_category.assert_called_once_with("books")
        assert "Error getting products by category" not in caplog.text

    def test_get_products_by_category_no_results(self, product_data_service, mock_local_service):
        """
        Test retrieval of products by category when no products match.
        Ensures an empty list is returned.
        """
        mock_local_service.get_products_by_category.return_value = []
        result = product_data_service.get_products_by_category("nonexistent_cat", limit=5)
        assert result == []
        mock_local_service.get_products_by_category.assert_called_once_with("nonexistent_cat")

    def test_get_products_by_category_limit_exceeds_available(self, product_data_service, mock_local_service):
        """
        Test retrieval of products by category when the limit is higher than available products.
        Ensures all available products are returned (not padded).
        """
        mock_products_short = [{"id": "c1", "category": "toys"}, {"id": "c2", "category": "toys"}]
        mock_local_service.get_products_by_category.return_value = mock_products_short

        result = product_data_service.get_products_by_category("toys", limit=5)

        assert len(result) == 2
        assert result == mock_products_short
        mock_local_service.get_products_by_category.assert_called_once_with("toys")

    def test_get_products_by_category_error(self, product_data_service, mock_local_service, caplog):
        """
        Test get_products_by_category when an error occurs.
        Ensures an empty list is returned and error is logged.
        """
        mock_local_service.get_products_by_category.side_effect = Exception("Category data error")

        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_products_by_category("error_cat", limit=10)

            assert result == []
            mock_local_service.get_products_by_category.assert_called_once_with("error_cat")
            assert "Error getting products by category: Category data error" in caplog.text

    def test_get_all_products_success(self, product_data_service, mock_local_service, caplog):
        """
        Test successful retrieval of all products, respecting the limit.
        """
        # Return more items than limit to verify slicing
        mock_products_long = [{"id": f"p{i}", "name": f"Product {i}"} for i in range(30)]
        mock_local_service.get_products.return_value = mock_products_long

        result = product_data_service.get_all_products(limit=20)

        assert len(result) == 20
        assert result == mock_products_long[:20]
        mock_local_service.get_products.assert_called_once_with(20)
        assert "Error getting all products" not in caplog.text

    def test_get_all_products_no_results(self, product_data_service, mock_local_service):
        """
        Test retrieval of all products when no products are available.
        Ensures an empty list is returned.
        """
        mock_local_service.get_products.return_value = []
        result = product_data_service.get_all_products(limit=10)
        assert result == []
        mock_local_service.get_products.assert_called_once_with(10)

    def test_get_all_products_limit_exceeds_available(self, product_data_service, mock_local_service):
        """
        Test retrieval of all products when the limit is higher than available products.
        Ensures all available products are returned.
        """
        mock_products_short = [{"id": "p1"}, {"id": "p2"}]
        mock_local_service.get_products.return_value = mock_products_short

        result = product_data_service.get_all_products(limit=5)

        assert len(result) == 2
        assert result == mock_products_short
        mock_local_service.get_products.assert_called_once_with(5)

    def test_get_all_products_error(self, product_data_service, mock_local_service, caplog):
        """
        Test get_all_products when an error occurs.
        Ensures an empty list is returned and error is logged.
        """
        mock_local_service.get_products.side_effect = Exception("All products data error")

        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_all_products(limit=20)

            assert result == []
            mock_local_service.get_products.assert_called_once_with(20)
            assert "Error getting all products: All products data error" in caplog.text

    def test_get_product_details_success(self, product_data_service, mock_local_service, caplog):
        """
        Test successful retrieval of product details by ID.
        """
        mock_product_details = {"id": "prod123", "name": "Fancy Gadget", "price": 99.99, "description": "A cool gadget."}
        mock_local_service.get_product_details.return_value = mock_product_details

        result = product_data_service.get_product_details("prod123")

        assert result == mock_product_details
        mock_local_service.get_product_details.assert_called_once_with("prod123")
        assert "Error getting product details" not in caplog.text

    def test_get_product_details_not_found(self, product_data_service, mock_local_service):
        """
        Test retrieval of product details for a non-existent product ID.
        Ensures None is returned.
        """
        mock_local_service.get_product_details.return_value = None

        result = product_data_service.get_product_details("nonexistent_id")

        assert result is None
        mock_local_service.get_product_details.assert_called_once_with("nonexistent_id")

    def test_get_product_details_error(self, product_data_service, mock_local_service, caplog):
        """
        Test get_product_details when an error occurs.
        Ensures None is returned and error is logged.
        """
        mock_local_service.get_product_details.side_effect = Exception("Details fetch error")

        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_product_details("error_id")

            assert result is None
            mock_local_service.get_product_details.assert_called_once_with("error_id")
            assert "Error getting product details: Details fetch error" in caplog.text

    def test_get_brands_success(self, product_data_service, mock_local_service, caplog):
        """
        Test successful retrieval of available brands.
        """
        mock_brands = ["Brand A", "Brand B", "Brand C"]
        mock_local_service.get_brands.return_value = mock_brands

        result = product_data_service.get_brands()

        assert result == mock_brands
        mock_local_service.get_brands.assert_called_once()
        assert "Error getting brands" not in caplog.text

    def test_get_brands_error(self, product_data_service, mock_local_service, caplog):
        """
        Test get_brands when an error occurs.
        Ensures an empty list is returned and error is logged.
        """
        mock_local_service.get_brands.side_effect = Exception("Brands API error")

        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_brands()

            assert result == []
            mock_local_service.get_brands.assert_called_once()
            assert "Error getting brands: Brands API error" in caplog.text

    def test_get_products_by_brand_success(self, product_data_service, mock_local_service, caplog):
        """
        Test successful retrieval of products by brand, respecting the limit.
        """
        # Return more items than limit to verify slicing
        mock_products_long = [{"id": f"b{i}", "brand": "BrandX"} for i in range(15)]
        mock_local_service.get_products_by_brand.return_value = mock_products_long

        result = product_data_service.get_products_by_brand("BrandX", limit=10)

        assert len(result) == 10
        assert result == mock_products_long[:10]
        mock_local_service.get_products_by_brand.assert_called_once_with("BrandX")
        assert "Error getting products by brand" not in caplog.text

    def test_get_products_by_brand_no_results(self, product_data_service, mock_local_service):
        """
        Test retrieval of products by brand when no products match.
        Ensures an empty list is returned.
        """
        mock_local_service.get_products_by_brand.return_value = []
        result = product_data_service.get_products_by_brand("NonExistentBrand", limit=5)
        assert result == []
        mock_local_service.get_products_by_brand.assert_called_once_with("NonExistentBrand")

    def test_get_products_by_brand_limit_exceeds_available(self, product_data_service, mock_local_service):
        """
        Test retrieval of products by brand when the limit is higher than available products.
        Ensures all available products are returned.
        """
        mock_products_short = [{"id": "b1", "brand": "BrandY"}, {"id": "b2", "brand": "BrandY"}]
        mock_local_service.get_products_by_brand.return_value = mock_products_short

        result = product_data_service.get_products_by_brand("BrandY", limit=5)

        assert len(result) == 2
        assert result == mock_products_short
        mock_local_service.get_products_by_brand.assert_called_once_with("BrandY")

    def test_get_products_by_brand_error(self, product_data_service, mock_local_service, caplog):
        """
        Test get_products_by_brand when an error occurs.
        Ensures an empty list is returned and error is logged.
        """
        mock_local_service.get_products_by_brand.side_effect = Exception("Brand filter data error")

        with caplog.at_level(logging.ERROR):
            result = product_data_service.get_products_by_brand("ErrorBrand", limit=10)

            assert result == []
            mock_local_service.get_products_by_brand.assert_called_once_with("ErrorBrand")
            assert "Error getting products by brand: Brand filter data error" in caplog.text

    @pytest.mark.asyncio
    async def test_smart_search_products_success(self, product_data_service, mock_local_service):
        """
        Test successful smart search with all parameters.
        Ensures correct arguments are passed and the tuple (products, message) is returned.
        """
        mock_products = [{"id": "smartelectronics", "name": "Smart Speaker"}]
        mock_message = "Found 1 smart electronics product."
        mock_local_service.smart_search_products.return_value = (mock_products, mock_message)

        products, message = await product_data_service.smart_search_products(
            keyword="smart", category="electronics", max_price=100, limit=3
        )

        assert products == mock_products
        assert message == mock_message
        mock_local_service.smart_search_products.assert_called_once_with(
            "smart", "electronics", 100, 3
        )

    @pytest.mark.asyncio
    async def test_smart_search_products_no_params(self, product_data_service, mock_local_service):
        """
        Test smart search using default parameters (no args provided).
        """
        mock_products = [{"id": "default_prod"}]
        mock_message = "Default search results for general items."
        mock_local_service.smart_search_products.return_value = (mock_products, mock_message)

        products, message = await product_data_service.smart_search_products() # Call without arguments

        assert products == mock_products
        assert message == mock_message
        mock_local_service.smart_search_products.assert_called_once_with(
            '', None, None, 5 # Check against default values in method signature
        )

    @pytest.mark.asyncio
    async def test_smart_search_products_error_propagation(self, product_data_service, mock_local_service):
        """
        Test smart search error. The current implementation of smart_search_products
        in ProductDataService does not have its own try-except, so exceptions
        from LocalProductService.smart_search_products should propagate.
        """
        mock_local_service.smart_search_products.side_effect = Exception("Smart search backend error")

        with pytest.raises(Exception) as excinfo:
            await product_data_service.smart_search_products("fail_keyword")

        assert "Smart search backend error" in str(excinfo.value)
        mock_local_service.smart_search_products.assert_called_once_with(
            "fail_keyword", None, None, 5 # Default limit and optional args
        )