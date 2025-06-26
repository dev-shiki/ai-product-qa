import pytest
import asyncio
from unittest.mock import MagicMock, patch

# Adjust the import path based on the structure
# Assuming the test file will be at test_services/product_data_service.py
# and the source at app/services/product_data_service.py
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService # Used for type hinting and mocking target


# --- Fixtures ---

@pytest.fixture
def mock_local_product_service(mocker):
    """
    Fixture to mock the LocalProductService class.
    We patch the class itself so that ProductDataService instantiates our mock.
    """
    mock_service = mocker.MagicMock(spec=LocalProductService)
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_service)
    return mock_service

@pytest.fixture
def product_data_service(mock_local_product_service):
    """
    Fixture to provide an instance of ProductDataService
    with a mocked LocalProductService dependency.
    """
    return ProductDataService()

# --- Sample Data ---

SAMPLE_PRODUCTS = [
    {"id": "1", "name": "Laptop Pro", "category": "Electronics", "price": 1200, "rating": 4.5, "brand": "TechCorp", "is_best_selling": True, "is_top_rated": True},
    {"id": "2", "name": "Mechanical Keyboard", "category": "Electronics", "price": 150, "rating": 4.8, "brand": "KeyGen", "is_best_selling": False, "is_top_rated": True},
    {"id": "3", "name": "Coffee Maker", "category": "Home Goods", "price": 80, "rating": 4.2, "brand": "BrewCo", "is_best_selling": True, "is_top_rated": False},
    {"id": "4", "name": "Smartphone X", "category": "Electronics", "price": 800, "rating": 4.6, "brand": "TechCorp", "is_best_selling": True, "is_top_rated": True},
    {"id": "5", "name": "Wireless Mouse", "category": "Electronics", "price": 30, "rating": 4.0, "brand": "AccessoryCo", "is_best_selling": False, "is_top_rated": False},
    {"id": "6", "name": "Desk Lamp", "category": "Home Goods", "price": 45, "rating": 3.9, "brand": "LightUp", "is_best_selling": False, "is_top_rated": False},
    {"id": "7", "name": "Gaming Headset", "category": "Electronics", "price": 90, "rating": 4.7, "brand": "AudioGen", "is_best_selling": False, "is_top_rated": True},
    {"id": "8", "name": "Espresso Machine", "category": "Home Goods", "price": 300, "rating": 4.9, "brand": "BrewCo", "is_best_selling": True, "is_top_rated": True},
]

SAMPLE_CATEGORIES = ["Electronics", "Home Goods", "Books", "Clothing"]
SAMPLE_BRANDS = ["TechCorp", "KeyGen", "BrewCo", "AccessoryCo", "LightUp", "AudioGen"]


# --- Test Cases ---

class TestProductDataServiceInit:
    """Tests for the ProductDataService __init__ method."""

    def test_init_sets_local_service_and_logs(self, mock_local_product_service, caplog):
        """
        Verify that ProductDataService initializes LocalProductService
        and logs an info message upon instantiation.
        """
        with caplog.at_level('INFO'):
            service = ProductDataService()
            assert service.local_service == mock_local_product_service
            assert "ProductDataService initialized with LocalProductService" in caplog.text


