import pytest
import json
from unittest import mock
from pathlib import Path
import logging
import io
import re

# Import the class to be tested
from app.services.local_product_service import LocalProductService

# Define common test data
VALID_PRODUCT_DATA = {
    "products": [
        {
            "id": "prod1", "name": "Smartphone X", "category": "Electronics", "brand": "BrandA",
            "price": 10000000, "currency": "IDR", "description": "High-end smartphone with advanced features.",
            "specifications": {"rating": 4.5, "stock_count": 100}, "availability": "in_stock", "reviews_count": 50
        },
        {
            "id": "prod2", "name": "Laptop Y", "category": "Computers", "brand": "BrandB",
            "price": 15000000, "currency": "IDR", "description": "Powerful laptop for gaming and productivity.",
            "specifications": {"rating": 4.8, "stock_count": 50}, "availability": "in_stock", "reviews_count": 75
        },
        {
            "id": "prod3", "name": "Headphones Z", "category": "Audio", "brand": "BrandA",
            "price": 2000000, "currency": "IDR", "description": "Noise-cancelling headphones for immersive audio.",
            "specifications": {"rating": 4.0, "stock_count": 200}, "availability": "in_stock", "reviews_count": 30
        },
        {
            "id": "prod4", "name": "Budget Phone", "category": "Electronics", "brand": "BrandC",
            "price": 3000000, "currency": "IDR", "description": "Affordable smartphone for everyday use.",
            "specifications": {"rating": 3.9, "stock_count": 150}, "availability": "in_stock", "reviews_count": 20
        },
        {
            "id": "prod5", "name": "Gaming PC", "category": "Computers", "brand": "BrandD",
            "price": 25000000, "currency": "IDR", "description": "Ultimate gaming machine for high-performance.",
            "specifications": {"rating": 4.9, "stock_count": 20}, "availability": "in_stock", "reviews_count": 90
        },
        {
            "id": "prod6", "name": "Tablet A", "category": "Tablet", "brand": "BrandA",
            "price": 7000000, "currency": "IDR", "description": "Portable tablet for entertainment and work.",
            "specifications": {"rating": 4.2, "stock_count": 80}, "availability": "in_stock", "reviews_count": 40
        }
    ]
}

EMPTY_PRODUCT_DATA = {"products": []}

@pytest.fixture(autouse=True)
def mock_random_randint(mocker):
    """Fixture to mock random.randint for predictable 'sold' values."""
    mocker.patch('random.randint', return_value=500) # Consistent value for 'sold'

@pytest.fixture
def mock_path_exists(mocker):
    """
    Fixture to mock Path.exists() for products.json.
    Returns a function that can configure its return value.
    """
    mock_file_path = mocker.MagicMock(spec=Path)
    mock_file_path.name = "products.json"
    mock_file_path.__str__.return_value = "/mock/path/to/data/products.json" # For logging

    # Mock Path(__file__).parent.parent.parent / "data" / "products.json" chain
    mock_parent_path = mocker.MagicMock(spec=Path)
    mock_parent_path.__truediv__.return_value = mock_file_path # / "data"
    mock_parent_path.parent.parent.parent = mock_parent_path # Simulate chain back to itself for path resolution

    # Patch Path constructor so it returns our mock for Path(__file__)
    mocker.patch('pathlib.Path', autospec=True, side_effect=lambda *args, **kwargs: mock_parent_path if args and args[0] == __file__ else Path(*args, **kwargs))
    
    def _configure_exists(exists_value: bool):
        mock_file_path.exists.return_value = exists_value
    return _configure_exists

@pytest.fixture
def mock_open_file(mocker):
    """
    Fixture to mock builtins.open.
    Returns a function that can configure the content and potential side effects for open.
    """
    def _configure_open(content: str, side_effect=None):
        mock_file = mocker.mock_open(read_data=content)
        if side_effect:
            mock_file.side_effect = side_effect
            # If side_effect is an exception, ensure read() will also raise it.
            if isinstance(side_effect, Exception) or callable(side_effect):
                mock_file.return_value.__enter__.return_value.read.side_effect = side_effect
        mocker.patch('builtins.open', mock_file)
    return _configure_open

@pytest.fixture
def mock_logger(mocker):
    """Fixture to mock the logger methods."""
    mocker.patch('logging.Logger.info')
    mocker.patch('logging.Logger.warning')
    mocker.patch('logging.Logger.error')
    return logging.getLogger(__name__)

@pytest.fixture
def service_with_valid_data(mock_path_exists, mock_open_file):
    """Initializes LocalProductService with valid product data."""
    mock_path_exists(True)
    mock_open_file(json.dumps(VALID_PRODUCT_DATA))
    return LocalProductService()

@pytest.fixture
def service_with_empty_data(mock_path_exists, mock_open_file):
    """Initializes LocalProductService with empty product data."""
    mock_path_exists(True)
    mock_open_file(json.dumps(EMPTY_PRODUCT_DATA))
    return LocalProductService()

