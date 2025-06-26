import pytest
import json
from unittest.mock import mock_open, patch, MagicMock
from pathlib import Path
import random
import logging

# Import the class to be tested
from app.services.local_product_service import LocalProductService

# Define a mock data structure for products to use across tests
# This mimics the transformed product structure
MOCK_TRANSFORMED_PRODUCTS = [
    {
        "id": "1",
        "name": "Mock iPhone 15 Pro Max",
        "category": "Smartphone",
        "brand": "Apple",
        "price": 25000000,
        "currency": "IDR",
        "description": "Powerful smartphone from Apple.",
        "specifications": {
            "rating": 4.8,
            "sold": 1250,
            "stock": 50,
            "condition": "Baru",
            "shop_location": "Jakarta",
            "shop_name": "Apple Store Indonesia",
            "storage": "256GB"
        },
        "availability": "in_stock",
        "reviews_count": 100,
        "images": ["https://example.com/1.jpg"],
        "url": "https://shopee.co.id/1"
    },
    {
        "id": "2",
        "name": "Mock Samsung Galaxy S24 Ultra",
        "category": "Smartphone",
        "brand": "Samsung",
        "price": 22000000,
        "currency": "IDR",
        "description": "Android flagship with S Pen.",
        "specifications": {
            "rating": 4.7,
            "sold": 980,
            "stock": 35,
            "condition": "Baru",
            "shop_location": "Surabaya",
            "shop_name": "Samsung Store",
            "storage": "512GB"
        },
        "availability": "in_stock",
        "reviews_count": 80,
        "images": ["https://example.com/2.jpg"],
        "url": "https://shopee.co.id/2"
    },
    {
        "id": "3",
        "name": "Mock MacBook Air M2",
        "category": "Laptop",
        "brand": "Apple",
        "price": 18000000,
        "currency": "IDR",
        "description": "Thin and light laptop from Apple.",
        "specifications": {
            "rating": 4.9,
            "sold": 500,
            "stock": 20,
            "condition": "Baru",
            "shop_location": "Jakarta",
            "shop_name": "Apple Store Indonesia",
            "storage": "512GB"
        },
        "availability": "in_stock",
        "reviews_count": 120,
        "images": ["https://example.com/3.jpg"],
        "url": "https://shopee.co.id/3"
    },
    {
        "id": "4",
        "name": "Mock Gaming Laptop XYZ",
        "category": "Laptop",
        "brand": "ASUS",
        "price": 15000000,
        "currency": "IDR",
        "description": "High-performance gaming laptop.",
        "specifications": {
            "rating": 4.5,
            "sold": 700,
            "stock": 10,
            "condition": "Baru",
            "shop_location": "Bandung",
            "shop_name": "ASUS Gaming",
            "storage": "1TB SSD"
        },
        "availability": "in_stock",
        "reviews_count": 60,
        "images": ["https://example.com/4.jpg"],
        "url": "https://shopee.co.id/4"
    },
    {
        "id": "5",
        "name": "Mock Wireless Earbuds Pro",
        "category": "Audio",
        "brand": "Sony",
        "price": 3000000,
        "currency": "IDR",
        "description": "Noise-cancelling earbuds.",
        "specifications": {
            "rating": 4.6,
            "sold": 1500,
            "stock": 100,
            "condition": "Baru",
            "shop_location": "Jakarta",
            "shop_name": "Sony Audio",
            "color": "Black"
        },
        "availability": "in_stock",
        "reviews_count": 150,
        "images": ["https://example.com/5.jpg"],
        "url": "https://shopee.co.id/5"
    },
    {
        "id": "6",
        "name": "Mock Budget Smartphone",
        "category": "Smartphone",
        "brand": "Xiaomi",
        "price": 2500000,
        "currency": "IDR",
        "description": "Affordable smartphone with good features.",
        "specifications": {
            "rating": 4.2,
            "sold": 2000,
            "stock": 200,
            "condition": "Baru",
            "shop_location": "Semarang",
            "shop_name": "Xiaomi Store",
            "storage": "64GB"
        },
        "availability": "in_stock",
        "reviews_count": 200,
        "images": ["https://example.com/6.jpg"],
        "url": "https://shopee.co.id/6"
    }
]

# Mock raw JSON content that _load_local_products would read
MOCK_RAW_JSON_CONTENT = {
    "products": [
        {
            "id": "1", "name": "Mock iPhone 15 Pro Max", "category": "Smartphone",
            "brand": "Apple", "price": 25000000, "description": "Powerful smartphone from Apple.",
            "rating": 4.8, "stock_count": 50, "availability": "in_stock", "reviews_count": 100,
            "specifications": {"storage": "256GB"}
        },
        {
            "id": "2", "name": "Mock Samsung Galaxy S24 Ultra", "category": "Smartphone",
            "brand": "Samsung", "price": 22000000, "description": "Android flagship with S Pen.",
            "rating": 4.7, "stock_count": 35, "availability": "in_stock", "reviews_count": 80,
            "specifications": {"storage": "512GB"}
        },
        {
            "id": "3", "name": "Mock MacBook Air M2", "category": "Laptop",
            "brand": "Apple", "price": 18000000, "description": "Thin and light laptop from Apple.",
            "rating": 4.9, "stock_count": 20, "availability": "in_stock", "reviews_count": 120,
            "specifications": {"storage": "512GB"}
        },
        {
            "id": "4", "name": "Mock Gaming Laptop XYZ", "category": "Laptop",
            "brand": "ASUS", "price": 15000000, "description": "High-performance gaming laptop.",
            "rating": 4.5, "stock_count": 10, "availability": "in_stock", "reviews_count": 60,
            "specifications": {"storage": "1TB SSD"}
        },
        {
            "id": "5", "name": "Mock Wireless Earbuds Pro", "category": "Audio",
            "brand": "Sony", "price": 3000000, "description": "Noise-cancelling earbuds.",
            "rating": 4.6, "stock_count": 100, "availability": "in_stock", "reviews_count": 150,
            "specifications": {"color": "Black"}
        },
        {
            "id": "6", "name": "Mock Budget Smartphone", "category": "Smartphone",
            "brand": "Xiaomi", "price": 2500000,
            "description": "Affordable smartphone with good features.",
            "rating": 4.2, "stock_count": 200, "availability": "in_stock", "reviews_count": 200,
            "specifications": {"storage": "64GB"}
        }
    ]
}


