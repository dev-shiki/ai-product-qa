import pytest
from unittest.mock import MagicMock, AsyncMock
import logging
import sys
import os

# Adjust the path to import from the app directory correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.services.product_data_service import ProductDataService
# No need to import LocalProductService directly as it will be mocked

@pytest.fixture
def mock_local_product_service(mocker):
    """
    Fixture to mock the LocalProductService class.
    ProductDataService will use an instance of this mocked class.
    """
    # Patch the LocalProductService class itself where it's imported in product_data_service.py
    mock_service_class = mocker.patch('app.services.product_data_service.LocalProductService')
    # Return the mock instance that ProductDataService's __init__ will use
    return mock_service_class.return_value

@pytest.fixture
def product_data_service(mock_local_product_service):
    """
    Fixture to provide an instance of ProductDataService with mocked dependencies.
    """
    return ProductDataService()

@pytest.fixture(autouse=True)
def setup_logging(caplog):
    """
    Fixture to set logging level for tests and capture logs.
    """
    caplog.set_level(logging.INFO)
    yield # Allow test to run
    caplog.clear() # Clear logs after each test

# --- Test __init__ ---
class TestProductDataServiceInit:
    def test_init_sets_local_service_and_logs(self, mock_local_product_service, product_data_service, caplog):
        """
        Test that ProductDataService initializes LocalProductService and logs an info message.
        """
        # Verify LocalProductService constructor was called once
        mock_local_product_service.assert_called_once()
        # Verify the local_service attribute is indeed our mock instance
        assert isinstance(product_data_service.local_service, MagicMock)
        # Verify the initialization log message
        assert "ProductDataService initialized with LocalProductService" in caplog.text
        assert caplog.records[-1].levelname == "INFO"

# --- Test search_products (async) ---
class TestSearchProducts:
    @pytest.mark.asyncio
    async def test_search_products_success_default_limit(self, product_data_service, mock_local_product_service):
        """
        Test search_products returns products successfully with default limit.
        """
        expected_products = [{"id": "1", "name": "Laptop"}, {"id": "2", "name": "Mouse"}]
        mock_local_product_service.search_products.return_value = expected_products

        products = await product_data_service.search_products("tech")

        # Verify the underlying LocalProductService method was called with correct arguments
        mock_local_product_service.search_products.assert_called_once_with("tech", 10)
        assert products == expected_products

    @pytest.mark.asyncio
    async def test_search_products_success_custom_limit(self, product_data_service, mock_local_product_service):
        """
        Test search_products returns products successfully with a custom limit.
        """
        expected_products = [{"id": "3", "name": "Keyboard"}]
        mock_local_product_service.search_products.return_value = expected_products

        products = await product_data_service.search_products("keyboard", limit=1)

        mock_local_product_service.search_products.assert_called_once_with("keyboard", 1)
        assert products == expected_products

    @pytest.mark.asyncio
    async def test_search_products_no_results(self, product_data_service, mock_local_product_service):
        """
        Test search_products returns an empty list when no products are found.
        """
        mock_local_product_service.search_products.return_value = []

        products = await product_data_service.search_products("nonexistent")

        mock_local_product_service.search_products.assert_called_once_with("nonexistent", 10)
        assert products == []

    @pytest.mark.asyncio
    async def test_search_products_exception_handling(self, product_data_service, mock_local_product_service, caplog):
        """
        Test search_products handles exceptions gracefully, returning an empty list and logging.
        """
        mock_local_product_service.search_products.side_effect = Exception("Service unavailable")

        products = await product_data_service.search_products("error_case")

        mock_local_product_service.search_products.assert_called_once_with("error_case", 10)
        assert products == []
        assert "Error searching products: Service unavailable" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