@pytest.fixture
def service_with_custom_product_data(mocker, mock_path_exists, mock_open_file):
    """
    Fixture to create a LocalProductService instance with custom product data.
    Takes a product list (transformed) as input.
    """
    def _create_service(products_list):
        # Create a mock for the full `_load_local_products` method
        # and make it return the pre-transformed list directly.
        # This avoids re-implementing transformation logic in tests, assuming
        # _load_local_products is tested separately for its internal logic.
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=products_list)
        
        # We still need to mock path and open for the __init__ to pass without actual file ops
        mock_path_exists(True)
        # Provide some dummy content, as _load_local_products is mocked away
        mock_open_file(json.dumps({"products": products_list}))
        
        return LocalProductService()
    return _create_service

# --- Test cases for __init__ and _load_local_products ---

def test_init_loads_valid_products(service_with_valid_data, mock_logger):
    """
    Test that __init__ successfully loads products from a valid JSON file.
    """
    service = service_with_valid_data
    assert len(service.products) == len(VALID_PRODUCT_DATA['products'])
    mock_logger.info.assert_any_call(f"Loaded {len(VALID_PRODUCT_DATA['products'])} local products from JSON file")
    # Check transformation for a product
    prod1 = next(p for p in service.products if p['id'] == 'prod1')
    assert prod1['name'] == 'Smartphone X'
    assert 'url' in prod1
    assert 'images' in prod1
    assert prod1['specifications']['sold'] == 500 # From mocked random.randint

def test_init_loads_empty_products(service_with_empty_data, mock_logger):
    """
    Test that __init__ correctly handles an empty products list in the JSON file.
    """
    service = service_with_empty_data
    assert len(service.products) == 0
    mock_logger.info.assert_any_call("Loaded 0 local products from JSON file")

def test_init_falls_back_if_file_not_found(mock_path_exists, mock_logger):
    """
    Test that __init__ falls back to default products if products.json is not found.
    """
    mock_path_exists(False)
    service = LocalProductService()
    fallback_products = service._get_fallback_products() # Get the actual fallback products for comparison
    assert service.products == fallback_products
    mock_logger.error.assert_any_call(f"Products JSON file not found at: /mock/path/to/data/products.json")
    mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error")

def test_load_local_products_handles_malformed_json(mock_path_exists, mock_open_file, mock_logger):
    """
    Test _load_local_products falls back when JSON is malformed for all encodings.
    """
    mock_path_exists(True)
    # Simulate repeated failure for all encodings
    def failing_read(file_path, mode='r', encoding=None):
        # Always raise JSONDecodeError when trying to load content
        raise json.JSONDecodeError("Expecting value", "", 0)

    mock_open_file(content="this is not json {", side_effect=failing_read)
    
    service = LocalProductService() # This will call _load_local_products
    assert service.products == service._get_fallback_products()
    assert mock_logger.warning.call_count >= len(service.encodings) # At least one warning per encoding attempt
    mock_logger.error.assert_any_call("All encoding attempts failed, using fallback products")
    mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error") # from _get_fallback_products


def test_load_local_products_handles_unicode_decode_error_all_encodings(mock_path_exists, mock_open_file, mock_logger):
    """
    Test _load_local_products falls back when UnicodeDecodeError occurs for all encodings.
    """
    mock_path_exists(True)
    def mock_open_side_effect(file_path, mode='r', encoding=None):
        raise UnicodeDecodeError("mockcodec", b'\xbe', 0, 1, "invalid start byte")

    mock_open_file(content="", side_effect=mock_open_side_effect)
    
    service = LocalProductService()
    assert service.products == service._get_fallback_products()
    assert mock_logger.warning.call_count >= len(service.encodings) # Expect warnings for each encoding failure
    mock_logger.error.assert_any_call("All encoding attempts failed, using fallback products")
    mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error")


def test_load_local_products_handles_file_io_error(mock_path_exists, mock_open_file, mock_logger):
    """
    Test _load_local_products falls back when an OSError (e.g., permission error) occurs.
    """
    mock_path_exists(True)
    mock_open_file(content="", side_effect=OSError("Permission denied"))
    
    service = LocalProductService()
    assert service.products == service._get_fallback_products()
    mock_logger.error.assert_called_once_with("Error loading products from JSON file: Permission denied")
    mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error")

def test_load_local_products_with_bom(mock_path_exists, mock_open_file, mock_logger):
    """
    Test _load_local_products correctly handles JSON with a BOM (e.g., UTF-8 BOM).
    """
    bom_content = '\ufeff' + json.dumps(VALID_PRODUCT_DATA)
    mock_path_exists(True)
    mock_open_file(bom_content) # The service will iterate encodings; utf-8-sig should handle it
    service = LocalProductService()
    assert len(service.products) == len(VALID_PRODUCT_DATA['products'])
    # The exact encoding logged depends on the order and success, but it should succeed.
    mock_logger.info.assert_any_call(mock.ANY) # Check that success message was logged
    info_calls = [call.args[0] for call in mock_logger.info.call_args_list if "Successfully loaded" in call.args[0]]
    assert any("utf-8-sig" in s for s in info_calls) or any("utf-8" in s for s in info_calls)