@pytest.fixture
def mock_path_objects(mocker):
    """
    Fixture to mock pathlib.Path and its methods to control file system interactions.
    This allows controlling `Path.exists()` for the target products.json path.
    """
    # Create mock Path objects for the chain
    mock_file_path_instance = MagicMock(spec=Path, name='Path(__file__)')
    mock_parent_dir = MagicMock(spec=Path, name='current_dir')
    mock_data_dir = MagicMock(spec=Path, name='data_dir')
    mock_products_json = MagicMock(spec=Path, name='products.json_path')

    # Chain the .parent calls correctly: Path(__file__).parent.parent.parent
    # This specific chain needs to return mock_parent_dir
    mock_file_path_instance.parent.parent.parent.return_value = mock_parent_dir

    # Mock the / operator for path joining: current_dir / "data" / "products.json"
    def mock_truediv(self_path, other):
        if str(self_path.name) == "current_dir" and str(other) == "data":
            return mock_data_dir
        elif str(self_path.name) == "data_dir" and str(other) == "products.json":
            return mock_products_json
        return MagicMock(spec=Path) # Default for other Path operations

    mock_parent_dir.__truediv__.side_effect = mock_truediv
    mock_data_dir.__truediv__.side_effect = mock_truediv

    # Patch the Path class constructor to return our initial mock instance.
    # This means when `Path(__file__)` is called, it returns `mock_file_path_instance`.
    mocker.patch('app.services.local_product_service.Path', return_value=mock_file_path_instance)

    # Return the mock for the final products.json path, so its .exists() can be controlled
    return mock_products_json


@pytest.fixture
def mock_open_file(mocker):
    """Fixture to mock builtins.open."""
    m = mock_open()
    mocker.patch('builtins.open', m)
    return m

@pytest.fixture
def mock_random_randint(mocker):
    """Fixture to mock random.randint for deterministic sold counts."""
    return mocker.patch('random.randint', return_value=1000) # Consistent mock sold count

@pytest.fixture
def mock_json_content_loader(mocker):
    """Fixture to control the content returned by json.loads."""
    m = mocker.patch('json.loads', return_value=MOCK_RAW_JSON_CONTENT)
    return m

@pytest.fixture
def local_product_service(mock_path_objects, mock_open_file, mock_random_randint, mock_json_content_loader):
    """
    Fixture to provide a LocalProductService instance with mocked dependencies.
    It implicitly tests the __init__ and _load_local_products happy path.
    """
    # Configure the mock_path_objects to simulate file existence
    mock_path_objects.exists.return_value = True
    
    # Set the read_data for the mock_open_file to return stringified JSON
    mock_open_file.return_value.read.return_value = json.dumps(MOCK_RAW_JSON_CONTENT)
    
    # The mock_json_content_loader is already configured to return MOCK_RAW_JSON_CONTENT
    
    # _load_local_products will use these mocks, and __init__ calls it.
    service = LocalProductService()
    
    # Verify that it loaded the transformed products
    assert len(service.products) == len(MOCK_TRANSFORMED_PRODUCTS)
    
    return service

@pytest.fixture
def local_product_service_with_custom_products():
    """
    Fixture to provide a LocalProductService instance where products are
    directly set, bypassing file loading for simpler testing of other methods.
    """
    service = LocalProductService()
    # Directly set products for testing
    service.products = MOCK_TRANSFORMED_PRODUCTS
    return service

# --- Test __init__ and _load_local_products ---

def test_init_loads_products_successfully(mocker, mock_path_objects, mock_open_file, mock_random_randint, mock_json_content_loader, caplog):
    """
    Test that __init__ successfully loads products from a valid JSON file.
    """
    caplog.set_level(logging.INFO)
    mock_path_objects.exists.return_value = True
    mock_open_file.return_value.read.return_value = json.dumps(MOCK_RAW_JSON_CONTENT)

    service = LocalProductService()

    assert len(service.products) == len(MOCK_TRANSFORMED_PRODUCTS)
    assert service.products[0]['id'] == MOCK_TRANSFORMED_PRODUCTS[0]['id']
    assert service.products[0]['specifications']['sold'] == mock_random_randint.return_value # Verify random is mocked
    
    assert "Loaded 6 local products from JSON file" in caplog.text
    assert "Successfully loaded 6 products from JSON file using utf-8 encoding" in caplog.text


