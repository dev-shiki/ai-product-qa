import pytest
import asyncio
from unittest.mock import MagicMock, patch

# Assuming the file structure is app/services/product_data_service.py
# and the test file is test_services/test_product_data_service.py
from app.services.product_data_service import ProductDataService

# --- Fixtures ---

@pytest.fixture
def mock_local_product_service():
    """Fixture for mocking LocalProductService dependency."""
    # Use patch to replace the LocalProductService class at the module level
    # where ProductDataService imports it.
    with patch('app.services.product_data_service.LocalProductService') as MockLocalService:
        mock_instance = MockLocalService.return_value
        
        # Set default return values for all methods of the mocked service.
        # This ensures that tests don't fail unexpectedly if a method
        # is called without a specific mock setup.
        mock_instance.search_products.return_value = []
        mock_instance.get_products.return_value = []
        mock_instance.get_categories.return_value = []
        mock_instance.get_top_rated_products.return_value = []
        mock_instance.get_best_selling_products.return_value = []
        mock_instance.get_products_by_category.return_value = []
        mock_instance.get_product_details.return_value = None
        mock_instance.get_brands.return_value = []
        mock_instance.get_products_by_brand.return_value = []
        # smart_search_products returns a tuple (list, string)
        mock_instance.smart_search_products.return_value = ([], "No results found.")
        
        yield mock_instance

@pytest.fixture
def product_data_service(mock_local_product_service):
    """Fixture for ProductDataService instance with mocked LocalProductService."""
    # When ProductDataService is instantiated, its __init__ will call
    # LocalProductService(), which is now our patched mock class.
    service = ProductDataService()
    # Ensure the local_service attribute points to our mock instance
    # (though it should already be due to the patch if init is called).
    assert service.local_service is mock_local_product_service
    return service

# --- Sample Data ---
SAMPLE_PRODUCTS = [
    {"id": "1", "name": "Laptop Pro", "category": "Electronics", "price": 1500, "rating": 4.8, "brand": "BrandX"},
    {"id": "2", "name": "Mechanical Keyboard", "category": "Electronics", "price": 120, "rating": 4.2, "brand": "BrandY"},
    {"id": "3", "name": "Office Desk", "category": "Furniture", "price": 400, "rating": 4.5, "brand": "BrandZ"},
    {"id": "4", "name": "Smartphone Elite", "category": "Electronics", "price": 1000, "rating": 4.7, "brand": "BrandX"},
    {"id": "5", "name": "Cookbook: Italian Delights", "category": "Books", "price": 30, "rating": 3.9, "brand": "BrandA"},
]
SAMPLE_CATEGORIES = ["Electronics", "Furniture", "Books"]
SAMPLE_BRANDS = ["BrandX", "BrandY", "BrandZ", "BrandA"]

# --- Tests for ProductDataService ---