def test_load_local_products_different_encoding_success(mock_path_exists, mock_open_file, mock_logger):
    """
    Test _load_local_products successfully loads with a non-UTF8 encoding (e.g., UTF-16-LE).
    Simulates UTF-8 failing first, then UTF-16-LE succeeding.
    """
    mock_path_exists(True)
    
    # Simulate a file that is correctly UTF-16-LE but would fail UTF-8
    valid_utf16_le_content_str = json.dumps(VALID_PRODUCT_DATA)

    # Create a mock open that behaves differently based on encoding
    # We need to explicitly reset mock_logger for this test to control call count precisely
    mock_logger.warning.reset_mock()
    mock_logger.info.reset_mock()

    mock_attempts = 0
    def selective_open(file_path, mode='r', encoding=None):
        nonlocal mock_attempts
        mock_attempts += 1
        if encoding == 'utf-8':
            raise UnicodeDecodeError("utf-8", b'', 0, 1, "invalid byte for utf-8")
        elif encoding == 'utf-16-le':
            return io.StringIO(valid_utf16_le_content_str)
        else:
            # For other encodings, let's say they fail too
            raise UnicodeDecodeError("mock", b'', 0, 1, f"fail for {encoding}")

    mock_open_file(content="", side_effect=selective_open)
    
    service = LocalProductService()
    assert len(service.products) == len(VALID_PRODUCT_DATA['products'])
    mock_logger.warning.assert_any_call("Failed to load with utf-8 encoding: invalid byte for utf-8")
    mock_logger.info.assert_any_call(f"Successfully loaded {len(VALID_PRODUCT_DATA['products'])} products from JSON file using utf-16-le encoding")
    # Should try utf-8, then utf-16, then succeed and return.
    # The actual order of encodings is 'utf-16-le', 'utf-16', 'utf-8', ...
    # So it will hit 'utf-16-le' first in the list if it's the correct one.
    # Let's adjust the mock_open_side_effect to match the service's encoding order.
    
    # Reset and re-test with adjusted logic matching the service's 'encodings' list
    mock_logger.warning.reset_mock()
    mock_logger.info.reset_mock()
    
    # LocalProductService.encodings: ['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    def new_selective_open(file_path, mode='r', encoding=None):
        if encoding == 'utf-16-le':
            return io.StringIO(valid_utf16_le_content_str) # This one succeeds first
        elif encoding == 'utf-16':
             # Try to simulate it failing if it's not the exact LE or BE, or if no BOM
             raise UnicodeDecodeError("utf-16", b'', 0, 1, "invalid byte for utf-16")
        elif encoding == 'utf-8':
            raise UnicodeDecodeError("utf-8", b'', 0, 1, "invalid byte for utf-8")
        else:
            return io.StringIO(valid_utf16_le_content_str) # Allow others to succeed if tested last
    
    mock_open_file(content="", side_effect=new_selective_open) # Re-configure mock_open
    service = LocalProductService() # Re-initialize to hit the new mock_open
    assert len(service.products) == len(VALID_PRODUCT_DATA['products'])
    mock_logger.info.assert_called_once_with(f"Successfully loaded {len(VALID_PRODUCT_DATA['products'])} products from JSON file using utf-16-le encoding")
    assert mock_logger.warning.call_count == 0 # No warnings if it succeeds on the first try

# --- Test cases for _get_fallback_products ---

def test_get_fallback_products(service_with_valid_data, mock_logger):
    """
    Test that _get_fallback_products returns a list of dictionaries and logs a warning.
    """
    service = service_with_valid_data # Use any service instance
    # Reset logger calls for this specific method call test
    mock_logger.warning.reset_mock() 
    fallback_products = service._get_fallback_products()
    assert isinstance(fallback_products, list)
    assert len(fallback_products) > 0
    assert all(isinstance(p, dict) for p in fallback_products)
    mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error")

# --- Test cases for search_products ---

def test_search_products_by_name(service_with_valid_data, mock_logger):
    """Test searching products by name keyword."""
    mock_logger.info.reset_mock()
    results = service_with_valid_data.search_products("Smartphone X")
    assert len(results) == 1
    assert results[0]['id'] == 'prod1'
    mock_logger.info.assert_called_once_with("Searching products with keyword: Smartphone X")
    mock_logger.info.assert_any_call("Found 1 products")

def test_search_products_by_category(service_with_valid_data):
    """Test searching products by category keyword."""
    results = service_with_valid_data.search_products("Electronics")
    assert len(results) == 2
    assert any(p['id'] == 'prod1' for p in results)
    assert any(p['id'] == 'prod4' for p in results)

def test_search_products_by_brand_case_insensitive(service_with_valid_data):
    """Test searching products by brand keyword, case-insensitive."""
    results = service_with_valid_data.search_products("branda")
    assert len(results) == 2
    assert any(p['id'] == 'prod1' for p in results)
    assert any(p['id'] == 'prod3' for p in results)

def test_search_products_by_description(service_with_valid_data):
    """Test searching products by description keyword."""
    results = service_with_valid_data.search_products("gaming")
    assert len(results) == 2
    assert any(p['id'] == 'prod2' for p in results)
    assert any(p['id'] == 'prod5' for p in results)