def test_load_local_products_file_not_found(mocker, mock_path_objects, caplog):
    """
    Test _load_local_products when the JSON file does not exist.
    It should return fallback products.
    """
    caplog.set_level(logging.ERROR)
    mock_path_objects.exists.return_value = False # Simulate file not found
    
    service = LocalProductService() # __init__ calls _load_local_products
    
    fallback_products = service._get_fallback_products() # Get actual fallback for comparison
    assert service.products == fallback_products
    assert "Products JSON file not found at:" in caplog.text
    assert "Using fallback products due to JSON file loading error" in caplog.text


def test_load_local_products_all_encodings_fail_unicode_decode_error(mocker, mock_path_objects, mock_open_file, caplog):
    """
    Test _load_local_products when all encoding attempts fail due to UnicodeDecodeError.
    It should return fallback products.
    """
    caplog.set_level(logging.WARNING)
    mock_path_objects.exists.return_value = True
    # Simulate UnicodeDecodeError for all read attempts
    mock_open_file.return_value.read.side_effect = UnicodeDecodeError('utf-8', b'', 0, 1, 'bad data')

    service = LocalProductService()
    
    fallback_products = service._get_fallback_products()
    assert service.products == fallback_products
    assert "Failed to load with utf-16-le encoding" in caplog.text
    assert "Failed to load with utf-16 encoding" in caplog.text
    assert "Failed to load with utf-8 encoding" in caplog.text
    assert "All encoding attempts failed, using fallback products" in caplog.text


def test_load_local_products_all_encodings_fail_json_decode_error(mocker, mock_path_objects, mock_open_file, caplog):
    """
    Test _load_local_products when all encoding attempts result in JSONDecodeError.
    It should return fallback products.
    """
    caplog.set_level(logging.WARNING)
    mock_path_objects.exists.return_value = True
    # Simulate valid read, but json.loads fails
    mock_open_file.return_value.read.return_value = "{ invalid json"
    mocker.patch('json.loads', side_effect=json.JSONDecodeError('Expecting value', '', 0))

    service = LocalProductService()
    
    fallback_products = service._get_fallback_products()
    assert service.products == fallback_products
    assert "Failed to load with utf-16-le encoding" in caplog.text
    assert "Failed to load with utf-8 encoding" in caplog.text # Will attempt different encodings, all leading to JSONDecodeError
    assert "All encoding attempts failed, using fallback products" in caplog.text


def test_load_local_products_open_raises_exception(mocker, mock_path_objects, mock_open_file, caplog):
    """
    Test _load_local_products when opening the file raises a generic Exception.
    It should return fallback products.
    """
    caplog.set_level(logging.ERROR)
    mock_path_objects.exists.return_value = True
    mock_open_file.side_effect = IOError("Permission denied") # Simulate file system error

    service = LocalProductService()
    
    fallback_products = service._get_fallback_products()
    assert service.products == fallback_products
    assert "Error loading products from JSON file: Permission denied" in caplog.text
    assert "Using fallback products due to JSON file loading error" in caplog.text


def test_load_local_products_json_with_bom(mocker, mock_path_objects, mock_open_file, mock_random_randint, caplog):
    """
    Test _load_local_products with a UTF-8 BOM.
    """
    caplog.set_level(logging.INFO)
    mock_path_objects.exists.return_value = True
    # Simulate content with BOM
    json_content_with_bom = '\ufeff' + json.dumps(MOCK_RAW_JSON_CONTENT)
    mock_open_file.return_value.read.return_value = json_content_with_bom
    
    service = LocalProductService()
    
    assert len(service.products) == len(MOCK_TRANSFORMED_PRODUCTS)
    assert service.products[0]['id'] == MOCK_TRANSFORMED_PRODUCTS[0]['id']
    assert "Successfully loaded 6 products from JSON file using utf-8 encoding" in caplog.text # utf-8-sig or utf-8 will handle it


def test_load_local_products_json_missing_keys(mocker, mock_path_objects, mock_open_file, mock_random_randint):
    """
    Test _load_local_products when the JSON has missing product keys.
    Default values should be applied.
    """
    mock_path_objects.exists.return_value = True
    
    # JSON with missing 'name', 'price', 'rating', etc.
    malformed_raw_json = {
        "products": [
            {"id": "missing_data", "category": "Test"}
        ]
    }
    mock_open_file.return_value.read.return_value = json.dumps(malformed_raw_json)
    mocker.patch('json.loads', return_value=malformed_raw_json)

    service = LocalProductService()
    
    assert len(service.products) == 1
    product = service.products[0]
    assert product['id'] == "missing_data"
    assert product['name'] == "" # Default
    assert product['price'] == 0 # Default
    assert product['currency'] == "IDR" # Default
    assert product['specifications']['rating'] == 0 # Default
    assert product['specifications']['sold'] == mock_random_randint.return_value
    assert product['images'] == ["https://example.com/missing_data.jpg"]

def test_load_local_products_empty_products_list_in_json(mocker, mock_path_objects, mock_open_file, caplog):
    """
    Test _load_local_products when the JSON file contains an empty 'products' list.
    """
    caplog.set_level(logging.INFO)
    mock_path_objects.exists.return_value = True
    empty_products_json = {"products": []}
    mock_open_file.return_value.read.return_value = json.dumps(empty_products_json)
    mocker.patch('json.loads', return_value=empty_products_json)

    service = LocalProductService()
    
    assert service.products == []
    assert "Loaded 0 local products from JSON file" in caplog.text
    assert "Successfully loaded 0 products from JSON file using utf-8 encoding" in caplog.text


