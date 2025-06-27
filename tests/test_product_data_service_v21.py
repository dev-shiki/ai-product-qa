import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Assuming app is in the Python path, or adjust sys.path
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService # Required for correct patching target


@pytest.fixture
def mock_local_service(mocker):
    """
    Fixture to mock the LocalProductService class.
    When ProductDataService initializes, it will receive this mock instance.
    """
    # Patch the LocalProductService where it's imported (in product_data_service.py)
    # .return_value makes the mock callable and returns an instance of the mock
    mock_service_instance = mocker.patch(
        'app.services.product_data_service.LocalProductService', autospec=True
    ).return_value
    return mock_service_instance


@pytest.fixture
def product_data_service(mock_local_service):
    """
    Fixture to create an instance of ProductDataService with a mocked LocalProductService.
    """
    return ProductDataService()


# --- Test __init__ ---
def test_product_data_service_init(mock_local_service, caplog):
    """
    Test ProductDataService initialization logs an info message and sets up local_service.
    """
    with caplog.at_level('INFO'):
        service = ProductDataService()
        # Assert that LocalProductService constructor was called
        mock_local_service.assert_called_once()
        assert "ProductDataService initialized with LocalProductService" in caplog.text
        # Verify that the local_service attribute is the mocked instance
        assert isinstance(service.local_service, MagicMock)


# --- Test search_products ---
@pytest.mark.asyncio
async def test_search_products_success(product_data_service, mock_local_service, caplog):
    """
    Test search_products returns products successfully and logs info.
    """
    expected_products = [{"id": "p1", "name": "Laptop"}, {"id": "p2", "name": "Monitor"}]
    mock_local_service.search_products.return_value = expected_products

    with caplog.at_level('INFO'):
        products = await product_data_service.search_products("electronic", 10)

        mock_local_service.search_products.assert_called_once_with("electronic", 10)
        assert products == expected_products
        assert f"Searching products with keyword: electronic" in caplog.text
        assert f"Found {len(expected_products)} products for keyword: electronic" in caplog.text


@pytest.mark.asyncio
async def test_search_products_no_results(product_data_service, mock_local_service, caplog):
    """
    Test search_products returns an empty list when no products are found.
    """
    mock_local_service.search_products.return_value = []

    with caplog.at_level('INFO'):
        products = await product_data_service.search_products("nonexistent", 5)

        mock_local_service.search_products.assert_called_once_with("nonexistent", 5)
        assert products == []
        assert f"Found 0 products for keyword: nonexistent" in caplog.text


@pytest.mark.asyncio
async def test_search_products_exception(product_data_service, mock_local_service, caplog):
    """
    Test search_products handles exceptions gracefully and returns an empty list.
    """
    mock_local_service.search_products.side_effect = Exception("Local service connection error")

    with caplog.at_level('ERROR'):
        products = await product_data_service.search_products("keyword", 10)

        mock_local_service.search_products.assert_called_once_with("keyword", 10)
        assert products == []
        assert "Error searching products: Local service connection error" in caplog.text


# --- Test get_products (dispatching logic) ---
@pytest.mark.asyncio
async def test_get_products_with_search_param_delegates(product_data_service, mocker):
    """
    Test get_products calls search_products when 'search' parameter is provided.
    """
    # Mock the internal method within ProductDataService itself
    mock_search = mocker.patch.object(product_data_service, 'search_products', new_callable=AsyncMock)
    mock_search.return_value = [{"id": "s1", "name": "Found by Search"}]

    products = await product_data_service.get_products(search="query", limit=5)

    mock_search.assert_called_once_with("query", 5)
    assert products == [{"id": "s1", "name": "Found by Search"}]