class TestProductDataServiceAsyncMethods:
    """Tests for asynchronous methods of ProductDataService."""

    @pytest.mark.asyncio
    @patch('asyncio.get_event_loop')
    async def test_search_products_success(self, mock_get_event_loop, product_data_service, mock_local_product_service, caplog):
        """
        Test `search_products` method for successful product retrieval.
        Mocks `asyncio.get_event_loop().run_in_executor` to return data.
        """
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop

        # Configure the synchronous return value for the mocked LocalProductService method
        mock_local_product_service.search_products.return_value = [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]]

        # Create a future that will resolve with the expected result from the executor
        future_result = [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]]
        mock_future = asyncio.Future()
        mock_future.set_result(future_result)
        mock_loop.run_in_executor.return_value = mock_future

        keyword = "laptop"
        limit = 5
        with caplog.at_level('INFO'):
            products = await product_data_service.search_products(keyword, limit)

            mock_local_product_service.search_products.assert_called_once_with(keyword, limit)
            mock_loop.run_in_executor.assert_called_once_with(None, mock_local_product_service.search_products, keyword, limit)

            assert len(products) == 2
            assert products[0]["name"] == "Laptop Pro"
            assert f"Searching products with keyword: {keyword}" in caplog.text
            assert f"Found 2 products for keyword: {keyword}" in caplog.text

    @pytest.mark.asyncio
    @patch('asyncio.get_event_loop')
    async def test_search_products_no_results(self, mock_get_event_loop, product_data_service, mock_local_product_service, caplog):
        """
        Test `search_products` when no results are found for the given keyword.
        """
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop

        mock_local_product_service.search_products.return_value = []
        mock_future = asyncio.Future()
        mock_future.set_result([])
        mock_loop.run_in_executor.return_value = mock_future

        keyword = "nonexistent"
        limit = 5
        with caplog.at_level('INFO'):
            products = await product_data_service.search_products(keyword, limit)

            mock_local_product_service.search_products.assert_called_once_with(keyword, limit)
            assert products == []
            assert f"Found 0 products for keyword: {keyword}" in caplog.text

    @pytest.mark.asyncio
    @patch('asyncio.get_event_loop')
    async def test_search_products_exception(self, mock_get_event_loop, product_data_service, mock_local_product_service, caplog):
        """
        Test `search_products` handles an exception from the underlying service
        by returning an empty list and logging an error.
        """
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop

        # Simulate the executor raising an exception
        mock_future = asyncio.Future()
        mock_future.set_exception(Exception("Simulated search error"))
        mock_loop.run_in_executor.return_value = mock_future

        keyword = "error_test"
        limit = 5
        with caplog.at_level('ERROR'):
            products = await product_data_service.search_products(keyword, limit)

            # Note: local_service.search_products is passed to executor, it's not directly called by PDS
            # so we only assert run_in_executor was called and it resulted in an error caught by PDS
            mock_loop.run_in_executor.assert_called_once()
            assert products == []
            assert "Error searching products: Simulated search error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_products_with_search_param(self, product_data_service, mocker):
        """
        Test `get_products` when the `search` parameter is provided,
        ensuring `search_products` is called.
        """
        mock_search_products = mocker.patch.object(product_data_service, 'search_products', new_callable=mocker.AsyncMock, return_value=[SAMPLE_PRODUCTS[0]])
        
        limit = 5
        search_keyword = "keyboard"
        
        products = await product_data_service.get_products(limit=limit, search=search_keyword)
        
        mock_search_products.assert_called_once_with(search_keyword, limit)
        assert products == [SAMPLE_PRODUCTS[0]]

    @pytest.mark.asyncio
    async def test_get_products_with_category_param(self, product_data_service, mocker):
        """
        Test `get_products` when the `category` parameter is provided,
        ensuring `get_products_by_category` is called.
        """
        mock_get_products_by_category = mocker.patch.object(product_data_service, 'get_products_by_category', return_value=[SAMPLE_PRODUCTS[2]])
        
        limit = 5
        category_name = "Home Goods"
        
        products = await product_data_service.get_products(limit=limit, category=category_name)
        
        mock_get_products_by_category.assert_called_once_with(category_name, limit)
        assert products == [SAMPLE_PRODUCTS[2]]

    @pytest.mark.asyncio
    async def test_get_products_with_no_params_calls_all_products(self, product_data_service, mocker):
        """
        Test `get_products` when neither `search` nor `category` is provided,
        ensuring `get_all_products` is called.
        """
        mock_get_all_products = mocker.patch.object(product_data_service, 'get_all_products', return_value=SAMPLE_PRODUCTS)
        
        limit = 15 # Custom limit
        
        products = await product_data_service.get_products(limit=limit)
        
        mock_get_all_products.assert_called_once_with(limit)
        assert products == SAMPLE_PRODUCTS

    @pytest.mark.asyncio
    async def test_get_products_exception_fallback(self, product_data_service, mock_local_product_service, mocker, caplog):
        """
        Test `get_products` handles an exception during an internal call (e.g., search path)
        by logging the error and falling back to `local_service.get_products`.
        """
        # Simulate an exception in the `search_products` path
        mocker.patch.object(product_data_service, 'search_products', new_callable=mocker.AsyncMock, side_effect=Exception("Simulated internal search error"))
        
        # Configure fallback return value
        mock_local_product_service.get_products.return_value = [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]]
        
        with caplog.at_level('ERROR'):
            products = await product_data_service.get_products(search="test_keyword")
            
            product_data_service.search_products.assert_called_once_with("test_keyword", 20) # Default limit for get_products
            mock_local_product_service.get_products.assert_called_once_with(20) # Default limit for fallback
            assert products == [SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]]
            assert "Error getting products: Simulated internal search error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_categories_success(self, product_data_service, mock_local_product_service):
        """
        Test `get_categories` successfully retrieves a list of categories.
        """
        mock_local_product_service.get_categories.return_value = SAMPLE_CATEGORIES
        categories = await product_data_service.get_categories()
        mock_local_product_service.get_categories.assert_called_once()
        assert categories == SAMPLE_CATEGORIES

    @pytest.mark.asyncio
    async def test_get_categories_empty(self, product_data_service, mock_local_product_service):
        """
        Test `get_categories` returns an empty list if no categories are available.
        """
        mock_local_product_service.get_categories.return_value = []
        categories = await product_data_service.get_categories()
        mock_local_product_service.get_categories.assert_called_once()
        assert categories == []

    @pytest.mark.asyncio
    async def test_get_categories_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_categories` handles an exception by returning an empty list
        and logging an error.
        """
        mock_local_product_service.get_categories.side_effect = Exception("Category service down")
        with caplog.at_level('ERROR'):
            categories = await product_data_service.get_categories()
            mock_local_product_service.get_categories.assert_called_once()
            assert categories == []
            assert "Error getting categories: Category service down" in caplog.text
            
    @pytest.mark.asyncio
    async def test_get_top_rated_products_success(self, product_data_service, mock_local_product_service):
        """
        Test `get_top_rated_products` successfully retrieves top-rated products.
        """
        top_rated = [p for p in SAMPLE_PRODUCTS if p.get("is_top_rated")]
        mock_local_product_service.get_top_rated_products.return_value = top_rated[:2]
        products = await product_data_service.get_top_rated_products(limit=2)
        mock_local_product_service.get_top_rated_products.assert_called_once_with(2)
        assert products == top_rated[:2]

    @pytest.mark.asyncio
    async def test_get_top_rated_products_empty(self, product_data_service, mock_local_product_service):
        """
        Test `get_top_rated_products` returns an empty list if no products are top-rated.
        """
        mock_local_product_service.get_top_rated_products.return_value = []
        products = await product_data_service.get_top_rated_products(limit=5)
        mock_local_product_service.get_top_rated_products.assert_called_once_with(5)
        assert products == []

    @pytest.mark.asyncio
    async def test_get_top_rated_products_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_top_rated_products` handles an exception by returning an empty list
        and logging an error.
        """
        mock_local_product_service.get_top_rated_products.side_effect = Exception("Top rated service error")
        with caplog.at_level('ERROR'):
            products = await product_data_service.get_top_rated_products(limit=5)
            mock_local_product_service.get_top_rated_products.assert_called_once_with(5)
            assert products == []
            assert "Error getting top rated products: Top rated service error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_best_selling_products_success(self, product_data_service, mock_local_product_service):
        """
        Test `get_best_selling_products` successfully retrieves best-selling products.
        """
        best_selling = [p for p in SAMPLE_PRODUCTS if p.get("is_best_selling")]
        mock_local_product_service.get_best_selling_products.return_value = best_selling[:2]
        products = await product_data_service.get_best_selling_products(limit=2)
        mock_local_product_service.get_best_selling_products.assert_called_once_with(2)
        assert products == best_selling[:2]

    @pytest.mark.asyncio
    async def test_get_best_selling_products_empty(self, product_data_service, mock_local_product_service):
        """
        Test `get_best_selling_products` returns an empty list if no products are best-selling.
        """
        mock_local_product_service.get_best_selling_products.return_value = []
        products = await product_data_service.get_best_selling_products(limit=5)
        mock_local_product_service.get_best_selling_products.assert_called_once_with(5)
        assert products == []

    @pytest.mark.asyncio
    async def test_get_best_selling_products_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_best_selling_products` handles an exception by returning an empty list
        and logging an error.
        """
        mock_local_product_service.get_best_selling_products.side_effect = Exception("Best selling service error")
        with caplog.at_level('ERROR'):
            products = await product_data_service.get_best_selling_products(limit=5)
            mock_local_product_service.get_best_selling_products.assert_called_once_with(5)
            assert products == []
            assert "Error getting best selling products: Best selling service error" in caplog.text

    @pytest.mark.asyncio
    @patch('asyncio.get_event_loop')
    async def test_smart_search_products_success_all_params(self, mock_get_event_loop, product_data_service, mock_local_product_service):
        """
        Test `smart_search_products` successfully retrieves products and message
        when all parameters are provided.
        """
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop

        expected_products_msg = ([SAMPLE_PRODUCTS[0], SAMPLE_PRODUCTS[1]], "Smart search successful")
        mock_local_product_service.smart_search_products.return_value = expected_products_msg
        
        mock_future = asyncio.Future()
        mock_future.set_result(expected_products_msg)
        mock_loop.run_in_executor.return_value = mock_future

        keyword = "laptop"
        category = "Electronics"
        max_price = 1500
        limit = 2

        products, message = await product_data_service.smart_search_products(
            keyword=keyword, category=category, max_price=max_price, limit=limit
        )

        mock_local_product_service.smart_search_products.assert_called_once_with(
            keyword, category, max_price, limit
        )
        mock_loop.run_in_executor.assert_called_once_with(
            None, mock_local_product_service.smart_search_products, keyword, category, max_price, limit
        )
        assert products == expected_products_msg[0]
        assert message == expected_products_msg[1]

    @pytest.mark.asyncio
    @patch('asyncio.get_event_loop')
    async def test_smart_search_products_only_keyword(self, mock_get_event_loop, product_data_service, mock_local_product_service):
        """
        Test `smart_search_products` with only a keyword provided, using default values for others.
        """
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop

        expected_products_msg = ([SAMPLE_PRODUCTS[0]], "Keyword match only")
        mock_local_product_service.smart_search_products.return_value = expected_products_msg
        
        mock_future = asyncio.Future()
        mock_future.set_result(expected_products_msg)
        mock_loop.run_in_executor.return_value = mock_future

        keyword = "laptop"
        
        products, message = await product_data_service.smart_search_products(keyword=keyword)
        
        mock_local_product_service.smart_search_products.assert_called_once_with(
            keyword, None, None, 5 # default limit
        )
        assert products == expected_products_msg[0]
        assert message == expected_products_msg[1]

    @pytest.mark.asyncio
    @patch('asyncio.get_event_loop')
    async def test_smart_search_products_no_results(self, mock_get_event_loop, product_data_service, mock_local_product_service):
        """
        Test `smart_search_products` when no products match the criteria.
        """
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop

        expected_products_msg = ([], "No products found for your criteria.")
        mock_local_product_service.smart_search_products.return_value = expected_products_msg
        
        mock_future = asyncio.Future()
        mock_future.set_result(expected_products_msg)
        mock_loop.run_in_executor.return_value = mock_future

        keyword = "nonexistent"
        
        products, message = await product_data_service.smart_search_products(keyword=keyword)
        
        assert products == []
        assert message == "No products found for your criteria."

    @pytest.mark.asyncio
    @patch('asyncio.get_event_loop')
    async def test_smart_search_products_exception_propagates(self, mock_get_event_loop, product_data_service, mock_local_product_service):
        """
        Test `smart_search_products` when an exception occurs in the underlying service.
        Since the method doesn't have a try-except, the exception should propagate.
        """
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop

        mock_local_product_service.smart_search_products.side_effect = Exception("Smart search internal error")
        mock_future = asyncio.Future()
        mock_future.set_exception(Exception("Smart search internal error"))
        mock_loop.run_in_executor.return_value = mock_future
        
        with pytest.raises(Exception, match="Smart search internal error"):
            await product_data_service.smart_search_products(keyword="error")