def test_get_fallback_products():
    """
    Test _get_fallback_products returns a non-empty list of dictionaries.
    """
    service = LocalProductService() # Don't need mocks for this specific test
    products = service._get_fallback_products()
    assert isinstance(products, list)
    assert len(products) > 0
    assert isinstance(products[0], dict)
    assert "id" in products[0]
    assert "name" in products[0]

# --- Test search_products ---

def test_search_products_by_name(local_product_service_with_custom_products):
    """Test searching products by name keyword."""
    service = local_product_service_with_custom_products
    results = service.search_products("iPhone")
    assert len(results) == 1
    assert results[0]['id'] == "1"
    assert "iPhone" in results[0]['name']

def test_search_products_by_brand_case_insensitive(local_product_service_with_custom_products):
    """Test searching products by brand keyword (case-insensitive)."""
    service = local_product_service_with_custom_products
    results = service.search_products("apple")
    # Should find iPhone, MacBook Air
    assert len(results) == 2
    apple_product_names = {p['name'] for p in results}
    assert "Mock iPhone 15 Pro Max" in apple_product_names
    assert "Mock MacBook Air M2" in apple_product_names

def test_search_products_by_category(local_product_service_with_custom_products):
    """Test searching products by category keyword."""
    service = local_product_service_with_custom_products
    results = service.search_products("Laptop")
    assert len(results) == 2
    laptop_product_names = {p['name'] for p in results}
    assert "Mock MacBook Air M2" in laptop_product_names
    assert "Mock Gaming Laptop XYZ" in laptop_product_names

def test_search_products_by_description(local_product_service_with_custom_products):
    """Test searching products by description keyword."""
    service = local_product_service_with_custom_products
    results = service.search_products("flagship")
    assert len(results) == 1
    assert results[0]['id'] == "2" # Samsung Galaxy S24 Ultra

def test_search_products_by_specifications(local_product_service_with_custom_products):
    """Test searching products by specifications keyword."""
    service = local_product_service_with_custom_products
    results = service.search_products("256GB")
    assert len(results) == 1
    assert results[0]['id'] == "1" # Mock iPhone 15 Pro Max

def test_search_products_no_match(local_product_service_with_custom_products):
    """Test searching with a keyword that yields no results."""
    service = local_product_service_with_custom_products
    results = service.search_products("nonexistent_product")
    assert len(results) == 0

def test_search_products_limit(local_product_service_with_custom_products):
    """Test the limit parameter for search results."""
    service = local_product_service_with_custom_products
    results = service.search_products("Mock", limit=3) # "Mock" will match all
    assert len(results) == 3

def test_search_products_empty_keyword(local_product_service_with_custom_products):
    """Test searching with an empty keyword, should return all products up to limit."""
    service = local_product_service_with_custom_products
    results = service.search_products("")
    assert len(results) == 6 # All products

def test_search_products_with_price_keyword_juta(local_product_service_with_custom_products):
    """Test searching with a price keyword like 'juta'."""
    service = local_product_service_with_custom_products
    # Should find products <= 20 juta (Laptop XYZ, MacBook Air, Earbuds, Budget Phone)
    results = service.search_products("20 juta")
    assert len(results) == 4
    product_names = {p['name'] for p in results}
    assert "Mock Gaming Laptop XYZ" in product_names
    assert "Mock MacBook Air M2" in product_names
    assert "Mock Wireless Earbuds Pro" in product_names
    assert "Mock Budget Smartphone" in product_names
    assert results[0]['name'] == "Mock Budget Smartphone"
    assert results[1]['name'] == "Mock Wireless Earbuds Pro"

def test_search_products_with_price_keyword_ribu(local_product_service_with_custom_products):
    """Test searching with a price keyword like 'ribu'."""
    service = local_product_service_with_custom_products
    # Should find products <= 3 juta (Earbuds, Budget Phone)
    results = service.search_products("3000 ribu")
    assert len(results) == 2
    product_names = {p['name'] for p in results}
    assert "Mock Wireless Earbuds Pro" in product_names
    assert "Mock Budget Smartphone" in product_names

def test_search_products_with_budget_keyword(local_product_service_with_custom_products):
    """Test searching with a budget keyword like 'murah'."""
    service = local_product_service_with_custom_products
    # 'murah' maps to 5,000,000 IDR
    results = service.search_products("smartphone murah")
    assert len(results) == 1
    assert results[0]['id'] == "6" # Mock Budget Smartphone (2.5M)

def test_search_products_relevance_sorting(local_product_service_with_custom_products):
    """Test that results are sorted by relevance."""
    service = local_product_service_with_custom_products
    results = service.search_products("laptop")
    assert len(results) == 2
    # "Mock Gaming Laptop XYZ": name match (10) + category match (3) = 13
    # "Mock MacBook Air M2": category match (3) = 3
    assert results[0]['name'] == "Mock Gaming Laptop XYZ"
    assert results[1]['name'] == "Mock MacBook Air M2"

def test_search_products_error_handling(mocker, caplog, local_product_service_with_custom_products):
    """Test search_products error handling."""
    caplog.set_level(logging.ERROR)
    service = local_product_service_with_custom_products
    
    # Simulate an error within the search loop by corrupting a product
    corrupt_products = list(service.products)
    corrupt_products.append({"id": "broken", "name": 123}) # A non-string name will cause type error
    service.products = corrupt_products

    results = service.search_products("any")
    assert results == []
    assert "Error searching products:" in caplog.text


