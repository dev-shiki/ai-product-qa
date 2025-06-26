import pytest
import json
from unittest.mock import patch, mock_open, MagicMock
import logging
from pathlib import Path
import sys

# Add the parent directory to the path to import the module
# This ensures that the test can find the module 'app.services'
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.local_product_service import LocalProductService

# --- Fixtures ---

@pytest.fixture
def mock_products_data():
    """Mock product data for successful loading."""
    return {
        "products": [
            {
                "id": "prod1",
                "name": "Smartphone X",
                "category": "Smartphone",
                "brand": "Brand A",
                "price": 10000000,
                "currency": "IDR",
                "description": "Powerful smartphone",
                "specifications": {"rating": 4.5, "stock_count": 100},
                "availability": "in_stock",
                "reviews_count": 50
            },
            {
                "id": "prod2",
                "name": "Laptop Y",
                "category": "Laptop",
                "brand": "Brand B",
                "price": 15000000,
                "currency": "IDR",
                "description": "High-performance laptop",
                "specifications": {"rating": 4.8, "stock_count": 50, "storage": "512GB"},
                "availability": "in_stock",
                "reviews_count": 70
            },
            {
                "id": "prod3",
                "name": "Headphone Z",
                "category": "Audio",
                "brand": "Brand C",
                "price": 2000000,
                "currency": "IDR",
                "description": "Noise-cancelling headphones",
                "specifications": {"rating": 4.0, "stock_count": 200},
                "availability": "out_of_stock",
                "reviews_count": 30
            },
            {
                "id": "prod4",
                "name": "Budget Phone",
                "category": "Smartphone",
                "brand": "Brand A",
                "price": 1500000, # cheap product
                "currency": "IDR",
                "description": "Affordable smartphone for daily use",
                "specifications": {"rating": 3.5, "stock_count": 300},
                "availability": "in_stock",
                "reviews_count": 10
            },
            {
                "id": "prod5",
                "name": "Gaming Laptop",
                "category": "Laptop",
                "brand": "Brand B",
                "price": 20000000,
                "currency": "IDR",
                "description": "Ultimate gaming machine",
                "specifications": {"rating": 4.9, "stock_count": 20},
                "availability": "in_stock",
                "reviews_count": 90
            }
        ]
    }

@pytest.fixture
def mock_transformed_products():
    """Expected transformed product structure for mock_products_data."""
    # This assumes random.randint is mocked to return a fixed value, e.g., 500
    return [
        {
            "id": "prod1", "name": "Smartphone X", "category": "Smartphone", "brand": "Brand A",
            "price": 10000000, "currency": "IDR", "description": "Powerful smartphone",
            "specifications": {
                "rating": 4.5, "sold": 500, "stock": 100, "condition": "Baru",
                "shop_location": "Indonesia", "shop_name": "Brand A Store"
            },
            "availability": "in_stock", "reviews_count": 50,
            "images": ["https://example.com/prod1.jpg"], "url": "https://shopee.co.id/prod1"
        },
        {
            "id": "prod2", "name": "Laptop Y", "category": "Laptop", "brand": "Brand B",
            "price": 15000000, "currency": "IDR", "description": "High-performance laptop",
            "specifications": {
                "rating": 4.8, "sold": 500, "stock": 50, "storage": "512GB", "condition": "Baru",
                "shop_location": "Indonesia", "shop_name": "Brand B Store"
            },
            "availability": "in_stock", "reviews_count": 70,
            "images": ["https://example.com/prod2.jpg"], "url": "https://shopee.co.id/prod2"
        },
        {
            "id": "prod3", "name": "Headphone Z", "category": "Audio", "brand": "Brand C",
            "price": 2000000, "currency": "IDR", "description": "Noise-cancelling headphones",
            "specifications": {
                "rating": 4.0, "sold": 500, "stock": 200, "condition": "Baru",
                "shop_location": "Indonesia", "shop_name": "Brand C Store"
            },
            "availability": "out_of_stock", "reviews_count": 30,
            "images": ["https://example.com/prod3.jpg"], "url": "https://shopee.co.id/prod3"
        },
        {
            "id": "prod4", "name": "Budget Phone", "category": "Smartphone", "brand": "Brand A",
            "price": 1500000, "currency": "IDR", "description": "Affordable smartphone for daily use",
            "specifications": {
                "rating": 3.5, "sold": 500, "stock": 300, "condition": "Baru",
                "shop_location": "Indonesia", "shop_name": "Brand A Store"
            },
            "availability": "in_stock", "reviews_count": 10,
            "images": ["https://example.com/prod4.jpg"], "url": "https://shopee.co.id/prod4"
        },
        {
            "id": "prod5", "name": "Gaming Laptop", "category": "Laptop", "brand": "Brand B",
            "price": 20000000, "currency": "IDR", "description": "Ultimate gaming machine",
            "specifications": {
                "rating": 4.9, "sold": 500, "stock": 20, "condition": "Baru",
                "shop_location": "Indonesia", "shop_name": "Brand B Store"
            },
            "availability": "in_stock", "reviews_count": 90,
            "images": ["https://example.com/prod5.jpg"], "url": "https://shopee.co.id/prod5"
        }
    ]

