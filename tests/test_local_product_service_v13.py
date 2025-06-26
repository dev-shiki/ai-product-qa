import pytest
import json
import logging
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

# Sample product data mimicking the structure in products.json
# Note: 'sold' count will be added by the service, mocking random.randint for predictability
SAMPLE_PRODUCTS_DATA = {
    "products": [
        {
            "id": "prod1",
            "name": "Test Product 1",
            "category": "Test Category A",
            "brand": "Brand X",
            "price": 100000,
            "currency": "IDR",
            "description": "Description for test product 1. Ideal for everyday use.",
            "specifications": {
                "rating": 4.5,
                "stock_count": 10
            },
            "reviews_count": 5
        },
        {
            "id": "prod2",
            "name": "Another Product",
            "category": "Test Category B",
            "brand": "Brand Y",
            "price": 200000,
            "currency": "IDR",
            "description": "Description for test product 2.",
            "specifications": {
                "rating": 3.0,
                "stock_count": 5,
                "color": "Red"
            },
            "reviews_count": 2
        },
        {
            "id": "prod3",
            "name": "Budget Phone",
            "category": "Smartphone",
            "brand": "Brand Z",
            "price": 1500000,
            "currency": "IDR",
            "description": "A phone for budget users with great features.",
            "specifications": {
                "rating": 4.0,
                "stock_count": 20
            },
            "reviews_count": 10
        },
        {
            "id": "prod4",
            "name": "Luxury Laptop",
            "category": "Laptop",
            "brand": "Brand A",
            "price": 25000000,
            "currency": "IDR",
            "description": "High-end laptop for professionals. Best performance.",
            "specifications": {
                "rating": 4.9,
                "stock_count": 3
            },
            "reviews_count": 25
        },
        # Product with some missing optional fields to test defaults
        {
            "id": "prod5",
            "name": "Simple Item",
            "category": "Miscellaneous",
            "brand": "Brand B",
            "price": 5000,
            # currency, description, specifications, reviews_count missing
        },
        # Products for 'sold' sorting test, explicitly setting initial sold values
        {
            "id": "prod6",
            "name": "High Sold Electronics",
            "category": "Electronics",
            "brand": "Brand H",
            "price": 500000,
            "specifications": {
                "rating": 4.2,
                "sold": 5000 # High sold count for testing
            }
        },
        {
            "id": "prod7",
            "name": "Low Sold Gadget",
            "category": "Electronics",
            "brand": "Brand L",
            "price": 200000,
            "specifications": {
                "rating": 4.1,
                "sold": 100 # Low sold count for testing
            }
        }
    ]
}

# Expected transformed products after LocalProductService internal processing.
# 'sold' will be fixed to 1000 by mock_random_randint unless explicitly set in SAMPLE_PRODUCTS_DATA
EXPECTED_TRANSFORMED_PRODUCTS = [
    {
        "id": "prod1", "name": "Test Product 1", "category": "Test Category A", "brand": "Brand X",
        "price": 100000, "currency": "IDR", "description": "Description for test product 1. Ideal for everyday use.",
        "specifications": {"rating": 4.5, "sold": 1000, "stock": 10, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "Brand X Store"},
        "availability": "in_stock", "reviews_count": 5, "images": ["https://example.com/prod1.jpg"], "url": "https://shopee.co.id/prod1"
    },
    {
        "id": "prod2", "name": "Another Product", "category": "Test Category B", "brand": "Brand Y",
        "price": 200000, "currency": "IDR", "description": "Description for test product 2.",
        "specifications": {"rating": 3.0, "sold": 1000, "stock": 5, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "Brand Y Store", "color": "Red"},
        "availability": "in_stock", "reviews_count": 2, "images": ["https://example.com/prod2.jpg"], "url": "https://shopee.co.id/prod2"
    },
    {
        "id": "prod3", "name": "Budget Phone", "category": "Smartphone", "brand": "Brand Z",
        "price": 1500000, "currency": "IDR", "description": "A phone for budget users with great features.",
        "specifications": {"rating": 4.0, "sold": 1000, "stock": 20, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "Brand Z Store"},
        "availability": "in_stock", "reviews_count": 10, "images": ["https://example.com/prod3.jpg"], "url": "https://shopee.co.id/prod3"
    },
    {
        "id": "prod4", "name": "Luxury Laptop", "category": "Laptop", "brand": "Brand A",
        "price": 25000000, "currency": "IDR", "description": "High-end laptop for professionals. Best performance.",
        "specifications": {"rating": 4.9, "sold": 1000, "stock": 3, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "Brand A Store"},
        "availability": "in_stock", "reviews_count": 25, "images": ["https://example.com/prod4.jpg"], "url": "https://shopee.co.id/prod4"
    },
    {
        "id": "prod5", "name": "Simple Item", "category": "Miscellaneous", "brand": "Brand B",
        "price": 5000, "currency": "IDR", "description": "",
        "specifications": {"rating": 0, "sold": 1000, "stock": 0, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "Brand B Store"},
        "availability": "in_stock", "reviews_count": 0, "images": ["https://example.com/prod5.jpg"], "url": "https://shopee.co.id/prod5"
    },
    {
        "id": "prod6", "name": "High Sold Electronics", "category": "Electronics", "brand": "Brand H",
        "price": 500000, "currency": "IDR", "description": "",
        "specifications": {"rating": 4.2, "sold": 5000, "stock": 0, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "Brand H Store"},
        "availability": "in_stock", "reviews_count": 0, "images": ["https://example.com/prod6.jpg"], "url": "https://shopee.co.id/prod6"
    },
    {
        "id": "prod7", "name": "Low Sold Gadget", "category": "Electronics", "brand": "Brand L",
        "price": 200000, "currency": "IDR", "description": "",
        "specifications": {"rating": 4.1, "sold": 100, "stock": 0, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "Brand L Store"},
        "availability": "in_stock", "reviews_count": 0, "images": ["https://example.com/prod7.jpg"], "url": "https://shopee.co.id/prod7"
    }
]


