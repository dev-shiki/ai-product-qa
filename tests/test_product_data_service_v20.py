import pytest
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock, patch

# Adjust the import path based on the project structure
from app.services.product_data_service import ProductDataService
# No need to import LocalProductService explicitly as it's mocked

# Configure logging to suppress during tests or capture for assertion if needed
logging.basicConfig(level=logging.CRITICAL)

# --- Sample Data for Mocks ---
SAMPLE_PRODUCTS = [
    {"id": "1", "name": "Laptop Pro", "category": "Electronics", "price": 1200, "rating": 4.5, "brand": "TechCo"},
    {"id": "2", "name": "Mechanical Keyboard", "category": "Electronics", "price": 150, "rating": 4.8, "brand": "KBDMaster"},
    {"id": "3", "name": "Ergonomic Chair", "category": "Office", "price": 400, "rating": 4.2, "brand": "ComfySeats"},
    {"id": "4", "name": "Wireless Mouse", "category": "Electronics", "price": 50, "rating": 3.9, "brand": "TechCo"},
    {"id": "5", "name": "Monitor UltraWide", "category": "Electronics", "price": 600, "rating": 4.7, "brand": "DisplayCorp"},
    {"id": "6", "name": "The Great Novel", "category": "Books", "price": 25, "rating": 4.1, "brand": "LitPublish"},
]

SAMPLE_CATEGORIES = ["Electronics", "Office", "Books"]
SAMPLE_BRANDS = ["TechCo", "KBDMaster", "ComfySeats", "DisplayCorp", "LitPublish"]

# --- Fixtures ---

@pytest.fixture
def mock_local_product_service():
    """
    Fixture to mock the LocalProductService class that ProductDataService depends on.
    This patch ensures that any instance of LocalProductService created by ProductDataService
    will be our mock.
    """
    with patch('app.services.product_data_service.LocalProductService') as MockLocalProductService:
        # Get the instance that ProductDataService will use
        mock_instance = MockLocalProductService.return_value

        # Configure default return values for the mock methods
        mock_instance.search_products.return_value = [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]]
        mock_instance.get_products.return_value = SAMPLE_PRODUCTS # Used by get_all_products & get_products fallback
        mock_instance.get_categories.return_value = SAMPLE_CATEGORIES
        mock_instance.get_top_rated_products.return_value = [SAMPLE_PRODUCTS[1], SAMPLE_PRODUCTS[0]] # Example top rated
        mock_instance.get_best_selling_products.return_value = [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[2]] # Example best selling
        
        # For methods where ProductDataService applies slicing, the mock should return the full list
        mock_instance.get_products_by_category.side_effect = \
            lambda category: [p for p in SAMPLE_PRODUCTS if p["category"] == category]
        mock_instance.get_products_by_brand.side_effect = \
            lambda brand: [p for p in SAMPLE_PRODUCTS if p["brand"] == brand]
        
        mock_instance.get_product_details.side_effect = \
            lambda product_id: next((p for p in SAMPLE_PRODUCTS if p["id"] == product_id), None)
        
        mock_instance.get_brands.return_value = SAMPLE_BRANDS

        mock_instance.smart_search_products.return_value = (
            [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]], "Smart search found relevant items."
        )

        yield mock_instance

@pytest.fixture
def product_data_service(mock_local_product_service):
    """
    Fixture to provide an instance of ProductDataService with its dependencies mocked.
    """
    service = ProductDataService()
    return service

# --- Test Cases for ProductDataService ---