def test_search_products_by_specifications(service_with_valid_data):
    """Test searching products by keyword in specifications (as string)."""
    # This relies on specifications being converted to string. Rating is a key in specs.
    results = service_with_valid_data.search_products("rating") 
    assert len(results) == len(VALID_PRODUCT_DATA['products']) # All products have rating in spec and thus will be found.
    results = service_with_valid_data.search_products("stock_count")
    assert len(results) == len(VALID_PRODUCT_DATA['products'])

def test_search_products_no_match(service_with_valid_data):
    """Test searching for a keyword that does not match any product."""
    results = service_with_valid_data.search_products("NonExistentProduct")
    assert len(results) == 0

def test_search_products_empty_keyword_returns_all_limited(service_with_valid_data):
    """Test searching with an empty keyword returns all products up to limit."""
    results = service_with_valid_data.search_products("", limit=3)
    assert len(results) == 3
    # Check if the products are from the initial list (order might vary based on internal sort)
    assert all(p in service_with_valid_data.products for p in results)

def test_search_products_limit(service_with_valid_data):
    """Test the limit parameter for search results."""
    results = service_with_valid_data.search_products("phone", limit=1)
    assert len(results) == 1
    assert results[0]['id'] == 'prod1' # "Smartphone X" has higher relevance than "Budget Phone"

def test_search_products_with_price_keyword_juta(service_with_valid_data):
    """Test searching products by keyword with 'juta' price, and sorting preference for lower price."""
    results = service_with_valid_data.search_products("smartphone 4 juta")
    # Products matching "smartphone": prod1 (10m), prod4 (3m).
    # Products matching price <= 4m: prod3 (2m), prod4 (3m).
    # The search logic appends if price matches OR keyword matches.
    # So prod1 (10m) matches "smartphone". prod3 (2m) matches "4 juta". prod4 (3m) matches both.
    # Relevance score should prioritize prod4 because it's cheaper.
    assert len(results) == 3
    # Expected order: prod4 (3m, matches both keyword and price, lower price), prod3 (2m, matches price), prod1 (10m, matches keyword)
    assert results[0]['id'] == 'prod4'
    assert results[1]['id'] == 'prod3'
    assert results[2]['id'] == 'prod1'

def test_search_products_with_budget_keyword(service_with_valid_data):
    """Test searching products with budget keywords like 'murah'."""
    results = service_with_valid_data.search_products("smartphone murah")
    # "murah" sets max_price to 5,000,000.
    # Products: prod1 (Smartphone X, 10m), prod4 (Budget Phone, 3m).
    # Both contain 'smartphone'. Prod4 is cheaper and fits 'murah'.
    assert len(results) == 2 
    assert results[0]['id'] == 'prod4' # Budget Phone should come first due to lower price and budget keyword
    assert results[1]['id'] == 'prod1'

def test_search_products_handles_exception(mocker, service_with_valid_data, mock_logger):
    """Test search_products error handling."""
    # Mocking self.products directly to raise an exception when accessed during iteration
    mocker.patch.object(service_with_valid_data, 'products', new_callable=mock.PropertyMock(side_effect=Exception("Test error")))
    results = service_with_valid_data.search_products("any")
    assert results == []
    mock_logger.error.assert_called_once_with("Error searching products: Test error")

# --- Test cases for _extract_price_from_keyword ---

@pytest.mark.parametrize("keyword, expected_price", [
    ("handphone 10 juta", 10000000),
    ("laptop 500 ribu", 500000),
    ("rp 12345 barang", 12345),
    ("produk 9999rp", 9999),
    ("speaker 20k", 20000),
    ("tablet 1m", 1000000),
    ("murah hp", 5000000),
    ("budget pc", 5000000),
    ("hemat headset", 3000000),
    ("terjangkau smartphone", 4000000),
    ("ekonomis", 2000000),
    ("no price here", None),
    ("", None),
    ("100000", None) # No unit specified, so not extracted
])
def test_extract_price_from_keyword_success(service_with_valid_data, keyword, expected_price):
    """Test successful price extraction from various keyword patterns."""
    price = service_with_valid_data._extract_price_from_keyword(keyword)
    assert price == expected_price

def test_extract_price_from_keyword_error_handling(mocker, service_with_valid_data, mock_logger):
    """Test _extract_price_from_keyword error handling."""
    mocker.patch('re.search', side_effect=Exception("Regex error"))
    price = service_with_valid_data._extract_price_from_keyword("any keyword")
    assert price is None
    mock_logger.error.assert_called_once_with("Error extracting price from keyword: Regex error")

# --- Test cases for get_product_details ---

def test_get_product_details_existing_id(service_with_valid_data):
    """Test retrieving details for an existing product ID."""
    details = service_with_valid_data.get_product_details("prod1")
    assert details is not None
    assert details['id'] == 'prod1'
    assert details['name'] == 'Smartphone X'

def test_get_product_details_non_existing_id(service_with_valid_data):
    """Test retrieving details for a non-existent product ID."""
    details = service_with_valid_data.get_product_details("nonexistent")
    assert details is None

def test_get_product_details_empty_id(service_with_valid_data):
    """Test retrieving details with an empty product ID."""
    details = service_with_valid_data.get_product_details("")
    assert details is None