@pytest.fixture(autouse=True)
def mock_pathlib_path_and_open(mocker):
    """
    Mocks pathlib.Path behavior and builtins.open to control file access.
    This fixture is automatically applied to all tests in this file.
    It simulates the app/data/products.json file path resolution.
    """
    # Mock the Path class itself
    mock_path_class = mocker.patch('app.services.local_product_service.Path')

    # Create a mock for the specific `products.json` Path object
    mock_json_file_path = MagicMock(spec=Path)

    # Configure the chained calls to return `mock_json_file_path`
    # Path(__file__) -> .parent (services) -> .parent (app) -> .parent (project_root)
    mock_file_path_obj = MagicMock(spec=Path)
    mock_app_dir = MagicMock(spec=Path)
    mock_root_dir = MagicMock(spec=Path)
    mock_data_dir = MagicMock(spec=Path)

    mock_file_path_obj.parent = MagicMock(spec=Path) # represents 'services' dir
    mock_file_path_obj.parent.parent = mock_app_dir # represents 'app' dir
    mock_app_dir.parent = mock_root_dir # represents 'project_root' dir

    mock_path_class.return_value = mock_file_path_obj # So Path(__file__) returns this

    mock_root_dir.__truediv__.return_value = mock_data_dir # project_root / "data"
    mock_data_dir.__truediv__.return_value = mock_json_file_path # data / "products.json"

    # Default behavior: file exists, open returns content
    mock_json_file_path.exists.return_value = True
    # Patch builtins.open, but allow it to be configured by other fixtures/tests
    mock_open_builtin = mocker.patch('builtins.open', new_callable=mock_open)

    # Provide access to the crucial mock for individual tests to configure `exists` and `open`
    yield mock_json_file_path, mock_open_builtin

    mocker.stopall()


@pytest.fixture
def mock_random_randint(mocker):
    """Mocks random.randint to return a fixed value for predictable tests."""
    mock_rand = mocker.patch('app.services.local_product_service.random.randint')
    mock_rand.return_value = 1000  # A fixed value for 'sold' count for products where it's missing
    return mock_rand

@pytest.fixture
def mock_open_json(mock_pathlib_path_and_open, mock_random_randint):
    """
    Fixture to set up a mock `open` that returns valid JSON content
    and ensures `random.randint` is mocked.
    """
    mock_json_file_path, mock_open_builtin = mock_pathlib_path_and_open
    mock_json_file_path.exists.return_value = True
    mock_open_builtin.side_effect = mock_open(read_data=json.dumps(SAMPLE_PRODUCTS_DATA))
    yield


# Import LocalProductService after setting up fixtures for proper patching
from app.services.local_product_service import LocalProductService


@pytest.fixture
def local_product_service_instance(mock_open_json):
    """
    Provides a LocalProductService instance with mocked JSON loading.
    The mock_open_json fixture ensures that _load_local_products will succeed
    and random.randint is predictable.
    """
    service = LocalProductService()
    # Replace the internally loaded products with the predictable ones
    # This simplifies testing subsequent methods, as they won't rely on random.randint
    # for 'sold' each time they are accessed, only on initial load.
    # The `_load_local_products` already incorporates the mocked random.randint.
    # We use a deep copy of the expected transformed data to prevent test modifications
    # from affecting other tests.
    service.products = json.loads(json.dumps(EXPECTED_TRANSFORMED_PRODUCTS))
    return service

@pytest.fixture
def caplog_info(caplog):
    """Fixture to capture log messages at INFO level."""
    caplog.set_level(logging.INFO)
    return caplog

@pytest.fixture
def caplog_warning(caplog):
    """Fixture to capture log messages at WARNING level."""
    caplog.set_level(logging.WARNING)
    return caplog

@pytest.fixture
def caplog_error(caplog):
    """Fixture to capture log messages at ERROR level."""
    caplog.set_level(logging.ERROR)
    return caplog


# --- Test Cases for LocalProductService ---