# --- Test _extract_price_from_keyword ---

@pytest.mark.parametrize("keyword, expected_price", [
    ("handphone 10 juta", 10000000),
    ("laptop 5.5 juta", 5000000), # 5.5 is parsed as 5 for "juta" regex
    ("baju 500 ribu", 500000),
    ("headset rp 250000", 250000),
    ("camera 1.2jt", None), # 'jt' is not in regex, only 'juta', 'm'
    ("monitor 2k", 2000), # 'k' for thousand
    ("monitor 2m", 2000000), # 'm' for million
    ("mouse 50k", 50000),
    ("hp murah", 5000000),
    ("laptop budget", 5000000),
    ("tv hemat", 3000000),
    ("tablet terjangkau", 4000000),
    ("printer ekonomis", 2000000),
    ("no price here", None),
    ("", None),
    ("rp 100", 100),
    ("100 rp", 100),
    ("Rp 1.000.000", 1), # Regex only takes digits before 'rp', so 1.000.000 -> 1
    ("Rp. 1,000,000", None), # No regex match for comma/dot separators
    ("iphone", None), # No price/budget keyword
])
def test_extract_price_from_keyword_success(local_product_service_with_custom_products, keyword, expected_price):
    """Test successful price extraction from various keyword formats."""
    service = local_product_service_with_custom_products
    price = service._extract_price_from_keyword(keyword)
    assert price == expected_price

def test_extract_price_from_keyword_error_handling(mocker, caplog, local_product_service_with_custom_products):
    """Test _extract_price_from_keyword error handling."""
    caplog.set_level(logging.ERROR)
    service = local_product_service_with_custom_products
    
    # Mock re.search to raise an exception
    mocker.patch('re.search', side_effect=TypeError("Regex error"))
    
    price = service._extract_price_from_keyword("10 juta")
    assert price is None
    assert "Error extracting price from keyword: Regex error" in caplog.text

# --- Test get_product_details ---

def test_get_product_details_found(local_product_service_with_custom_products):
    """Test getting details for an existing product ID."""
    service = local_product_service_with_custom_products
    product = service.get_product_details("1")
    assert product is not None
    assert product['id'] == "1"
    assert product['name'] == "Mock iPhone 15 Pro Max"

def test_get_product_details_not_found(local_product_service_with_custom_products):
    """Test getting details for a non-existent product ID."""
    service = local_product_service_with_custom_products
    product = service.get_product_details("99")
    assert product is None

def test_get_product_details_empty_products_list(mocker):
    """Test getting product details when there are no products loaded."""
    service = LocalProductService()
    service.products = [] # Explicitly set to empty list for this test
    product = service.get_product_details("1")
    assert product is None

def test_get_product_details_error_handling(mocker, caplog, local_product_service_with_custom_products):
    """Test get_product_details error handling."""
    caplog.set_level(logging.ERROR)
    service = local_product_service_with_custom_products
    
    # Corrupt the product list to cause an error
    service.products = [{"id": "bad"}, 123] # Non-dict in list
    
    product = service.get_product_details("bad")
    assert product is None
    assert "Error getting product details: 'get' must be called with a callable" in caplog.text


# --- Test get_categories ---

def test_get_categories_success(local_product_service_with_custom_products):
    """Test getting unique sorted categories."""
    service = local_product_service_with_custom_products
    categories = service.get_categories()
    expected_categories = sorted(['Smartphone', 'Laptop', 'Audio'])
    assert categories == expected_categories

def test_get_categories_empty_products(mocker):
    """Test getting categories when product list is empty."""
    service = LocalProductService()
    service.products = []
    categories = service.get_categories()
    assert categories == []

def test_get_categories_products_missing_category_key(mocker):
    """Test getting categories when products miss the 'category' key."""
    service = LocalProductService()
    service.products = [
        {"id": "1", "name": "No Category Product"},
        {"id": "2", "name": "Another Product", "category": "Gadgets"}
    ]
    categories = service.get_categories()
    assert categories == ["", "Gadgets"] # Empty string from missing key is included and sorted


# --- Test get_brands ---

def test_get_brands_success(local_product_service_with_custom_products):
    """Test getting unique sorted brands."""
    service = local_product_service_with_custom_products
    brands = service.get_brands()
    expected_brands = sorted(['Apple', 'Samsung', 'ASUS', 'Sony', 'Xiaomi'])
    assert brands == expected_brands

def test_get_brands_empty_products(mocker):
    """Test getting brands when product list is empty."""
    service = LocalProductService()
    service.products = []
    brands = service.get_brands()
    assert brands == []

def test_get_brands_products_missing_brand_key(mocker):
    """Test getting brands when products miss the 'brand' key."""
    service = LocalProductService()
    service.products = [
        {"id": "1", "name": "No Brand Product"},
        {"id": "2", "name": "Another Product", "brand": "Generic"}
    ]
    brands = service.get_brands()
    assert brands == ["", "Generic"]


# --- Test get_products_by_category ---

def test_get_products_by_category_found(local_product_service_with_custom_products):
    """Test getting products by an existing category (case-insensitive)."""
    service = local_product_service_with_custom_products
    results = service.get_products_by_category("smartphone")
    assert len(results) == 3
    category_names = {p['name'] for p in results}
    assert "Mock iPhone 15 Pro Max" in category_names
    assert "Mock Samsung Galaxy S24 Ultra" in category_names
    assert "Mock Budget Smartphone" in category_names