def test_get_product_details_handles_exception(mocker, service_with_valid_data, mock_logger):
    """Test get_product_details error handling."""
    mocker.patch.object(service_with_valid_data, 'products', new_callable=mock.PropertyMock(side_effect=Exception("Test error")))
    details = service_with_valid_data.get_product_details("prod1")
    assert details is None
    mock_logger.error.assert_called_once_with("Error getting product details: Test error")

# --- Test cases for get_categories ---

def test_get_categories_from_products(service_with_valid_data):
    """Test retrieving distinct product categories."""
    categories = service_with_valid_data.get_categories()
    expected_categories = sorted(['Electronics', 'Computers', 'Audio', 'Tablet'])
    assert categories == expected_categories

def test_get_categories_empty_products(service_with_empty_data):
    """Test retrieving categories when no products are loaded."""
    categories = service_with_empty_data.get_categories()
    assert categories == []

def test_get_categories_product_without_category(service_with_custom_product_data):
    """Test handling products missing 'category' key."""
    # Prepare data where one product explicitly lacks 'category'
    modified_products_for_test = [
        {"id": "p1", "name": "Nocat Prod", "brand": "B", "price": 1000},
        {"id": "p2", "name": "Cat Prod", "category": "TestCat", "brand": "C", "price": 2000}
    ]
    # Simulate the transformation by adding default values to missing fields as if it came from _load_local_products
    transformed_products = []
    for p in modified_products_for_test:
        transformed_p = {
            "id": p.get('id', ''),
            "name": p.get('name', ''),
            "category": p.get('category', ''), # This will be '' for p1
            "brand": p.get('brand', ''),
            "price": p.get('price', 0),
            "currency": p.get('currency', 'IDR'),
            "description": p.get('description', ''),
            "specifications": {
                "rating": p.get('rating', 0),
                "sold": 500, # Mocked
                "stock": p.get('stock_count', 0),
                "condition": "Baru",
                "shop_location": "Indonesia",
                "shop_name": f"{p.get('brand', 'Unknown')} Store",
                **p.get('specifications', {})
            },
            "availability": p.get('availability', 'in_stock'),
            "reviews_count": p.get('reviews_count', 0),
            "images": [f"https://example.com/{p.get('id', 'product')}.jpg"],
            "url": f"https://shopee.co.id/{p.get('id', 'product')}"
        }
        transformed_products.append(transformed_p)

    service = service_with_custom_product_data(transformed_products)
    
    categories = service.get_categories()
    expected_categories = sorted(['', 'TestCat']) # Empty string for missing category
    assert categories == expected_categories

# --- Test cases for get_brands ---

def test_get_brands_from_products(service_with_valid_data):
    """Test retrieving distinct product brands."""
    brands = service_with_valid_data.get_brands()
    expected_brands = sorted(['BrandA', 'BrandB', 'BrandC', 'BrandD'])
    assert brands == expected_brands

def test_get_brands_empty_products(service_with_empty_data):
    """Test retrieving brands when no products are loaded."""
    brands = service_with_empty_data.get_brands()
    assert brands == []

def test_get_brands_product_without_brand(service_with_custom_product_data):
    """Test handling products missing 'brand' key."""
    # Prepare data where one product explicitly lacks 'brand'
    modified_products_for_test = [
        {"id": "p1", "name": "Nobrand Prod", "category": "CatA", "price": 1000},
        {"id": "p2", "name": "Brand Prod", "category": "CatB", "brand": "TestBrand", "price": 2000}
    ]
    # Simulate transformation
    transformed_products = []
    for p in modified_products_for_test:
        transformed_p = {
            "id": p.get('id', ''), "name": p.get('name', ''), "category": p.get('category', ''),
            "brand": p.get('brand', ''), # This will be '' for p1
            "price": p.get('price', 0), "currency": p.get('currency', 'IDR'), "description": p.get('description', ''),
            "specifications": {"rating": p.get('rating', 0), "sold": 500, "stock": p.get('stock_count', 0), "condition": "Baru", "shop_location": "Indonesia", "shop_name": f"{p.get('brand', 'Unknown')} Store", **p.get('specifications', {})},
            "availability": p.get('availability', 'in_stock'), "reviews_count": p.get('reviews_count', 0),
            "images": [f"https://example.com/{p.get('id', 'product')}.jpg"], "url": f"https://shopee.co.id/{p.get('id', 'product')}"
        }
        transformed_products.append(transformed_p)
    service = service_with_custom_product_data(transformed_products)
    
    brands = service.get_brands()
    expected_brands = sorted(['', 'TestBrand'])
    assert brands == expected_brands

# --- Test cases for get_products_by_category ---

def test_get_products_by_category_existing(service_with_valid_data):
    """Test filtering products by an existing category."""
    results = service_with_valid_data.get_products_by_category("Electronics")
    assert len(results) == 2
    assert all(p['category'] == 'Electronics' for p in results)

def test_get_products_by_category_case_insensitive(service_with_valid_data):
    """Test filtering products by category with case-insensitivity."""
    results = service_with_valid_data.get_products_by_category("electronics")
    assert len(results) == 2
    assert all(p['category'].lower() == 'electronics' for p in results)

