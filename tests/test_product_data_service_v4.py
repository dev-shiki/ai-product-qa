import pytest
import asyncio
import logging
from unittest.mock import MagicMock, patch

# Assume LocalProductService exists for type hinting/mocking purposes.
# In a real project, you'd ensure this import path is correct and the dummy/mocked
# version of LocalProductService is available during testing.
from app.services.local_product_service import LocalProductService

# The class under test
from app.services.product_data_service import ProductDataService

# Configure logging to capture logs during tests
# This is usually done in conftest.py or test setup
# For standalone test file, setting it here for clarity.
logger = logging.getLogger('app.services.product_data_service')
logger.setLevel(logging.INFO)
# Prevent propagation to avoid duplicate output if root logger also handles it
logger.propagate = False

# --- Fixtures ---

@pytest.fixture
def mock_local_product_service():
    """Fixture for a MagicMock instance of LocalProductService."""
    return MagicMock(spec=LocalProductService)

@pytest.fixture
def product_data_service(mock_local_product_service):
    """
    Fixture for ProductDataService instance with mocked LocalProductService.
    Patches LocalProductService during initialization of ProductDataService.
    """
    with patch('app.services.product_data_service.LocalProductService', return_value=mock_local_product_service):
        service = ProductDataService()
        # Assert that the service's internal local_service is indeed our mock
        assert service.local_service is mock_local_product_service
        yield service

# --- Tests ---

def test_product_data_service_init(mock_local_product_service, caplog):
    """
    Test ProductDataService initialization.
    Ensures local_service is correctly set and an info log is emitted.
    """
    with caplog.at_level(logging.INFO):
        with patch('app.services.product_data_service.LocalProductService', return_value=mock_local_product_service):
            service = ProductDataService()
            assert service.local_service is mock_local_product_service
            assert "ProductDataService initialized with LocalProductService" in caplog.text

# Test async methods using asyncio.get_event_loop().run_in_executor
@pytest.mark.asyncio
@patch('asyncio.get_event_loop')
async def test_search_products_success(mock_get_event_loop, product_data_service, mock_local_product_service, caplog):
    """
    Test search_products successful execution.
    Mocks asyncio.get_event_loop().run_in_executor to control its return value.
    """
    mock_loop = MagicMock()
    mock_get_event_loop.return_value = mock_loop
    expected_products = [{"id": "1", "name": "Laptop XYZ", "price": 1200}]
    mock_loop.run_in_executor.return_value = expected_products

    with caplog.at_level(logging.INFO):
        products = await product_data_service.search_products("laptop", limit=5)

        assert products == expected_products
        mock_get_event_loop.assert_called_once()
        mock_loop.run_in_executor.assert_called_once_with(
            None, mock_local_product_service.search_products, "laptop", 5
        )
        assert f"Searching products with keyword: laptop" in caplog.text
        assert f"Found {len(expected_products)} products for keyword: laptop" in caplog.text

@pytest.mark.asyncio
@patch('asyncio.get_event_loop')
async def test_search_products_no_results(mock_get_event_loop, product_data_service, mock_local_product_service, caplog):
    """
    Test search_products when no results are found.
    Ensures an empty list is returned and logs reflect 0 products found.
    """
    mock_loop = MagicMock()
    mock_get_event_loop.return_value = mock_loop
    mock_loop.run_in_executor.return_value = []

    with caplog.at_level(logging.INFO):
        products = await product_data_service.search_products("nonexistent_item")
        assert products == []
        mock_loop.run_in_executor.assert_called_once_with(
            None, mock_local_product_service.search_products, "nonexistent_item", 10
        )
        assert f"Searching products with keyword: nonexistent_item" in caplog.text
        assert f"Found 0 products for keyword: nonexistent_item" in caplog.text