def test_get_products_by_category_not_found(local_product_service_with_custom_products):
    """Test getting products for a non-existent category."""
    service = local_product_service_with_custom_products
    results = service.get_products_by_category("nonexistent_category")
    assert results == []

def test_get_products_by_category_empty_products(mocker):
    """Test getting products by category when product list is empty."""
    service = LocalProductService()
    service.products = []
    results = service.get_products_by_category("any")
    assert results == []

def test_get_products_by_category_error_handling(mocker, caplog, local_product_service_with_custom_products):
    """Test get_products_by_category error handling."""
    caplog.set_level(logging.ERROR)
    service = local_product_service_with_custom_products
    
    # Corrupt a product
    service.products = [{"id": "bad", "category": "Test"}, 123]
    
    results = service.get_products_by_category("Test")
    assert results == []
    assert "Error getting products by category: 'get' must be called with a callable" in caplog.text


# --- Test get_products_by_brand ---

def test_get_products_by_brand_found(local_product_service_with_custom_products):
    """Test getting products by an existing brand (case-insensitive)."""
    service = local_product_service_with_custom_products
    results = service.get_products_by_brand("apple")
    assert len(results) == 2
    brand_names = {p['name'] for p in results}
    assert "Mock iPhone 15 Pro Max" in brand_names
    assert "Mock MacBook Air M2" in brand_names

def test_get_products_by_brand_not_found(local_product_service_with_custom_products):
    """Test getting products for a non-existent brand."""
    service = local_product_service_with_custom_products
    results = service.get_products_by_brand("nonexistent_brand")
    assert results == []

def test_get_products_by_brand_empty_products(mocker):
    """Test getting products by brand when product list is empty."""
    service = LocalProductService()
    service.products = []
    results = service.get_products_by_brand("any")
    assert results == []

def test_get_products_by_brand_error_handling(mocker, caplog, local_product_service_with_custom_products):
    """Test get_products_by_brand error handling."""
    caplog.set_level(logging.ERROR)
    service = local_product_service_with_custom_products
    
    # Corrupt a product
    service.products = [{"id": "bad", "brand": "Test"}, 123]
    
    results = service.get_products_by_brand("Test")
    assert results == []
    assert "Error getting products by brand: 'get' must be called with a callable" in caplog.text


# --- Test get_top_rated_products ---

def test_get_top_rated_products_success(local_product_service_with_custom_products):
    """Test getting top rated products with default limit."""
    service = local_product_service_with_custom_products
    # Ratings: MacBook Air (4.9), iPhone (4.8), Samsung (4.7), Earbuds (4.6), Gaming Laptop (4.5), Budget Phone (4.2)
    results = service.get_top_rated_products() # Default limit 5
    assert len(results) == 5
    assert results[0]['id'] == "3" # MacBook Air M2 (4.9)
    assert results[1]['id'] == "1" # iPhone 15 Pro Max (4.8)
    assert results[2]['id'] == "2" # Samsung Galaxy S24 Ultra (4.7)
    assert results[3]['id'] == "5" # Wireless Earbuds Pro (4.6)
    assert results[4]['id'] == "4" # Gaming Laptop XYZ (4.5)

def test_get_top_rated_products_with_limit(local_product_service_with_custom_products):
    """Test getting top rated products with a specific limit."""
    service = local_product_service_with_custom_products
    results = service.get_top_rated_products(limit=2)
    assert len(results) == 2
    assert results[0]['id'] == "3"
    assert results[1]['id'] == "1"

def test_get_top_rated_products_limit_exceeds_total(local_product_service_with_custom_products):
    """Test getting top rated products with a limit greater than total products."""
    service = local_product_service_with_custom_products
    results = service.get_top_rated_products(limit=100)
    assert len(results) == len(MOCK_TRANSFORMED_PRODUCTS)

def test_get_top_rated_products_empty_products(mocker):
    """Test getting top rated products when product list is empty."""
    service = LocalProductService()
    service.products = []
    results = service.get_top_rated_products()
    assert results == []

def test_get_top_rated_products_missing_rating_key(mocker):
    """Test getting top rated products when some products miss rating or specifications."""
    service = LocalProductService()
    service.products = [
        {"id": "A", "specifications": {"rating": 5.0}, "name": "Best"},
        {"id": "B", "specifications": {}, "name": "No Rating"}, # rating defaults to 0
        {"id": "C", "name": "No Specs"}, # specs defaults to {}, rating to 0
        {"id": "D", "specifications": {"rating": 4.0}, "name": "Good"},
    ]
    results = service.get_top_rated_products(limit=3)
    assert len(results) == 3
    assert results[0]['id'] == "A"
    assert results[1]['id'] == "D"
    assert results[2]['id'] in ["B", "C"] # Order of same-rated products (0) isn't guaranteed

def test_get_top_rated_products_error_handling(mocker, caplog, local_product_service_with_custom_products):
    """Test get_top_rated_products error handling."""
    caplog.set_level(logging.ERROR)
    service = local_product_service_with_custom_products
    
    # Corrupt a product to cause a TypeError in lambda
    service.products = [{"id": "good", "specifications": {"rating": 5}}, 123]
    
    results = service.get_top_rated_products()
    assert results == []
    assert "Error getting top rated products: 'get' must be called with a callable" in caplog.text


# --- Test get_best_selling_products ---