# --- Test get_products (async) ---
class TestGetProducts:
    @pytest.mark.asyncio
    async def test_get_products_with_search_param(self, product_data_service, mock_local_product_service, mocker):
        """
        Test get_products correctly delegates to search_products when 'search' is provided.
        """
        mock_search_products = mocker.patch.object(product_data_service, 'search_products', new_callable=AsyncMock)
        mock_search_products.return_value = [{"id": "s1", "name": "Searched Item"}]

        products = await product_data_service.get_products(search="test_search", limit=5)

        mock_search_products.assert_called_once_with("test_search", 5)
        # Ensure that LocalProductService's search_products was not directly called (it would be via the patched method)
        mock_local_product_service.search_products.assert_not_called()
        assert products == [{"id": "s1", "name": "Searched Item"}]

    @pytest.mark.asyncio
    async def test_get_products_with_category_param(self, product_data_service, mock_local_product_service, mocker):
        """
        Test get_products correctly delegates to get_products_by_category when 'category' is provided.
        """
        mock_get_products_by_category = mocker.patch.object(product_data_service, 'get_products_by_category')
        mock_get_products_by_category.return_value = [{"id": "c1", "name": "Category Item"}]

        products = await product_data_service.get_products(category="electronics", limit=15)

        mock_get_products_by_category.assert_called_once_with("electronics", 15)
        mock_local_product_service.get_products_by_category.assert_not_called()
        assert products == [{"id": "c1", "name": "Category Item"}]

    @pytest.mark.asyncio
    async def test_get_products_no_params(self, product_data_service, mock_local_product_service, mocker):
        """
        Test get_products correctly delegates to get_all_products when no 'search' or 'category' is provided.
        """
        mock_get_all_products = mocker.patch.object(product_data_service, 'get_all_products')
        mock_get_all_products.return_value = [{"id": "a1", "name": "All Items"}]

        products = await product_data_service.get_products(limit=10)

        mock_get_all_products.assert_called_once_with(10)
        mock_local_product_service.get_products.assert_not_called()
        assert products == [{"id": "a1", "name": "All Items"}]

    @pytest.mark.asyncio
    async def test_get_products_exception_fallback(self, product_data_service, mock_local_product_service, mocker, caplog):
        """
        Test get_products handles internal exceptions by falling back to local_service.get_products.
        """
        # Simulate an error in the internal delegated method (e.g., get_all_products)
        mocker.patch.object(product_data_service, 'get_all_products', side_effect=Exception("Internal delegation error"))
        
        # Configure the fallback method's return value
        mock_local_product_service.get_products.return_value = [{"id": "f1", "name": "Fallback Item"}]

        products = await product_data_service.get_products(limit=5)

        mock_local_product_service.get_products.assert_called_once_with(5) # Verify fallback was called
        assert products == [{"id": "f1", "name": "Fallback Item"}]
        assert "Error getting products: Internal delegation error" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