@pytest.mark.asyncio
@patch('asyncio.get_event_loop')
async def test_search_products_error(mock_get_event_loop, product_data_service, mock_local_product_service, caplog):
    """
    Test search_products when an exception occurs during the async call.
    Ensures an empty list is returned and an error log is emitted.
    """
    mock_loop = MagicMock()
    mock_get_event_loop.return_value = mock_loop
    mock_loop.run_in_executor.side_effect = Exception("Local service connection error")

    with caplog.at_level(logging.ERROR):
        products = await product_data_service.search_products("error_test")
        assert products == []
        mock_loop.run_in_executor.assert_called_once_with(
            None, mock_local_product_service.search_products, "error_test", 10
        )
        assert "Error searching products: Local service connection error" in caplog.text

# Test get_products (dispatch method)
@pytest.mark.asyncio
async def test_get_products_with_search(product_data_service):
    """
    Test get_products dispatches to search_products when 'search' keyword is provided.
    Patches search_products method to isolate dispatch logic testing.
    """
    expected_products = [{"id": "s1", "name": "Searched Item"}]
    with patch.object(product_data_service, 'search_products', new_callable=MagicMock) as mock_search_products:
        mock_search_products.return_value = expected_products
        products = await product_data_service.get_products(limit=5, search="query")
        assert products == expected_products
        mock_search_products.assert_called_once_with("query", 5)
        # Ensure other methods are NOT called
        product_data_service.get_products_by_category.assert_not_called()
        product_data_service.get_all_products.assert_not_called()

@pytest.mark.asyncio
async def test_get_products_with_category(product_data_service):
    """
    Test get_products dispatches to get_products_by_category when 'category' is provided.
    Patches get_products_by_category method to isolate dispatch logic testing.
    """
    expected_products = [{"id": "c1", "name": "Category Item"}]
    with patch.object(product_data_service, 'get_products_by_category', new_callable=MagicMock) as mock_get_products_by_category:
        mock_get_products_by_category.return_value = expected_products
        products = await product_data_service.get_products(limit=15, category="electronics")
        assert products == expected_products
        mock_get_products_by_category.assert_called_once_with("electronics", 15)
        # Ensure other methods are NOT called
        product_data_service.search_products.assert_not_called()
        product_data_service.get_all_products.assert_not_called()

@pytest.mark.asyncio
async def test_get_products_without_filters(product_data_service):
    """
    Test get_products dispatches to get_all_products when no filters are provided.
    Patches get_all_products method to isolate dispatch logic testing.
    """
    expected_products = [{"id": "a1", "name": "All Item"}]
    with patch.object(product_data_service, 'get_all_products', new_callable=MagicMock) as mock_get_all_products:
        mock_get_all_products.return_value = expected_products
        products = await product_data_service.get_products(limit=25)
        assert products == expected_products
        mock_get_all_products.assert_called_once_with(25)
        # Ensure other methods are NOT called
        product_data_service.search_products.assert_not_called()
        product_data_service.get_products_by_category.assert_not_called()

@pytest.mark.asyncio
async def test_get_products_error_fallback(product_data_service, mock_local_product_service, caplog):
    """
    Test get_products falls back to local_service.get_products on internal error.
    Simulates an error in one of the dispatched methods and checks fallback.
    """
    mock_local_product_service.get_products.return_value = [{"id": "fb1", "name": "Fallback Product"}]
    # Make one of the internal calls raise an exception to trigger the fallback
    with patch.object(product_data_service, 'get_all_products', side_effect=Exception("Internal processing error")):
        with caplog.at_level(logging.ERROR):
            products = await product_data_service.get_products(limit=10)
            assert products == [{"id": "fb1", "name": "Fallback Product"}]
            mock_local_product_service.get_products.assert_called_once_with(10)
            assert "Error getting products: Internal processing error" in caplog.text

# Test get_categories
@pytest.mark.asyncio
async def test_get_categories_success(product_data_service, mock_local_product_service):
    """Test get_categories successful execution."""
    mock_local_product_service.get_categories.return_value = ["Electronics", "Books", "Clothing"]
    categories = await product_data_service.get_categories()
    assert categories == ["Electronics", "Books", "Clothing"]
    mock_local_product_service.get_categories.assert_called_once()