def test_get_best_selling_products_success(local_product_service_with_custom_products, caplog):
    """Test getting best selling products with default limit."""
    caplog.set_level(logging.INFO)
    service = local_product_service_with_custom_products
    # Sold: Budget Phone (2000), Earbuds (1500), iPhone (1250), Samsung (980), Gaming Laptop (700), MacBook (500)
    results = service.get_best_selling_products() # Default limit 5
    assert len(results) == 5
    assert results[0]['id'] == "6" # Budget Phone (2000)
    assert results[1]['id'] == "5" # Wireless Earbuds (1500)
    assert results[2]['id'] == "1" # iPhone (1250)
    assert results[3]['id'] == "2" # Samsung (980)
    assert results[4]['id'] == "4" # Gaming Laptop (700)
    assert "Getting best selling products, limit: 5" in caplog.text
    assert "Returning 5 best selling products" in caplog.text


def test_get_best_selling_products_with_limit(local_product_service_with_custom_products):
    """Test getting best selling products with a specific limit."""
    service = local_product_service_with_custom_products
    results = service.get_best_selling_products(limit=2)
    assert len(results) == 2
    assert results[0]['id'] == "6"
    assert results[1]['id'] == "5"

def test_get_best_selling_products_limit_exceeds_total(local_product_service_with_custom_products):
    """Test getting best selling products with a limit greater than total products."""
    service = local_product_service_with_custom_products
    results = service.get_best_selling_products(limit=100)
    assert len(results) == len(MOCK_TRANSFORMED_PRODUCTS)

def test_get_best_selling_products_empty_products(mocker):
    """Test getting best selling products when product list is empty."""
    service = LocalProductService()
    service.products = []
    results = service.get_best_selling_products()
    assert results == []

def test_get_best_selling_products_missing_sold_key(mocker):
    """Test getting best selling products when some products miss sold count or specifications."""
    service = LocalProductService()
    service.products = [
        {"id": "A", "specifications": {"sold": 1000}, "name": "High Sales"},
        {"id": "B", "specifications": {}, "name": "No Sold"}, # sold defaults to 0
        {"id": "C", "name": "No Specs"}, # specs defaults to {}, sold to 0
        {"id": "D", "specifications": {"sold": 500}, "name": "Medium Sales"},
    ]
    results = service.get_best_selling_products(limit=3)
    assert len(results) == 3
    assert results[0]['id'] == "A"
    assert results[1]['id'] == "D"
    assert results[2]['id'] in ["B", "C"]

def test_get_best_selling_products_error_handling(mocker, caplog, local_product_service_with_custom_products):
    """Test get_best_selling_products error handling."""
    caplog.set_level(logging.ERROR)
    service = local_product_service_with_custom_products
    
    # Corrupt a product to cause a TypeError in lambda
    service.products = [{"id": "good", "specifications": {"sold": 100}}, 123]
    
    results = service.get_best_selling_products()
    assert results == []
    assert "Error getting best selling products: 'get' must be called with a callable" in caplog.text


# --- Test get_products ---

def test_get_products_success(local_product_service_with_custom_products, caplog):
    """Test getting all products with default limit."""
    caplog.set_level(logging.INFO)
    service = local_product_service_with_custom_products
    results = service.get_products() # Default limit 10
    assert len(results) == 6 # Total products is 6, limit 10 returns all
    assert "Getting all products, limit: 10" in caplog.text

def test_get_products_with_limit(local_product_service_with_custom_products):
    """Test getting all products with a specific limit."""
    service = local_product_service_with_custom_products
    results = service.get_products(limit=3)
    assert len(results) == 3

def test_get_products_empty_products(mocker):
    """Test getting products when product list is empty."""
    service = LocalProductService()
    service.products = []
    results = service.get_products()
    assert results == []

def test_get_products_error_handling(mocker, caplog, local_product_service_with_custom_products):
    """Test get_products error handling (e.g., if products list is not a list)."""
    caplog.set_level(logging.ERROR)
    service = local_product_service_with_custom_products
    
    # Simulate a scenario where self.products is not iterable or causes error during slice
    service.products = None 
    
    results = service.get_products()
    assert results == []
    assert "Error getting products: 'NoneType' object is not subscriptable" in caplog.text


# --- Test smart_search_products ---

def test_smart_search_products_best_general(local_product_service_with_custom_products):
    """Test smart_search_products for general "best" request."""
    service = local_product_service_with_custom_products
    # MacBook Air (4.9), iPhone (4.8), Samsung (4.7), Earbuds (4.6), Gaming Laptop (4.5)
    products, message = service.smart_search_products(keyword="terbaik")
    assert len(products) == 5
    assert products[0]['id'] == "3" # MacBook Air M2 (4.9)
    assert "Berikut produk terbaik berdasarkan rating:" in message

def test_smart_search_products_best_by_category_found(local_product_service_with_custom_products):
    """Test smart_search_products for "best" in a specific category."""
    service = local_product_service_with_custom_products
    # Smartphones: iPhone (4.8), Samsung (4.7), Budget Phone (4.2)
    products, message = service.smart_search_products(keyword="terbaik", category="Smartphone")
    assert len(products) == 3
    assert products[0]['id'] == "1" # iPhone 15 Pro Max (4.8)
    assert "Berikut Smartphone terbaik berdasarkan rating:" in message