@pytest.mark.asyncio
async def test_get_products_with_category_param_delegates(product_data_service, mocker):
    """
    Test get_products calls get_products_by_category when 'category' parameter is provided.
    """
    mock_get_by_category = mocker.patch.object(product_data_service, 'get_products_by_category')
    mock_get_by_category.return_value = [{"id": "c1", "name": "Category Item"}]

    products = await product_data_service.get_products(category="books", limit=10)

    mock_get_by_category.assert_called_once_with("books", 10)
    assert products == [{"id": "c1", "name": "Category Item"}]


@pytest.mark.asyncio
async def test_get_products_no_params_delegates_to_all_products(product_data_service, mocker):
    """
    Test get_products calls get_all_products when no 'search' or 'category' is provided.
    """
    mock_get_all_products = mocker.patch.object(product_data_service, 'get_all_products')
    mock_get_all_products.return_value = [{"id": "a1", "name": "All Item"}]

    products = await product_data_service.get_products(limit=20)

    mock_get_all_products.assert_called_once_with(20)
    assert products == [{"id": "a1", "name": "All Item"}]


@pytest.mark.asyncio
async def test_get_products_exception_fallback(product_data_service, mock_local_service, mocker, caplog):
    """
    Test get_products handles exceptions during delegation and falls back to local_service.get_products.
    """
    # Simulate an exception from a delegated method (e.g., search_products)
    mocker.patch.object(product_data_service, 'search_products', side_effect=Exception("Internal search error"))

    # Configure fallback return value
    mock_local_service.get_products.return_value = [{"id": "fb1", "name": "Fallback Product"}]

    with caplog.at_level('ERROR'):
        products = await product_data_service.get_products(search="error_query", limit=15)

        assert "Error getting products: Internal search error" in caplog.text
        # Ensure the fallback to mock_local_service.get_products happened
        mock_local_service.get_products.assert_called_once_with(15)
        assert products == [{"id": "fb1", "name": "Fallback Product"}]


# --- Test get_categories ---
@pytest.mark.asyncio
async def test_get_categories_success(product_data_service, mock_local_service):
    """
    Test get_categories returns available categories successfully.
    """
    expected_categories = ["Electronics", "Clothing", "Books"]
    mock_local_service.get_categories.return_value = expected_categories

    categories = await product_data_service.get_categories()

    mock_local_service.get_categories.assert_called_once()
    assert categories == expected_categories


@pytest.mark.asyncio
async def test_get_categories_exception(product_data_service, mock_local_service, caplog):
    """
    Test get_categories handles exceptions gracefully and returns an empty list.
    """
    mock_local_service.get_categories.side_effect = Exception("Category service down")

    with caplog.at_level('ERROR'):
        categories = await product_data_service.get_categories()

        mock_local_service.get_categories.assert_called_once()
        assert categories == []
        assert "Error getting categories: Category service down" in caplog.text


# --- Test get_top_rated_products ---
@pytest.mark.asyncio
async def test_get_top_rated_products_success(product_data_service, mock_local_service):
    """
    Test get_top_rated_products returns top-rated products successfully.
    """
    expected_products = [{"id": "tr1", "rating": 5.0}, {"id": "tr2", "rating": 4.9}]
    mock_local_service.get_top_rated_products.return_value = expected_products

    products = await product_data_service.get_top_rated_products(limit=5)

    mock_local_service.get_top_rated_products.assert_called_once_with(5)
    assert products == expected_products


@pytest.mark.asyncio
async def test_get_top_rated_products_exception(product_data_service, mock_local_service, caplog):
    """
    Test get_top_rated_products handles exceptions gracefully and returns an empty list.
    """
    mock_local_service.get_top_rated_products.side_effect = Exception("Rating API error")

    with caplog.at_level('ERROR'):
        products = await product_data_service.get_top_rated_products(limit=5)

        mock_local_service.get_top_rated_products.assert_called_once_with(5)
        assert products == []
        assert "Error getting top rated products: Rating API error" in caplog.text