@pytest.fixture
def service_with_mock_products(mock_products_data, mock_transformed_products):
    """
    Fixture for LocalProductService instance with mocked product loading.
    Mocks Path.exists to true, open to return valid JSON, and random.randint.
    """
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=json.dumps(mock_products_data))), \
         patch('random.randint', return_value=500), \
         patch.object(LocalProductService, '_get_fallback_products') as mock_fallback: # Mock fallback
        # Ensure fallback is not called in this fixture
        mock_fallback.return_value = [] # This return value should not be used
        service = LocalProductService()
        # Overwrite products with the expected transformed output for consistent tests
        service.products = mock_transformed_products
        yield service

@pytest.fixture(autouse=True)
def mock_logger():
    """Mock the logger to capture logs during tests."""
    with patch('app.services.local_product_service.logger') as mock_log:
        yield mock_log

# --- Test LocalProductService Initialization and _load_local_products ---

def test_init_loads_products_successfully(service_with_mock_products, mock_logger, mock_transformed_products):
    """
    Test that __init__ successfully loads products from a mock file.
    """
    service = service_with_mock_products
    assert len(service.products) == len(mock_transformed_products)
    assert service.products == mock_transformed_products
    mock_logger.info.assert_any_call(f"Loaded {len(mock_transformed_products)} local products from JSON file")
    mock_logger.info.assert_any_call(f"Successfully loaded {len(mock_transformed_products)} products from JSON file using utf-8 encoding")

@patch('pathlib.Path.exists', return_value=False)
def test_init_uses_fallback_if_file_not_found(mock_exists, mock_logger):
    """
    Test that __init__ uses fallback products if the JSON file is not found.
    """
    service = LocalProductService()
    assert len(service.products) > 0  # Fallback products should be loaded
    mock_exists.assert_called_once()
    mock_logger.error.assert_any_call(f"Products JSON file not found at: {Path(__file__).parent.parent.parent / 'data' / 'products.json'}")
    mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error")
    mock_logger.info.assert_any_call(f"Loaded {len(service.products)} local products from JSON file")


@patch('builtins.open', new_callable=mock_open, read_data='invalid json')
@patch('pathlib.Path.exists', return_value=True)
def test_load_local_products_handles_json_decode_error(mock_exists, mock_open_file, mock_logger):
    """
    Test that _load_local_products handles JSONDecodeError and uses fallback.
    """
    service = LocalProductService()
    assert len(service.products) > 0  # Should fall back
    mock_exists.assert_called_once()
    # Check attempts with different encodings
    assert mock_open_file.call_count == len(LocalProductService._load_local_products.__defaults__[0]) 
    mock_logger.warning.assert_called() # Should log warnings for each failed encoding
    mock_logger.error.assert_any_call("All encoding attempts failed, using fallback products")
    mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error")

@patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'\xfe\xff', 0, 1, 'mock error'))
@patch('pathlib.Path.exists', return_value=True)
def test_load_local_products_handles_unicode_decode_error(mock_exists, mock_open_file, mock_logger):
    """
    Test that _load_local_products handles UnicodeDecodeError for all encodings and uses fallback.
    """
    service = LocalProductService()
    assert len(service.products) > 0  # Should fall back
    mock_exists.assert_called_once()
    # Check attempts with different encodings
    assert mock_open_file.call_count == len(LocalProductService._load_local_products.__defaults__[0])
    mock_logger.warning.assert_called() # Should log warnings for each failed encoding
    mock_logger.error.assert_any_call("All encoding attempts failed, using fallback products")
    mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error")

@patch('builtins.open', new_callable=mock_open, read_data='{}') # Empty JSON
@patch('pathlib.Path.exists', return_value=True)
@patch('random.randint', return_value=500)
def test_load_local_products_handles_empty_json_data(mock_randint, mock_exists, mock_open_file, mock_logger):
    """
    Test that _load_local_products handles an empty JSON object (no 'products' key).
    """
    service = LocalProductService()
    assert service.products == []
    mock_logger.info.assert_any_call("Successfully loaded 0 products from JSON file using utf-8 encoding")

@patch('builtins.open', new_callable=mock_open, read_data=json.dumps({"products": []})) # Empty products list
@patch('pathlib.Path.exists', return_value=True)
@patch('random.randint', return_value=500)
def test_load_local_products_handles_empty_products_list(mock_randint, mock_exists, mock_open_file, mock_logger):
    """
    Test that _load_local_products handles a JSON file with an empty 'products' list.
    """
    service = LocalProductService()
    assert service.products == []
    mock_logger.info.assert_any_call("Successfully loaded 0 products from JSON file using utf-8 encoding")