@pytest.mark.asyncio
async def test_get_categories_error(product_data_service, mock_local_product_service, caplog):
    """Test get_categories error handling."""
    mock_local_product_service.get_categories.side_effect = Exception("Category service down")
    with caplog.at_level(logging.ERROR):
        categories = await product_data_service.get_categories()
        assert categories == []
        mock_local_product_service.get_categories.assert_called_once()
        assert "Error getting categories: Category service down" in caplog.text

# Test get_top_rated_products
@pytest.mark.asyncio
async def test_get_top_rated_products_success(product_data_service, mock_local_product_service):
    """Test get_top_rated_products successful execution."""
    expected_products = [{"id": "tr1", "rating": 5.0, "name": "Highly Rated Gadget"}]
    mock_local_product_service.get_top_rated_products.return_value = expected_products
    products = await product_data_service.get_top_rated_products(limit=3)
    assert products == expected_products
    mock_local_product_service.get_top_rated_products.assert_called_once_with(3)

@pytest.mark.asyncio
async def test_get_top_rated_products_error(product_data_service, mock_local_product_service, caplog):
    """Test get_top_rated_products error handling."""
    mock_local_product_service.get_top_rated_products.side_effect = Exception("Rating service unavailable")
    with caplog.at_level(logging.ERROR):
        products = await product_data_service.get_top_rated_products()
        assert products == []
        mock_local_product_service.get_top_rated_products.assert_called_once_with(10) # Default limit
        assert "Error getting top rated products: Rating service unavailable" in caplog.text

# Test get_best_selling_products
@pytest.mark.asyncio
async def test_get_best_selling_products_success(product_data_service, mock_local_product_service):
    """Test get_best_selling_products successful execution."""
    expected_products = [{"id": "bs1", "sales_count": 1000, "name": "Best Seller Book"}]
    mock_local_product_service.get_best_selling_products.return_value = expected_products
    products = await product_data_service.get_best_selling_products(limit=2)
    assert products == expected_products
    mock_local_product_service.get_best_selling_products.assert_called_once_with(2)

@pytest.mark.asyncio
async def test_get_best_selling_products_error(product_data_service, mock_local_product_service, caplog):
    """Test get_best_selling_products error handling."""
    mock_local_product_service.get_best_selling_products.side_effect = Exception("Sales data corrupted")
    with caplog.at_level(logging.ERROR):
        products = await product_data_service.get_best_selling_products()
        assert products == []
        mock_local_product_service.get_best_selling_products.assert_called_once_with(10) # Default limit
        assert "Error getting best selling products: Sales data corrupted" in caplog.text

# Test get_products_by_category (sync method)
def test_get_products_by_category_success(product_data_service, mock_local_product_service):
    """
    Test get_products_by_category successful execution with limit.
    Ensures the correct category is queried and results are correctly limited.
    """
    mock_local_product_service.get_products_by_category.return_value = [
        {"id": "c1", "name": "Coffee Maker", "category": "kitchen"},
        {"id": "c2", "name": "Blender", "category": "kitchen"},
        {"id": "c3", "name": "Toaster", "category": "kitchen"},
        {"id": "c4", "name": "Microwave", "category": "kitchen"}
    ]
    products = product_data_service.get_products_by_category("kitchen", limit=2)
    assert products == [
        {"id": "c1", "name": "Coffee Maker", "category": "kitchen"},
        {"id": "c2", "name": "Blender", "category": "kitchen"}
    ]
    mock_local_product_service.get_products_by_category.assert_called_once_with("kitchen")

def test_get_products_by_category_no_results(product_data_service, mock_local_product_service):
    """Test get_products_by_category when no products are found for a category."""
    mock_local_product_service.get_products_by_category.return_value = []
    products = product_data_service.get_products_by_category("nonexistent_category")
    assert products == []
    mock_local_product_service.get_products_by_category.assert_called_once_with("nonexistent_category")

