import pytest
from unittest.mock import MagicMock, patch
import asyncio
import logging

# Ensure the path is correct for importing the service
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService

# Sample data for mocking
PRODUCT_1 = {"id": "1", "name": "Product A", "price": 100, "category": "Electronics", "brand": "BrandX", "rating": 4.5, "sales": 1000}
PRODUCT_2 = {"id": "2", "name": "Product B", "price": 200, "category": "Books", "brand": "BrandY", "rating": 3.8, "sales": 500}
PRODUCT_3 = {"id": "3", "name": "Product C", "price": 150, "category": "Electronics", "brand": "BrandX", "rating": 4.0, "sales": 750}
PRODUCT_LIST = [PRODUCT_1, PRODUCT_2, PRODUCT_3]

CATEGORY_LIST = ["Electronics", "Books", "Clothing"]
BRAND_LIST = ["BrandX", "BrandY", "BrandZ"]

@pytest.fixture
def mock_local_service(mocker):
    """
    Fixture to mock the LocalProductService.
    We patch the class itself, so any instance of ProductDataService
    will receive this mock.
    """
    mock = mocker.patch('app.services.product_data_service.LocalProductService', autospec=True)
    
    # Configure default return values for mock methods
    # These are sync methods on LocalProductService, even if ProductDataService calls them async.
    mock_instance = mock.return_value
    mock_instance.get_products.return_value = PRODUCT_LIST
    mock_instance.get_categories.return_value = CATEGORY_LIST
    mock_instance.get_brands.return_value = BRAND_LIST
    mock_instance.get_product_details.return_value = PRODUCT_1
    mock_instance.get_products_by_category.return_value = [PRODUCT_1, PRODUCT_3]
    mock_instance.get_products_by_brand.return_value = [PRODUCT_1, PRODUCT_3]
    mock_instance.get_top_rated_products.return_value = [PRODUCT_1, PRODUCT_3]
    mock_instance.get_best_selling_products.return_value = [PRODUCT_1, PRODUCT_3]
    
    # Async methods within ProductDataService that call sync methods on LocalProductService via executor
    mock_instance.search_products.return_value = [PRODUCT_1, PRODUCT_3]
    mock_instance.smart_search_products.return_value = ([PRODUCT_1], "Search successful.")

    return mock_instance # Return the mocked instance for direct manipulation in tests

@pytest.fixture
def product_data_service(mock_local_service):
    """
    Fixture to provide an instance of ProductDataService with a mocked LocalProductService.
    """
    return ProductDataService()

@pytest.mark.asyncio
async def test_init(mock_local_service, caplog):
    """Test ProductDataService initialization and logging."""
    with caplog.at_level(logging.INFO):
        service = ProductDataService()
        mock_local_service.assert_called_once() # Ensures LocalProductService was instantiated
        assert service.local_service is mock_local_service
        assert "ProductDataService initialized with LocalProductService" in caplog.text

@pytest.mark.asyncio
async def test_search_products_success(product_data_service, mock_local_service, caplog):
    """Test search_products with successful results."""
    mock_local_service.search_products.return_value = [PRODUCT_1, PRODUCT_3]
    
    with caplog.at_level(logging.INFO):
        products = await product_data_service.search_products("product", limit=2)
        
        mock_local_service.search_products.assert_called_once_with("product", 2)
        assert products == [PRODUCT_1, PRODUCT_3]
        assert "Searching products with keyword: product" in caplog.text
        assert "Found 2 products for keyword: product" in caplog.text

@pytest.mark.asyncio
async def test_search_products_no_results(product_data_service, mock_local_service, caplog):
    """Test search_products when no products are found."""
    mock_local_service.search_products.return_value = []
    
    with caplog.at_level(logging.INFO):
        products = await product_data_service.search_products("nonexistent", limit=5)
        
        mock_local_service.search_products.assert_called_once_with("nonexistent", 5)
        assert products == []
        assert "Found 0 products for keyword: nonexistent" in caplog.text

@pytest.mark.asyncio
async def test_search_products_exception(product_data_service, mock_local_service, caplog):
    """Test search_products handles exceptions and returns an empty list."""
    mock_local_service.search_products.side_effect = Exception("Mock search error")
    
    with caplog.at_level(logging.ERROR):
        products = await product_data_service.search_products("error", limit=10)
        
        mock_local_service.search_products.assert_called_once_with("error", 10)
        assert products == []
        assert "Error searching products: Mock search error" in caplog.text