def test_get_products_by_category_non_existing(service_with_valid_data):
    """Test filtering products by a non-existent category."""
    results = service_with_valid_data.get_products_by_category("Gadgets")
    assert len(results) == 0

def test_get_products_by_category_empty_category_name(service_with_valid_data):
    """Test filtering products by an empty category name."""
    results = service_with_valid_data.get_products_by_category("")
    assert len(results) == 0 # No product has an empty category in VALID_PRODUCT_DATA

def test_get_products_by_category_handles_exception(mocker, service_with_valid_data, mock_logger):
    """Test get_products_by_category error handling."""
    mocker.patch.object(service_with_valid_data, 'products', new_callable=mock.PropertyMock(side_effect=Exception("Test error")))
    results = service_with_valid_data.get_products_by_category("Electronics")
    assert results == []
    mock_logger.error.assert_called_once_with("Error getting products by category: Test error")

# --- Test cases for get_products_by_brand ---

def test_get_products_by_brand_existing(service_with_valid_data):
    """Test filtering products by an existing brand."""
    results = service_with_valid_data.get_products_by_brand("BrandA")
    assert len(results) == 2
    assert all(p['brand'] == 'BrandA' for p in results)

def test_get_products_by_brand_case_insensitive(service_with_valid_data):
    """Test filtering products by brand with case-insensitivity."""
    results = service_with_valid_data.get_products_by_brand("branda")
    assert len(results) == 2
    assert all(p['brand'].lower() == 'branda' for p in results)

def test_get_products_by_brand_non_existing(service_with_valid_data):
    """Test filtering products by a non-existent brand."""
    results = service_with_valid_data.get_products_by_brand("BrandZ")
    assert len(results) == 0

def test_get_products_by_brand_empty_brand_name(service_with_valid_data):
    """Test filtering products by an empty brand name."""
    results = service_with_valid_data.get_products_by_brand("")
    assert len(results) == 0 # No product has an empty brand in VALID_PRODUCT_DATA

def test_get_products_by_brand_handles_exception(mocker, service_with_valid_data, mock_logger):
    """Test get_products_by_brand error handling."""
    mocker.patch.object(service_with_valid_data, 'products', new_callable=mock.PropertyMock(side_effect=Exception("Test error")))
    results = service_with_valid_data.get_products_by_brand("BrandA")
    assert results == []
    mock_logger.error.assert_called_once_with("Error getting products by brand: Test error")

# --- Test cases for get_top_rated_products ---

def test_get_top_rated_products_default_limit(service_with_valid_data):
    """Test retrieving top-rated products with default limit."""
    results = service_with_valid_data.get_top_rated_products()
    assert len(results) == 5
    # Expected order by rating: prod5(4.9), prod2(4.8), prod1(4.5), prod6(4.2), prod3(4.0)
    assert results[0]['id'] == 'prod5'
    assert results[1]['id'] == 'prod2'
    assert results[2]['id'] == 'prod1'
    assert results[3]['id'] == 'prod6'
    assert results[4]['id'] == 'prod3'

def test_get_top_rated_products_custom_limit(service_with_valid_data):
    """Test retrieving top-rated products with a custom limit."""
    results = service_with_valid_data.get_top_rated_products(limit=2)
    assert len(results) == 2
    assert results[0]['id'] == 'prod5'
    assert results[1]['id'] == 'prod2'

def test_get_top_rated_products_limit_exceeds_total(service_with_valid_data):
    """Test retrieving top-rated products with a limit greater than total products."""
    results = service_with_valid_data.get_top_rated_products(limit=10)
    assert len(results) == len(VALID_PRODUCT_DATA['products']) # Should return all products

def test_get_top_rated_products_no_rating(service_with_custom_product_data):
    """Test handling products without 'rating' in specifications."""
    # Modify products so one has no rating
    modified_products_for_test = [
        {**p, "specifications": {k:v for k,v in p.get("specifications",{}).items() if k != 'rating'}} if p['id'] == 'prod1' else p
        for p in VALID_PRODUCT_DATA['products']
    ]
    service = service_with_custom_product_data(modified_products_for_test)
    
    results = service.get_top_rated_products(limit=5)
    # Products without rating should default to 0, so they appear at the end when sorted descending.
    # Ratings: prod5(4.9), prod2(4.8), prod6(4.2), prod3(4.0), prod4(3.9), prod1(0)
    assert results[0]['id'] == 'prod5'
    assert results[1]['id'] == 'prod2'
    assert results[2]['id'] == 'prod6'
    assert results[3]['id'] == 'prod3'
    assert results[4]['id'] == 'prod4'
    assert results[-1]['id'] == 'prod1' # 'prod1' should be last because its rating defaulted to 0

def test_get_top_rated_products_empty_products(service_with_empty_data):
    """Test retrieving top-rated products when no products are loaded."""
    results = service_with_empty_data.get_top_rated_products()
    assert results == []

def test_get_top_rated_products_handles_exception(mocker, service_with_valid_data, mock_logger):
    """Test get_top_rated_products error handling."""
    mocker.patch.object(service_with_valid_data, 'products', new_callable=mock.PropertyMock(side_effect=Exception("Test error")))
    results = service_with_valid_data.get_top_rated_products()
    assert results == []
    mock_logger.error.assert_called_once_with("Error getting top rated products: Test error")