def test_get_products_by_category_error(product_data_service, mock_local_product_service, caplog):
    """Test get_products_by_category error handling."""
    mock_local_product_service.get_products_by_category.side_effect = Exception("Category DB read error")
    with caplog.at_level(logging.ERROR):
        products = product_data_service.get_products_by_category("error_category")
        assert products == []
        mock_local_product_service.get_products_by_category.assert_called_once_with("error_category")
        assert "Error getting products by category: Category DB read error" in caplog.text

# Test get_all_products (sync method)
def test_get_all_products_success(product_data_service, mock_local_product_service):
    """Test get_all_products successful execution."""
    expected_products = [{"id": "a1", "name": "Product A"}, {"id": "a2", "name": "Product B"}]
    mock_local_product_service.get_products.return_value = expected_products
    products = product_data_service.get_all_products(limit=2)
    assert products == expected_products
    mock_local_product_service.get_products.assert_called_once_with(2)

def test_get_all_products_error(product_data_service, mock_local_product_service, caplog):
    """Test get_all_products error handling."""
    mock_local_product_service.get_products.side_effect = Exception("Generic product data fetch error")
    with caplog.at_level(logging.ERROR):
        products = product_data_service.get_all_products()
        assert products == []
        mock_local_product_service.get_products.assert_called_once_with(20) # Default limit
        assert "Error getting all products: Generic product data fetch error" in caplog.text

# Test get_product_details (sync method)
def test_get_product_details_found(product_data_service, mock_local_product_service):
    """Test get_product_details when product is found."""
    expected_details = {"id": "p123", "name": "Specific Widget", "description": "A very useful item."}
    mock_local_product_service.get_product_details.return_value = expected_details
    details = product_data_service.get_product_details("p123")
    assert details == expected_details
    mock_local_product_service.get_product_details.assert_called_once_with("p123")

def test_get_product_details_not_found(product_data_service, mock_local_product_service):
    """Test get_product_details when product is not found (returns None)."""
    mock_local_product_service.get_product_details.return_value = None
    details = product_data_service.get_product_details("p999")
    assert details is None
    mock_local_product_service.get_product_details.assert_called_once_with("p999")

def test_get_product_details_error(product_data_service, mock_local_product_service, caplog):
    """Test get_product_details error handling."""
    mock_local_product_service.get_product_details.side_effect = Exception("Details service unavailable")
    with caplog.at_level(logging.ERROR):
        details = product_data_service.get_product_details("p_error")
        assert details is None
        mock_local_product_service.get_product_details.assert_called_once_with("p_error")
        assert "Error getting product details: Details service unavailable" in caplog.text

# Test get_brands (sync method)
def test_get_brands_success(product_data_service, mock_local_product_service):
    """Test get_brands successful execution."""
    mock_local_product_service.get_brands.return_value = ["BrandX", "BrandY", "BrandZ"]
    brands = product_data_service.get_brands()
    assert brands == ["BrandX", "BrandY", "BrandZ"]
    mock_local_product_service.get_brands.assert_called_once()

def test_get_brands_error(product_data_service, mock_local_product_service, caplog):
    """Test get_brands error handling."""
    mock_local_product_service.get_brands.side_effect = Exception("Brand data source error")
    with caplog.at_level(logging.ERROR):
        brands = product_data_service.get_brands()
        assert brands == []
        mock_local_product_service.get_brands.assert_called_once()
        assert "Error getting brands: Brand data source error" in caplog.text