@patch('builtins.open', new_callable=mock_open, read_data='\ufeff' + json.dumps({"products": [{"id": "bom_prod", "name": "BOM Product"}]}))
@patch('pathlib.Path.exists', return_value=True)
@patch('random.randint', return_value=500)
def test_load_local_products_handles_bom(mock_randint, mock_exists, mock_open_file, mock_logger):
    """
    Test that _load_local_products correctly handles JSON with a BOM.
    """
    service = LocalProductService()
    assert len(service.products) == 1
    assert service.products[0]['id'] == "bom_prod"
    assert service.products[0]['name'] == "BOM Product"
    mock_logger.info.assert_any_call("Successfully loaded 1 products from JSON file using utf-8 encoding")


@patch('builtins.open', new_callable=mock_open, read_data=json.dumps({"products": [{"id": "missing_fields"}]}))
@patch('pathlib.Path.exists', return_value=True)
@patch('random.randint', return_value=500)
def test_load_local_products_applies_default_values_for_missing_fields(mock_randint, mock_exists, mock_open_file, mock_logger):
    """
    Test that _load_local_products applies default values for missing product fields.
    """
    service = LocalProductService()
    assert len(service.products) == 1
    product = service.products[0]
    assert product['id'] == 'missing_fields'
    assert product['name'] == ''
    assert product['category'] == ''
    assert product['brand'] == ''
    assert product['price'] == 0
    assert product['currency'] == 'IDR'
    assert product['description'] == ''
    assert product['specifications']['rating'] == 0
    assert product['specifications']['sold'] == 500 # Mocked value
    assert product['specifications']['stock'] == 0
    assert product['availability'] == 'in_stock'
    assert product['reviews_count'] == 0
    assert product['images'] == ["https://example.com/missing_fields.jpg"]
    assert product['url'] == "https://shopee.co.id/missing_fields"

@patch('builtins.open', side_effect=IOError("Permission denied"))
@patch('pathlib.Path.exists', return_value=True)
def test_load_local_products_handles_generic_exception(mock_exists, mock_open_file, mock_logger):
    """
    Test that _load_local_products handles a generic exception during file operation and uses fallback.
    """
    service = LocalProductService()
    assert len(service.products) > 0  # Should fall back
    mock_exists.assert_called_once()
    mock_logger.error.assert_called_once_with("Error loading products from JSON file: Permission denied")
    mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error")

def test_get_fallback_products_returns_expected_data(mock_logger):
    """
    Test that _get_fallback_products returns a non-empty list of structured products.
    """
    service = LocalProductService() # This will auto-call fallback if no file
    # We want to test _get_fallback_products in isolation here
    fallback_products = service._get_fallback_products()
    assert isinstance(fallback_products, list)
    assert len(fallback_products) > 0
    assert "iPhone 15 Pro Max" in [p['name'] for p in fallback_products]
    mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error")

# --- Test search_products ---

def test_search_products_by_name(service_with_mock_products):
    """
    Test searching products by name (case-insensitive, partial).
    """
    results = service_with_mock_products.search_products("smartphone")
    assert len(results) == 2
    assert "Smartphone X" in [p['name'] for p in results]
    assert "Budget Phone" in [p['name'] for p in results]

def test_search_products_by_category(service_with_mock_products):
    """
    Test searching products by category.
    """
    results = service_with_mock_products.search_products("Laptop")
    assert len(results) == 2
    assert "Laptop Y" in [p['name'] for p in results]
    assert "Gaming Laptop" in [p['name'] for p in results]

def test_search_products_by_brand(service_with_mock_products):
    """
    Test searching products by brand.
    """
    results = service_with_mock_products.search_products("Brand A")
    assert len(results) == 2
    assert "Smartphone X" in [p['name'] for p in results]
    assert "Budget Phone" in [p['name'] for p in results]

def test_search_products_by_description(service_with_mock_products):
    """
    Test searching products by description.
    """
    results = service_with_mock_products.search_products("high-performance")
    assert len(results) == 1
    assert results[0]['name'] == "Laptop Y"

def test_search_products_by_specifications(service_with_mock_products):
    """
    Test searching products by specifications content.
    """
    results = service_with_mock_products.search_products("512gb")
    assert len(results) == 1
    assert results[0]['name'] == "Laptop Y"

def test_search_products_no_match(service_with_mock_products):
    """
    Test searching for a keyword that does not match any product.
    """
    results = service_with_mock_products.search_products("nonexistent product")
    assert len(results) == 0

def test_search_products_with_limit(service_with_mock_products):
    """
    Test that the limit parameter works correctly.
    """
    results = service_with_mock_products.search_products("phone", limit=1)
    assert len(results) == 1
    # Check if the highest relevance (Smartphone X) is returned first due to default sorting
    assert results[0]['name'] == "Smartphone X" # 'Smartphone' exact match in name, 'Phone' is partial for 'Budget Phone'

def test_search_products_empty_keyword_returns_all_limited(service_with_mock_products):
    """
    Test that an empty keyword returns all products up to the limit.
    """
    results = service_with_mock_products.search_products("", limit=3)
    assert len(results) == 3
    # Check default sorting (relevance_score will default to name, then price)
    expected_names = ["Gaming Laptop", "Laptop Y", "Smartphone X"]
    assert all(p['name'] in expected_names for p in results)