class TestProductDataService:

    @pytest.mark.asyncio
    async def test_init(self, mock_local_product_service, product_data_service):
        """
        Test that ProductDataService initializes correctly,
        creating an instance of LocalProductService.
        """
        mock_local_product_service.assert_called_once()
        # Verify that product_data_service.local_service is indeed our mock instance
        assert product_data_service.local_service is mock_local_product_service

    @pytest.mark.asyncio
    async def test_search_products_success(self, product_data_service, mock_local_product_service):
        """
        Test `search_products` method for a successful search.
        Ensures `local_service.search_products` is called with correct arguments
        and returns the expected products.
        """
        keyword = "laptop"
        limit = 5
        products = await product_data_service.search_products(keyword, limit)
        mock_local_product_service.search_products.assert_called_once_with(keyword, limit)
        assert products == [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]]
        assert len(products) == 2

    @pytest.mark.asyncio
    async def test_search_products_no_results(self, product_data_service, mock_local_product_service):
        """
        Test `search_products` when no products match the keyword.
        """
        mock_local_product_service.search_products.return_value = []
        keyword = "nonexistent"
        limit = 5
        products = await product_data_service.search_products(keyword, limit)
        mock_local_product_service.search_products.assert_called_once_with(keyword, limit)
        assert products == []
        assert len(products) == 0

    @pytest.mark.asyncio
    async def test_search_products_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `search_products` when an exception occurs in the underlying service call.
        Ensures an empty list is returned and an error is logged.
        """
        mock_local_product_service.search_products.side_effect = Exception("Simulated search error")
        keyword = "error"
        limit = 5
        
        with caplog.at_level(logging.ERROR):
            products = await product_data_service.search_products(keyword, limit)
        
        mock_local_product_service.search_products.assert_called_once_with(keyword, limit)
        assert products == []
        assert "Error searching products: Simulated search error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_products_with_search_filter(self, product_data_service, mock_local_product_service, mocker):
        """
        Test `get_products` when a 'search' keyword is provided.
        It should delegate to `search_products` and return its result.
        """
        # We mock product_data_service.search_products directly as get_products calls it
        mocker.patch.object(product_data_service, 'search_products', new_callable=AsyncMock)
        product_data_service.search_products.return_value = [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[3]]

        limit = 10
        search_keyword = "tech"
        products = await product_data_service.get_products(limit=limit, search=search_keyword)

        product_data_service.search_products.assert_called_once_with(search_keyword, limit)
        mock_local_product_service.get_products.assert_not_called()
        mock_local_product_service.get_products_by_category.assert_not_called()
        assert products == [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[3]]

    @pytest.mark.asyncio
    async def test_get_products_with_category_filter(self, product_data_service, mock_local_product_service, mocker):
        """
        Test `get_products` when a 'category' is provided (and no 'search').
        It should delegate to `get_products_by_category` and return its result.
        """
        # We mock product_data_service.get_products_by_category directly as get_products calls it
        mocker.patch.object(product_data_service, 'get_products_by_category', return_value=[SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]])

        limit = 10
        category_name = "Electronics"
        products = await product_data_service.get_products(limit=limit, category=category_name)

        product_data_service.get_products_by_category.assert_called_once_with(category_name, limit)
        mock_local_product_service.get_products.assert_not_called()
        product_data_service.search_products.assert_not_called() # Ensure search path wasn't taken
        assert products == [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]]

    @pytest.mark.asyncio
    async def test_get_products_no_filters(self, product_data_service, mock_local_product_service, mocker):
        """
        Test `get_products` when neither 'search' nor 'category' is provided.
        It should delegate to `get_all_products` and return its result.
        """
        # We mock product_data_service.get_all_products directly as get_products calls it
        mocker.patch.object(product_data_service, 'get_all_products', return_value=SAMPLE_PRODUCTS[:3])

        limit = 20
        products = await product_data_service.get_products(limit=limit)

        product_data_service.get_all_products.assert_called_once_with(limit)
        mock_local_product_service.get_products.assert_not_called() # Fallback not used
        mock_local_product_service.get_products_by_category.assert_not_called()
        product_data_service.search_products.assert_not_called()
        assert products == SAMPLE_PRODUCTS[:3]

    @pytest.mark.asyncio
    async def test_get_products_exception_fallback(self, product_data_service, mock_local_product_service, mocker, caplog):
        """
        Test `get_products` error handling: if an exception occurs in any
        of its internal calls (search, category, or all), it should fall back
        to `local_service.get_products`.
        """
        # Simulate an error in the path that would be taken (e.g., get_all_products)
        mocker.patch.object(product_data_service, 'get_all_products', side_effect=Exception("Internal branch error"))
        
        limit = 20
        
        with caplog.at_level(logging.ERROR):
            products = await product_data_service.get_products(limit=limit)

        # Ensure the fallback to local_service.get_products was called
        mock_local_product_service.get_products.assert_called_once_with(limit)
        assert products == SAMPLE_PRODUCTS # Expected return from local_service.get_products
        assert "Error getting products: Internal branch error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service, mock_local_product_service):
        """Test `get_categories` success case."""
        categories = await product_data_service.get_categories()
        mock_local_product_service.get_categories.assert_called_once()
        assert categories == SAMPLE_CATEGORIES

    @pytest.mark.asyncio
    async def test_get_categories_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test `get_categories` when an exception occurs."""
        mock_local_product_service.get_categories.side_effect = Exception("Category fetch error")
        with caplog.at_level(logging.ERROR):
            categories = await product_data_service.get_categories()
        mock_local_product_service.get_categories.assert_called_once()
        assert categories == []
        assert "Error getting categories: Category fetch error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service, mock_local_product_service):
        """Test `get_top_rated_products` success case."""
        limit = 5
        products = await product_data_service.get_top_rated_products(limit)
        mock_local_product_service.get_top_rated_products.assert_called_once_with(limit)
        assert products == [SAMPLE_PRODUCTS[1], SAMPLE_PRODUCTS[0]]

    @pytest.mark.asyncio
    async def test_get_top_rated_products_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test `get_top_rated_products` when an exception occurs."""
        mock_local_product_service.get_top_rated_products.side_effect = Exception("Top rated fetch error")
        with caplog.at_level(logging.ERROR):
            products = await product_data_service.get_top_rated_products()
        mock_local_product_service.get_top_rated_products.assert_called_once()
        assert products == []
        assert "Error getting top rated products: Top rated fetch error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service, mock_local_product_service):
        """Test `get_best_selling_products` success case."""
        limit = 5
        products = await product_data_service.get_best_selling_products(limit)
        mock_local_product_service.get_best_selling_products.assert_called_once_with(limit)
        assert products == [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[2]]

    @pytest.mark.asyncio
    async def test_get_best_selling_products_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test `get_best_selling_products` when an exception occurs."""
        mock_local_product_service.get_best_selling_products.side_effect = Exception("Best selling fetch error")
        with caplog.at_level(logging.ERROR):
            products = await product_data_service.get_best_selling_products()
        mock_local_product_service.get_best_selling_products.assert_called_once()
        assert products == []
        assert "Error getting best selling products: Best selling fetch error" in caplog.text

    def test_get_products_by_category_success(self, product_data_service, mock_local_product_service):
        """
        Test `get_products_by_category` success case.
        Verifies correct delegation and application of the limit.
        """
        category = "Electronics"
        limit = 2
        
        # The mock is configured to return ALL products for 'Electronics'
        # ProductDataService's method should then apply the [:limit] slice
        products = product_data_service.get_products_by_category(category, limit)
        
        mock_local_product_service.get_products_by_category.assert_called_once_with(category)
        expected_products = [p for p in SAMPLE_PRODUCTS if p["category"] == category][:limit]
        assert products == expected_products
        assert len(products) == limit

    def test_get_products_by_category_no_results(self, product_data_service, mock_local_product_service):
        """Test `get_products_by_category` when no products match the category."""
        mock_local_product_service.get_products_by_category.return_value = []
        category = "NonExistentCategory"
        limit = 5
        products = product_data_service.get_products_by_category(category, limit)
        mock_local_product_service.get_products_by_category.assert_called_once_with(category)
        assert products == []

    def test_get_products_by_category_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test `get_products_by_category` when an exception occurs."""
        mock_local_product_service.get_products_by_category.side_effect = Exception("Category search error")
        category = "Electronics"
        limit = 5
        with caplog.at_level(logging.ERROR):
            products = product_data_service.get_products_by_category(category, limit)
        mock_local_product_service.get_products_by_category.assert_called_once_with(category)
        assert products == []
        assert "Error getting products by category: Category search error" in caplog.text

    def test_get_all_products_success(self, product_data_service, mock_local_product_service):
        """Test `get_all_products` success case."""
        limit = 3
        products = product_data_service.get_all_products(limit)
        # The underlying local_service.get_products is mocked to return all SAMPLE_PRODUCTS
        # ProductDataService's get_all_products should pass the limit to it
        mock_local_product_service.get_products.assert_called_once_with(limit)
        assert products == SAMPLE_PRODUCTS # Mock is set to return full list for get_products

    def test_get_all_products_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test `get_all_products` when an exception occurs."""
        mock_local_product_service.get_products.side_effect = Exception("All products fetch error")
        limit = 5
        with caplog.at_level(logging.ERROR):
            products = product_data_service.get_all_products(limit)
        mock_local_product_service.get_products.assert_called_once_with(limit)
        assert products == []
        assert "Error getting all products: All products fetch error" in caplog.text

    def test_get_product_details_success(self, product_data_service, mock_local_product_service):
        """Test `get_product_details` success case."""
        product_id = "1"
        details = product_data_service.get_product_details(product_id)
        mock_local_product_service.get_product_details.assert_called_once_with(product_id)
        assert details == SAMPLE_PRODUCTS[0]

    def test_get_product_details_not_found(self, product_data_service, mock_local_product_service):
        """Test `get_product_details` when product ID is not found."""
        product_id = "999"
        # Mock's side_effect already handles returning None for non-existent IDs
        details = product_data_service.get_product_details(product_id)
        mock_local_product_service.get_product_details.assert_called_once_with(product_id)
        assert details is None

    def test_get_product_details_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test `get_product_details` when an exception occurs."""
        mock_local_product_service.get_product_details.side_effect = Exception("Details fetch error")
        product_id = "1"
        with caplog.at_level(logging.ERROR):
            details = product_data_service.get_product_details(product_id)
        mock_local_product_service.get_product_details.assert_called_once_with(product_id)
        assert details is None
        assert "Error getting product details: Details fetch error" in caplog.text

    def test_get_brands_success(self, product_data_service, mock_local_product_service):
        """Test `get_brands` success case."""
        brands = product_data_service.get_brands()
        mock_local_product_service.get_brands.assert_called_once()
        assert brands == SAMPLE_BRANDS

    def test_get_brands_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test `get_brands` when an exception occurs."""
        mock_local_product_service.get_brands.side_effect = Exception("Brands fetch error")
        with caplog.at_level(logging.ERROR):
            brands = product_data_service.get_brands()
        mock_local_product_service.get_brands.assert_called_once()
        assert brands == []
        assert "Error getting brands: Brands fetch error" in caplog.text

    def test_get_products_by_brand_success(self, product_data_service, mock_local_product_service):
        """
        Test `get_products_by_brand` success case.
        Verifies correct delegation and application of the limit.
        """
        brand = "TechCo"
        limit = 1
        products = product_data_service.get_products_by_brand(brand, limit)
        mock_local_product_service.get_products_by_brand.assert_called_once_with(brand)
        expected_products = [p for p in SAMPLE_PRODUCTS if p["brand"] == brand][:limit]
        assert products == expected_products
        assert len(products) == limit

    def test_get_products_by_brand_no_results(self, product_data_service, mock_local_product_service):
        """Test `get_products_by_brand` when no products match the brand."""
        mock_local_product_service.get_products_by_brand.return_value = []
        brand = "NonExistentBrand"
        limit = 5
        products = product_data_service.get_products_by_brand(brand, limit)
        mock_local_product_service.get_products_by_brand.assert_called_once_with(brand)
        assert products == []

    def test_get_products_by_brand_exception(self, product_data_service, mock_local_product_service, caplog):
        """Test `get_products_by_brand` when an exception occurs."""
        mock_local_product_service.get_products_by_brand.side_effect = Exception("Brand search error")
        brand = "TechCo"
        limit = 5
        with caplog.at_level(logging.ERROR):
            products = product_data_service.get_products_by_brand(brand, limit)
        mock_local_product_service.get_products_by_brand.assert_called_once_with(brand)
        assert products == []
        assert "Error getting products by brand: Brand search error" in caplog.text

    @pytest.mark.asyncio
    async def test_smart_search_products_success(self, product_data_service, mock_local_product_service):
        """
        Test `smart_search_products` method success case.
        Ensures correct arguments are passed and return values are handled.
        """
        keyword = "smart"
        category = "Electronics"
        max_price = 1000
        limit = 2
        
        products, message = await product_data_service.smart_search_products(keyword, category, max_price, limit)
        
        mock_local_product_service.smart_search_products.assert_called_once_with(
            keyword, category, max_price, limit
        )
        assert products == [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]]
        assert message == "Smart search found relevant items."

    @pytest.mark.asyncio
    async def test_smart_search_products_default_args(self, product_data_service, mock_local_product_service):
        """Test `smart_search_products` with only keyword, using default args for others."""
        keyword = "default_test"
        await product_data_service.smart_search_products(keyword)
        mock_local_product_service.smart_search_products.assert_called_once_with(
            keyword, None, None, 5 # Default values from method signature
        )

    @pytest.mark.asyncio
    async def test_smart_search_products_exception(self, product_data_service, mock_local_product_service):
        """
        Test `smart_search_products` when an exception occurs.
        As the method does not have its own try-except, the exception should propagate.
        """
        mock_local_product_service.smart_search_products.side_effect = Exception("Smart search internal error")
        
        keyword = "error_smart"
        with pytest.raises(Exception, match="Smart search internal error"):
            await product_data_service.smart_search_products(keyword)
        
        mock_local_product_service.smart_search_products.assert_called_once_with(
            keyword, None, None, 5 # Default values
        )