# Test get_products_by_brand (sync method)
def test_get_products_by_brand_success(product_data_service, mock_local_product_service):
    """
    Test get_products_by_brand successful execution with limit.
    Ensures the correct brand is queried and results are correctly limited.
    """
    mock_local_product_service.get_products_by_brand.return_value = [
        {"id": "b1", "name": "Shoe A", "brand": "Nike"},
        {"id": "b2", "name": "Shoe B", "brand": "Nike"},
        {"id": "b3", "name": "Shoe C", "brand": "Nike"}
    ]
    products = product_data_service.get_products_by_brand("Nike", limit=2)
    assert products == [
        {"id": "b1", "name": "Shoe A", "brand": "Nike"},
        {"id": "b2", "name": "Shoe B", "brand": "Nike"}
    ]
    mock_local_product_service.get_products_by_brand.assert_called_once_with("Nike")

def test_get_products_by_brand_no_results(product_data_service, mock_local_product_service):
    """Test get_products_by_brand when no products are found for a brand."""
    mock_local_product_service.get_products_by_brand.return_value = []
    products = product_data_service.get_products_by_brand("nonexistent_brand")
    assert products == []
    mock_local_product_service.get_products_by_brand.assert_called_once_with("nonexistent_brand")

def test_get_products_by_brand_error(product_data_service, mock_local_product_service, caplog):
    """Test get_products_by_brand error handling."""
    mock_local_product_service.get_products_by_brand.side_effect = Exception("Brand filter error")
    with caplog.at_level(logging.ERROR):
        products = product_data_service.get_products_by_brand("error_brand")
        assert products == []
        mock_local_product_service.get_products_by_brand.assert_called_once_with("error_brand")
        assert "Error getting products by brand: Brand filter error" in caplog.text

# Test smart_search_products (async method with run_in_executor)
@pytest.mark.asyncio
@patch('asyncio.get_event_loop')
async def test_smart_search_products_success(mock_get_event_loop, product_data_service, mock_local_product_service):
    """
    Test smart_search_products successful execution.
    Mocks asyncio.get_event_loop().run_in_executor to control its return value.
    """
    mock_loop = MagicMock()
    mock_get_event_loop.return_value = mock_loop
    expected_products = [{"id": "ss1", "name": "Smart Speaker"}, {"id": "ss2", "name": "Smart Watch"}]
    expected_message = "Smart search completed with 2 results."
    mock_loop.run_in_executor.return_value = (expected_products, expected_message)

    products, message = await product_data_service.smart_search_products(
        keyword="smart", category="electronics", max_price=200, limit=2
    )

    assert products == expected_products
    assert message == expected_message
    mock_get_event_loop.assert_called_once()
    mock_loop.run_in_executor.assert_called_once_with(
        None, mock_local_product_service.smart_search_products, "smart", "electronics", 200, 2
    )

@pytest.mark.asyncio
@patch('asyncio.get_event_loop')
async def test_smart_search_products_default_params(mock_get_event_loop, product_data_service, mock_local_product_service):
    """
    Test smart_search_products with default parameters.
    """
    mock_loop = MagicMock()
    mock_get_event_loop.return_value = mock_loop
    expected_products = [{"id": "def1", "name": "Default Product"}]
    expected_message = "Default search completed."
    mock_loop.run_in_executor.return_value = (expected_products, expected_message)

    products, message = await product_data_service.smart_search_products()

    assert products == expected_products
    assert message == expected_message
    mock_loop.run_in_executor.assert_called_once_with(
        None, mock_local_product_service.smart_search_products, '', None, None, 5 # Default values
    )

@pytest.mark.asyncio
@patch('asyncio.get_event_loop')
async def test_smart_search_products_error_propagation(mock_get_event_loop, product_data_service, mock_local_product_service):
    """
    Test smart_search_products propagates exceptions from run_in_executor
    as it does not have its own try-except block.
    """
    mock_loop = MagicMock()
    mock_get_event_loop.return_value = mock_loop
    mock_loop.run_in_executor.side_effect = ValueError("Invalid search parameters provided to local service")

    with pytest.raises(ValueError, match="Invalid search parameters provided to local service"):
        await product_data_service.smart_search_products(keyword="invalid")

    mock_loop.run_in_executor.assert_called_once_with(
        None, mock_local_product_service.smart_search_products, "invalid", None, None, 5
    )