# --- Test get_best_selling_products ---
@pytest.mark.asyncio
async def test_get_best_selling_products_success(product_data_service, mock_local_service):
    """
    Test get_best_selling_products returns best-selling products successfully.
    """
    expected_products = [{"id": "bs1", "sales": 1000}, {"id": "bs2", "sales": 950}]
    mock_local_service.get_best_selling_products.return_value = expected_products

    products = await product_data_service.get_best_selling_products(limit=3)

    mock_local_service.get_best_selling_products.assert_called_once_with(3)
    assert products == expected_products


@pytest.mark.asyncio
async def test_get_best_selling_products_exception(product_data_service, mock_local_service, caplog):
    """
    Test get_best_selling_products handles exceptions gracefully and returns an empty list.
    """
    mock_local_service.get_best_selling_products.side_effect = Exception("Sales data unavailable")

    with caplog.at_level('ERROR'):
        products = await product_data_service.get_best_selling_products(limit=3)

        mock_local_service.get_best_selling_products.assert_called_once_with(3)
        assert products == []
        assert "Error getting best selling products: Sales data unavailable" in caplog.text


# --- Test get_products_by_category ---
def test_get_products_by_category_success(product_data_service, mock_local_service):
    """
    Test get_products_by_category returns products for a given category, applying limit.
    """
    mock_local_service.get_products_by_category.return_value = [
        {"id": "c1", "name": "Book A", "category": "Fiction"},
        {"id": "c2", "name": "Book B", "category": "Fiction"},
        {"id": "c3", "name": "Book C", "category": "Fiction"},
        {"id": "c4", "name": "Book D", "category": "Fiction"},
    ]

    products = product_data_service.get_products_by_category("Fiction", limit=2)

    mock_local_service.get_products_by_category.assert_called_once_with("Fiction")
    assert len(products) == 2
    assert products == [
        {"id": "c1", "name": "Book A", "category": "Fiction"},
        {"id": "c2", "name": "Book B", "category": "Fiction"},
    ]


def test_get_products_by_category_limit_more_than_available(product_data_service, mock_local_service):
    """
    Test get_products_by_category returns all available products if limit exceeds count.
    """
    mock_local_service.get_products_by_category.return_value = [
        {"id": "c1", "name": "Book A", "category": "Fiction"},
        {"id": "c2", "name": "Book B", "category": "Fiction"},
    ]

    products = product_data_service.get_products_by_category("Fiction", limit=10) # Request 10, only 2 available

    mock_local_service.get_products_by_category.assert_called_once_with("Fiction")
    assert len(products) == 2
    assert products == [
        {"id": "c1", "name": "Book A", "category": "Fiction"},
        {"id": "c2", "name": "Book B", "category": "Fiction"},
    ]


def test_get_products_by_category_no_results(product_data_service, mock_local_service):
    """
    Test get_products_by_category returns an empty list for a non-existent category.
    """
    mock_local_service.get_products_by_category.return_value = []

    products = product_data_service.get_products_by_category("NonExistent", limit=5)

    mock_local_service.get_products_by_category.assert_called_once_with("NonExistent")
    assert products == []


def test_get_products_by_category_exception(product_data_service, mock_local_service, caplog):
    """
    Test get_products_by_category handles exceptions gracefully and returns an empty list.
    """
    mock_local_service.get_products_by_category.side_effect = Exception("Category data load error")

    with caplog.at_level('ERROR'):
        products = product_data_service.get_products_by_category("Electronics", limit=5)

        mock_local_service.get_products_by_category.assert_called_once_with("Electronics")
        assert products == []
        assert "Error getting products by category: Category data load error" in caplog.text


# --- Test get_all_products ---
def test_get_all_products_success(product_data_service, mock_local_service):
    """
    Test get_all_products returns products, applying the limit.
    """
    mock_local_service.get_products.return_value = [
        {"id": "a1", "name": "Product 1"},
        {"id": "a2", "name": "Product 2"},
        {"id": "a3", "name": "Product 3"},
    ]

    products = product_data_service.get_all_products(limit=2)

    mock_local_service.get_products.assert_called_once_with(2)
    assert len(products) == 2
    assert products == [{"id": "a1", "name": "Product 1"}, {"id": "a2", "name": "Product 2"}]