def test_search_products_sorts_by_relevance(service_with_mock_products):
    """
    Test that products are sorted by relevance (name match, brand, category).
    """
    # "Brand A" is both a brand and part of "Smartphone X" name/category search,
    # but "Smartphone X" name match gives higher score.
    # "Budget Phone" also Brand A, but has "Phone" in name (partial match vs "Smartphone X" full)
    results = service_with_mock_products.search_products("Phone Brand A")
    assert results[0]['name'] == "Smartphone X" # "Smartphone X" has "phone" in name AND "Brand A"
    assert results[1]['name'] == "Budget Phone" # "Budget Phone" has "phone" in name AND "Brand A"
    assert len(results) == 2


def test_search_products_with_price_keyword_juta(service_with_mock_products):
    """
    Test search with price keyword 'juta'.
    """
    # Smartphone X (10juta), Laptop Y (15juta), Headphone Z (2juta), Budget Phone (1.5juta), Gaming Laptop (20juta)
    # Search for "smartphone 12 juta" -> should get Smartphone X (10juta), Budget Phone (1.5juta)
    results = service_with_mock_products.search_products("smartphone 12 juta")
    assert len(results) == 2
    assert all(p['price'] <= 12000000 for p in results)
    assert results[0]['name'] == "Smartphone X" # Closer to 12juta (higher relevance)
    assert results[1]['name'] == "Budget Phone"


def test_search_products_with_price_keyword_ribu(service_with_mock_products):
    """
    Test search with price keyword 'ribu'.
    """
    results = service_with_mock_products.search_products("headphone 3000 ribu") # 3,000,000
    assert len(results) == 1
    assert results[0]['name'] == "Headphone Z"
    assert results[0]['price'] <= 3000000

def test_search_products_with_price_keyword_rp(service_with_mock_products):
    """
    Test search with price keyword 'rp'.
    """
    results = service_with_mock_products.search_products("laptop rp 18000000") # 18,000,000
    assert len(results) == 2 # Laptop Y (15m), Gaming Laptop (20m) - should include Laptop Y
    assert results[0]['name'] == "Laptop Y" # Higher relevance score (price + laptop keyword)

def test_search_products_with_budget_keyword_murah(service_with_mock_products):
    """
    Test search with budget keyword 'murah'.
    (murah defaults to 5juta)
    """
    results = service_with_mock_products.search_products("phone murah")
    assert len(results) == 2
    assert results[0]['name'] == "Budget Phone" # Price 1.5M, "murah" preference
    assert results[1]['name'] == "Smartphone X" # Price 10M, but "phone" is present
    assert results[0]['price'] < results[1]['price'] # Lower price preferred for budget searches

def test_search_products_with_budget_keyword_terjangkau(service_with_mock_products):
    """
    Test search with budget keyword 'terjangkau'.
    (terjangkau defaults to 4juta)
    """
    results = service_with_mock_products.search_products("audio terjangkau")
    assert len(results) == 1
    assert results[0]['name'] == "Headphone Z" # Price 2M
    assert results[0]['price'] <= 4000000

@patch.object(LocalProductService, '_extract_price_from_keyword', side_effect=Exception("Price extract error"))
def test_search_products_handles_extract_price_exception(mock_extract_price, service_with_mock_products, mock_logger):
    """
    Test that search_products handles exceptions during price extraction.
    """
    results = service_with_mock_products.search_products("any keyword")
    assert len(results) > 0 # Should still perform keyword search
    mock_extract_price.assert_called_once()
    mock_logger.error.assert_called_with("Error extracting price from keyword: Price extract error")

@patch.object(LocalProductService, 'products', new_callable=MagicMock, side_effect=Exception("Product access error"))
def test_search_products_handles_generic_exception(mock_products_access, mock_logger):
    """
    Test that search_products handles generic exceptions during iteration.
    """
    service = LocalProductService()
    service.products = [] # Reset to avoid initial load issues
    mock_products_access.side_effect = Exception("Product access error") # Set after init
    
    results = service.search_products("keyword")
    assert results == []
    mock_logger.error.assert_called_once_with("Error searching products: Product access error")


# --- Test _extract_price_from_keyword ---

@pytest.mark.parametrize("keyword, expected_price", [
    ("laptop 10 juta", 10000000),
    ("smartphone 2.5 juta", None), # Decimal not supported by regex, should return None
    ("headphone 500 ribu", 500000),
    ("camera rp 12000000", 12000000),
    ("drone 750000 rp", 750000),
    ("monitor 10k", 10000),
    ("pc 2m", 2000000),
    ("murah laptop", 5000000),
    ("budget pc", 5000000),
    ("headset hemat", 3000000),
    ("tv terjangkau", 4000000),
    ("printer ekonomis", 2000000),
    ("laptop 10 juta murah", 10000000), # Price pattern takes precedence
    ("murah 10 juta laptop", 10000000)
])
def test_extract_price_from_keyword_success(keyword, expected_price):
    """
    Test successful extraction of price from various keyword patterns.
    """
    service = LocalProductService() # We don't need mock products for this method
    price = service._extract_price_from_keyword(keyword)
    assert price == expected_price