class TestLocalProductService:

    # Test __init__ and _load_local_products success
    def test_init_loads_products_successfully(self, mock_open_json, caplog_info):
        """
        GIVEN a valid products.json file and mocked random.randint
        WHEN LocalProductService is initialized
        THEN it should load and transform products successfully and log info.
        """
        service = LocalProductService()
        assert len(service.products) == len(SAMPLE_PRODUCTS_DATA['products'])
        # Verify the transformation of one product, e.g., 'prod1'
        # Check against the fixed expected transformed products
        assert service.products[0] == EXPECTED_TRANSFORMED_PRODUCTS[0]
        assert f"Loaded {len(SAMPLE_PRODUCTS_DATA['products'])} local products from JSON file" in caplog_info.text
        assert f"Successfully loaded {len(SAMPLE_PRODUCTS_DATA['products'])} products from JSON file using utf-16-le encoding" in caplog_info.text

    # Test _load_local_products - file not found
    def test_load_local_products_file_not_found(self, mock_pathlib_path_and_open, caplog_error, caplog_warning):
        """
        GIVEN products.json file does not exist
        WHEN _load_local_products is called (via __init__)
        THEN it should log an error, use fallback products, and log a warning.
        """
        mock_json_file_path, _ = mock_pathlib_path_and_open
        mock_json_file_path.exists.return_value = False
        service = LocalProductService()
        assert len(service.products) == 8  # Fallback products count
        assert "Products JSON file not found at:" in caplog_error.text
        assert "Using fallback products due to JSON file loading error" in caplog_warning.text

    # Test _load_local_products - JSONDecodeError (malformed JSON)
    def test_load_local_products_json_decode_error(self, mock_pathlib_path_and_open, mock_random_randint, caplog_error, caplog_warning):
        """
        GIVEN products.json file exists but contains malformed JSON
        WHEN _load_local_products is called
        THEN it should try multiple encodings, log warnings for failures,
             eventually log an error for all failures, and use fallback products.
        """
        mock_json_file_path, mock_open_builtin = mock_pathlib_path_and_open
        mock_json_file_path.exists.return_value = True
        # Simulate malformed JSON for all encoding attempts
        mock_open_builtin.side_effect = [
            mock_open(read_data='{"products": [invalid json').return_value,
            mock_open(read_data='{"products": [invalid json').return_value,
            mock_open(read_data='{"products": [invalid json').return_value,
            mock_open(read_data='{"products": [invalid json').return_value,
            mock_open(read_data='{"products": [invalid json').return_value,
            mock_open(read_data='{"products": [invalid json').return_value,
        ]
        service = LocalProductService()
        assert len(service.products) == 8  # Fallback products count
        # Check for warnings for each encoding attempt (first few attempts will fail)
        assert "Failed to load with utf-16-le encoding: Expecting value:" in caplog_warning.text
        assert "Failed to load with utf-8 encoding: Expecting value:" in caplog_warning.text
        assert "All encoding attempts failed, using fallback products" in caplog_error.text
        assert "Using fallback products due to JSON file loading error" in caplog_warning.text

    # Test _load_local_products - UnicodeDecodeError (wrong encoding)
    def test_load_local_products_unicode_decode_error(self, mock_pathlib_path_and_open, mock_random_randint, caplog_error, caplog_warning):
        """
        GIVEN products.json file exists but causes UnicodeDecodeError with initial encodings
        WHEN _load_local_products is called
        THEN it should try multiple encodings, log warnings for failures,
             eventually log an error for all failures, and use fallback products.
        """
        mock_json_file_path, mock_open_builtin = mock_pathlib_path_and_open
        mock_json_file_path.exists.return_value = True
        # Simulate content that causes UnicodeDecodeError for initial encodings
        # and then fails completely for all
        mock_open_builtin.side_effect = [
            mock_open(read_data=b'\xff\xfe\x00\x00'.decode('utf-16-le', errors='ignore')).return_value, # Invalid data
            mock_open(read_data=b'\xff\xfe\x00\x00'.decode('utf-16', errors='ignore')).return_value,
            mock_open(read_data=b'\xff\xfe\x00\x00'.decode('utf-8', errors='ignore')).return_value,
            mock_open(read_data=b'\xff\xfe\x00\x00'.decode('utf-8-sig', errors='ignore')).return_value,
            mock_open(read_data=b'\xff\xfe\x00\x00'.decode('latin-1', errors='ignore')).return_value,
            mock_open(read_data=b'\xff\xfe\x00\x00'.decode('cp1252', errors='ignore')).return_value,
        ]
        service = LocalProductService()
        assert len(service.products) == 8  # Fallback products count
        assert "Failed to load with utf-16-le encoding: " in caplog_warning.text
        assert "Failed to load with utf-8 encoding: " in caplog_warning.text # Should be logged for utf-8
        assert "All encoding attempts failed, using fallback products" in caplog_error.text
        assert "Using fallback products due to JSON file loading error" in caplog_warning.text

    # Test _load_local_products - other exception during loading
    def test_load_local_products_general_exception(self, mock_pathlib_path_and_open, caplog_error, caplog_warning):
        """
        GIVEN an unexpected exception occurs during file reading (e.g., IOError)
        WHEN _load_local_products is called
        THEN it should log an error and use fallback products.
        """
        mock_json_file_path, mock_open_builtin = mock_pathlib_path_and_open
        mock_json_file_path.exists.return_value = True
        mock_open_builtin.side_effect = IOError("Permission denied")
        service = LocalProductService()
        assert len(service.products) == 8  # Fallback products count
        assert "Error loading products from JSON file: Permission denied" in caplog_error.text
        assert "Using fallback products due to JSON file loading error" in caplog_warning.text

    # Test _load_local_products - BOM handling
    def test_load_local_products_with_bom(self, mock_pathlib_path_and_open, mock_random_randint, caplog_info):
        """
        GIVEN a products.json file with a BOM
        WHEN _load_local_products is called
        THEN it should remove the BOM and load correctly.
        """
        mock_json_file_path, mock_open_builtin = mock_pathlib_path_and_open
        mock_json_file_path.exists.return_value = True
        bom_content = '\ufeff' + json.dumps(SAMPLE_PRODUCTS_DATA)
        mock_open_builtin.side_effect = mock_open(read_data=bom_content)
        service = LocalProductService()
        assert len(service.products) == len(SAMPLE_PRODUCTS_DATA['products'])
        assert service.products[0] == EXPECTED_TRANSFORMED_PRODUCTS[0]
        assert "Successfully loaded" in caplog_info.text


    # Test _get_fallback_products
    def test_get_fallback_products(self, caplog_warning):
        """
        GIVEN _get_fallback_products is called
        WHEN it provides fallback data
        THEN it should return the hardcoded list of products and log a warning.
        """
        service = LocalProductService() # This will trigger fallback via __init__ if not mocked otherwise
        products = service._get_fallback_products()
        assert len(products) == 8
        assert products[0]['id'] == '1'
        assert products[0]['name'] == 'iPhone 15 Pro Max'
        assert "Using fallback products due to JSON file loading error" in caplog_warning.text

    # Test search_products
    def test_search_products_by_name(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN searching by product name keyword
        THEN it should return matching products.
        """
        service = local_product_service_instance
        results = service.search_products("Test Product 1")
        assert len(results) == 1
        assert results[0]['id'] == 'prod1'
        assert results[0]['name'] == 'Test Product 1'

    def test_search_products_case_insensitivity(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN searching with case-insensitive keyword
        THEN it should return matching products.
        """
        service = local_product_service_instance
        results = service.search_products("test product 1")
        assert len(results) == 1
        assert results[0]['id'] == 'prod1'

    def test_search_products_by_description(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN searching by description keyword
        THEN it should return matching products.
        """
        service = local_product_service_instance
        results = service.search_products("everyday use")
        assert len(results) == 1
        assert results[0]['id'] == 'prod1'

    def test_search_products_by_category(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN searching by category keyword
        THEN it should return matching products.
        """
        service = local_product_service_instance
        results = service.search_products("Category A")
        assert len(results) == 1
        assert results[0]['id'] == 'prod1'

    def test_search_products_by_brand(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN searching by brand keyword
        THEN it should return matching products.
        """
        service = local_product_service_instance
        results = service.search_products("Brand Y")
        assert len(results) == 1
        assert results[0]['id'] == 'prod2'

    def test_search_products_by_specifications(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN searching by specification keyword
        THEN it should return matching products.
        """
        service = local_product_service_instance
        results = service.search_products("color: Red")
        assert len(results) == 1
        assert results[0]['id'] == 'prod2'

    def test_search_products_no_results(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN searching for a non-existent keyword
        THEN it should return an empty list.
        """
        service = local_product_service_instance
        results = service.search_products("nonexistent_product_xyz")
        assert len(results) == 0

    def test_search_products_limit(self, local_product_service_instance):
        """
        GIVEN multiple matching products
        WHEN searching with a limit
        THEN it should return only up to the specified limit, sorted by relevance.
        """
        service = local_product_service_instance
        # "Product" keyword will match prod1, prod2. prod1 is "Test Product 1", prod2 is "Another Product".
        # Both get name match score of 10. No price keyword. So default order is preserved.
        results = service.search_products("Product", limit=1)
        assert len(results) == 1
        assert results[0]['id'] == 'prod1'

    def test_search_products_with_price_limit_juta(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN searching with a price limit (e.g., "1.5 juta")
        THEN it should return products within that price range and keyword relevant.
        """
        service = local_product_service_instance
        results = service.search_products("phone 1.5 juta")
        # prod3 (1.5M, Smartphone, "phone") - highest relevance
        # prod1 (100k, Test Product 1) - included by price, lower relevance
        # prod2 (200k, Another Product) - included by price, lower relevance
        # prod5 (5k, Simple Item) - included by price, lowest relevance
        assert len(results) == 4
        assert [p['id'] for p in results] == ['prod3', 'prod5', 'prod1', 'prod2']

    def test_search_products_with_budget_keyword(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN searching with a budget keyword (e.g., "laptop murah")
        THEN it should return products within the associated price range,
             prioritizing cheaper ones if "murah" is present, and include keyword matches.
        """
        service = local_product_service_instance
        # "laptop murah" -> max_price from 'murah' is 5_000_000.
        # Products <= 5M: prod1 (100k), prod2 (200k), prod3 (1.5M), prod5 (5k), prod6 (500k), prod7 (200k)
        # Prod4 (25M) is NOT <= 5M.
        # Relevance:
        # prod4: name 'Luxury Laptop' (score 10), price score negative. Total score 10.
        # prod5: price 5k, (10M - 0.005M)/1M = 9.995. Total ~9.995
        # prod1: price 100k, (10M - 0.1M)/1M = 9.9. Total ~9.9
        # prod2: price 200k, (10M - 0.2M)/1M = 9.8. Total ~9.8
        # prod7: price 200k, (10M - 0.2M)/1M = 9.8. Total ~9.8
        # prod6: price 500k, (10M - 0.5M)/1M = 9.5. Total ~9.5
        # prod3: price 1.5M, (10M - 1.5M)/1M = 8.5. Total ~8.5
        # The logic `if max_price and product_price <= max_price: filtered_products.append(product); continue`
        # means prod4 is only added by keyword match, not price.
        # `if keyword_lower in searchable_text: filtered_products.append(product)` then adds keyword matches.
        # The `filtered_products` will contain all products whose price is <= max_price OR whose text matches keyword.
        # Prod4 matches 'laptop' keyword.
        results = service.search_products("laptop murah", limit=7)
        product_ids = [p['id'] for p in results]
        assert len(results) == 7 # All 7 products will be considered for 'laptop murah' logic
        assert results[0]['id'] == 'prod4' # Highest keyword relevance
        assert results[1]['id'] == 'prod5' # Lowest price, highest price score
        assert results[2]['id'] == 'prod1'
        assert results[3]['id'] in ['prod2', 'prod7']
        assert results[4]['id'] in ['prod2', 'prod7'] and results[4]['id'] != results[3]['id']
        assert results[5]['id'] == 'prod6'
        assert results[6]['id'] == 'prod3'


    def test_search_products_error_handling(self, local_product_service_instance, caplog_error):
        """
        GIVEN an error occurs during search (e.g., bad product data structure)
        WHEN search_products is called
        THEN it should log an error and return an empty list.
        """
        service = local_product_service_instance
        # Simulate an error by making products list contain non-dict elements
        service.products = [1, 2, 3] # This will cause an AttributeError when .get is called
        results = service.search_products("any")
        assert len(results) == 0
        assert "Error searching products:" in caplog_error.text


    # Test _extract_price_from_keyword
    @pytest.mark.parametrize("keyword, expected_price", [
        ("iphone 10 juta", 10000000),
        ("laptop 15 ribu", 15000),
        ("camera rp 500000", 500000),
        ("TV 2500000 rp", 2500000),
        ("headphone 500k", 500000),
        ("monitor 2m", 2000000),
        ("mouse murah", 5000000),
        ("keyboard budget", 5000000),
        ("speaker hemat", 3000000),
        ("charger terjangkau", 4000000),
        ("tablet ekonomis", 2000000),
        ("no price here", None),
        ("1.5jt", None), # Current regex won't match this format
        ("rp 1,234,567", 1), # Regex `(\d+)` matches only '1'
        ("rp100000", 100000), # Test no space
        ("100000rp", 100000), # Test no space
    ])
    def test_extract_price_from_keyword(self, local_product_service_instance, keyword, expected_price):
        """
        GIVEN various keywords
        WHEN _extract_price_from_keyword is called
        THEN it should correctly extract the price or return None.
        """
        service = local_product_service_instance
        price = service._extract_price_from_keyword(keyword)
        assert price == expected_price

    def test_extract_price_from_keyword_error_handling(self, local_product_service_instance, mocker, caplog_error):
        """
        GIVEN an error occurs during price extraction (e.g., regex error)
        WHEN _extract_price_from_keyword is called
        THEN it should log an error and return None.
        """
        service = local_product_service_instance
        mocker.patch('app.services.local_product_service.re.search', side_effect=Exception("Regex error"))
        price = service._extract_price_from_keyword("some keyword")
        assert price is None
        assert "Error extracting price from keyword: Regex error" in caplog_error.text


    # Test get_product_details
    def test_get_product_details_found(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN requesting details for an existing product ID
        THEN it should return the correct product dictionary.
        """
        service = local_product_service_instance
        product = service.get_product_details("prod1")
        assert product is not None
        assert product['id'] == 'prod1'
        assert product['name'] == 'Test Product 1'

    def test_get_product_details_not_found(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN requesting details for a non-existent product ID
        THEN it should return None.
        """
        service = local_product_service_instance
        product = service.get_product_details("non_existent_id")
        assert product is None

    def test_get_product_details_error_handling(self, local_product_service_instance, mocker, caplog_error):
        """
        GIVEN an error occurs (e.g., products list corrupted)
        WHEN get_product_details is called
        THEN it should log an error and return None.
        """
        service = local_product_service_instance
        # Simulate corrupted data to cause an error on .get('id')
        service.products = [None]
        product = service.get_product_details("prod1")
        assert product is None
        assert "Error getting product details:" in caplog_error.text


    # Test get_categories
    def test_get_categories(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN requesting categories
        THEN it should return a sorted list of unique categories.
        """
        service = local_product_service_instance
        categories = service.get_categories()
        expected_categories = sorted(['Test Category A', 'Test Category B', 'Smartphone', 'Laptop', 'Miscellaneous', 'Electronics'])
        assert categories == expected_categories

    def test_get_categories_empty_products(self, mocker):
        """
        GIVEN an empty product list
        WHEN requesting categories
        THEN it should return an empty list.
        """
        # Mock _load_local_products to ensure the service initializes with an empty list
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        categories = service.get_categories()
        assert categories == []

    # Test get_brands
    def test_get_brands(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN requesting brands
        THEN it should return a sorted list of unique brands.
        """
        service = local_product_service_instance
        brands = service.get_brands()
        expected_brands = sorted(['Brand X', 'Brand Y', 'Brand Z', 'Brand A', 'Brand B', 'Brand H', 'Brand L'])
        assert brands == expected_brands

    def test_get_brands_empty_products(self, mocker):
        """
        GIVEN an empty product list
        WHEN requesting brands
        THEN it should return an empty list.
        """
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        brands = service.get_brands()
        assert brands == []

    # Test get_products_by_category
    def test_get_products_by_category_found(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN requesting products by an existing category (case-insensitive)
        THEN it should return matching products.
        """
        service = local_product_service_instance
        products = service.get_products_by_category("test category a")
        assert len(products) == 1
        assert products[0]['id'] == 'prod1'

    def test_get_products_by_category_not_found(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN requesting products by a non-existent category
        THEN it should return an empty list.
        """
        service = local_product_service_instance
        products = service.get_products_by_category("NonExistentCategory")
        assert len(products) == 0

    def test_get_products_by_category_error_handling(self, local_product_service_instance, mocker, caplog_error):
        """
        GIVEN an error occurs (e.g., products list corrupted)
        WHEN get_products_by_category is called
        THEN it should log an error and return an empty list.
        """
        service = local_product_service_instance
        service.products = [None] # Simulate corrupted data
        products = service.get_products_by_category("some category")
        assert len(products) == 0
        assert "Error getting products by category:" in caplog_error.text


    # Test get_products_by_brand
    def test_get_products_by_brand_found(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN requesting products by an existing brand (case-insensitive)
        THEN it should return matching products.
        """
        service = local_product_service_instance
        products = service.get_products_by_brand("brand y")
        assert len(products) == 1
        assert products[0]['id'] == 'prod2'

    def test_get_products_by_brand_not_found(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN requesting products by a non-existent brand
        THEN it should return an empty list.
        """
        service = local_product_service_instance
        products = service.get_products_by_brand("NonExistentBrand")
        assert len(products) == 0

    def test_get_products_by_brand_error_handling(self, local_product_service_instance, mocker, caplog_error):
        """
        GIVEN an error occurs (e.g., products list corrupted)
        WHEN get_products_by_brand is called
        THEN it should log an error and return an empty list.
        """
        service = local_product_service_instance
        service.products = [None] # Simulate corrupted data
        products = service.get_products_by_brand("some brand")
        assert len(products) == 0
        assert "Error getting products by brand:" in caplog_error.text


    # Test get_top_rated_products
    def test_get_top_rated_products_default_limit(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN requesting top-rated products with default limit
        THEN it should return the top 5 sorted by rating descending.
        """
        service = local_product_service_instance
        # Expected order based on rating from EXPECTED_TRANSFORMED_PRODUCTS
        # (prod4=4.9, prod1=4.5, prod6=4.2, prod7=4.1, prod3=4.0)
        top_products = service.get_top_rated_products()
        assert len(top_products) == 5
        assert [p['id'] for p in top_products] == ['prod4', 'prod1', 'prod6', 'prod7', 'prod3']

    def test_get_top_rated_products_custom_limit(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN requesting top-rated products with custom limit
        THEN it should return the correct number of top products.
        """
        service = local_product_service_instance
        top_products = service.get_top_rated_products(limit=2)
        assert len(top_products) == 2
        assert [p['id'] for p in top_products] == ['prod4', 'prod1']

    def test_get_top_rated_products_no_rating(self, local_product_service_instance):
        """
        GIVEN products where 'rating' in specifications is missing or zero
        WHEN requesting top-rated products
        THEN products without rating should be treated as rating 0 and sorted last.
        """
        service = local_product_service_instance
        # prod5 has no rating, should be treated as rating 0.
        top_products = service.get_top_rated_products(limit=7) # Get all to see where prod5 ends up
        assert top_products[-1]['id'] == 'prod5' # Should be last due to default 0 rating

    def test_get_top_rated_products_error_handling(self, local_product_service_instance, mocker, caplog_error):
        """
        GIVEN an error occurs (e.g., products list corrupted)
        WHEN get_top_rated_products is called
        THEN it should log an error and return an empty list.
        """
        service = local_product_service_instance
        service.products = [None] # Corrupt data to cause an error on .get
        top_products = service.get_top_rated_products()
        assert len(top_products) == 0
        assert "Error getting top rated products:" in caplog_error.text


    # Test get_best_selling_products
    def test_get_best_selling_products_default_limit(self, local_product_service_instance, caplog_info):
        """
        GIVEN products loaded
        WHEN requesting best-selling products with default limit
        THEN it should return the top 5 sorted by sold count descending.
        """
        service = local_product_service_instance
        # The fixture sets `service.products` using EXPECTED_TRANSFORMED_PRODUCTS.
        # Sold values are: prod6=5000, prod4=1000, prod2=1000, prod5=1000, prod1=1000, prod3=1000, prod7=100.
        # Order should be prod6, then prod4/prod2/prod5/prod1/prod3 (ties broken by original order), then prod7.
        # To make it deterministic for ties, we could adjust `EXPECTED_TRANSFORMED_PRODUCTS` or manually set
        # distinct `sold` values in the test. Let's explicitly set distinct values for this test for clarity.
        service.products[0]['specifications']['sold'] = 1500 # prod1
        service.products[1]['specifications']['sold'] = 2500 # prod2
        service.products[2]['specifications']['sold'] = 500  # prod3
        service.products[3]['specifications']['sold'] = 3000 # prod4
        service.products[4]['specifications']['sold'] = 2000 # prod5
        service.products[5]['specifications']['sold'] = 5000 # prod6 (already 5000)
        service.products[6]['specifications']['sold'] = 100  # prod7 (already 100)

        best_products = service.get_best_selling_products()
        assert len(best_products) == 5
        # Expected order based on adjusted sold counts:
        # (prod6=5000, prod4=3000, prod2=2500, prod5=2000, prod1=1500)
        assert [p['id'] for p in best_products] == ['prod6', 'prod4', 'prod2', 'prod5', 'prod1']
        assert "Getting best selling products, limit: 5" in caplog_info.text
        assert "Returning 5 best selling products" in caplog_info.text


    def test_get_best_selling_products_custom_limit(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN requesting best-selling products with custom limit
        THEN it should return the correct number of top products.
        """
        service = local_product_service_instance
        # Set distinct sold counts for predictable sorting
        service.products[0]['specifications']['sold'] = 1500 # prod1
        service.products[1]['specifications']['sold'] = 2500 # prod2
        service.products[2]['specifications']['sold'] = 500  # prod3
        service.products[3]['specifications']['sold'] = 3000 # prod4
        service.products[4]['specifications']['sold'] = 2000 # prod5
        service.products[5]['specifications']['sold'] = 5000 # prod6
        service.products[6]['specifications']['sold'] = 100  # prod7

        best_products = service.get_best_selling_products(limit=2)
        assert len(best_products) == 2
        assert [p['id'] for p in best_products] == ['prod6', 'prod4']


    def test_get_best_selling_products_no_sold_data(self, local_product_service_instance):
        """
        GIVEN products without a 'sold' in specifications
        WHEN requesting best-selling products
        THEN they should be treated as sold 0 and sorted accordingly.
        """
        service = local_product_service_instance
        # Manually create products for this specific test
        service.products = [
            {'id': 'p_high', 'name': 'High Sold', 'specifications': {'sold': 10000, 'rating': 5.0}},
            {'id': 'p_medium', 'name': 'Medium Sold', 'specifications': {'sold': 5000, 'rating': 4.0}},
            {'id': 'p_low', 'name': 'Low Sold', 'specifications': {'sold': 1000, 'rating': 3.0}},
            {'id': 'p_no_sold', 'name': 'No Sold Data', 'specifications': {'rating': 2.0}}, # Should default to 0 sold
            {'id': 'p_no_specs', 'name': 'No Specs Data'}, # Also defaults to 0 sold
        ]
        best_products = service.get_best_selling_products(limit=5)
        assert len(best_products) == 5
        # Expected order based on sold (p_high=10000, p_medium=5000, p_low=1000, p_no_sold=0, p_no_specs=0)
        # Ties between p_no_sold and p_no_specs are broken by original list order.
        assert [p['id'] for p in best_products] == ['p_high', 'p_medium', 'p_low', 'p_no_sold', 'p_no_specs']

    def test_get_best_selling_products_error_handling(self, local_product_service_instance, mocker, caplog_error):
        """
        GIVEN an error occurs (e.g., products list corrupted)
        WHEN get_best_selling_products is called
        THEN it should log an error and return an empty list.
        """
        service = local_product_service_instance
        service.products = [None]
        best_products = service.get_best_selling_products()
        assert len(best_products) == 0
        assert "Error getting best selling products:" in caplog_error.text


    # Test get_products
    def test_get_products_default_limit(self, local_product_service_instance, caplog_info):
        """
        GIVEN products loaded
        WHEN requesting all products with default limit
        THEN it should return the first 10 products (or all if less than 10).
        """
        service = local_product_service_instance
        all_products = service.get_products()
        assert len(all_products) == 7 # Our sample data has 7 products, so it returns all 7 if limit is 10
        assert all_products[0]['id'] == 'prod1'
        assert "Getting all products, limit: 10" in caplog_info.text


    def test_get_products_custom_limit(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN requesting all products with custom limit
        THEN it should return the correct number of products.
        """
        service = local_product_service_instance
        all_products = service.get_products(limit=2)
        assert len(all_products) == 2
        assert all_products[0]['id'] == 'prod1'
        assert all_products[1]['id'] == 'prod2'

    def test_get_products_limit_exceeds_total(self, local_product_service_instance):
        """
        GIVEN products loaded
        WHEN requesting products with a limit greater than total available
        THEN it should return all available products.
        """
        service = local_product_service_instance
        all_products = service.get_products(limit=100)
        assert len(all_products) == 7 # Total products in sample data
        assert all_products[0]['id'] == 'prod1'

    def test_get_products_error_handling(self, local_product_service_instance, mocker, caplog_error):
        """
        GIVEN an error occurs (e.g., products list corrupted)
        WHEN get_products is called
        THEN it should log an error and return an empty list.
        """
        service = local_product_service_instance
        # Simulate an error by making products not iterable
        service.products = None
        products = service.get_products()
        assert len(products) == 0
        assert "Error getting products:" in caplog_error.text


    # Test smart_search_products - complex method
    def test_smart_search_best_no_category(self, local_product_service_instance):
        """
        GIVEN request for "best" products without a specific category
        WHEN smart_search_products is called
        THEN it should return general top-rated products with a specific message.
        """
        service = local_product_service_instance
        # Top rated: prod4 (4.9), prod1 (4.5)
        products, message = service.smart_search_products(keyword="produk terbaik", limit=2)
        assert len(products) == 2
        assert products[0]['id'] == 'prod4'
        assert products[1]['id'] == 'prod1'
        assert message == "Berikut produk terbaik berdasarkan rating:"

    def test_smart_search_best_with_existing_category(self, local_product_service_instance):
        """
        GIVEN request for "best" products within an existing category
        WHEN smart_search_products is called
        THEN it should return top-rated products from that category.
        """
        service = local_product_service_instance
        # In 'Smartphone' category, only prod3 (4.0 rating)
        products, message = service.smart_search_products(keyword="terbaik", category="Smartphone", limit=10)
        assert len(products) == 1
        assert products[0]['id'] == 'prod3'
        assert products[0]['category'] == 'Smartphone'
        assert message == "Berikut Smartphone terbaik berdasarkan rating:"

    def test_smart_search_best_with_non_existing_category_fallback(self, local_product_service_instance):
        """
        GIVEN request for "best" products within a non-existent category
        WHEN smart_search_products is called
        THEN it should fallback to general top-rated products with a specific message.
        """
        service = local_product_service_instance
        # No products in 'NonExistentCategory', so fall back to general best.
        # Top rated: prod4 (4.9), prod1 (4.5)
        products, message = service.smart_search_products(keyword="best", category="NonExistentCategory", limit=2)
        assert len(products) == 2
        assert products[0]['id'] == 'prod4'
        assert products[1]['id'] == 'prod1'
        assert message == "Tidak ada produk kategori NonExistentCategory, berikut produk terbaik secara umum:"

    def test_smart_search_all_criteria_match(self, local_product_service_instance):
        """
        GIVEN keyword, category, and max_price all match existing products
        WHEN smart_search_products is called
        THEN it should return products matching all criteria.
        """
        service = local_product_service_instance
        # prod3: Smartphone, "phone", 1.5M. Fits all criteria.
        products, message = service.smart_search_products(
            keyword="phone", category="Smartphone", max_price=2000000, limit=10
        )
        assert len(products) == 1
        assert products[0]['id'] == 'prod3'
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_no_exact_match_fallback_category_only(self, local_product_service_instance):
        """
        GIVEN no exact match for all criteria, but category matches (and price/keyword filters are too restrictive)
        WHEN smart_search_products is called
        THEN it should fallback to products in the specified category (sorted by price).
        """
        service = local_product_service_instance
        # Search for keyword "super_expensive" (no match) in "Smartphone" category.
        # max_price=100000, which excludes prod3 (1.5M).
        # Fallback 4: "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."
        products, message = service.smart_search_products(
            keyword="super_expensive", category="Smartphone", max_price=100000, limit=10
        )
        assert len(products) == 1
        assert products[0]['id'] == 'prod3' # Only Smartphone product
        assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."

    def test_smart_search_no_exact_match_fallback_price_only(self, local_product_service_instance):
        """
        GIVEN no exact match, no category match, but max_price matches other products
        WHEN smart_search_products is called
        THEN it should fallback to products within the specified max_price.
        """
        service = local_product_service_instance
        # Search for keyword "nonexistent" (no match), category "NonCategory" (no match).
        # But max_price=100000. Products <= 100k: prod1 (100k), prod5 (5k)
        # Fallback 5: "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."
        products, message = service.smart_search_products(
            keyword="nonexistent", category="NonCategory", max_price=100000, limit=10
        )
        assert len(products) == 2
        # Order is not guaranteed by default in this fallback, but it should contain these products.
        assert 'prod1' in [p['id'] for p in products]
        assert 'prod5' in [p['id'] for p in products]
        assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

    def test_smart_search_no_match_fallback_popular(self, local_product_service_instance):
        """
        GIVEN no match for any specific criteria, including price and category fallbacks
        WHEN smart_search_products is called
        THEN it should fallback to popular/best-selling products.
        """
        service = local_product_service_instance
        # Set distinct sold counts for predictability for popular fallback
        service.products[0]['specifications']['sold'] = 1500 # prod1
        service.products[1]['specifications']['sold'] = 2500 # prod2
        service.products[2]['specifications']['sold'] = 500  # prod3
        service.products[3]['specifications']['sold'] = 3000 # prod4
        service.products[4]['specifications']['sold'] = 2000 # prod5
        service.products[5]['specifications']['sold'] = 5000 # prod6
        service.products[6]['specifications']['sold'] = 100  # prod7

        # Search for something entirely unrelated
        # Fallback 6: "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
        products, message = service.smart_search_products(
            keyword="xyz_abc_123", category="DefinitelyNotHere", max_price=1, limit=5
        )
        assert len(products) == 5
        # Expected order based on sold: (prod6=5000, prod4=3000, prod2=2500, prod5=2000, prod1=1500)
        assert [p['id'] for p in products] == ['prod6', 'prod4', 'prod2', 'prod5', 'prod1']
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_empty_keyword_only_category(self, local_product_service_instance):
        """
        GIVEN only a category is provided, no keyword or price
        WHEN smart_search_products is called
        THEN it should return all products in that category matching the general criteria.
        """
        service = local_product_service_instance
        # Only prod3 in 'Smartphone' category.
        products, message = service.smart_search_products(category="Smartphone", limit=10)
        assert len(products) == 1
        assert products[0]['id'] == 'prod3'
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_empty_keyword_only_max_price(self, local_product_service_instance):
        """
        GIVEN only max_price is provided, no keyword or category
        WHEN smart_search_products is called
        THEN it should return products below that max_price.
        """
        service = local_product_service_instance
        # Products <= 100k: prod1 (100k), prod5 (5k).
        products, message = service.smart_search_products(max_price=100000, limit=10)
        assert len(products) == 2
        # Order is determined by internal list order as no specific sorting applied for this criteria.
        assert [p['id'] for p in products] == ['prod1', 'prod5']
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_empty_all_params(self, local_product_service_instance):
        """
        GIVEN no parameters provided to smart_search_products
        WHEN smart_search_products is called
        THEN it should return all products up to the limit, as they match "no criteria".
        """
        service = local_product_service_instance
        # This case falls into the first `results` check (all products match no filters).
        products, message = service.smart_search_products(limit=3)
        assert len(products) == 3
        assert products[0]['id'] == 'prod1'
        assert products[1]['id'] == 'prod2'
        assert products[2]['id'] == 'prod3'
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_category_case_insensitivity(self, local_product_service_instance):
        """
        Test case-insensitivity for category parameter in smart_search_products.
        """
        service = local_product_service_instance
        products, message = service.smart_search_products(category="smartphone", limit=10)
        assert len(products) == 1
        assert products[0]['id'] == 'prod3'
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_zero_limit(self, local_product_service_instance):
        """
        Test smart_search_products with a limit of 0.
        """
        service = local_product_service_instance
        products, message = service.smart_search_products(keyword="Test Product", limit=0)
        assert len(products) == 0
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_limit_exceeds_available(self, local_product_service_instance):
        """
        Test smart_search_products with a limit greater than available products.
        """
        service = local_product_service_instance
        # There are 7 sample products. Ask for 10.
        products, message = service.smart_search_products(limit=10)
        assert len(products) == 7
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."