def test_get_all_products_limit_more_than_available(product_data_service, mock_local_service):
    """
    Test get_all_products returns all available products if limit exceeds count.
    """
    mock_local_service.get_products.return_value = [
        {"id": "a1", "name": "Product 1"},
        {"id": "a2", "name": "Product 2"},
    ]

    products = product_data_service.get_all_products(limit=10) # Request 10, only 2 available

    mock_local_service.get_products.assert_called_once_with(10)
    assert len(products) == 2
    assert products == [
        {"id": "a1", "name": "Product 1"},
        {"id": "a2", "name": "Product 2"},
    ]


def test_get_all_products_exception(product_data_service, mock_local_service, caplog):
    """
    Test get_all_products handles exceptions gracefully and returns an empty list.
    """
    mock_local_service.get_products.side_effect = Exception("All products data error")

    with caplog.at_level('ERROR'):
        products = product_data_service.get_all_products(limit=10)

        mock_local_service.get_products.assert_called_once_with(10)
        assert products == []
        assert "Error getting all products: All products data error" in caplog.text


# --- Test get_product_details ---
def test_get_product_details_success(product_data_service, mock_local_service):
    """
    Test get_product_details returns details for a valid product ID.
    """
    expected_details = {"id": "prod123", "name": "Product X", "price": 99.99}
    mock_local_service.get_product_details.return_value = expected_details

    details = product_data_service.get_product_details("prod123")

    mock_local_service.get_product_details.assert_called_once_with("prod123")
    assert details == expected_details


def test_get_product_details_not_found(product_data_service, mock_local_service):
    """
    Test get_product_details returns None for a non-existent product ID.
    """
    mock_local_service.get_product_details.return_value = None

    details = product_data_service.get_product_details("nonexistent_id")

    mock_local_service.get_product_details.assert_called_once_with("nonexistent_id")
    assert details is None


def test_get_product_details_exception(product_data_service, mock_local_service, caplog):
    """
    Test get_product_details handles exceptions gracefully and returns None.
    """
    mock_local_service.get_product_details.side_effect = Exception("Details service error")

    with caplog.at_level('ERROR'):
        details = product_data_service.get_product_details("prod_error")

        mock_local_service.get_product_details.assert_called_once_with("prod_error")
        assert details is None
        assert "Error getting product details: Details service error" in caplog.text


# --- Test get_brands ---
def test_get_brands_success(product_data_service, mock_local_service):
    """
    Test get_brands returns available brands successfully.
    """
    expected_brands = ["BrandA", "BrandB", "BrandC"]
    mock_local_service.get_brands.return_value = expected_brands

    brands = product_data_service.get_brands()

    mock_local_service.get_brands.assert_called_once()
    assert brands == expected_brands


def test_get_brands_exception(product_data_service, mock_local_service, caplog):
    """
    Test get_brands handles exceptions gracefully and returns an empty list.
    """
    mock_local_service.get_brands.side_effect = Exception("Brand service unavailable")

    with caplog.at_level('ERROR'):
        brands = product_data_service.get_brands()

        mock_local_service.get_brands.assert_called_once()
        assert brands == []
        assert "Error getting brands: Brand service unavailable" in caplog.text


# --- Test get_products_by_brand ---
def test_get_products_by_brand_success(product_data_service, mock_local_service):
    """
    Test get_products_by_brand returns products for a given brand, applying limit.
    """
    mock_local_service.get_products_by_brand.return_value = [
        {"id": "b1", "name": "BrandX Phone", "brand": "BrandX"},
        {"id": "b2", "name": "BrandX Laptop", "brand": "BrandX"},
        {"id": "b3", "name": "BrandX Tablet", "brand": "BrandX"},
    ]

    products = product_data_service.get_products_by_brand("BrandX", limit=2)

    mock_local_service.get_products_by_brand.assert_called_once_with("BrandX")
    assert len(products) == 2
    assert products == [
        {"id": "b1", "name": "BrandX Phone", "brand": "BrandX"},
        {"id": "b2", "name": "BrandX Laptop", "brand": "BrandX"},
    ]


