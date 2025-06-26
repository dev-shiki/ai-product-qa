import pytest
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock

# Adjust import path based on your project structure if necessary
# Assuming tests are run from the project root or PYTHONPATH is configured
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService # Used for spec mocking


@pytest.fixture(autouse=True)
def setup_logging(caplog):
    """
    Fixture to set up logging capture for all tests.
    Captures INFO level logs and above from any logger.
    """
    caplog.set_level(logging.INFO)


@pytest.fixture
def mock_local_service(mocker):
    """
    Fixture to mock the LocalProductService dependency.
    It patches `app.services.product_data_service.LocalProductService`
    and sets up default return values for its methods.
    """
    mock_service = mocker.MagicMock(spec=LocalProductService)

    # Configure default return values for mocked methods
    mock_service.search_products.return_value = [
        {"id": "p_search_1", "name": "Mock Product Search 1"}
    ]
    mock_service.get_products.return_value = [
        {"id": "p_all_1", "name": "Mock All Product 1"}
    ]
    mock_service.get_categories.return_value = ["Electronics", "Books"]
    mock_service.get_top_rated_products.return_value = [
        {"id": "p_top_1", "name": "Mock Top Product"}
    ]
    mock_service.get_best_selling_products.return_value = [
        {"id": "p_best_1", "name": "Mock Best Seller"}
    ]
    mock_service.get_products_by_category.return_value = [
        {"id": "p_cat_1", "name": "Mock Category Product"}
    ]
    mock_service.get_product_details.return_value = {
        "id": "p_details_1",
        "name": "Mock Product Details",
    }
    mock_service.get_brands.return_value = ["BrandX", "BrandY"]
    mock_service.get_products_by_brand.return_value = [
        {"id": "p_brand_1", "name": "Mock Brand Product"}
    ]
    mock_service.smart_search_products.return_value = (
        [{"id": "p_smart_1", "name": "Mock Smart Product"}],
        "Smart search successful.",
    )

    # Patch the LocalProductService in the module under test
    mocker.patch(
        "app.services.product_data_service.LocalProductService",
        return_value=mock_service,
    )
    return mock_service


@pytest.fixture
def product_data_service(mock_local_service):
    """
    Fixture to provide an instance of ProductDataService with mocked dependencies.
    """
    return ProductDataService()