class TestProductDataService:

    @pytest.mark.asyncio
    async def test_init_local_service_creation(self, mock_local_product_service):
        """Test ProductDataService initialization correctly instantiates LocalProductService."""
        # The product_data_service fixture already does this, but this test
        # explicitly verifies the __init__ behavior in isolation.
        with patch('app.services.product_data_service.LocalProductService') as MockLocalService:
            service = ProductDataService()
            MockLocalService.assert_called_once_with()
            assert service.local_service is MockLocalService.return_value

    @pytest.mark.asyncio
    async def test_search_products_success(self, product_data_service, mock_local_product_service):
        """Test search_products method for successful product retrieval."""
        mock_local_product_service.search_products.return_value = [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[3]]
        
        result = await product_data_service.search_products("Laptop", limit=2)
        
        mock_local_product_service.search_products.assert_called_once_with("Laptop", 2)
        assert result == [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[3]]
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_search_products_no_results(self, product_data_service, mock_local_product_service):
        """Test search_products method when no products match the keyword."""
        mock_local_product_service.search_products.return_value = []
        
        result = await product_data_service.search_products("NonExistentProduct", limit=10)
        
        mock_local_product_service.search_products.assert_called_once_with("NonExistentProduct", 10)
        assert result == []
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_products_exception_handling(self, product_data_service, mock_local_product_service):
        """Test search_products method handles exceptions gracefully by returning an empty list."""
        mock_local_product_service.search_products.side_effect = Exception("Simulated search error")
        
        result = await product_data_service.search_products("ErrorTest", limit=5)
        
        mock_local_product_service.search_products.assert_called_once_with("ErrorTest", 5)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_products_with_search_parameter(self, product_data_service):
        """Test get_products method when 'search' parameter is provided, delegating to search_products."""
        # Patch search_products of ProductDataService to verify internal delegation
        with patch.object(product_data_service, 'search_products', new_callable=MagicMock) as mock_search_products:
            mock_search_products.return_value = [SAMPLE_PRODUCTS[0]]
            
            result = await product_data_service.get_products(search="Laptop", limit=1)
            
            mock_search_products.assert_called_once_with("Laptop", 1)
            assert result == [SAMPLE_PRODUCTS[0]]

    @pytest.mark.asyncio
    async def test_get_products_with_category_parameter(self, product_data_service):
        """Test get_products method when 'category' parameter is provided, delegating to get_products_by_category."""
        # Patch get_products_by_category of ProductDataService to verify internal delegation
        with patch.object(product_data_service, 'get_products_by_category', new_callable=MagicMock) as mock_get_by_category:
            mock_get_by_category.return_value = [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]]
            
            result = await product_data_service.get_products(category="Electronics", limit=2)
            
            mock_get_by_category.assert_called_once_with("Electronics", 2)
            assert result == [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]]

    @pytest.mark.asyncio
    async def test_get_products_without_filters(self, product_data_service):
        """Test get_products method when no filters are provided, delegating to get_all_products."""
        # Patch get_all_products of ProductDataService to verify internal delegation
        with patch.object(product_data_service, 'get_all_products', new_callable=MagicMock) as mock_get_all_products:
            mock_get_all_products.return_value = SAMPLE_PRODUCTS[:3]
            
            result = await product_data_service.get_products(limit=3)
            
            mock_get_all_products.assert_called_once_with(3)
            assert result == SAMPLE_PRODUCTS[:3]

    @pytest.mark.asyncio
    async def test_get_products_exception_fallback(self, product_data_service, mock_local_product_service):
        """Test get_products method's exception handling, ensuring fallback to local_service.get_products."""
        # Force an internal method (e.g., get_all_products) to raise an exception
        with patch.object(product_data_service, 'get_all_products', new_callable=MagicMock) as mock_get_all_products:
            mock_get_all_products.side_effect = Exception("Internal error triggering fallback")
            mock_local_product_service.get_products.return_value = [SAMPLE_PRODUCTS[4]] # This is the fallback return
            
            result = await product_data_service.get_products(limit=5)
            
            mock_get_all_products.assert_called_once_with(5)
            mock_local_product_service.get_products.assert_called_once_with(5) # Ensure fallback is called with correct limit
            assert result == [SAMPLE_PRODUCTS[4]]

    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service, mock_local_product_service):
        """Test get_categories method for successful retrieval of categories."""
        mock_local_product_service.get_categories.return_value = SAMPLE_CATEGORIES
        
        result = await product_data_service.get_categories()
        
        mock_local_product_service.get_categories.assert_called_once_with()
        assert result == SAMPLE_CATEGORIES

    @pytest.mark.asyncio
    async def test_get_categories_no_categories(self, product_data_service, mock_local_product_service):
        """Test get_categories method when no categories are available."""
        mock_local_product_service.get_categories.return_value = []
        
        result = await product_data_service.get_categories()
        
        mock_local_product_service.get_categories.assert_called_once_with()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_categories_exception_handling(self, product_data_service, mock_local_product_service):
        """Test get_categories method handles exceptions gracefully."""
        mock_local_product_service.get_categories.side_effect = Exception("Category service error")
        
        result = await product_data_service.get_categories()
        
        mock_local_product_service.get_categories.assert_called_once_with()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service, mock_local_product_service):
        """Test get_top_rated_products method for successful retrieval."""
        mock_local_product_service.get_top_rated_products.return_value = [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[3]]
        
        result = await product_data_service.get_top_rated_products(limit=2)
        
        mock_local_product_service.get_top_rated_products.assert_called_once_with(2)
        assert result == [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[3]]

    @pytest.mark.asyncio
    async def test_get_top_rated_products_no_results(self, product_data_service, mock_local_product_service):
        """Test get_top_rated_products method when no top-rated products are found."""
        mock_local_product_service.get_top_rated_products.return_value = []
        
        result = await product_data_service.get_top_rated_products(limit=5)
        
        mock_local_product_service.get_top_rated_products.assert_called_once_with(5)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_top_rated_products_exception_handling(self, product_data_service, mock_local_product_service):
        """Test get_top_rated_products method handles exceptions gracefully."""
        mock_local_product_service.get_top_rated_products.side_effect = Exception("Top rated error")
        
        result = await product_data_service.get_top_rated_products(limit=5)
        
        mock_local_product_service.get_top_rated_products.assert_called_once_with(5)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service, mock_local_product_service):
        """Test get_best_selling_products method for successful retrieval."""
        mock_local_product_service.get_best_selling_products.return_value = [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]]
        
        result = await product_data_service.get_best_selling_products(limit=2)
        
        mock_local_product_service.get_best_selling_products.assert_called_once_with(2)
        assert result == [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]]

    @pytest.mark.asyncio
    async def test_get_best_selling_products_no_results(self, product_data_service, mock_local_product_service):
        """Test get_best_selling_products method when no best-selling products are found."""
        mock_local_product_service.get_best_selling_products.return_value = []
        
        result = await product_data_service.get_best_selling_products(limit=5)
        
        mock_local_product_service.get_best_selling_products.assert_called_once_with(5)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_best_selling_products_exception_handling(self, product_data_service, mock_local_product_service):
        """Test get_best_selling_products method handles exceptions gracefully."""
        mock_local_product_service.get_best_selling_products.side_effect = Exception("Best selling error")
        
        result = await product_data_service.get_best_selling_products(limit=5)
        
        mock_local_product_service.get_best_selling_products.assert_called_once_with(5)
        assert result == []

    def test_get_products_by_category_success_and_limit(self, product_data_service, mock_local_product_service):
        """Test get_products_by_category method for success, including local slicing by limit."""
        # The local service returns all products for the category, then ProductDataService slices.
        mock_local_product_service.get_products_by_category.return_value = [
            SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1], SAMPLE_PRODUCTS[3]
        ] # 3 Electronics products
        
        result = product_data_service.get_products_by_category("Electronics", 2)
        
        # LocalProductService's method should be called without the limit
        mock_local_product_service.get_products_by_category.assert_called_once_with("Electronics")
        assert result == [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]] # Expect sliced result
        assert len(result) == 2

    def test_get_products_by_category_no_results(self, product_data_service, mock_local_product_service):
        """Test get_products_by_category method when no products are found for the category."""
        mock_local_product_service.get_products_by_category.return_value = []
        
        result = product_data_service.get_products_by_category("NonExistentCategory", 10)
        
        mock_local_product_service.get_products_by_category.assert_called_once_with("NonExistentCategory")
        assert result == []

    def test_get_products_by_category_limit_exceeds_available(self, product_data_service, mock_local_product_service):
        """Test get_products_by_category when requested limit is higher than available products."""
        mock_local_product_service.get_products_by_category.return_value = [SAMPLE_PRODUCTS[2]] # Only 1 furniture product
        
        result = product_data_service.get_products_by_category("Furniture", 5) # Request 5, only 1 available
        
        mock_local_product_service.get_products_by_category.assert_called_once_with("Furniture")
        assert result == [SAMPLE_PRODUCTS[2]]
        assert len(result) == 1

    def test_get_products_by_category_exception_handling(self, product_data_service, mock_local_product_service):
        """Test get_products_by_category method handles exceptions gracefully."""
        mock_local_product_service.get_products_by_category.side_effect = Exception("Category filter error")
        
        result = product_data_service.get_products_by_category("AnyCategory", 5)
        
        mock_local_product_service.get_products_by_category.assert_called_once_with("AnyCategory")
        assert result == []

    def test_get_all_products_success(self, product_data_service, mock_local_product_service):
        """Test get_all_products method for successful retrieval."""
        # get_all_products directly passes the limit to local_service.get_products
        mock_local_product_service.get_products.return_value = SAMPLE_PRODUCTS[:3]
        
        result = product_data_service.get_all_products(limit=3)
        
        mock_local_product_service.get_products.assert_called_once_with(3)
        assert result == SAMPLE_PRODUCTS[:3]

    def test_get_all_products_no_results(self, product_data_service, mock_local_product_service):
        """Test get_all_products method when no products are available."""
        mock_local_product_service.get_products.return_value = []
        
        result = product_data_service.get_all_products(limit=10)
        
        mock_local_product_service.get_products.assert_called_once_with(10)
        assert result == []

    def test_get_all_products_exception_handling(self, product_data_service, mock_local_product_service):
        """Test get_all_products method handles exceptions gracefully."""
        mock_local_product_service.get_products.side_effect = Exception("All products error")
        
        result = product_data_service.get_all_products(limit=10)
        
        mock_local_product_service.get_products.assert_called_once_with(10)
        assert result == []

    def test_get_product_details_found(self, product_data_service, mock_local_product_service):
        """Test get_product_details method when a product is found by ID."""
        mock_local_product_service.get_product_details.return_value = SAMPLE_PRODUCTS[0]
        
        result = product_data_service.get_product_details("1")
        
        mock_local_product_service.get_product_details.assert_called_once_with("1")
        assert result == SAMPLE_PRODUCTS[0]

    def test_get_product_details_not_found(self, product_data_service, mock_local_product_service):
        """Test get_product_details method when a product is not found by ID."""
        mock_local_product_service.get_product_details.return_value = None
        
        result = product_data_service.get_product_details("999")
        
        mock_local_product_service.get_product_details.assert_called_once_with("999")
        assert result is None

    def test_get_product_details_exception_handling(self, product_data_service, mock_local_product_service):
        """Test get_product_details method handles exceptions gracefully."""
        mock_local_product_service.get_product_details.side_effect = Exception("Details retrieval error")
        
        result = product_data_service.get_product_details("123")
        
        mock_local_product_service.get_product_details.assert_called_once_with("123")
        assert result is None

    def test_get_brands_success(self, product_data_service, mock_local_product_service):
        """Test get_brands method for successful retrieval of brands."""
        mock_local_product_service.get_brands.return_value = SAMPLE_BRANDS
        
        result = product_data_service.get_brands()
        
        mock_local_product_service.get_brands.assert_called_once_with()
        assert result == SAMPLE_BRANDS

    def test_get_brands_no_brands(self, product_data_service, mock_local_product_service):
        """Test get_brands method when no brands are available."""
        mock_local_product_service.get_brands.return_value = []
        
        result = product_data_service.get_brands()
        
        mock_local_product_service.get_brands.assert_called_once_with()
        assert result == []

    def test_get_brands_exception_handling(self, product_data_service, mock_local_product_service):
        """Test get_brands method handles exceptions gracefully."""
        mock_local_product_service.get_brands.side_effect = Exception("Brand service error")
        
        result = product_data_service.get_brands()
        
        mock_local_product_service.get_brands.assert_called_once_with()
        assert result == []

    def test_get_products_by_brand_success_and_limit(self, product_data_service, mock_local_product_service):
        """Test get_products_by_brand method for success, including local slicing by limit."""
        # The local service returns all products for the brand, then ProductDataService slices.
        mock_local_product_service.get_products_by_brand.return_value = [
            SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[3]
        ] # 2 BrandX products
        
        result = product_data_service.get_products_by_brand("BrandX", 1)
        
        mock_local_product_service.get_products_by_brand.assert_called_once_with("BrandX")
        assert result == [SAMPLE_PRODUCTS[0]] # Expect sliced result
        assert len(result) == 1

    def test_get_products_by_brand_no_results(self, product_data_service, mock_local_product_service):
        """Test get_products_by_brand method when no products are found for the brand."""
        mock_local_product_service.get_products_by_brand.return_value = []
        
        result = product_data_service.get_products_by_brand("NonExistentBrand", 10)
        
        mock_local_product_service.get_products_by_brand.assert_called_once_with("NonExistentBrand")
        assert result == []

    def test_get_products_by_brand_limit_exceeds_available(self, product_data_service, mock_local_product_service):
        """Test get_products_by_brand when requested limit is higher than available products."""
        mock_local_product_service.get_products_by_brand.return_value = [SAMPLE_PRODUCTS[1]] # Only 1 BrandY product
        
        result = product_data_service.get_products_by_brand("BrandY", 5) # Request 5, only 1 available
        
        mock_local_product_service.get_products_by_brand.assert_called_once_with("BrandY")
        assert result == [SAMPLE_PRODUCTS[1]]
        assert len(result) == 1

    def test_get_products_by_brand_exception_handling(self, product_data_service, mock_local_product_service):
        """Test get_products_by_brand method handles exceptions gracefully."""
        mock_local_product_service.get_products_by_brand.side_effect = Exception("Brand filter error")
        
        result = product_data_service.get_products_by_brand("AnyBrand", 5)
        
        mock_local_product_service.get_products_by_brand.assert_called_once_with("AnyBrand")
        assert result == []

    @pytest.mark.asyncio
    async def test_smart_search_products_success(self, product_data_service, mock_local_product_service):
        """Test smart_search_products method for successful hybrid search."""
        expected_products = [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[3]]
        expected_message = "Found 2 matching products."
        mock_local_product_service.smart_search_products.return_value = (expected_products, expected_message)
        
        products, message = await product_data_service.smart_search_products(
            keyword="laptop", category="Electronics", max_price=2000, limit=3
        )
        
        mock_local_product_service.smart_search_products.assert_called_once_with(
            "laptop", "Electronics", 2000, 3
        )
        assert products == expected_products
        assert message == expected_message

    @pytest.mark.asyncio
    async def test_smart_search_products_no_results(self, product_data_service, mock_local_product_service):
        """Test smart_search_products method when no products are found."""
        expected_products = []
        expected_message = "No products found matching your criteria."
        mock_local_product_service.smart_search_products.return_value = (expected_products, expected_message)
        
        products, message = await product_data_service.smart_search_products(
            keyword="nonexistent", category="unknown"
        ) # Test with default limit
        
        mock_local_product_service.smart_search_products.assert_called_once_with(
            "nonexistent", "unknown", None, 5 # default limit is 5
        )
        assert products == expected_products
        assert message == expected_message

    @pytest.mark.asyncio
    async def test_smart_search_products_exception_re_raised(self, product_data_service, mock_local_product_service):
        """
        Test smart_search_products method re-raises exceptions from local_service,
        as it does not have its own try-except block.
        """
        mock_local_product_service.smart_search_products.side_effect = Exception("Critical smart search failure")
        
        with pytest.raises(Exception, match="Critical smart search failure"):
            await product_data_service.smart_search_products(keyword="error")
            
        mock_local_product_service.smart_search_products.assert_called_once_with("error", None, None, 5)