# Tests for get_products with its conditional logic
@pytest.mark.asyncio
async def test_get_products_with_search_filter(product_data_service, mock_local_service):
    """Test get_products when a search keyword is provided."""
    mock_local_service.search_products.return_value = [PRODUCT_1]
    
    products = await product_data_service.get_products(limit=5, search="keyword")
    
    mock_local_service.search_products.assert_called_once_with("keyword", 5)
    mock_local_service.get_products_by_category.assert_not_called()
    mock_local_service.get_products.assert_not_called() # get_all_products path
    assert products == [PRODUCT_1]

@pytest.mark.asyncio
async def test_get_products_with_category_filter(product_data_service, mock_local_service):
    """Test get_products when a category is provided (and no search)."""
    mock_local_service.get_products_by_category.return_value = [PRODUCT_1, PRODUCT_3]
    
    products = await product_data_service.get_products(limit=5, category="Electronics")
    
    mock_local_service.get_products_by_category.assert_called_once_with("Electronics")
    mock_local_service.search_products.assert_not_called()
    mock_local_service.get_products.assert_not_called() # get_all_products path
    assert products == [PRODUCT_1, PRODUCT_3]

@pytest.mark.asyncio
async def test_get_products_no_filters(product_data_service, mock_local_service):
    """Test get_products when no filters are provided (calls get_all_products)."""
    mock_local_service.get_products.return_value = PRODUCT_LIST[:2] # Simulate limit effect
    
    products = await product_data_service.get_products(limit=2)
    
    mock_local_service.get_products.assert_called_once_with(2) # Called by get_all_products
    mock_local_service.search_products.assert_not_called()
    mock_local_service.get_products_by_category.assert_not_called()
    assert products == PRODUCT_LIST[:2]

@pytest.mark.asyncio
async def test_get_products_exception_fallback(product_data_service, mock_local_service, caplog):
    """
    Test get_products' exception handling, ensuring it falls back to
    local_service.get_products(limit) if an internal call fails.
    Simulate failure in the get_all_products path.
    """
    # First call (from get_all_products) will fail, triggering the except block
    mock_local_service.get_products.side_effect = [Exception("Internal error in get_all_products"), PRODUCT_LIST[:5]]
    
    with caplog.at_level(logging.ERROR):
        products = await product_data_service.get_products(limit=5)
        
        # local_service.get_products is called once by get_all_products (which fails),
        # and then once as a fallback mechanism directly by get_products.
        assert mock_local_service.get_products.call_count == 2
        assert "Error getting products: Internal error in get_all_products" in caplog.text
        assert products == PRODUCT_LIST[:5] # Result from the fallback call

@pytest.mark.asyncio
async def test_get_categories_success(product_data_service, mock_local_service, caplog):
    """Test get_categories with successful results."""
    mock_local_service.get_categories.return_value = CATEGORY_LIST
    
    categories = await product_data_service.get_categories()
    
    mock_local_service.get_categories.assert_called_once()
    assert categories == CATEGORY_LIST

@pytest.mark.asyncio
async def test_get_categories_exception(product_data_service, mock_local_service, caplog):
    """Test get_categories handles exceptions."""
    mock_local_service.get_categories.side_effect = Exception("Category fetch error")
    
    with caplog.at_level(logging.ERROR):
        categories = await product_data_service.get_categories()
        
        mock_local_service.get_categories.assert_called_once()
        assert categories == []
        assert "Error getting categories: Category fetch error" in caplog.text

@pytest.mark.asyncio
async def test_get_top_rated_products_success(product_data_service, mock_local_service, caplog):
    """Test get_top_rated_products with successful results."""
    mock_local_service.get_top_rated_products.return_value = [PRODUCT_1, PRODUCT_3]
    
    products = await product_data_service.get_top_rated_products(limit=2)
    
    mock_local_service.get_top_rated_products.assert_called_once_with(2)
    assert products == [PRODUCT_1, PRODUCT_3]

@pytest.mark.asyncio
async def test_get_top_rated_products_exception(product_data_service, mock_local_service, caplog):
    """Test get_top_rated_products handles exceptions."""
    mock_local_service.get_top_rated_products.side_effect = Exception("Top rated error")
    
    with caplog.at_level(logging.ERROR):
        products = await product_data_service.get_top_rated_products(limit=5)
        
        mock_local_service.get_top_rated_products.assert_called_once_with(5)
        assert products == []
        assert "Error getting top rated products: Top rated error" in caplog.text