@pytest.mark.parametrize("keyword", [
    "no price here",
    "just some text",
    "rp", # Incomplete
    "juta", # Incomplete
    "1.5k", # Decimal not supported
    "" # Empty keyword
])
def test_extract_price_from_keyword_no_match(keyword):
    """
    Test _extract_price_from_keyword returns None for keywords without price patterns.
    """
    service = LocalProductService()
    price = service._extract_price_from_keyword(keyword)
    assert price is None

@patch('re.search', side_effect=Exception("Regex error"))
def test_extract_price_from_keyword_handles_exception(mock_re_search, mock_logger):
    """
    Test _extract_price_from_keyword handles internal exceptions.
    """
    service = LocalProductService()
    price = service._extract_price_from_keyword("10 juta")
    assert price is None
    mock_logger.error.assert_called_once_with("Error extracting price from keyword: Regex error")


# --- Test get_product_details ---

def test_get_product_details_found(service_with_mock_products):
    """
    Test getting product details for an existing product ID.
    """
    product = service_with_mock_products.get_product_details("prod1")
    assert product is not None
    assert product['id'] == "prod1"
    assert product['name'] == "Smartphone X"

def test_get_product_details_not_found(service_with_mock_products):
    """
    Test getting product details for a non-existent product ID.
    """
    product = service_with_mock_products.get_product_details("nonexistent_id")
    assert product is None

def test_get_product_details_empty_products_list():
    """
    Test getting product details when the product list is empty.
    """
    service = LocalProductService()
    service.products = []
    product = service.get_product_details("prod1")
    assert product is None

@patch.object(LocalProductService, 'products', new_callable=MagicMock, side_effect=Exception("Product access error"))
def test_get_product_details_handles_exception(mock_products_access, mock_logger):
    """
    Test that get_product_details handles generic exceptions during iteration.
    """
    service = LocalProductService()
    service.products = [] # Reset to avoid initial load issues
    mock_products_access.side_effect = Exception("Product access error") # Set after init

    details = service.get_product_details("prod1")
    assert details is None
    mock_logger.error.assert_called_once_with("Error getting product details: Product access error")


# --- Test get_categories ---

def test_get_categories(service_with_mock_products):
    """
    Test getting unique sorted product categories.
    """
    categories = service_with_mock_products.get_categories()
    expected_categories = sorted(["Smartphone", "Laptop", "Audio"])
    assert categories == expected_categories

def test_get_categories_empty_products_list():
    """
    Test getting categories when the product list is empty.
    """
    service = LocalProductService()
    service.products = []
    categories = service.get_categories()
    assert categories == []

def test_get_categories_with_missing_category_key():
    """
    Test getting categories when some products miss the 'category' key.
    """
    service = LocalProductService()
    service.products = [
        {"id": "1", "name": "Prod A", "category": "Category1"},
        {"id": "2", "name": "Prod B"}, # Missing category
        {"id": "3", "name": "Prod C", "category": "Category2"}
    ]
    categories = service.get_categories()
    expected_categories = sorted(["", "Category1", "Category2"]) # Empty string for missing category
    assert categories == expected_categories

# --- Test get_brands ---

def test_get_brands(service_with_mock_products):
    """
    Test getting unique sorted product brands.
    """
    brands = service_with_mock_products.get_brands()
    expected_brands = sorted(["Brand A", "Brand B", "Brand C"])
    assert brands == expected_brands

def test_get_brands_empty_products_list():
    """
    Test getting brands when the product list is empty.
    """
    service = LocalProductService()
    service.products = []
    brands = service.get_brands()
    assert brands == []

def test_get_brands_with_missing_brand_key():
    """
    Test getting brands when some products miss the 'brand' key.
    """
    service = LocalProductService()
    service.products = [
        {"id": "1", "name": "Prod A", "brand": "Brand1"},
        {"id": "2", "name": "Prod B"}, # Missing brand
        {"id": "3", "name": "Prod C", "brand": "Brand2"}
    ]
    brands = service.get_brands()
    expected_brands = sorted(["", "Brand1", "Brand2"]) # Empty string for missing brand
    assert brands == expected_brands

# --- Test get_products_by_category ---

def test_get_products_by_category_found(service_with_mock_products):
    """
    Test getting products by an existing category (case-insensitive).
    """
    products = service_with_mock_products.get_products_by_category("smartphone")
    assert len(products) == 2
    assert "Smartphone X" in [p['name'] for p in products]
    assert "Budget Phone" in [p['name'] for p in products]

def test_get_products_by_category_not_found(service_with_mock_products):
    """
    Test getting products by a non-existent category.
    """
    products = service_with_mock_products.get_products_by_category("NonExistentCategory")
    assert products == []