# --- Test cases for get_best_selling_products ---

def test_get_best_selling_products_sorting_and_limit(service_with_custom_product_data, mock_logger):
    """Test retrieving best-selling products with default limit and custom sold counts."""
    # Create a product list with distinct 'sold' counts for predictable sorting
    custom_products_with_sold = [
        {**p, "specifications": {**p.get("specifications", {}), "sold": 100 * (i + 1)}}
        for i, p in enumerate(VALID_PRODUCT_DATA['products'])
    ]
    # To get consistent order for default data, make sure order matches original with sorted sold counts
    # (prod1: 100, prod2: 200, prod3: 300, prod4: 400, prod5: 500, prod6: 600)
    # Sorted descending: prod6, prod5, prod4, prod3, prod2, prod1
    
    service = service_with_custom_product_data(custom_products_with_sold)
    
    results = service.get_best_selling_products()
    assert len(results) == 5
    # Expected sorted by sold DESC: prod6, prod5, prod4, prod3, prod2
    assert results[0]['id'] == 'prod6'
    assert results[1]['id'] == 'prod5'
    assert results[2]['id'] == 'prod4'
    assert results[3]['id'] == 'prod3'
    assert results[4]['id'] == 'prod2'
    
    mock_logger.info.assert_any_call("Getting best selling products, limit: 5")
    mock_logger.info.assert_any_call("Returning 5 best selling products")

def test_get_best_selling_products_custom_limit(service_with_custom_product_data):
    """Test retrieving best-selling products with a custom limit."""
    custom_products_with_sold = [
        {**p, "specifications": {**p.get("specifications", {}), "sold": 100 * (i + 1)}}
        for i, p in enumerate(VALID_PRODUCT_DATA['products'])
    ]
    service = service_with_custom_product_data(custom_products_with_sold)

    results = service.get_best_selling_products(limit=2)
    assert len(results) == 2
    assert results[0]['id'] == 'prod6'
    assert results[1]['id'] == 'prod5'

def test_get_best_selling_products_no_sold_count(service_with_custom_product_data):
    """Test handling products without 'sold' in specifications."""
    modified_products_for_test = []
    for p in VALID_PRODUCT_DATA['products']:
        temp_p = p.copy()
        temp_spec = temp_p.get("specifications", {}).copy()
        if p['id'] == 'prod1':
            if 'sold' in temp_spec:
                del temp_spec['sold'] # Remove sold count from first product
        else:
            temp_spec['sold'] = 1000 if p['id'] == 'prod5' else 500 # Set explicit sold counts for others
        temp_p['specifications'] = temp_spec
        modified_products_for_test.append(temp_p)

    service = service_with_custom_product_data(modified_products_for_test)
    results = service.get_best_selling_products(limit=3)
    # Products without 'sold' should default to 0 and appear at the end.
    # Order: prod5 (1000), then any two others with 500. prod1 (0) would be last.
    assert results[0]['id'] == 'prod5'
    assert 'sold' not in next(p['specifications'] for p in results if p['id'] == 'prod1') # prod1 was modified
    assert results[-1]['id'] == 'prod1' # prod1 should be last if it's within the limit

def test_get_best_selling_products_empty_products(service_with_empty_data):
    """Test retrieving best-selling products when no products are loaded."""
    results = service_with_empty_data.get_best_selling_products()
    assert results == []

def test_get_best_selling_products_handles_exception(mocker, service_with_valid_data, mock_logger):
    """Test get_best_selling_products error handling."""
    mocker.patch.object(service_with_valid_data, 'products', new_callable=mock.PropertyMock(side_effect=Exception("Test error")))
    results = service_with_valid_data.get_best_selling_products()
    assert results == []
    mock_logger.error.assert_called_once_with("Error getting best selling products: Test error")

# --- Test cases for get_products ---

def test_get_products_default_limit(service_with_valid_data):
    """Test retrieving all products with default limit."""
    results = service_with_valid_data.get_products()
    assert len(results) == len(VALID_PRODUCT_DATA['products']) # Default limit is 10, but we only have 6
    assert results == service_with_valid_data.products

def test_get_products_custom_limit(service_with_valid_data):
    """Test retrieving all products with a custom limit."""
    results = service_with_valid_data.get_products(limit=3)
    assert len(results) == 3
    assert results == service_with_valid_data.products[:3]

def test_get_products_limit_exceeds_total(service_with_valid_data):
    """Test retrieving all products with a limit greater than total products."""
    results = service_with_valid_data.get_products(limit=10)
    assert len(results) == len(VALID_PRODUCT_DATA['products'])

def test_get_products_empty_products(service_with_empty_data):
    """Test retrieving all products when no products are loaded."""
    results = service_with_empty_data.get_products()
    assert results == []

def test_get_products_handles_exception(mocker, service_with_valid_data, mock_logger):
    """Test get_products error handling."""
    mocker.patch.object(service_with_valid_data, 'products', new_callable=mock.PropertyMock(side_effect=Exception("Test error")))
    results = service_with_valid_data.get_products()
    assert results == []
    mock_logger.error.assert_called_once_with("Error getting products: Test error")