@pytest.mark.asyncio
class TestProductDataService:
    """
    Comprehensive test suite for ProductDataService.
    """

    async def test_init(self, product_data_service, mock_local_service, caplog):
        """
        Test ProductDataService initialization.
        Ensures LocalProductService is instantiated and a log message is generated.
        """
        # The product_data_service fixture already initializes the service.
        # We just need to verify the effects.
        assert isinstance(product_data_service.local_service, MagicMock)
        mock_local_service.assert_called_once()  # Asserts LocalProductService() was called

        # Check for the initialization log message
        assert "ProductDataService initialized with LocalProductService" in caplog.text

    @pytest.mark.parametrize(
        "keyword, limit, mock_return, expected_products",
        [
            ("test", 5, [{"id": "p1", "name": "Test Product"}], [{"id": "p1", "name": "Test Product"}]),
            ("none", 1, [], []),  # Test case where no products are found
        ],
    )
    async def test_search_products_success(
        self,
        product_data_service,
        mock_local_service,
        keyword,
        limit,
        mock_return,
        expected_products,
        caplog
    ):
        """
        Test search_products method for successful execution.
        Verifies correct arguments are passed and return value is as expected.
        """
        mock_local_service.search_products.return_value = mock_return

        products = await product_data_service.search_products(keyword, limit)

        assert products == expected_products
        mock_local_service.search_products.assert_called_once_with(keyword, limit)
        assert f"Searching products with keyword: {keyword}" in caplog.text
        assert f"Found {len(expected_products)} products for keyword: {keyword}" in caplog.text

    async def test_search_products_error(
        self, product_data_service, mock_local_service, caplog
    ):
        """
        Test search_products method for error handling.
        Ensures an empty list is returned and an error message is logged on exception.
        """
        mock_local_service.search_products.side_effect = Exception("Search service down")

        products = await product_data_service.search_products("error_test", 10)

        assert products == []
        assert "Error searching products: Search service down" in caplog.text
        mock_local_service.search_products.assert_called_once_with("error_test", 10)

    @pytest.mark.parametrize(
        "search, category, expected_call_method, expected_result_id",
        [
            ("keyword", None, "search_products", "s_mock"),  # Test search branch
            (None, "category_name", "get_products_by_category", "c_mock"),  # Test category branch
            (None, None, "get_all_products", "a_mock"),  # Test default (all products) branch
        ],
    )
    async def test_get_products_branches(
        self,
        product_data_service,
        mock_local_service,
        search,
        category,
        expected_call_method,
        expected_result_id,
        mocker,
    ):
        """
        Test get_products method to ensure correct branching based on parameters.
        Mocks internal calls to verify which method is invoked.
        """
        # Mock internal methods of ProductDataService to control their behavior
        mock_search_products = mocker.patch.object(
            product_data_service, "search_products", new_callable=AsyncMock
        )
        mock_get_products_by_category = mocker.patch.object(
            product_data_service, "get_products_by_category"
        )
        mock_get_all_products = mocker.patch.object(
            product_data_service, "get_all_products"
        )

        # Configure mock return values for the internal methods
        mock_search_products.return_value = [{"id": f"{expected_result_id}"}]
        mock_get_products_by_category.return_value = [{"id": f"{expected_result_id}"}]
        mock_get_all_products.return_value = [{"id": f"{expected_result_id}"}]

        limit = 10
        result = await product_data_service.get_products(
            limit=limit, category=category, search=search
        )

        # Assertions based on the expected call method
        if expected_call_method == "search_products":
            mock_search_products.assert_awaited_once_with(search, limit)
            mock_get_products_by_category.assert_not_called()
            mock_get_all_products.assert_not_called()
        elif expected_call_method == "get_products_by_category":
            mock_search_products.assert_not_called()
            mock_get_products_by_category.assert_called_once_with(category, limit)
            mock_get_all_products.assert_not_called()
        elif expected_call_method == "get_all_products":
            mock_search_products.assert_not_called()
            mock_get_products_by_category.assert_not_called()
            mock_get_all_products.assert_called_once_with(limit)

        assert result == [{"id": f"{expected_result_id}"}]

    async def test_get_products_error_fallback(
        self, product_data_service, mock_local_service, mocker, caplog
    ):
        """
        Test get_products method's error handling and fallback mechanism.
        If an internal call (e.g., get_products_by_category) raises an error,
        it should fall back to `local_service.get_products`.
        """
        # Simulate an error in one of the internal calls (e.g., `get_products_by_category`)
        mocker.patch.object(
            product_data_service, "get_products_by_category", side_effect=ValueError("Category lookup failed")
        )

        # Configure the fallback method's return value
        mock_local_service.get_products.return_value = [{"id": "fallback_product"}]

        result = await product_data_service.get_products(category="nonexistent_cat")

        assert result == [{"id": "fallback_product"}]
        # Check that the error was logged and fallback happened
        assert "Error getting products: Category lookup failed" in caplog.text
        mock_local_service.get_products.assert_called_once()  # Fallback called

    async def test_get_categories_success(
        self, product_data_service, mock_local_service
    ):
        """Test get_categories method for successful execution."""
        mock_local_service.get_categories.return_value = ["Category A", "Category B"]
        categories = await product_data_service.get_categories()
        assert categories == ["Category A", "Category B"]
        mock_local_service.get_categories.assert_called_once()

    async def test_get_categories_error(
        self, product_data_service, mock_local_service, caplog
    ):
        """Test get_categories method for error handling."""
        mock_local_service.get_categories.side_effect = Exception("DB error")
        categories = await product_data_service.get_categories()
        assert categories == []
        assert "Error getting categories: DB error" in caplog.text
        mock_local_service.get_categories.assert_called_once()

    async def test_get_top_rated_products_success(
        self, product_data_service, mock_local_service
    ):
        """Test get_top_rated_products method for successful execution."""
        mock_local_service.get_top_rated_products.return_value = [
            {"id": "tr1", "rating": 4.9}
        ]
        products = await product_data_service.get_top_rated_products(limit=5)
        assert products == [{"id": "tr1", "rating": 4.9}]
        mock_local_service.get_top_rated_products.assert_called_once_with(5)

    async def test_get_top_rated_products_error(
        self, product_data_service, mock_local_service, caplog
    ):
        """Test get_top_rated_products method for error handling."""
        mock_local_service.get_top_rated_products.side_effect = Exception(
            "Rating service error"
        )
        products = await product_data_service.get_top_rated_products(limit=5)
        assert products == []
        assert "Error getting top rated products: Rating service error" in caplog.text
        mock_local_service.get_top_rated_products.assert_called_once_with(5)

    async def test_get_best_selling_products_success(
        self, product_data_service, mock_local_service
    ):
        """Test get_best_selling_products method for successful execution."""
        mock_local_service.get_best_selling_products.return_value = [
            {"id": "bs1", "sales_rank": 1}
        ]
        products = await product_data_service.get_best_selling_products(limit=3)
        assert products == [{"id": "bs1", "sales_rank": 1}]
        mock_local_service.get_best_selling_products.assert_called_once_with(3)

    async def test_get_best_selling_products_error(
        self, product_data_service, mock_local_service, caplog
    ):
        """Test get_best_selling_products method for error handling."""
        mock_local_service.get_best_selling_products.side_effect = Exception(
            "Sales data error"
        )
        products = await product_data_service.get_best_selling_products(limit=3)
        assert products == []
        assert "Error getting best selling products: Sales data error" in caplog.text
        mock_local_service.get_best_selling_products.assert_called_once_with(3)

    @pytest.mark.parametrize(
        "mock_products, limit, expected_products",
        [
            ([{"id": "c1"}, {"id": "c2"}, {"id": "c3"}], 2, [{"id": "c1"}, {"id": "c2"}]),  # Limit applied
            ([{"id": "c1"}], 5, [{"id": "c1"}]),  # Limit greater than available
            ([], 10, []),  # No products found
        ],
    )
    def test_get_products_by_category_success(
        self,
        product_data_service,
        mock_local_service,
        mock_products,
        limit,
        expected_products,
    ):
        """
        Test get_products_by_category method for successful execution and limit application.
        """
        mock_local_service.get_products_by_category.return_value = mock_products
        products = product_data_service.get_products_by_category("Electronics", limit)
        assert products == expected_products
        mock_local_service.get_products_by_category.assert_called_once_with(
            "Electronics"
        )  # Limit is applied after call

    def test_get_products_by_category_error(
        self, product_data_service, mock_local_service, caplog
    ):
        """Test get_products_by_category method for error handling."""
        mock_local_service.get_products_by_category.side_effect = Exception(
            "Category fetch error"
        )
        products = product_data_service.get_products_by_category("Electronics", 10)
        assert products == []
        assert "Error getting products by category: Category fetch error" in caplog.text
        mock_local_service.get_products_by_category.assert_called_once_with(
            "Electronics"
        )

    @pytest.mark.parametrize(
        "mock_products, limit",
        [
            ([{"id": "a1"}, {"id": "a2"}, {"id": "a3"}], 20),
            ([], 5),
        ],
    )
    def test_get_all_products_success(
        self, product_data_service, mock_local_service, mock_products, limit
    ):
        """
        Test get_all_products method for successful execution.
        Note: The `[:limit]` slicing is *not* done in this method itself,
        but the limit is passed to `local_service.get_products`.
        """
        mock_local_service.get_products.return_value = mock_products
        products = product_data_service.get_all_products(limit)
        assert products == mock_products
        mock_local_service.get_products.assert_called_once_with(limit)

    def test_get_all_products_error(
        self, product_data_service, mock_local_service, caplog
    ):
        """Test get_all_products method for error handling."""
        mock_local_service.get_products.side_effect = Exception("All products fetch error")
        products = product_data_service.get_all_products(20)
        assert products == []
        assert "Error getting all products: All products fetch error" in caplog.text
        mock_local_service.get_products.assert_called_once_with(20)

    @pytest.mark.parametrize(
        "mock_return_value, expected_result",
        [
            ({"id": "p123", "name": "Specific Product"}, {"id": "p123", "name": "Specific Product"}),
            (None, None),  # Product not found scenario
        ],
    )
    def test_get_product_details_success(
        self,
        product_data_service,
        mock_local_service,
        mock_return_value,
        expected_result,
    ):
        """
        Test get_product_details method for successful retrieval and not-found cases.
        """
        mock_local_service.get_product_details.return_value = mock_return_value
        details = product_data_service.get_product_details("p123")
        assert details == expected_result
        mock_local_service.get_product_details.assert_called_once_with("p123")

    def test_get_product_details_error(
        self, product_data_service, mock_local_service, caplog
    ):
        """Test get_product_details method for error handling."""
        mock_local_service.get_product_details.side_effect = Exception(
            "Details lookup error"
        )
        details = product_data_service.get_product_details("p123")
        assert details is None
        assert "Error getting product details: Details lookup error" in caplog.text
        mock_local_service.get_product_details.assert_called_once_with("p123")

    def test_get_brands_success(self, product_data_service, mock_local_service):
        """Test get_brands method for successful execution."""
        mock_local_service.get_brands.return_value = ["Brand A", "Brand B"]
        brands = product_data_service.get_brands()
        assert brands == ["Brand A", "Brand B"]
        mock_local_service.get_brands.assert_called_once()

    def test_get_brands_error(
        self, product_data_service, mock_local_service, caplog
    ):
        """Test get_brands method for error handling."""
        mock_local_service.get_brands.side_effect = Exception("Brands data error")
        brands = product_data_service.get_brands()
        assert brands == []
        assert "Error getting brands: Brands data error" in caplog.text
        mock_local_service.get_brands.assert_called_once()

    @pytest.mark.parametrize(
        "mock_products, limit, expected_products",
        [
            ([{"id": "b1"}, {"id": "b2"}, {"id": "b3"}], 2, [{"id": "b1"}, {"id": "b2"}]),  # Limit applied
            ([{"id": "b1"}], 5, [{"id": "b1"}]),  # Limit greater than available
            ([], 10, []),  # No products found
        ],
    )
    def test_get_products_by_brand_success(
        self,
        product_data_service,
        mock_local_service,
        mock_products,
        limit,
        expected_products,
    ):
        """
        Test get_products_by_brand method for successful execution and limit application.
        """
        mock_local_service.get_products_by_brand.return_value = mock_products
        products = product_data_service.get_products_by_brand("BrandX", limit)
        assert products == expected_products
        mock_local_service.get_products_by_brand.assert_called_once_with("BrandX")

    def test_get_products_by_brand_error(
        self, product_data_service, mock_local_service, caplog
    ):
        """Test get_products_by_brand method for error handling."""
        mock_local_service.get_products_by_brand.side_effect = Exception(
            "Brand products fetch error"
        )
        products = product_data_service.get_products_by_brand("BrandX", 10)
        assert products == []
        assert "Error getting products by brand: Brand products fetch error" in caplog.text
        mock_local_service.get_products_by_brand.assert_called_once_with("BrandX")

    @pytest.mark.parametrize(
        "keyword, category, max_price, limit, mock_return_products, mock_return_message, expected_products, expected_message",
        [
            (
                "laptop",
                "electronics",
                1200,
                2,
                [{"id": "sp1", "name": "Laptop Pro"}],
                "Found matching laptops",
                [{"id": "sp1", "name": "Laptop Pro"}],
                "Found matching laptops",
            ),
            (
                "",
                None,
                None,
                5,
                [],
                "No smart search results",
                [],
                "No smart search results",
            ),
        ],
    )
    async def test_smart_search_products_success(
        self,
        product_data_service,
        mock_local_service,
        keyword,
        category,
        max_price,
        limit,
        mock_return_products,
        mock_return_message,
        expected_products,
        expected_message,
    ):
        """
        Test smart_search_products method for successful execution.
        Verifies correct arguments are passed and the tuple (products, message) is returned.
        """
        mock_local_service.smart_search_products.return_value = (
            mock_return_products,
            mock_return_message,
        )

        products, message = await product_data_service.smart_search_products(
            keyword, category, max_price, limit
        )

        assert products == expected_products
        assert message == expected_message
        mock_local_service.smart_search_products.assert_called_once_with(
            keyword, category, max_price, limit
        )

    async def test_smart_search_products_error_propagation(
        self, product_data_service, mock_local_service
    ):
        """
        Test smart_search_products method error propagation.
        Since this method does not have a try-except block, exceptions from the
        underlying local service should propagate.
        """
        mock_local_service.smart_search_products.side_effect = ValueError(
            "Smart search internal failure"
        )

        with pytest.raises(ValueError, match="Smart search internal failure"):
            await product_data_service.smart_search_products(
                "error", "cat", 100, 5
            )

        mock_local_service.smart_search_products.assert_called_once_with(
            "error", "cat", 100, 5
        )