def test_get_products_by_category_empty_products_list():
    """
    Test getting products by category when the product list is empty.
    """
    service = LocalProductService()
    service.products = []
    products = service.get_products_by_category("any")
    assert products == []

@patch.object(LocalProductService, 'products', new_callable=MagicMock, side_effect=Exception("Product access error"))
def test_get_products_by_category_handles_exception(mock_products_access, mock_logger):
    """
    Test that get_products_by_category handles generic exceptions during iteration.
    """
    service = LocalProductService()
    service.products = [] # Reset to avoid initial load issues
    mock_products_access.side_effect = Exception("Product access error") # Set after init

    products = service.get_products_by_category("category")
    assert products == []
    mock_logger.error.assert_called_once_with("Error getting products by category: Product access error")


# --- Test get_products_by_brand ---

def test_get_products_by_brand_found(service_with_mock_products):
    """
    Test getting products by an existing brand (case-insensitive).
    """
    products = service_with_mock_products.get_products_by_brand("brand a")
    assert len(products) == 2
    assert "Smartphone X" in [p['name'] for p in products]
    assert "Budget Phone" in [p['name'] for p in products]

def test_get_products_by_brand_not_found(service_with_mock_products):
    """
    Test getting products by a non-existent brand.
    """
    products = service_with_mock_products.get_products_by_brand("NonExistentBrand")
    assert products == []

def test_get_products_by_brand_empty_products_list():
    """
    Test getting products by brand when the product list is empty.
    """
    service = LocalProductService()
    service.products = []
    products = service.get_products_by_brand("any")
    assert products == []

@patch.object(LocalProductService, 'products', new_callable=MagicMock, side_effect=Exception("Product access error"))
def test_get_products_by_brand_handles_exception(mock_products_access, mock_logger):
    """
    Test that get_products_by_brand handles generic exceptions during iteration.
    """
    service = LocalProductService()
    service.products = [] # Reset to avoid initial load issues
    mock_products_access.side_effect = Exception("Product access error") # Set after init

    products = service.get_products_by_brand("brand")
    assert products == []
    mock_logger.error.assert_called_once_with("Error getting products by brand: Product access error")


# --- Test get_top_rated_products ---

def test_get_top_rated_products(service_with_mock_products):
    """
    Test getting top rated products sorted correctly and limited.
    Ratings: Gaming Laptop (4.9), Laptop Y (4.8), Smartphone X (4.5), Headphone Z (4.0), Budget Phone (3.5)
    """
    top_products = service_with_mock_products.get_top_rated_products(limit=3)
    assert len(top_products) == 3
    assert top_products[0]['name'] == "Gaming Laptop"
    assert top_products[1]['name'] == "Laptop Y"
    assert top_products[2]['name'] == "Smartphone X"

def test_get_top_rated_products_limit_all(service_with_mock_products):
    """
    Test getting top rated products with limit greater than total products.
    """
    top_products = service_with_mock_products.get_top_rated_products(limit=10)
    assert len(top_products) == 5 # All products
    assert top_products[0]['name'] == "Gaming Laptop"

def test_get_top_rated_products_empty_products_list():
    """
    Test getting top rated products when the product list is empty.
    """
    service = LocalProductService()
    service.products = []
    top_products = service.get_top_rated_products()
    assert top_products == []

def test_get_top_rated_products_with_missing_rating_key():
    """
    Test getting top rated products when some products miss the 'rating' key.
    """
    service = LocalProductService()
    service.products = [
        {"id": "1", "name": "Prod A", "specifications": {"rating": 5.0}},
        {"id": "2", "name": "Prod B", "specifications": {}}, # Missing rating
        {"id": "3", "name": "Prod C", "specifications": {"rating": 3.0}}
    ]
    top_products = service.get_top_rated_products(limit=2)
    assert len(top_products) == 2
    assert top_products[0]['name'] == "Prod A" # Rating 5.0
    assert top_products[1]['name'] == "Prod C" # Rating 3.0 (Prod B has 0 rating)

@patch.object(LocalProductService, 'products', new_callable=MagicMock, side_effect=Exception("Product access error"))
def test_get_top_rated_products_handles_exception(mock_products_access, mock_logger):
    """
    Test that get_top_rated_products handles generic exceptions during sorting.
    """
    service = LocalProductService()
    service.products = [] # Reset to avoid initial load issues
    mock_products_access.side_effect = Exception("Product access error") # Set after init

    products = service.get_top_rated_products()
    assert products == []
    mock_logger.error.assert_called_once_with("Error getting top rated products: Product access error")


# --- Test get_best_selling_products ---

def test_get_best_selling_products(service_with_mock_products):
    """
    Test getting best selling products sorted correctly and limited.
    (mocked sold count is 500 for all, so sort order will be by original list order if all have same sold)
    """
    best_selling = service_with_mock_products.get_best_selling_products(limit=3)
    assert len(best_selling) == 3
    # Since sold count is mocked to 500 for all, it will return the first `limit` products
    # as per their initial order from `mock_transformed_products`.
    assert best_selling[0]['name'] == "Smartphone X"
    assert best_selling[1]['name'] == "Laptop Y"
    assert best_selling[2]['name'] == "Headphone Z"

