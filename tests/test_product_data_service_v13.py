import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.product_data_service import ProductDataService
# No need to import LocalProductService directly here, as we patch its path

# --- Fixtures ---

@pytest.fixture
def mock_local_service():
    """
    Fixture to mock LocalProductService globally for ProductDataService.
    Patches LocalProductService in the module where ProductDataService is defined.
    """
    with patch('app.services.product_data_service.LocalProductService') as MockLocalServiceClass:
        # Configure the mock instance that ProductDataService will use
        mock_instance = MockLocalServiceClass.return_value
        yield mock_instance

@pytest.fixture
def product_data_service(mock_local_service):
    """
    Fixture to provide an instance of ProductDataService with a mocked LocalProductService.
    The __init__ method will be called during this fixture setup.
    """
    service = ProductDataService()
    return service

# --- Test Cases ---

class TestProductDataService:
    """
    Comprehensive test suite for ProductDataService.
    Covers all methods, success paths, error paths, and edge cases.
    """

    @pytest.mark.asyncio
    async def test_init(self, mock_local_service, caplog):
        """
        Test that ProductDataService initializes correctly and logs an info message.
        """
        with caplog.at_level('INFO'):
            # Re-initialize ProductDataService to capture init logs within this test
            service = ProductDataService()
            mock_local_service.assert_called_once_with() # Assert LocalProductService was instantiated
            assert "ProductDataService initialized with LocalProductService" in caplog.text

    @pytest.mark.asyncio
    async def test_search_products_success(self, product_data_service, mock_local_service):
        """
        Test successful product search.
        Ensures local_service.search_products is called via run_in_executor and returns data.
        """
        expected_products = [{"id": "1", "name": "Laptop A", "price": 1200}]
        mock_local_service.search_products.return_value = expected_products

        result = await product_data_service.search_products("laptop", 5)

        mock_local_service.search_products.assert_called_once_with("laptop", 5)
        assert result == expected_products
        # Verify logging of found products (optional, but good for coverage)
        # Note: caplog from fixture is not cleared between tests by default, consider clearing or checking specific logs.

    @pytest.mark.asyncio
    async def test_search_products_no_results(self, product_data_service, mock_local_service):
        """
        Test product search returning no results.
        """
        mock_local_service.search_products.return_value = []

        result = await product_data_service.search_products("nonexistent", 10)

        mock_local_service.search_products.assert_called_once_with("nonexistent", 10)
        assert result == []

    @pytest.mark.asyncio
    async def test_search_products_exception(self, product_data_service, mock_local_service, caplog):
        """
        Test product search handling exceptions.
        Ensures an error is logged and an empty list is returned.
        """
        mock_local_service.search_products.side_effect = Exception("Search failed")

        with caplog.at_level('ERROR'):
            result = await product_data_service.search_products("error_test", 5)

            mock_local_service.search_products.assert_called_once_with("error_test", 5)
            assert result == []
            assert "Error searching products: Search failed" in caplog.text

    @pytest.mark.asyncio
    async def test_get_products_with_search(self, product_data_service, mock_local_service):
        """
        Test get_products when a search keyword is provided.
        Should delegate to search_products.
        """
        expected_products = [{"id": "2", "name": "Keyboard B"}]
        # Patch the internal `search_products` method of the service instance
        with patch.object(product_data_service, 'search_products', new_callable=AsyncMock) as mock_search_products:
            mock_search_products.return_value = expected_products
            result = await product_data_service.get_products(search="keyboard", limit=5)

            mock_search_products.assert_called_once_with("keyboard", 5)
            # Ensure the underlying mock_local_service was not called for this path
            mock_local_service.get_products.assert_not_called()
            assert result == expected_products

    @pytest.mark.asyncio
    async def test_get_products_with_category(self, product_data_service, mock_local_service):
        """
        Test get_products when a category is provided.
        Should delegate to get_products_by_category.
        """
        expected_products = [{"id": "3", "name": "Mouse C", "category": "Electronics"}]
        # Patch the internal `get_products_by_category` method of the service instance
        with patch.object(product_data_service, 'get_products_by_category') as mock_get_by_category:
            mock_get_by_category.return_value = expected_products
            result = await product_data_service.get_products(category="Electronics", limit=10)

            mock_get_by_category.assert_called_once_with("Electronics", 10)
            mock_local_service.get_products.assert_not_called()
            assert result == expected_products

    @pytest.mark.asyncio
    async def test_get_products_no_filters(self, product_data_service, mock_local_service):
        """
        Test get_products when no filters are provided.
        Should delegate to get_all_products.
        """
        expected_products = [{"id": "4", "name": "Monitor D"}]
        # Patch the internal `get_all_products` method of the service instance
        with patch.object(product_data_service, 'get_all_products') as mock_get_all_products:
            mock_get_all_products.return_value = expected_products
            result = await product_data_service.get_products(limit=15)

            mock_get_all_products.assert_called_once_with(15)
            mock_local_service.get_products.assert_not_called()
            assert result == expected_products

    @pytest.mark.asyncio
    async def test_get_products_exception_fallback(self, product_data_service, mock_local_service, caplog):
        """
        Test get_products handling exceptions within its own logic.
        Should log an error and fall back to local_service.get_products.
        We'll force an exception in one of its internal calls (e.g., get_products_by_category).
        """
        fallback_products = [{"id": "fallback", "name": "Fallback Product"}]
        mock_local_service.get_products.return_value = fallback_products

        # Patch get_products_by_category to raise an exception when called by get_products
        with patch.object(product_data_service, 'get_products_by_category', side_effect=Exception("Internal error")):
            with caplog.at_level('ERROR'):
                result = await product_data_service.get_products(category="Electronics", limit=10)

                assert result == fallback_products
                mock_local_service.get_products.assert_called_once_with(10) # Ensure fallback call
                assert "Error getting products: Internal error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service, mock_local_service):
        """
        Test successful retrieval of categories.
        """
        expected_categories = ["Electronics", "Books", "Clothing"]
        mock_local_service.get_categories.return_value = expected_categories

        result = await product_data_service.get_categories()

        mock_local_service.get_categories.assert_called_once_with()
        assert result == expected_categories

    @pytest.mark.asyncio
    async def test_get_categories_exception(self, product_data_service, mock_local_service, caplog):
        """
        Test get_categories handling exceptions.
        Ensures an error is logged and an empty list is returned.
        """
        mock_local_service.get_categories.side_effect = Exception("Category error")

        with caplog.at_level('ERROR'):
            result = await product_data_service.get_categories()

            mock_local_service.get_categories.assert_called_once_with()
            assert result == []
            assert "Error getting categories: Category error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service, mock_local_service):
        """
        Test successful retrieval of top-rated products.
        """
        expected_products = [{"id": "5", "name": "5-star Product"}]
        mock_local_service.get_top_rated_products.return_value = expected_products

        result = await product_data_service.get_top_rated_products(limit=3)

        mock_local_service.get_top_rated_products.assert_called_once_with(3)
        assert result == expected_products

    @pytest.mark.asyncio
    async def test_get_top_rated_products_exception(self, product_data_service, mock_local_service, caplog):
        """
        Test get_top_rated_products handling exceptions.
        Ensures an error is logged and an empty list is returned.
        """
        mock_local_service.get_top_rated_products.side_effect = Exception("Top rated error")

        with caplog.at_level('ERROR'):
            result = await product_data_service.get_top_rated_products(limit=5)

            mock_local_service.get_top_rated_products.assert_called_once_with(5)
            assert result == []
            assert "Error getting top rated products: Top rated error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service, mock_local_service):
        """
        Test successful retrieval of best-selling products.
        """
        expected_products = [{"id": "6", "name": "Best Seller A"}]
        mock_local_service.get_best_selling_products.return_value = expected_products

        result = await product_data_service.get_best_selling_products(limit=2)

        mock_local_service.get_best_selling_products.assert_called_once_with(2)
        assert result == expected_products

    @pytest.mark.asyncio
    async def test_get_best_selling_products_exception(self, product_data_service, mock_local_service, caplog):
        """
        Test get_best_selling_products handling exceptions.
        Ensures an error is logged and an empty list is returned.
        """
        mock_local_service.get_best_selling_products.side_effect = Exception("Best selling error")

        with caplog.at_level('ERROR'):
            result = await product_data_service.get_best_selling_products(limit=4)

            mock_local_service.get_best_selling_products.assert_called_once_with(4)
            assert result == []
            assert "Error getting best selling products: Best selling error" in caplog.text

    def test_get_products_by_category_success(self, product_data_service, mock_local_service):
        """
        Test successful retrieval of products by category, ensuring limit slicing works.
        """
        # Ensure the mock returns more items than the limit to properly test slicing
        all_category_products = [
            {"id": "c1", "name": "Item C1"},
            {"id": "c2", "name": "Item C2"},
            {"id": "c3", "name": "Item C3"},
            {"id": "c4", "name": "Item C4"},
        ]
        mock_local_service.get_products_by_category.return_value = all_category_products

        result = product_data_service.get_products_by_category("Electronics", 2)

        mock_local_service.get_products_by_category.assert_called_once_with("Electronics")
        assert result == [{"id": "c1", "name": "Item C1"}, {"id": "c2", "name": "Item C2"}]
        assert len(result) == 2

    def test_get_products_by_category_limit_exceeds_available(self, product_data_service, mock_local_service):
        """
        Test get_products_by_category when limit is greater than available items.
        Should return all available items without error.
        """
        all_category_products = [
            {"id": "c1", "name": "Item C1"},
            {"id": "c2", "name": "Item C2"},
        ]
        mock_local_service.get_products_by_category.return_value = all_category_products

        result = product_data_service.get_products_by_category("Electronics", 5)

        mock_local_service.get_products_by_category.assert_called_once_with("Electronics")
        assert result == all_category_products
        assert len(result) == 2

    def test_get_products_by_category_exception(self, product_data_service, mock_local_service, caplog):
        """
        Test get_products_by_category handling exceptions.
        Ensures an error is logged and an empty list is returned.
        """
        mock_local_service.get_products_by_category.side_effect = Exception("Category search error")

        with caplog.at_level('ERROR'):
            result = product_data_service.get_products_by_category("Books", 5)

            mock_local_service.get_products_by_category.assert_called_once_with("Books")
            assert result == []
            assert "Error getting products by category: Category search error" in caplog.text

    def test_get_all_products_success(self, product_data_service, mock_local_service):
        """
        Test successful retrieval of all products.
        """
        expected_products = [{"id": "a1", "name": "All Product 1"}, {"id": "a2", "name": "All Product 2"}]
        mock_local_service.get_products.return_value = expected_products

        result = product_data_service.get_all_products(limit=10)

        mock_local_service.get_products.assert_called_once_with(10)
        assert result == expected_products

    def test_get_all_products_exception(self, product_data_service, mock_local_service, caplog):
        """
        Test get_all_products handling exceptions.
        Ensures an error is logged and an empty list is returned.
        """
        mock_local_service.get_products.side_effect = Exception("Get all error")

        with caplog.at_level('ERROR'):
            result = product_data_service.get_all_products(limit=20)

            mock_local_service.get_products.assert_called_once_with(20)
            assert result == []
            assert "Error getting all products: Get all error" in caplog.text

    def test_get_product_details_found(self, product_data_service, mock_local_service):
        """
        Test successful retrieval of product details.
        """
        expected_details = {"id": "p123", "name": "Product X", "description": "Details here"}
        mock_local_service.get_product_details.return_value = expected_details

        result = product_data_service.get_product_details("p123")

        mock_local_service.get_product_details.assert_called_once_with("p123")
        assert result == expected_details

    def test_get_product_details_not_found(self, product_data_service, mock_local_service):
        """
        Test retrieval of product details when ID is not found.
        Should return None.
        """
        mock_local_service.get_product_details.return_value = None

        result = product_data_service.get_product_details("nonexistent_id")

        mock_local_service.get_product_details.assert_called_once_with("nonexistent_id")
        assert result is None

    def test_get_product_details_exception(self, product_data_service, mock_local_service, caplog):
        """
        Test get_product_details handling exceptions.
        Ensures an error is logged and None is returned.
        """
        mock_local_service.get_product_details.side_effect = Exception("Details error")

        with caplog.at_level('ERROR'):
            result = product_data_service.get_product_details("error_id")

            mock_local_service.get_product_details.assert_called_once_with("error_id")
            assert result is None
            assert "Error getting product details: Details error" in caplog.text

    def test_get_brands_success(self, product_data_service, mock_local_service):
        """
        Test successful retrieval of brands.
        """
        expected_brands = ["Brand A", "Brand B"]
        mock_local_service.get_brands.return_value = expected_brands

        result = product_data_service.get_brands()

        mock_local_service.get_brands.assert_called_once_with()
        assert result == expected_brands

    def test_get_brands_exception(self, product_data_service, mock_local_service, caplog):
        """
        Test get_brands handling exceptions.
        Ensures an error is logged and an empty list is returned.
        """
        mock_local_service.get_brands.side_effect = Exception("Brands error")

        with caplog.at_level('ERROR'):
            result = product_data_service.get_brands()

            mock_local_service.get_brands.assert_called_once_with()
            assert result == []
            assert "Error getting brands: Brands error" in caplog.text

    def test_get_products_by_brand_success(self, product_data_service, mock_local_service):
        """
        Test successful retrieval of products by brand, ensuring limit slicing works.
        """
        # Ensure the mock returns more items than the limit to properly test slicing
        all_brand_products = [
            {"id": "b1", "name": "Brand Item 1"},
            {"id": "b2", "name": "Brand Item 2"},
            {"id": "b3", "name": "Brand Item 3"},
        ]
        mock_local_service.get_products_by_brand.return_value = all_brand_products

        result = product_data_service.get_products_by_brand("BrandX", 2)

        mock_local_service.get_products_by_brand.assert_called_once_with("BrandX")
        assert result == [{"id": "b1", "name": "Brand Item 1"}, {"id": "b2", "name": "Brand Item 2"}]
        assert len(result) == 2

    def test_get_products_by_brand_limit_exceeds_available(self, product_data_service, mock_local_service):
        """
        Test get_products_by_brand when limit is greater than available items.
        Should return all available items without error.
        """
        all_brand_products = [
            {"id": "b1", "name": "Brand Item 1"},
            {"id": "b2", "name": "Brand Item 2"},
        ]
        mock_local_service.get_products_by_brand.return_value = all_brand_products

        result = product_data_service.get_products_by_brand("BrandY", 5)

        mock_local_service.get_products_by_brand.assert_called_once_with("BrandY")
        assert result == all_brand_products
        assert len(result) == 2

    def test_get_products_by_brand_exception(self, product_data_service, mock_local_service, caplog):
        """
        Test get_products_by_brand handling exceptions.
        Ensures an error is logged and an empty list is returned.
        """
        mock_local_service.get_products_by_brand.side_effect = Exception("Brand search error")

        with caplog.at_level('ERROR'):
            result = product_data_service.get_products_by_brand("BrandZ", 5)

            mock_local_service.get_products_by_brand.assert_called_once_with("BrandZ")
            assert result == []
            assert "Error getting products by brand: Brand search error" in caplog.text

    @pytest.mark.asyncio
    async def test_smart_search_products_success(self, product_data_service, mock_local_service):
        """
        Test successful smart product search.
        Ensures local_service.smart_search_products is called via run_in_executor.
        """
        expected_products = [{"id": "s1", "name": "Smart Product A"}]
        expected_message = "Smart search successful."
        mock_local_service.smart_search_products.return_value = (expected_products, expected_message)

        products, message = await product_data_service.smart_search_products(
            keyword="smart", category="misc", max_price=100, limit=2
        )

        mock_local_service.smart_search_products.assert_called_once_with(
            "smart", "misc", 100, 2
        )
        assert products == expected_products
        assert message == expected_message

    @pytest.mark.asyncio
    async def test_smart_search_products_default_params(self, product_data_service, mock_local_service):
        """
        Test smart_search_products with default parameters.
        """
        expected_products = [{"id": "s2", "name": "Default Smart Product"}]
        expected_message = "Default search successful."
        mock_local_service.smart_search_products.return_value = (expected_products, expected_message)

        products, message = await product_data_service.smart_search_products() # Call without explicit arguments

        mock_local_service.smart_search_products.assert_called_once_with(
            '', None, None, 5 # Default values as per method signature
        )
        assert products == expected_products
        assert message == expected_message

    @pytest.mark.asyncio
    async def test_smart_search_products_exception_propagation(self, product_data_service, mock_local_service):
        """
        Test smart_search_products propagates exceptions from the underlying local service
        as it does not have its own try-except block.
        """
        mock_local_service.smart_search_products.side_effect = ValueError("Invalid search parameters")

        with pytest.raises(ValueError, match="Invalid search parameters"):
            await product_data_service.smart_search_products("bad", "category", 50, 1)
        
        mock_local_service.smart_search_products.assert_called_once_with("bad", "category", 50, 1)