# --- Test cases for smart_search_products ---

def test_smart_search_best_request_no_category(service_with_valid_data):
    """Test smart_search for 'terbaik' or 'best' without a specific category."""
    # Should return top 5 rated products overall
    results, message = service_with_valid_data.smart_search_products(keyword="produk terbaik")
    assert message == "Berikut produk terbaik berdasarkan rating:"
    assert len(results) == 5
    # Expect sorted by rating DESC: prod5(4.9), prod2(4.8), prod1(4.5), prod6(4.2), prod3(4.0)
    assert results[0]['id'] == 'prod5'
    assert results[1]['id'] == 'prod2'

def test_smart_search_best_request_with_category_found(service_with_valid_data):
    """Test smart_search for 'terbaik' with an existing category."""
    results, message = service_with_valid_data.smart_search_products(keyword="laptop terbaik", category="Computers")
    assert message == "Berikut Computers terbaik berdasarkan rating:"
    assert len(results) == 2 # prod2, prod5
    # Expect sorted by rating DESC within category: prod5(4.9), prod2(4.8)
    assert results[0]['id'] == 'prod5'
    assert results[1]['id'] == 'prod2'

def test_smart_search_best_request_with_category_not_found(service_with_valid_data):
    """Test smart_search for 'terbaik' with a non-existent category, fallback to general best."""
    results, message = service_with_valid_data.smart_search_products(keyword="kamera terbaik", category="Cameras")
    assert message == "Tidak ada produk kategori Cameras, berikut produk terbaik secara umum:"
    assert len(results) == 5
    assert results[0]['id'] == 'prod5'

def test_smart_search_all_criteria_met(service_with_valid_data):
    """Test smart_search where keyword, category, and max_price criteria are all met."""
    results, message = service_with_valid_data.smart_search_products(
        keyword="smartphone", category="Electronics", max_price=5000000, limit=1
    )
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."
    assert len(results) == 1
    assert results[0]['id'] == 'prod4' # Budget Phone (3m) should match

def test_smart_search_no_match_fallback_to_category_only(service_with_valid_data):
    """
    Test smart_search fallback:
    1. Keyword does not match
    2. Max price is too low for matching products with keyword
    3. Category *does* match, so it falls back to products in that category, sorted by price.
    """
    results, message = service_with_valid_data.smart_search_products(
        keyword="nonexistent keyword", category="Electronics", max_price=1000000
    )
    assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."
    assert len(results) == 2 # Products in "Electronics": prod1 (10m), prod4 (3m)
    assert results[0]['id'] == 'prod4' # Budget Phone, cheaper
    assert results[1]['id'] == 'prod1' # Smartphone X, more expensive

def test_smart_search_no_match_fallback_to_budget_only(service_with_valid_data):
    """
    Test smart_search fallback:
    1. Keyword does not match
    2. Category does not match
    3. Max price *does* match, so it falls back to products within that budget.
    """
    results, message = service_with_valid_data.smart_search_products(
        keyword="nonexistent keyword", category="NonExistentCategory", max_price=3000000
    )
    assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."
    assert len(results) == 2 # Products <= 3m: prod3 (2m), prod4 (3m)
    # The default sort is not specified for this fallback, but it should be consistent.
    # In this case, they will be returned in the order they appear in the original list after filtering.
    # prod3 (2m), then prod4 (3m).
    assert results[0]['id'] == 'prod3'
    assert results[1]['id'] == 'prod4'

def test_smart_search_no_match_fallback_to_popular(service_with_valid_data):
    """
    Test smart_search fallback:
    1. No keyword match
    2. No category match
    3. No max_price match
    Should fallback to popular products (sorted by 'sold').
    """
    results, message = service_with_valid_data.smart_search_products(
        keyword="completely unique", category="NeverExists", max_price=1000
    )
    assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
    assert len(results) == 5 # Default limit
    # All products have sold = 500 (from mock_random_randint), so order is consistent but arbitrary without explicit sold values.
    # Just check that it returns something and it's from the original set.
    assert all(p['id'] in [x['id'] for x in service_with_valid_data.products] for p in results)

def test_smart_search_empty_inputs_returns_popular(service_with_valid_data):
    """Test smart_search with completely empty inputs, should fallback to popular."""
    results, message = service_with_valid_data.smart_search_products(keyword='', category=None, max_price=None)
    assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
    assert len(results) == 5
    # All products have sold = 500, so any 5 from the products list.

def test_smart_search_limit_parameter(service_with_valid_data):
    """Test the limit parameter in smart_search."""
    results, message = service_with_valid_data.smart_search_products(keyword="terbaik", limit=2)
    assert len(results) == 2
    assert results[0]['id'] == 'prod5'
    assert results[1]['id'] == 'prod2'

def test_smart_search_empty_products_in_service(service_with_empty_data):
    """Test smart_search when the service has no products loaded."""
    results, message = service_with_empty_data.smart_search_products(keyword="any")
    assert results == []
    assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
    # The fallback to popular products correctly returns an empty list if self.products is empty.