class TestProductDataServiceSyncMethods:
    """Tests for synchronous methods of ProductDataService."""

    def test_get_products_by_category_success_default_limit(self, product_data_service, mock_local_product_service):
        """
        Test `get_products_by_category` successfully retrieves products for a category
        and respects the default limit (10) via slicing.
        """
        electronics_products = [p for p in SAMPLE_PRODUCTS if p["category"] == "Electronics"]
        # Make the mock return more than the default limit to test slicing
        mock_local_product_service.get_products_by_category.return_value = electronics_products + [
            {"id": "9", "name": "Tablet", "category": "Electronics", "price": 500, "rating": 4.3, "brand": "TechCorp"},
            {"id": "10", "name": "Smartwatch", "category": "Electronics", "price": 250, "rating": 4.1, "brand": "TechCorp"},
        ] # Total 7 electronics
        
        category = "Electronics"
        products = product_data_service.get_products_by_category(category)
        
        mock_local_product_service.get_products_by_category.assert_called_once_with(category)
        assert len(products) == len(electronics_products) # Only 5 from SAMPLE_PRODUCTS, slicing up to 10
        assert all(p["category"] == category for p in products)

    def test_get_products_by_category_custom_limit(self, product_data_service, mock_local_product_service):
        """
        Test `get_products_by_category` with a custom limit, ensuring correct slicing.
        """
        electronics_products = [p for p in SAMPLE_PRODUCTS if p["category"] == "Electronics"]
        mock_local_product_service.get_products_by_category.return_value = electronics_products
        
        category = "Electronics"
        limit = 3
        products = product_data_service.get_products_by_category(category, limit)
        
        mock_local_product_service.get_products_by_category.assert_called_once_with(category)
        assert len(products) == limit
        assert products == electronics_products[:limit]

    def test_get_products_by_category_no_results(self, product_data_service, mock_local_product_service):
        """
        Test `get_products_by_category` when no products are found for the category.
        """
        mock_local_product_service.get_products_by_category.return_value = []
        
        category = "NonExistent"
        products = product_data_service.get_products_by_category(category)
        
        mock_local_product_service.get_products_by_category.assert_called_once_with(category)
        assert products == []

    def test_get_products_by_category_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_products_by_category` handles an exception by returning an empty list
        and logging an error.
        """
        mock_local_product_service.get_products_by_category.side_effect = Exception("Category DB error")
        
        category = "Electronics"
        with caplog.at_level('ERROR'):
            products = product_data_service.get_products_by_category(category)
            
            mock_local_product_service.get_products_by_category.assert_called_once_with(category)
            assert products == []
            assert "Error getting products by category: Category DB error" in caplog.text

    def test_get_all_products_success_default_limit(self, product_data_service, mock_local_product_service):
        """
        Test `get_all_products` successfully retrieves all products (up to default limit 20).
        """
        mock_local_product_service.get_products.return_value = SAMPLE_PRODUCTS
        
        products = product_data_service.get_all_products()
        
        mock_local_product_service.get_products.assert_called_once_with(20) # Default limit for this method
        assert products == SAMPLE_PRODUCTS # Local service handles limit internally

    def test_get_all_products_custom_limit(self, product_data_service, mock_local_product_service):
        """
        Test `get_all_products` with a custom limit.
        """
        mock_local_product_service.get_products.return_value = SAMPLE_PRODUCTS[:3] # Simulate local service returning limited items
        
        limit = 3
        products = product_data_service.get_all_products(limit)
        
        mock_local_product_service.get_products.assert_called_once_with(limit)
        assert products == SAMPLE_PRODUCTS[:3]

    def test_get_all_products_no_results(self, product_data_service, mock_local_product_service):
        """
        Test `get_all_products` when no products are available.
        """
        mock_local_product_service.get_products.return_value = []
        
        products = product_data_service.get_all_products()
        
        mock_local_product_service.get_products.assert_called_once_with(20)
        assert products == []

    def test_get_all_products_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_all_products` handles an exception by returning an empty list
        and logging an error.
        """
        mock_local_product_service.get_products.side_effect = Exception("All products service error")
        
        with caplog.at_level('ERROR'):
            products = product_data_service.get_all_products()
            
            mock_local_product_service.get_products.assert_called_once_with(20)
            assert products == []
            assert "Error getting all products: All products service error" in caplog.text

    def test_get_product_details_found(self, product_data_service, mock_local_product_service):
        """
        Test `get_product_details` when product is found by ID.
        """
        mock_local_product_service.get_product_details.return_value = SAMPLE_PRODUCTS[0]
        
        product_id = "1"
        details = product_data_service.get_product_details(product_id)
        
        mock_local_product_service.get_product_details.assert_called_once_with(product_id)
        assert details == SAMPLE_PRODUCTS[0]

    def test_get_product_details_not_found(self, product_data_service, mock_local_product_service):
        """
        Test `get_product_details` when product is not found by ID, should return None.
        """
        mock_local_product_service.get_product_details.return_value = None
        
        product_id = "non_existent_id"
        details = product_data_service.get_product_details(product_id)
        
        mock_local_product_service.get_product_details.assert_called_once_with(product_id)
        assert details is None

    def test_get_product_details_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_product_details` handles an exception by returning None
        and logging an error.
        """
        mock_local_product_service.get_product_details.side_effect = Exception("Details DB error")
        
        product_id = "123"
        with caplog.at_level('ERROR'):
            details = product_data_service.get_product_details(product_id)
            
            mock_local_product_service.get_product_details.assert_called_once_with(product_id)
            assert details is None
            assert "Error getting product details: Details DB error" in caplog.text

    def test_get_brands_success(self, product_data_service, mock_local_product_service):
        """
        Test `get_brands` successfully retrieves a list of brands.
        """
        mock_local_product_service.get_brands.return_value = SAMPLE_BRANDS
        brands = product_data_service.get_brands()
        mock_local_product_service.get_brands.assert_called_once()
        assert brands == SAMPLE_BRANDS

    def test_get_brands_empty(self, product_data_service, mock_local_product_service):
        """
        Test `get_brands` returns an empty list if no brands are available.
        """
        mock_local_product_service.get_brands.return_value = []
        brands = product_data_service.get_brands()
        mock_local_product_service.get_brands.assert_called_once()
        assert brands == []

    def test_get_brands_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_brands` handles an exception by returning an empty list
        and logging an error.
        """
        mock_local_product_service.get_brands.side_effect = Exception("Brand service error")
        with caplog.at_level('ERROR'):
            brands = product_data_service.get_brands()
            mock_local_product_service.get_brands.assert_called_once()
            assert brands == []
            assert "Error getting brands: Brand service error" in caplog.text

    def test_get_products_by_brand_success_default_limit(self, product_data_service, mock_local_product_service):
        """
        Test `get_products_by_brand` successfully retrieves products for a brand
        and respects the default limit (10) via slicing.
        """
        techcorp_products = [p for p in SAMPLE_PRODUCTS if p["brand"] == "TechCorp"]
        # Make the mock return more than the default limit to test slicing
        mock_local_product_service.get_products_by_brand.return_value = techcorp_products + [
            {"id": "9", "name": "Tablet", "category": "Electronics", "price": 500, "rating": 4.3, "brand": "TechCorp"},
            {"id": "10", "name": "Smartwatch", "category": "Electronics", "price": 250, "rating": 4.1, "brand": "TechCorp"},
        ] # Total 4 TechCorp products
        
        brand = "TechCorp"
        products = product_data_service.get_products_by_brand(brand)
        
        mock_local_product_service.get_products_by_brand.assert_called_once_with(brand)
        assert len(products) == len(mock_local_product_service.get_products_by_brand.return_value) # Sliced up to 10 by PDS
        assert all(p["brand"] == brand for p in products)

    def test_get_products_by_brand_custom_limit(self, product_data_service, mock_local_product_service):
        """
        Test `get_products_by_brand` with a custom limit, ensuring correct slicing.
        """
        techcorp_products = [p for p in SAMPLE_PRODUCTS if p["brand"] == "TechCorp"]
        mock_local_product_service.get_products_by_brand.return_value = techcorp_products + [
            {"id": "9", "name": "Tablet", "category": "Electronics", "price": 500, "rating": 4.3, "brand": "TechCorp"},
            {"id": "10", "name": "Smartwatch", "category": "Electronics", "price": 250, "rating": 4.1, "brand": "TechCorp"},
        ]
        
        brand = "TechCorp"
        limit = 3
        products = product_data_service.get_products_by_brand(brand, limit)
        
        mock_local_product_service.get_products_by_brand.assert_called_once_with(brand)
        assert len(products) == limit
        assert products == mock_local_product_service.get_products_by_brand.return_value[:limit]

    def test_get_products_by_brand_no_results(self, product_data_service, mock_local_product_service):
        """
        Test `get_products_by_brand` when no products are found for the brand.
        """
        mock_local_product_service.get_products_by_brand.return_value = []
        
        brand = "NonExistentBrand"
        products = product_data_service.get_products_by_brand(brand)
        
        mock_local_product_service.get_products_by_brand.assert_called_once_with(brand)
        assert products == []

    def test_get_products_by_brand_exception(self, product_data_service, mock_local_product_service, caplog):
        """
        Test `get_products_by_brand` handles an exception by returning an empty list
        and logging an error.
        """
        mock_local_product_service.get_products_by_brand.side_effect = Exception("Brand DB error")
        
        brand = "TestBrand"
        with caplog.at_level('ERROR'):
            products = product_data_service.get_products_by_brand(brand)
            
            mock_local_product_service.get_products_by_brand.assert_called_once_with(brand)
            assert products == []
            assert "Error getting products by brand: Brand DB error" in caplog.text