# --- Test get_categories (async) ---
class TestGetCategories:
    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service, mock_local_product_service):
        """
        Test get_categories returns a list of categories on success.
        """
        expected_categories = ["Electronics", "Books", "Clothing"]
        mock_local_product_service.get_categories.return_value = expected_categories

        categories = await product_data_service.get_categories()

        mock_local_product_service.get_categories.assert_called_once()
        assert categories == expected_categories

    @pytest.mark.asyncio
    async def test_get_categories_exception_handling(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_categories returns an empty list and logs error on exception.
        """
        mock_local_product_service.get_categories.side_effect = Exception("Category service down")

        categories = await product_data_service.get_categories()

        mock_local_product_service.get_categories.assert_called_once()
        assert categories == []
        assert "Error getting categories: Category service down" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

# --- Test get_top_rated_products (async) ---
class TestGetTopRatedProducts:
    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service, mock_local_product_service):
        """
        Test get_top_rated_products returns products on success.
        """
        expected_products = [{"id": "tr1", "rating": 5.0}]
        mock_local_product_service.get_top_rated_products.return_value = expected_products

        products = await product_data_service.get_top_rated_products(limit=1)

        mock_local_product_service.get_top_rated_products.assert_called_once_with(1)
        assert products == expected_products

    @pytest.mark.asyncio
    async def test_get_top_rated_products_exception_handling(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_top_rated_products returns empty list and logs error on exception.
        """
        mock_local_product_service.get_top_rated_products.side_effect = Exception("Top rated error")

        products = await product_data_service.get_top_rated_products()

        mock_local_product_service.get_top_rated_products.assert_called_once_with(10) # default limit
        assert products == []
        assert "Error getting top rated products: Top rated error" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

# --- Test get_best_selling_products (async) ---
class TestGetBestSellingProducts:
    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service, mock_local_product_service):
        """
        Test get_best_selling_products returns products on success.
        """
        expected_products = [{"id": "bs1", "sales": 999}]
        mock_local_product_service.get_best_selling_products.return_value = expected_products

        products = await product_data_service.get_best_selling_products(limit=1)

        mock_local_product_service.get_best_selling_products.assert_called_once_with(1)
        assert products == expected_products

    @pytest.mark.asyncio
    async def test_get_best_selling_products_exception_handling(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_best_selling_products returns empty list and logs error on exception.
        """
        mock_local_product_service.get_best_selling_products.side_effect = Exception("Best selling error")

        products = await product_data_service.get_best_selling_products()

        mock_local_product_service.get_best_selling_products.assert_called_once_with(10) # default limit
        assert products == []
        assert "Error getting best selling products: Best selling error" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

# --- Test get_products_by_category (sync) ---
class TestGetProductsByCategory:
    def test_get_products_by_category_success(self, product_data_service, mock_local_product_service):
        """
        Test get_products_by_category returns products for a specific category, respecting limit.
        """
        all_category_products = [
            {"id": "c1", "name": "Item 1", "category": "Gadgets"},
            {"id": "c2", "name": "Item 2", "category": "Gadgets"},
            {"id": "c3", "name": "Item 3", "category": "Gadgets"},
        ]
        mock_local_product_service.get_products_by_category.return_value = all_category_products

        products = product_data_service.get_products_by_category("Gadgets", limit=2)

        mock_local_product_service.get_products_by_category.assert_called_once_with("Gadgets")
        assert products == all_category_products[:2]

    def test_get_products_by_category_less_than_limit(self, product_data_service, mock_local_product_service):
        """
        Test get_products_by_category returns fewer products if available count is less than limit.
        """
        mock_local_product_service.get_products_by_category.return_value = [
            {"id": "c1", "name": "Item 1", "category": "Gadgets"},
        ]
        products = product_data_service.get_products_by_category("Gadgets", limit=5)
        assert len(products) == 1
        assert products[0]["id"] == "c1"

    def test_get_products_by_category_exception_handling(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_products_by_category returns empty list and logs error on exception.
        """
        mock_local_product_service.get_products_by_category.side_effect = Exception("Category lookup error")

        products = product_data_service.get_products_by_category("InvalidCategory")

        mock_local_product_service.get_products_by_category.assert_called_once_with("InvalidCategory")
        assert products == []
        assert "Error getting products by category: Category lookup error" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

# --- Test get_all_products (sync) ---
class TestGetAllProducts:
    def test_get_all_products_success(self, product_data_service, mock_local_product_service):
        """
        Test get_all_products returns all products, respecting limit.
        """
        all_products_data = [{"id": "p1"}, {"id": "p2"}, {"id": "p3"}]
        mock_local_product_service.get_products.return_value = all_products_data

        products = product_data_service.get_all_products(limit=2)

        mock_local_product_service.get_products.assert_called_once_with(2)
        assert products == [{"id": "p1"}, {"id": "p2"}]

    def test_get_all_products_success_default_limit(self, product_data_service, mock_local_product_service):
        """
        Test get_all_products returns all products with default limit.
        """
        all_products_data = [{"id": f"p{i}"} for i in range(25)]
        mock_local_product_service.get_products.return_value = all_products_data

        products = product_data_service.get_all_products()

        mock_local_product_service.get_products.assert_called_once_with(20)
        assert len(products) == 20

    def test_get_all_products_exception_handling(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_all_products returns empty list and logs error on exception.
        """
        mock_local_product_service.get_products.side_effect = Exception("All products service error")

        products = product_data_service.get_all_products()

        mock_local_product_service.get_products.assert_called_once_with(20)
        assert products == []
        assert "Error getting all products: All products service error" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

# --- Test get_product_details (sync) ---
class TestGetProductDetails:
    def test_get_product_details_success_found(self, product_data_service, mock_local_product_service):
        """
        Test get_product_details returns product details when found.
        """
        expected_details = {"id": "prod123", "name": "Specific Product", "price": 100.0}
        mock_local_product_service.get_product_details.return_value = expected_details

        details = product_data_service.get_product_details("prod123")

        mock_local_product_service.get_product_details.assert_called_once_with("prod123")
        assert details == expected_details

    def test_get_product_details_success_not_found(self, product_data_service, mock_local_product_service):
        """
        Test get_product_details returns None when product is not found.
        """
        mock_local_product_service.get_product_details.return_value = None

        details = product_data_service.get_product_details("nonexistent_id")

        mock_local_product_service.get_product_details.assert_called_once_with("nonexistent_id")
        assert details is None

    def test_get_product_details_exception_handling(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_product_details returns None and logs error on exception.
        """
        mock_local_product_service.get_product_details.side_effect = Exception("Details lookup failed")

        details = product_data_service.get_product_details("error_id")

        mock_local_product_service.get_product_details.assert_called_once_with("error_id")
        assert details is None
        assert "Error getting product details: Details lookup failed" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

# --- Test get_brands (sync) ---
class TestGetBrands:
    def test_get_brands_success(self, product_data_service, mock_local_product_service):
        """
        Test get_brands returns a list of brands on success.
        """
        expected_brands = ["Nike", "Adidas", "Puma"]
        mock_local_product_service.get_brands.return_value = expected_brands

        brands = product_data_service.get_brands()

        mock_local_product_service.get_brands.assert_called_once()
        assert brands == expected_brands

    def test_get_brands_exception_handling(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_brands returns empty list and logs error on exception.
        """
        mock_local_product_service.get_brands.side_effect = Exception("Brand service error")

        brands = product_data_service.get_brands()

        mock_local_product_service.get_brands.assert_called_once()
        assert brands == []
        assert "Error getting brands: Brand service error" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

# --- Test get_products_by_brand (sync) ---
class TestGetProductsByBrand:
    def test_get_products_by_brand_success(self, product_data_service, mock_local_product_service):
        """
        Test get_products_by_brand returns products for a specific brand, respecting limit.
        """
        all_brand_products = [
            {"id": "b1", "name": "Brand A Item 1", "brand": "BrandA"},
            {"id": "b2", "name": "Brand A Item 2", "brand": "BrandA"},
            {"id": "b3", "name": "Brand A Item 3", "brand": "BrandA"},
        ]
        mock_local_product_service.get_products_by_brand.return_value = all_brand_products

        products = product_data_service.get_products_by_brand("BrandA", limit=2)

        mock_local_product_service.get_products_by_brand.assert_called_once_with("BrandA")
        assert products == all_brand_products[:2]

    def test_get_products_by_brand_less_than_limit(self, product_data_service, mock_local_product_service):
        """
        Test get_products_by_brand returns fewer products if available count is less than limit.
        """
        mock_local_product_service.get_products_by_brand.return_value = [
            {"id": "b1", "name": "Brand A Item 1", "brand": "BrandA"},
        ]
        products = product_data_service.get_products_by_brand("BrandA", limit=5)
        assert len(products) == 1
        assert products[0]["id"] == "b1"

    def test_get_products_by_brand_exception_handling(self, product_data_service, mock_local_product_service, caplog):
        """
        Test get_products_by_brand returns empty list and logs error on exception.
        """
        mock_local_product_service.get_products_by_brand.side_effect = Exception("Brand lookup error")

        products = product_data_service.get_products_by_brand("InvalidBrand")

        mock_local_product_service.get_products_by_brand.assert_called_once_with("InvalidBrand")
        assert products == []
        assert "Error getting products by brand: Brand lookup error" in caplog.text
        assert caplog.records[-1].levelname == "ERROR"

# --- Test smart_search_products (async) ---
class TestSmartSearchProducts:
    @pytest.mark.asyncio
    async def test_smart_search_products_success(self, product_data_service, mock_local_product_service):
        """
        Test smart_search_products returns products and message on successful search.
        """
        expected_products = [{"id": "smarter1", "name": "Smart Product A"}]
        expected_message = "Found 1 matching product."
        mock_local_product_service.smart_search_products.return_value = (expected_products, expected_message)

        products, message = await product_data_service.smart_search_products(
            keyword="smart", category="electronics", max_price=500, limit=2
        )

        mock_local_product_service.smart_search_products.assert_called_once_with(
            "smart", "electronics", 500, 2
        )
        assert products == expected_products
        assert message == expected_message

    @pytest.mark.asyncio
    async def test_smart_search_products_success_default_args(self, product_data_service, mock_local_product_service):
        """
        Test smart_search_products with all default arguments.
        """
        expected_products = [{"id": "smarter2", "name": "Default Search Result"}]
        expected_message = "Default search results."
        mock_local_product_service.smart_search_products.return_value = (expected_products, expected_message)

        products, message = await product_data_service.smart_search_products()

        mock_local_product_service.smart_search_products.assert_called_once_with(
            '', None, None, 5 # Default values from method signature
        )
        assert products == expected_products
        assert message == expected_message

    @pytest.mark.asyncio
    async def test_smart_search_products_exception_propagation(self, product_data_service, mock_local_product_service):
        """
        Test smart_search_products propagates exceptions as per its current implementation (no internal try-except).
        """
        mock_local_product_service.smart_search_products.side_effect = Exception("Smart search backend error")

        with pytest.raises(Exception) as excinfo:
            await product_data_service.smart_search_products("fail_case")
        
        assert "Smart search backend error" in str(excinfo.value)
        mock_local_product_service.smart_search_products.assert_called_once_with("fail_case", None, None, 5)