@patch('random.randint', side_effect=[1000, 50, 2000, 10, 500]) # Vary sold counts
def test_get_best_selling_products_with_varied_sold(mock_randint, mock_products_data, mock_logger):
    """
    Test getting best selling products with actual varied sold counts.
    Expected order by sold: Headphone Z (2000), Smartphone X (1000), Gaming Laptop (500), Laptop Y (50), Budget Phone (10)
    """
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=json.dumps(mock_products_data))):
        service = LocalProductService()
        # Need to ensure products are reloaded with new random.randint sequence
        # The fixture `service_with_mock_products` already sets service.products directly.
        # So we need to re-initialize and let it call _load_local_products.
        service.products = service._load_local_products() # Re-load with new randint mock

    best_selling = service.get_best_selling_products(limit=3)
    assert len(best_selling) == 3
    assert best_selling[0]['name'] == "Headphone Z" # Sold: 2000
    assert best_selling[1]['name'] == "Smartphone X" # Sold: 1000
    assert best_selling[2]['name'] == "Gaming Laptop" # Sold: 500
    mock_logger.info.assert_any_call("Getting best selling products, limit: 3")
    mock_logger.info.assert_any_call("Returning 3 best selling products")


def test_get_best_selling_products_empty_products_list():
    """
    Test getting best selling products when the product list is empty.
    """
    service = LocalProductService()
    service.products = []
    best_selling = service.get_best_selling_products()
    assert best_selling == []

def test_get_best_selling_products_with_missing_sold_key():
    """
    Test getting best selling products when some products miss the 'sold' key.
    """
    service = LocalProductService()
    service.products = [
        {"id": "1", "name": "Prod A", "specifications": {"sold": 1000}},
        {"id": "2", "name": "Prod B", "specifications": {}}, # Missing sold (defaults to 0)
        {"id": "3", "name": "Prod C", "specifications": {"sold": 500}}
    ]
    best_selling = service.get_best_selling_products(limit=2)
    assert len(best_selling) == 2
    assert best_selling[0]['name'] == "Prod A" # Sold 1000
    assert best_selling[1]['name'] == "Prod C" # Sold 500 (Prod B has 0 sold)

@patch.object(LocalProductService, 'products', new_callable=MagicMock, side_effect=Exception("Product access error"))
def test_get_best_selling_products_handles_exception(mock_products_access, mock_logger):
    """
    Test that get_best_selling_products handles generic exceptions during sorting.
    """
    service = LocalProductService()
    service.products = [] # Reset to avoid initial load issues
    mock_products_access.side_effect = Exception("Product access error") # Set after init

    products = service.get_best_selling_products()
    assert products == []
    mock_logger.error.assert_called_once_with("Error getting best selling products: Product access error")


# --- Test get_products ---

def test_get_products(service_with_mock_products):
    """
    Test getting all products with default limit.
    """
    all_products = service_with_mock_products.get_products()
    assert len(all_products) == 5 # Default limit 10, but only 5 products available
    assert all_products == service_with_mock_products.products

def test_get_products_with_custom_limit(service_with_mock_products):
    """
    Test getting products with a custom limit.
    """
    limited_products = service_with_mock_products.get_products(limit=2)
    assert len(limited_products) == 2
    assert limited_products[0]['name'] == "Smartphone X"
    assert limited_products[1]['name'] == "Laptop Y"

def test_get_products_empty_products_list():
    """
    Test getting products when the product list is empty.
    """
    service = LocalProductService()
    service.products = []
    products = service.get_products()
    assert products == []

@patch.object(LocalProductService, 'products', new_callable=MagicMock, side_effect=Exception("Product access error"))
def test_get_products_handles_exception(mock_products_access, mock_logger):
    """
    Test that get_products handles generic exceptions.
    """
    service = LocalProductService()
    service.products = [] # Reset to avoid initial load issues
    mock_products_access.side_effect = Exception("Product access error") # Set after init

    products = service.get_products()
    assert products == []
    mock_logger.error.assert_called_once_with("Error getting products: Product access error")


# --- Test smart_search_products ---

def test_smart_search_best_no_category(service_with_mock_products):
    """
    Test smart_search for 'terbaik' without specific category (general top-rated).
    """
    products, message = service_with_mock_products.smart_search_products(keyword="produk terbaik")
    assert message == "Berikut produk terbaik berdasarkan rating:"
    assert len(products) == 5 # All products, as limit is 5 and all have ratings
    # Sorted by rating descending: Gaming Laptop (4.9), Laptop Y (4.8), Smartphone X (4.5), Headphone Z (4.0), Budget Phone (3.5)
    assert products[0]['name'] == "Gaming Laptop"
    assert products[1]['name'] == "Laptop Y"