def test_get_products_by_brand_limit_more_than_available(product_data_service, mock_local_service):
    """
    Test get_products_by_brand returns all available products if limit exceeds count.
    """
    mock_local_service.get_products_by_brand.return_value = [
        {"id": "b1", "name": "BrandY Earbuds", "brand": "BrandY"},
        {"id": "b2", "name": "BrandY Speaker", "brand": "BrandY"},
    ]

    products = product_data_service.get_products_by_brand("BrandY", limit=10) # Request 10, only 2 available

    mock_local_service.get_products_by_brand.assert_called_once_with("BrandY")
    assert len(products) == 2
    assert products == [
        {"id": "b1", "name": "BrandY Earbuds", "brand": "BrandY"},
        {"id": "b2", "name": "BrandY Speaker", "brand": "BrandY"},
    ]


def test_get_products_by_brand_no_results(product_data_service, mock_local_service):
    """
    Test get_products_by_brand returns an empty list for a non-existent brand.
    """
    mock_local_service.get_products_by_brand.return_value = []

    products = product_data_service.get_products_by_brand("NonExistentBrand", limit=5)

    mock_local_service.get_products_by_brand.assert_called_once_with("NonExistentBrand")
    assert products == []


def test_get_products_by_brand_exception(product_data_service, mock_local_service, caplog):
    """
    Test get_products_by_brand handles exceptions gracefully and returns an empty list.
    """
    mock_local_service.get_products_by_brand.side_effect = Exception("Brand data error")

    with caplog.at_level('ERROR'):
        products = product_data_service.get_products_by_brand("BrandZ", limit=5)

        mock_local_service.get_products_by_brand.assert_called_once_with("BrandZ")
        assert products == []
        assert "Error getting products by brand: Brand data error" in caplog.text


# --- Test smart_search_products ---
@pytest.mark.asyncio
async def test_smart_search_products_success(product_data_service, mock_local_service):
    """
    Test smart_search_products returns products and message successfully.
    """
    expected_products = [{"id": "ss1", "name": "Smart Speaker"}]
    expected_message = "Found 1 matching product."
    mock_local_service.smart_search_products.return_value = (expected_products, expected_message)

    products, message = await product_data_service.smart_search_products(
        keyword="speaker", category="Audio", max_price=150, limit=1
    )

    mock_local_service.smart_search_products.assert_called_once_with(
        "speaker", "Audio", 150, 1
    )
    assert products == expected_products
    assert message == expected_message


@pytest.mark.asyncio
async def test_smart_search_products_default_params(product_data_service, mock_local_service):
    """
    Test smart_search_products with default parameters values.
    """
    expected_products = [{"id": "ss_def", "name": "Default Product"}]
    expected_message = "Default search results."
    mock_local_service.smart_search_products.return_value = (expected_products, expected_message)

    products, message = await product_data_service.smart_search_products() # Call with no explicit args

    mock_local_service.smart_search_products.assert_called_once_with(
        '', None, None, 5 # Assert default arguments
    )
    assert products == expected_products
    assert message == expected_message


@pytest.mark.asyncio
async def test_smart_search_products_exception_propagates(product_data_service, mock_local_service):
    """
    Test smart_search_products propagates exceptions as it does not have a try-except block.
    """
    mock_local_service.smart_search_products.side_effect = RuntimeError("Smart search internal error")

    with pytest.raises(RuntimeError, match="Smart search internal error"):
        await product_data_service.smart_search_products(keyword="error")

    mock_local_service.smart_search_products.assert_called_once_with(
        "error", None, None, 5
    )