@pytest.mark.asyncio
async def test_get_best_selling_products_success(product_data_service, mock_local_service, caplog):
    """Test get_best_selling_products with successful results."""
    mock_local_service.get_best_selling_products.return_value = [PRODUCT_3, PRODUCT_1]
    
    products = await product_data_service.get_best_selling_products(limit=2)
    
    mock_local_service.get_best_selling_products.assert_called_once_with(2)
    assert products == [PRODUCT_3, PRODUCT_1]

@pytest.mark.asyncio
async def test_get_best_selling_products_exception(product_data_service, mock_local_service, caplog):
    """Test get_best_selling_products handles exceptions."""
    mock_local_service.get_best_selling_products.side_effect = Exception("Best selling error")
    
    with caplog.at_level(logging.ERROR):
        products = await product_data_service.get_best_selling_products(limit=5)
        
        mock_local_service.get_best_selling_products.assert_called_once_with(5)
        assert products == []
        assert "Error getting best selling products: Best selling error" in caplog.text

def test_get_products_by_category_success_with_limit(product_data_service, mock_local_service, caplog):
    """Test get_products_by_category with successful results, applying limit."""
    mock_local_service.get_products_by_category.return_value = [PRODUCT_1, PRODUCT_3, PRODUCT_2] # More than limit
    
    products = product_data_service.get_products_by_category("Electronics", limit=2)
    
    mock_local_service.get_products_by_category.assert_called_once_with("Electronics")
    assert products == [PRODUCT_1, PRODUCT_3]

def test_get_products_by_category_less_than_limit(product_data_service, mock_local_service, caplog):
    """Test get_products_by_category when fewer products than limit are available."""
    mock_local_service.get_products_by_category.return_value = [PRODUCT_1]
    
    products = product_data_service.get_products_by_category("Electronics", limit=5)
    
    mock_local_service.get_products_by_category.assert_called_once_with("Electronics")
    assert products == [PRODUCT_1]

def test_get_products_by_category_no_results(product_data_service, mock_local_service, caplog):
    """Test get_products_by_category with no results."""
    mock_local_service.get_products_by_category.return_value = []
    
    products = product_data_service.get_products_by_category("NonExistent", limit=5)
    
    mock_local_service.get_products_by_category.assert_called_once_with("NonExistent")
    assert products == []

def test_get_products_by_category_exception(product_data_service, mock_local_service, caplog):
    """Test get_products_by_category handles exceptions."""
    mock_local_service.get_products_by_category.side_effect = Exception("Category filter error")
    
    with caplog.at_level(logging.ERROR):
        products = product_data_service.get_products_by_category("Electronics", limit=5)
        
        mock_local_service.get_products_by_category.assert_called_once_with("Electronics")
        assert products == []
        assert "Error getting products by category: Category filter error" in caplog.text

def test_get_all_products_success(product_data_service, mock_local_service, caplog):
    """Test get_all_products with successful results, applying limit."""
    mock_local_service.get_products.return_value = PRODUCT_LIST # More than limit
    
    products = product_data_service.get_all_products(limit=2)
    
    mock_local_service.get_products.assert_called_once_with(2)
    assert products == [PRODUCT_1, PRODUCT_2]

def test_get_all_products_exception(product_data_service, mock_local_service, caplog):
    """Test get_all_products handles exceptions."""
    mock_local_service.get_products.side_effect = Exception("All products error")
    
    with caplog.at_level(logging.ERROR):
        products = product_data_service.get_all_products(limit=5)
        
        mock_local_service.get_products.assert_called_once_with(5)
        assert products == []
        assert "Error getting all products: All products error" in caplog.text

def test_get_product_details_success(product_data_service, mock_local_service, caplog):
    """Test get_product_details with successful result."""
    mock_local_service.get_product_details.return_value = PRODUCT_1
    
    product = product_data_service.get_product_details("1")
    
    mock_local_service.get_product_details.assert_called_once_with("1")
    assert product == PRODUCT_1

def test_get_product_details_not_found(product_data_service, mock_local_service, caplog):
    """Test get_product_details when product is not found."""
    mock_local_service.get_product_details.return_value = None
    
    product = product_data_service.get_product_details("999")
    
    mock_local_service.get_product_details.assert_called_once_with("999")
    assert product is None