def test_smart_search_best_with_category_found(service_with_mock_products):
    """
    Test smart_search for 'terbaik' with a specific, existing category.
    """
    products, message = service_with_mock_products.smart_search_products(keyword="laptop terbaik", category="Laptop")
    assert message == "Berikut Laptop terbaik berdasarkan rating:"
    assert len(products) == 2
    # Laptop ratings: Gaming Laptop (4.9), Laptop Y (4.8)
    assert products[0]['name'] == "Gaming Laptop"
    assert products[1]['name'] == "Laptop Y"

def test_smart_search_best_with_category_not_found(service_with_mock_products):
    """
    Test smart_search for 'terbaik' with a non-existent category, should fallback to general best.
    """
    products, message = service_with_mock_products.smart_search_products(keyword="tablet terbaik", category="Tablet")
    assert message == "Tidak ada produk kategori Tablet, berikut produk terbaik secara umum:"
    assert len(products) == 5
    assert products[0]['name'] == "Gaming Laptop" # Should be general top-rated

def test_smart_search_all_criteria_match(service_with_mock_products):
    """
    Test smart_search where keyword, category, and max_price all match.
    """
    products, message = service_with_mock_products.smart_search_products(
        keyword="smartphone", category="Smartphone", max_price=11000000, limit=1
    )
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."
    assert len(products) == 1
    assert products[0]['name'] == "Smartphone X" # price 10M

def test_smart_search_no_match_category_fallback(service_with_mock_products):
    """
    Test smart_search: no exact match, falls back to products in the same category (sorted by price).
    Scenario: keyword/price don't match, but category does.
    """
    # No "expensive" smartphone under 1M, but there are smartphones in general
    products, message = service_with_mock_products.smart_search_products(
        keyword="expensive", category="Smartphone", max_price=1000000, limit=5
    )
    assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."
    assert len(products) == 2
    # Smartphones: Budget Phone (1.5M), Smartphone X (10M)
    assert products[0]['name'] == "Budget Phone"
    assert products[1]['name'] == "Smartphone X"
    assert products[0]['price'] < products[1]['price'] # Should be sorted by price

def test_smart_search_no_match_price_fallback(service_with_mock_products):
    """
    Test smart_search: no exact match, falls back to products matching only max_price.
    Scenario: keyword/category don't match, but max_price does.
    """
    # No "unknown" category for a specific price
    products, message = service_with_mock_products.smart_search_products(
        keyword="unknown", category="NonExistent", max_price=3000000, limit=5
    )
    assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."
    assert len(products) == 2
    # Products under 3M: Headphone Z (2M), Budget Phone (1.5M)
    # The order will depend on internal iteration, then slicing.
    # The current code appends and then slices, so it's not strictly sorted
    # in any specific way within the `budget_results` before slicing.
    # We should ensure *any* 2 products under 3M are returned.
    returned_names = {p['name'] for p in products}
    assert "Headphone Z" in returned_names
    assert "Budget Phone" in returned_names

def test_smart_search_no_match_popular_fallback(service_with_mock_products):
    """
    Test smart_search: no match on any criteria, falls back to popular products.
    """
    products, message = service_with_mock_products.smart_search_products(
        keyword="xyz", category="NonExistent", max_price=10000, limit=5
    )
    assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
    assert len(products) == 5
    # All products have sold count 500 (mocked), so they'll be in original order
    assert products[0]['name'] == "Smartphone X"
    assert products[1]['name'] == "Laptop Y"

def test_smart_search_empty_product_list():
    """
    Test smart_search when the product list is empty.
    """
    service = LocalProductService()
    service.products = []
    products, message = service.smart_search_products(keyword="any")
    assert products == []
    assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." # Still returns this msg

def test_smart_search_no_parameters(service_with_mock_products):
    """
    Test smart_search with no parameters, should fallback to popular products.
    """
    products, message = service_with_mock_products.smart_search_products()
    assert message == "Berikut produk yang sesuai dengan kriteria Anda." # Matches all products if no criteria.
    assert len(products) == 5
    # If no criteria (keyword='', category=None, max_price=None), it matches all products initially.
    # Then it returns the first `limit` (default 5).
    # The initial `results` list building will include all products.
    assert products[0]['name'] == "Smartphone X"
    assert products[1]['name'] == "Laptop Y"

def test_smart_search_limit_parameter(service_with_mock_products):
    """
    Test smart_search respect the limit parameter in all scenarios.
    """
    products, message = service_with_mock_products.smart_search_products(keyword="laptop", limit=1)
    assert len(products) == 1
    assert products[0]['name'] == "Gaming Laptop" # Highest rated laptop, should come first due to general sorting.

    products, message = service_with_mock_products.smart_search_products(keyword="terbaik", limit=2)
    assert len(products) == 2
    assert products[0]['name'] == "Gaming Laptop"
    assert products[1]['name'] == "Laptop Y"

    products, message = service_with_mock_products.smart_search_products(max_price=3000000, limit=1)
    assert len(products) == 1
    # Either Headphone Z or Budget Phone, depending on initial order and price sorting.
    assert products[0]['name'] in ["Headphone Z", "Budget Phone"]