def test_smart_search_products_best_by_category_not_found_fallback(local_product_service_with_custom_products):
    """
    Test smart_search_products when "best" category is not found.
    Should fallback to general best products.
    """
    service = local_product_service_with_custom_products
    products, message = service.smart_search_products(keyword="best", category="NonExistentCategory")
    assert len(products) == 5 # Should be general best products
    assert products[0]['id'] == "3" # MacBook Air M2 (4.9)
    assert "Tidak ada produk kategori NonExistentCategory, berikut produk terbaik secara umum:" in message

def test_smart_search_products_all_criteria_match(local_product_service_with_custom_products):
    """Test smart_search_products where all keyword, category, max_price criteria match."""
    service = local_product_service_with_custom_products
    products, message = service.smart_search_products(
        keyword="Mock", category="Smartphone", max_price=23000000, limit=2
    )
    # Matches: iPhone (25M, too high), Samsung (22M), Budget (2.5M)
    # Only Samsung (22M) and Budget (2.5M) fit price and category.
    assert len(products) == 2
    product_ids = {p['id'] for p in products}
    assert "2" in product_ids # Samsung
    assert "6" in product_ids # Budget Smartphone
    assert "Berikut produk yang sesuai dengan kriteria Anda." in message

def test_smart_search_products_fallback_to_category_and_price_not_met(local_product_service_with_custom_products):
    """
    Test smart_search_products: no exact match, but category matches (fallback 4).
    Keyword: 'expensive', Category: 'Laptop', Max_price: 10M.
    No laptop is <= 10M. So the primary search yields nothing.
    It should then fallback to "products in the same category" (Laptops), sorted by price.
    """
    service = local_product_service_with_custom_products
    products, message = service.smart_search_products(keyword="expensive", category="Laptop", max_price=10000000)
    # Primary search: no "expensive" laptop <= 10M
    # Fallback to category "Laptop": MacBook Air (18M), Gaming Laptop (15M)
    assert len(products) == 2
    assert products[0]['id'] == "4" # Gaming Laptop XYZ (15M - cheapest laptop)
    assert products[1]['id'] == "3" # MacBook Air M2 (18M)
    assert "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut." in message

def test_smart_search_products_fallback_to_budget_only_category_not_met(local_product_service_with_custom_products):
    """
    Test smart_search_products: no exact match, no category match, but budget matches (fallback 5).
    Keyword: 'weird', Category: 'NonExistent', Max_price: 3.5M.
    """
    service = local_product_service_with_custom_products
    products, message = service.smart_search_products(keyword="weird", category="NonExistentCategory", max_price=3500000)
    # Primary search: no match
    # Fallback 4 (category): no NonExistentCategory
    # Fallback 5 (budget only): Earbuds (3M), Budget Smartphone (2.5M)
    assert len(products) == 2
    product_ids = {p['id'] for p in products}
    assert "5" in product_ids # Earbuds
    assert "6" in product_ids # Budget Smartphone
    assert "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda." in message

def test_smart_search_products_fallback_to_popular_all_fail(local_product_service_with_custom_products):
    """
    Test smart_search_products: no match on any criteria or fallbacks, should return popular products (fallback 6).
    Keyword: 'unfindable', Category: 'NonExistent', Max_price: 100.
    """
    service = local_product_service_with_custom_products
    products, message = service.smart_search_products(keyword="unfindable", category="NonExistentCategory", max_price=100)
    # All previous fallbacks fail.
    # Should return best selling (popular) products.
    # Sold: Budget Phone (2000), Earbuds (1500), iPhone (1250), Samsung (980), Gaming Laptop (700)
    assert len(products) == 5
    assert products[0]['id'] == "6" # Budget Phone
    assert "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in message

def test_smart_search_products_empty_products_list_fallback_popular(mocker):
    """Test smart_search_products when the product list is empty."""
    service = LocalProductService()
    service.products = []
    products, message = service.smart_search_products(keyword="any")
    assert products == []
    assert "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in message # Fallback 6 applies to empty list as well.

def test_smart_search_products_no_params_returns_all_matching_criteria(local_product_service_with_custom_products):
    """
    Test smart_search_products with no parameters provided.
    Should return all products up to limit, as all implicitly match the 'no criteria' filter.
    """
    service = local_product_service_with_custom_products
    products, message = service.smart_search_products()
    assert len(products) == 5 # Default limit
    assert products == MOCK_TRANSFORMED_PRODUCTS[:5] # Should return first 5 as no filtering happens
    assert "Berikut produk yang sesuai dengan kriteria Anda." in message

def test_smart_search_products_edge_case_keyword_match_only(local_product_service_with_custom_products):
    """Test smart search when only keyword matches, no category/price constraints."""
    service = local_product_service_with_custom_products
    products, message = service.smart_search_products(keyword="smartphone")
    assert len(products) == 3
    assert "Berikut produk yang sesuai dengan kriteria Anda." in message

def test_smart_search_products_edge_case_max_price_match_only(local_product_service_with_custom_products):
    """Test smart search when only max_price matches, no keyword/category constraints."""
    service = local_product_service_with_custom_products
    products, message = service.smart_search_products(max_price=3000000)
    assert len(products) == 2 # Earbuds (3M), Budget Smartphone (2.5M)
    assert "Berikut produk yang sesuai dengan kriteria Anda." in message

def test_smart_search_products_edge_case_category_match_only(local_product_service_with_custom_products):
    """Test smart search when only category matches, no keyword/price constraints."""
    service = local_product_service_with_custom_products
    products, message = service.smart_search_products(category="Laptop")
    assert len(products) == 2
    assert "Berikut produk yang sesuai dengan kriteria Anda." in message