def test_get_product_details_exception(product_data_service, mock_local_service, caplog):
    """Test get_product_details handles exceptions."""
    mock_local_service.get_product_details.side_effect = Exception("Details fetch error")
    
    with caplog.at_level(logging.ERROR):
        product = product_data_service.get_product_details("1")
        
        mock_local_service.get_product_details.assert_called_once_with("1")
        assert product is None
        assert "Error getting product details: Details fetch error" in caplog.text

def test_get_brands_success(product_data_service, mock_local_service, caplog):
    """Test get_brands with successful results."""
    mock_local_service.get_brands.return_value = BRAND_LIST
    
    brands = product_data_service.get_brands()
    
    mock_local_service.get_brands.assert_called_once()
    assert brands == BRAND_LIST

def test_get_brands_exception(product_data_service, mock_local_service, caplog):
    """Test get_brands handles exceptions."""
    mock_local_service.get_brands.side_effect = Exception("Brand fetch error")
    
    with caplog.at_level(logging.ERROR):
        brands = product_data_service.get_brands()
        
        mock_local_service.get_brands.assert_called_once()
        assert brands == []
        assert "Error getting brands: Brand fetch error" in caplog.text

def test_get_products_by_brand_success_with_limit(product_data_service, mock_local_service, caplog):
    """Test get_products_by_brand with successful results, applying limit."""
    mock_local_service.get_products_by_brand.return_value = [PRODUCT_1, PRODUCT_3, PRODUCT_2] # More than limit
    
    products = product_data_service.get_products_by_brand("BrandX", limit=2)
    
    mock_local_service.get_products_by_brand.assert_called_once_with("BrandX")
    assert products == [PRODUCT_1, PRODUCT_3]

def test_get_products_by_brand_no_results(product_data_service, mock_local_service, caplog):
    """Test get_products_by_brand with no results."""
    mock_local_service.get_products_by_brand.return_value = []
    
    products = product_data_service.get_products_by_brand("NonExistentBrand", limit=5)
    
    mock_local_service.get_products_by_brand.assert_called_once_with("NonExistentBrand")
    assert products == []

def test_get_products_by_brand_exception(product_data_service, mock_local_service, caplog):
    """Test get_products_by_brand handles exceptions."""
    mock_local_service.get_products_by_brand.side_effect = Exception("Brand filter error")
    
    with caplog.at_level(logging.ERROR):
        products = product_data_service.get_products_by_brand("BrandX", limit=5)
        
        mock_local_service.get_products_by_brand.assert_called_once_with("BrandX")
        assert products == []
        assert "Error getting products by brand: Brand filter error" in caplog.text

@pytest.mark.asyncio
async def test_smart_search_products_success_default_args(product_data_service, mock_local_service):
    """Test smart_search_products with successful results and default arguments."""
    expected_products = [PRODUCT_1]
    expected_message = "Search successful."
    mock_local_service.smart_search_products.return_value = (expected_products, expected_message)
    
    products, message = await product_data_service.smart_search_products(keyword="smart")
    
    mock_local_service.smart_search_products.assert_called_once_with("smart", None, None, 5)
    assert products == expected_products
    assert message == expected_message

@pytest.mark.asyncio
async def test_smart_search_products_with_all_args(product_data_service, mock_local_service):
    """Test smart_search_products with all possible arguments."""
    expected_products = [PRODUCT_3]
    expected_message = "Refined search successful."
    mock_local_service.smart_search_products.return_value = (expected_products, expected_message)
    
    products, message = await product_data_service.smart_search_products(
        keyword="C", category="Electronics", max_price=160, limit=1
    )
    
    mock_local_service.smart_search_products.assert_called_once_with("C", "Electronics", 160, 1)
    assert products == expected_products
    assert message == expected_message

@pytest.mark.asyncio
async def test_smart_search_products_exception(product_data_service, mock_local_service):
    """
    Test smart_search_products handles exceptions.
    Note: The method in source code does not have its own try-except,
    so exceptions are expected to propagate.
    """
    mock_local_service.smart_search_products.side_effect = Exception("Smart search internal error")
    
    with pytest.raises(Exception, match="Smart search internal error"):
        await product_data_service.smart_search_products(keyword="error")
    
    mock_local_service.smart_search_products.assert_called_once_with("error", None, None, 5)