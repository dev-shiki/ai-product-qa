import pytest
import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging
import random
import re

# Import the class under test
from app.services.local_product_service import LocalProductService

# Configure logging for tests
logger = logging.getLogger(__name__)

# --- Fixtures ---

@pytest.fixture
def temp_root_dir():
    """Creates a temporary root directory structure: temp_dir/data/products.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Simulate the project root structure
        project_root = Path(tmpdir)
        data_dir = project_root / "data"
        data_dir.mkdir()
        yield project_root

@pytest.fixture(autouse=True)
def mock_path_chain(temp_root_dir):
    """
    Mocks Path(__file__).parent.parent.parent to point to the temporary root directory.
    This ensures `_load_local_products` looks for `products.json` in our test setup.
    """
    # Create a mock for Path(__file__) that behaves like a real Path for parent access,
    # but points to our temporary directory at the desired depth.
    mock_file_path_obj = MagicMock(spec=Path)
    mock_file_path_obj.parent.parent.parent = temp_root_dir

    # Patch the `Path` class's __init__ method to inject our mock for the Path(__file__) call.
    # This specific heuristic for args[0] allows other Path() calls (e.g., for `/ "data"`)
    # to still create real Path objects, whose .exists() and .is_file() methods will work correctly
    # on the temporary filesystem.
    original_path_init = Path.__init__

    def custom_init(self, *args, **kwargs):
        # Call original init to maintain basic Path object functionality
        original_path_init(self, *args, **kwargs)
        # Check if this is likely the `Path(__file__)` call by looking for '__file__' string.
        # This is a heuristic, but sufficient for this specific SUT code.
        if args and isinstance(args[0], str) and '__file__' in args[0]:
            self.parent = MagicMock()
            self.parent.parent = MagicMock()
            self.parent.parent.parent = temp_root_dir

    with patch.object(Path, '__init__', new=custom_init, autospec=True):
        yield

@pytest.fixture(autouse=True)
def mock_random_randint():
    """Mocks random.randint to return a predictable value (1000) for consistent 'sold' counts."""
    with patch('app.services.local_product_service.random.randint', return_value=1000) as mock_randint:
        yield mock_randint

@pytest.fixture
def sample_products_json_data():
    """Returns sample product data as a dictionary to write to JSON files."""
    return {
        "products": [
            {
                "id": "1",
                "name": "Test Phone",
                "category": "Smartphone",
                "brand": "TestBrand",
                "price": 10000000,
                "currency": "IDR",
                "description": "A test smartphone.",
                "rating": 4.5,
                "stock_count": 50,
                "specifications": {"storage": "128GB"},
                "availability": "in_stock",
                "reviews_count": 10
            },
            {
                "id": "2",
                "name": "Test Laptop",
                "category": "Laptop",
                "brand": "AnotherBrand",
                "price": 15000000,
                "currency": "IDR",
                "description": "A test laptop.",
                "rating": 4.0,
                "stock_count": 30,
                "specifications": {"ram": "8GB"},
                "availability": "out_of_stock",
                "reviews_count": 5
            },
            {
                "id": "3",
                "name": "Test Headphone",
                "category": "Audio",
                "brand": "AudioBrand",
                "price": 2000000,
                "rating": 3.8,
                "stock_count": 20,
                "specifications": {}, # Empty specifications
                "availability": "pre_order",
                "reviews_count": 2
            },
            {
                "id": "4",
                "name": "Product Without Rating",
                "category": "Misc",
                "brand": "Other",
                "price": 500000,
                "stock_count": 10,
                # Missing rating, specifications, reviews_count
            }
        ]
    }

def _write_json_file(file_path: Path, data: dict, encoding: str = 'utf-8', write_mode: str = 'w'):
    """Helper to write JSON data to a file."""
    with open(file_path, write_mode, encoding=encoding) as f:
        if write_mode == 'w':
            json.dump(data, f)
        elif write_mode == 'wb': # For specific encodings that need bytes
            f.write(json.dumps(data).encode(encoding))


@pytest.fixture
def setup_valid_json_file(temp_root_dir, sample_products_json_data):
    """Writes valid JSON data to products.json in the temp directory."""
    json_file_path = temp_root_dir / "data" / "products.json"
    _write_json_file(json_file_path, sample_products_json_data, 'utf-8')
    return json_file_path

@pytest.fixture
def setup_empty_json_file(temp_root_dir):
    """Creates an empty products.json file."""
    json_file_path = temp_root_dir / "data" / "products.json"
    json_file_path.touch()
    return json_file_path

@pytest.fixture
def setup_invalid_json_file(temp_root_dir):
    """Writes invalid JSON data to products.json."""
    json_file_path = temp_root_dir / "data" / "products.json"
    with open(json_file_path, 'w', encoding='utf-8') as f:
        f.write("this is not json {")
    return json_file_path

@pytest.fixture
def setup_json_no_products_key(temp_root_dir):
    """Writes JSON without a 'products' key."""
    json_file_path = temp_root_dir / "data" / "products.json"
    _write_json_file(json_file_path, {"items": []}, 'utf-8')
    return json_file_path

@pytest.fixture
def setup_json_with_bom(temp_root_dir, sample_products_json_data):
    """Writes JSON with a UTF-8 BOM."""
    json_file_path = temp_root_dir / "data" / "products.json"
    _write_json_file(json_file_path, sample_products_json_data, 'utf-8-sig')
    return json_file_path

@pytest.fixture
def setup_json_utf16_le(temp_root_dir, sample_products_json_data):
    """Writes JSON with UTF-16-LE encoding."""
    json_file_path = temp_root_dir / "data" / "products.json"
    _write_json_file(json_file_path, sample_products_json_data, 'utf-16-le')
    return json_file_path

@pytest.fixture
def setup_json_with_malformed_product(temp_root_dir):
    """Writes JSON with a product missing many fields."""
    json_file_path = temp_root_dir / "data" / "products.json"
    data = {
        "products": [
            {"id": "incomplete_product"},
            {"id": "complete_product", "name": "Complete", "category": "Gadget", "price": 1000, "reviews_count": 5, "rating": 4.0}
        ]
    }
    _write_json_file(json_file_path, data, 'utf-8')
    return json_file_path

@pytest.fixture
def product_service_with_sample_data(setup_valid_json_file, mock_path_chain):
    """Fixture for LocalProductService initialized with sample data."""
    # The setup_valid_json_file fixture creates the file, and mock_path_chain
    # ensures LocalProductService finds it.
    return LocalProductService()

# --- Test LocalProductService Initialization and _load_local_products ---

def test_init_success_loads_products_and_logs(product_service_with_sample_data, caplog):
    """Test LocalProductService initialization with a valid products.json, verifying content and logs."""
    caplog.set_level(logging.INFO)
    service = LocalProductService() # Re-initialize to capture init logs cleanly
    assert len(service.products) == 4
    assert "Loaded 4 local products from JSON file" in caplog.text
    assert "Successfully loaded 4 products from JSON file using utf-8 encoding" in caplog.text
    
    # Verify product transformation logic on a sample product
    product = service.products[0]
    assert product['id'] == '1'
    assert product['name'] == 'Test Phone'
    assert product['price'] == 10000000
    assert product['currency'] == 'IDR'
    assert product['specifications']['rating'] == 4.5
    assert product['specifications']['sold'] == 1000 # Mocked random.randint
    assert product['specifications']['stock'] == 50
    assert product['specifications']['condition'] == 'Baru'
    assert product['specifications']['shop_location'] == 'Indonesia'
    assert product['specifications']['shop_name'] == 'TestBrand Store'
    assert product['specifications']['storage'] == '128GB' # Merged from specifications
    assert product['images'] == ["https://example.com/1.jpg"]
    assert product['url'] == "https://shopee.co.id/1"
    assert product['reviews_count'] == 10

def test_init_file_not_found_falls_back_and_logs(temp_root_dir, mock_path_chain, caplog):
    """Test LocalProductService initialization when products.json is not found, ensuring fallback and logs."""
    caplog.set_level(logging.ERROR)
    service = LocalProductService()
    assert len(service.products) == 8 # Fallback products count
    assert f"Products JSON file not found at: {temp_root_dir / 'data' / 'products.json'}" in caplog.text
    assert "All encoding attempts failed, using fallback products" in caplog.text # This is logged by _load_local_products
    assert "Using fallback products due to JSON file loading error" in caplog.text # This is logged by _get_fallback_products
    assert "Loaded 8 local products from JSON file" in caplog.text

def test_init_invalid_json_falls_back_and_logs_warnings(setup_invalid_json_file, mock_path_chain, caplog):
    """Test LocalProductService initialization with invalid JSON content, ensuring fallback and warnings."""
    caplog.set_level(logging.WARNING)
    service = LocalProductService()
    assert len(service.products) == 8 # Fallback products count
    assert "Failed to load with utf-16-le encoding: " in caplog.text
    assert "Failed to load with utf-16 encoding: " in caplog.text
    assert "Failed to load with utf-8 encoding: Expecting value: line 1 column 1 (char 0)" in caplog.text
    assert "All encoding attempts failed, using fallback products" in caplog.text
    assert "Using fallback products due to JSON file loading error" in caplog.text
    assert "Loaded 8 local products from JSON file" in caplog.text

def test_load_local_products_with_bom(setup_json_with_bom, mock_path_chain, caplog):
    """Test _load_local_products with a JSON file containing a UTF-8 BOM."""
    caplog.set_level(logging.INFO)
    service = LocalProductService()
    assert len(service.products) == 4
    assert "Successfully loaded 4 products from JSON file using utf-8-sig encoding" in caplog.text
    assert "Loaded 4 local products from JSON file" in caplog.text
    # Verify BOM is removed from content (by checking transformed product strings)
    assert '\ufeff' not in json.dumps(service.products[0])

def test_load_local_products_utf16_le_encoding(setup_json_utf16_le, mock_path_chain, caplog):
    """Test _load_local_products with a UTF-16-LE encoded JSON file."""
    caplog.set_level(logging.INFO)
    service = LocalProductService()
    assert len(service.products) == 4
    assert "Successfully loaded 4 products from JSON file using utf-16-le encoding" in caplog.text
    assert "Loaded 4 local products from JSON file" in caplog.text

def test_load_local_products_empty_file_falls_back(setup_empty_json_file, mock_path_chain, caplog):
    """Test _load_local_products with an empty JSON file, ensuring fallback."""
    caplog.set_level(logging.WARNING)
    service = LocalProductService()
    assert len(service.products) == 8
    assert "Failed to load with utf-8 encoding: Expecting value: line 1 column 1 (char 0)" in caplog.text
    assert "All encoding attempts failed, using fallback products" in caplog.text

def test_load_local_products_json_no_products_key_returns_empty_list(setup_json_no_products_key, mock_path_chain, caplog):
    """Test _load_local_products with JSON missing the 'products' key, returning an empty list."""
    caplog.set_level(logging.INFO)
    service = LocalProductService()
    assert len(service.products) == 0
    assert "Successfully loaded 0 products from JSON file using utf-8 encoding" in caplog.text
    assert "Loaded 0 local products from JSON file" in caplog.text

def test_load_local_products_malformed_product_data_uses_defaults(setup_json_with_malformed_product, mock_path_chain, caplog):
    """Test _load_local_products with products having missing fields, verifying default values."""
    caplog.set_level(logging.INFO)
    service = LocalProductService()
    assert len(service.products) == 2
    
    incomplete_product = service.products[0]
    assert incomplete_product['id'] == 'incomplete_product'
    assert incomplete_product['name'] == '' # Defaulted
    assert incomplete_product['price'] == 0 # Defaulted
    assert incomplete_product['currency'] == 'IDR' # Defaulted
    assert incomplete_product['specifications']['rating'] == 0 # Defaulted
    assert incomplete_product['specifications']['sold'] == 1000 # Mocked
    assert incomplete_product['specifications']['stock'] == 0 # Defaulted
    assert incomplete_product['images'] == ["https://example.com/incomplete_product.jpg"]

    complete_product = service.products[1]
    assert complete_product['id'] == 'complete_product'
    assert complete_product['name'] == 'Complete'
    assert complete_product['price'] == 1000
    assert complete_product['specifications']['rating'] == 4.0
    assert complete_product['reviews_count'] == 5


def test_load_local_products_general_exception_falls_back(mock_path_chain, caplog):
    """Test _load_local_products with a general exception during file read, ensuring fallback."""
    caplog.set_level(logging.ERROR)
    
    # Mock open to raise an exception for all encoding attempts
    with patch('app.services.local_product_service.open', side_effect=IOError("Permission denied")) as mock_open:
        service = LocalProductService()
        assert len(service.products) == 8 # Fallback products
        # Check that open was called for each encoding
        assert mock_open.call_count == len(LocalProductService()._load_local_products.__defaults__[0]) # Check against `encodings` list
        assert "Error loading products from JSON file: Permission denied" in caplog.text
        assert "Using fallback products due to JSON file loading error" in caplog.text

def test_get_fallback_products_returns_static_data_and_logs(caplog):
    """Test _get_fallback_products method returns the expected static list and logs."""
    caplog.set_level(logging.WARNING)
    # Initialize service to isolate _get_fallback_products call
    service = LocalProductService() 
    # Directly call the method to ensure it's logged
    fallback_products = service._get_fallback_products()
    assert len(fallback_products) == 8
    assert fallback_products[0]['id'] == '1'
    assert fallback_products[0]['name'] == 'iPhone 15 Pro Max'
    assert "Using fallback products due to JSON file loading error" in caplog.text

# --- Test search_products ---

def test_search_products_by_name_and_logs(product_service_with_sample_data, caplog):
    """Test searching products by name and verifies logging."""
    caplog.set_level(logging.INFO)
    results = product_service_with_sample_data.search_products(keyword="Test Phone")
    assert len(results) == 1
    assert results[0]['id'] == '1'
    assert "Searching products with keyword: Test Phone" in caplog.text
    assert "Found 1 products" in caplog.text

def test_search_products_case_insensitive_match(product_service_with_sample_data):
    """Test searching products with case-insensitive keyword match."""
    results = product_service_with_sample_data.search_products(keyword="test phone")
    assert len(results) == 1
    assert results[0]['id'] == '1'

def test_search_products_by_category_match(product_service_with_sample_data):
    """Test searching products by category keyword."""
    results = product_service_with_sample_data.search_products(keyword="Smartphone")
    assert len(results) == 1
    assert results[0]['id'] == '1'

def test_search_products_by_brand_match(product_service_with_sample_data):
    """Test searching products by brand keyword."""
    results = product_service_with_sample_data.search_products(keyword="testbrand")
    assert len(results) == 1
    assert results[0]['id'] == '1'

def test_search_products_by_description_match(product_service_with_sample_data):
    """Test searching products by description keyword."""
    results = product_service_with_sample_data.search_products(keyword="A test laptop.")
    assert len(results) == 1
    assert results[0]['id'] == '2'

def test_search_products_by_specifications_match(product_service_with_sample_data):
    """Test searching products by specifications keyword."""
    results = product_service_with_sample_data.search_products(keyword="128GB")
    assert len(results) == 1
    assert results[0]['id'] == '1'

def test_search_products_no_match_returns_empty_list(product_service_with_sample_data):
    """Test searching with a keyword that yields no matches."""
    results = product_service_with_sample_data.search_products(keyword="NonExistentProduct")
    assert len(results) == 0

def test_search_products_with_limit_parameter(product_service_with_sample_data):
    """Test search products with a specified limit."""
    # All products contain "Test" or "Product".
    # P1, P2, P3 have "Test". P4 has "Product".
    # Keyword "Test" should match P1, P2, P3.
    # Sorted by relevance score: 'Test Phone' (name match 10), 'Test Laptop' (name match 10), 'Test Headphone' (name match 10)
    # Since all have same score, their original order from `self.products` is preserved due to stable sort.
    results = product_service_with_sample_data.search_products(keyword="Test", limit=2)
    assert len(results) == 2
    assert results[0]['id'] == '1'
    assert results[1]['id'] == '2'

def test_search_products_with_price_limit_and_keyword_combination(product_service_with_sample_data):
    """
    Test searching products with a price limit extracted from keyword,
    and verify the interaction with keyword search and relevance sorting.
    """
    # Sample products: P1(10M), P2(15M), P3(2M), P4(0.5M)
    # Search for "phone 10 juta".
    # Max price extracted: 10,000,000. Keyword "phone".
    # Products added if price <= 10M OR keyword "phone" matches.
    # P1 (10M): <= 10M. Added. (Score from "phone" + price influence)
    # P2 (15M): > 10M. "phone" not in P2. Not added.
    # P3 (2M): <= 10M. Added. (Score from price influence only)
    # P4 (0.5M): <= 10M. Added. (Score from price influence only)
    # Resulting `filtered_products`: [P1, P3, P4] in their original order.
    # Relevance Score for "phone 10 juta" (max_price = 10M, budget search active):
    # P1 (Test Phone, 10M): `name` "phone" match (10) + `price` (10M-10M)/1M = 0. Total: 10.
    # P3 (Test Headphone, 2M): no "phone" match (0) + `price` (10M-2M)/1M = 8. Total: 8.
    # P4 (Product Without Rating, 0.5M): no "phone" match (0) + `price` (10M-0.5M)/1M = 9.5. Total: 9.5.
    # Sorted by score (desc): P1 (10), P4 (9.5), P3 (8).
    results = product_service_with_sample_data.search_products(keyword="phone 10 juta")
    assert len(results) == 3
    assert results[0]['id'] == '1'
    assert results[1]['id'] == '4'
    assert results[2]['id'] == '3'

def test_search_products_with_budget_keyword_and_relevance(product_service_with_sample_data):
    """
    Test searching products with a budget keyword ('murah') and verify relevance sorting.
    """
    # Search for "laptop murah". Max price for 'murah' is 5,000,000. Keyword "laptop".
    # Products: P1(10M), P2(15M), P3(2M), P4(0.5M)
    # Products added if price <= 5M OR keyword "laptop" matches.
    # P1 (10M): > 5M. "laptop" not in P1. Not added.
    # P2 (15M): > 5M. "laptop" in P2. Added.
    # P3 (2M): <= 5M. Added.
    # P4 (0.5M): <= 5M. Added.
    # Resulting `filtered_products`: [P2, P3, P4] in their original order.
    # Relevance Score for "laptop murah" (max_price = 5M, budget search active):
    # P2 (Test Laptop, 15M): `name` "laptop" match (10) + `price` (10M-15M)/1M = -5. Total: 5.
    # P3 (Test Headphone, 2M): no "laptop" match (0) + `price` (10M-2M)/1M = 8. Total: 8.
    # P4 (Product Without Rating, 0.5M): no "laptop" match (0) + `price` (10M-0.5M)/1M = 9.5. Total: 9.5.
    # Sorted by score (desc): P4 (9.5), P3 (8), P2 (5).
    results = product_service_with_sample_data.search_products(keyword="laptop murah")
    assert len(results) == 3
    assert results[0]['id'] == '4'
    assert results[1]['id'] == '3'
    assert results[2]['id'] == '2'

def test_search_products_empty_keyword_returns_all_within_limit(product_service_with_sample_data):
    """Test searching products with an empty keyword, should return all products within limit."""
    results = product_service_with_sample_data.search_products(keyword="", limit=3)
    assert len(results) == 3
    assert results[0]['id'] == '1'
    assert results[1]['id'] == '2'
    assert results[2]['id'] == '3'

def test_search_products_error_handling_returns_empty_list_and_logs(product_service_with_sample_data, caplog):
    """Test error handling in search_products, ensuring it returns an empty list and logs the error."""
    caplog.set_level(logging.ERROR)
    
    # Mock self.products to cause an error during iteration
    with patch.object(product_service_with_sample_data, 'products', new_callable=MagicMock) as mock_products:
        mock_products.__iter__.side_effect = Exception("Simulated iteration error")
        results = product_service_with_sample_data.search_products(keyword="test")
        assert results == []
        assert "Error searching products: Simulated iteration error" in caplog.text

# --- Test _extract_price_from_keyword ---
@pytest.mark.parametrize("keyword, expected_price", [
    ("iphone 10 juta", 10000000),
    ("laptop 5jt", 5000000),
    ("camera 2 ribu", 2000),
    ("rp 150000", 150000),
    ("250000 rp", 250000),
    ("headset 50k", 50000),
    ("tv 2m", 2000000),
    ("hp murah", 5000000),
    ("monitor budget", 5000000),
    ("speaker hemat", 3000000),
    ("drone terjangkau", 4000000),
    ("tablet ekonomis", 2000000),
    ("just a keyword", None),
    ("", None),
    ("1000", None), # Should not extract raw numbers without unit
    ("some product 100k price", 100000),
    ("rp 1.000.000", 1000000), # Handles dots as thousands separators (regex updated in original)
    ("rp. 500.000", 500000), # Handles dots and "rp." (regex updated in original)
    ("under 1jt", 1000000), # Test with "under" style keyword for price
    ("max 7.5 juta", 7500000),
    ("price up to 3jt", 3000000),
])
def test_extract_price_from_keyword_various_patterns(product_service_with_sample_data, keyword, expected_price):
    """Test _extract_price_from_keyword with various price patterns and budget keywords."""
    service = product_service_with_sample_data
    price = service._extract_price_from_keyword(keyword)
    assert price == expected_price

def test_extract_price_from_keyword_error_handling_returns_none_and_logs(product_service_with_sample_data, caplog):
    """Test error handling in _extract_price_from_keyword, ensuring it returns None and logs."""
    caplog.set_level(logging.ERROR)
    
    # Mock re.search to raise an error
    with patch('app.services.local_product_service.re.search', side_effect=Exception("Simulated regex error")):
        price = product_service_with_sample_data._extract_price_from_keyword("10 juta")
        assert price is None
        assert "Error extracting price from keyword: Simulated regex error" in caplog.text

# --- Test get_product_details ---
def test_get_product_details_existing_id_returns_product(product_service_with_sample_data):
    """Test getting details for an existing product ID."""
    details = product_service_with_sample_data.get_product_details("1")
    assert details is not None
    assert details['id'] == '1'
    assert details['name'] == 'Test Phone'

def test_get_product_details_non_existing_id_returns_none(product_service_with_sample_data):
    """Test getting details for a non-existing product ID."""
    details = product_service_with_sample_data.get_product_details("99")
    assert details is None

def test_get_product_details_empty_id_returns_none(product_service_with_sample_data):
    """Test getting details for an empty product ID."""
    details = product_service_with_sample_data.get_product_details("")
    assert details is None

def test_get_product_details_error_handling_returns_none_and_logs(product_service_with_sample_data, caplog):
    """Test error handling in get_product_details, ensuring it returns None and logs."""
    caplog.set_level(logging.ERROR)
    
    # Mock self.products to cause an error during iteration
    with patch.object(product_service_with_sample_data, 'products', new_callable=MagicMock) as mock_products:
        mock_products.__iter__.side_effect = Exception("Simulated iteration error")
        details = product_service_with_sample_data.get_product_details("1")
        assert details is None
        assert "Error getting product details: Simulated iteration error" in caplog.text

# --- Test get_categories ---
def test_get_categories_returns_unique_sorted_categories(product_service_with_sample_data):
    """Test getting unique sorted product categories."""
    categories = product_service_with_sample_data.get_categories()
    assert categories == ['Audio', 'Laptop', 'Misc', 'Smartphone']

def test_get_categories_empty_products_list_returns_empty_list(mock_path_chain):
    """Test get_categories when no products are loaded (empty list)."""
    with patch.object(LocalProductService, '_load_local_products', return_value=[]):
        service = LocalProductService()
        categories = service.get_categories()
        assert categories == []

def test_get_categories_products_missing_category_includes_empty_string(mock_path_chain):
    """Test get_categories when some products are missing 'category' key."""
    with patch.object(LocalProductService, '_load_local_products', return_value=[
        {'id': '1', 'name': 'Phone', 'category': 'Smartphone', 'price': 0, 'specifications': {}},
        {'id': '2', 'name': 'Laptop', 'price': 0, 'specifications': {}} # No 'category'
    ]):
        service = LocalProductService()
        categories = service.get_categories()
        assert categories == ['', 'Smartphone'] # Empty string for missing category, sorted correctly

# --- Test get_brands ---
def test_get_brands_returns_unique_sorted_brands(product_service_with_sample_data):
    """Test getting unique sorted product brands."""
    brands = product_service_with_sample_data.get_brands()
    assert brands == ['AnotherBrand', 'AudioBrand', 'Other', 'TestBrand']

def test_get_brands_empty_products_list_returns_empty_list(mock_path_chain):
    """Test get_brands when no products are loaded (empty list)."""
    with patch.object(LocalProductService, '_load_local_products', return_value=[]):
        service = LocalProductService()
        brands = service.get_brands()
        assert brands == []

def test_get_brands_products_missing_brand_includes_empty_string(mock_path_chain):
    """Test get_brands when some products are missing 'brand' key."""
    with patch.object(LocalProductService, '_load_local_products', return_value=[
        {'id': '1', 'name': 'Phone', 'brand': 'Apple', 'price': 0, 'specifications': {}},
        {'id': '2', 'name': 'Laptop', 'price': 0, 'specifications': {}} # No 'brand'
    ]):
        service = LocalProductService()
        brands = service.get_brands()
        assert brands == ['', 'Apple'] # Empty string for missing brand, sorted correctly

# --- Test get_products_by_category ---
def test_get_products_by_category_existing_returns_matches(product_service_with_sample_data):
    """Test getting products by an existing category."""
    results = product_service_with_sample_data.get_products_by_category("Smartphone")
    assert len(results) == 1
    assert results[0]['id'] == '1'

def test_get_products_by_category_case_insensitive_match(product_service_with_sample_data):
    """Test getting products by category with case-insensitive match."""
    results = product_service_with_sample_data.get_products_by_category("smartphone")
    assert len(results) == 1
    assert results[0]['id'] == '1'

def test_get_products_by_category_non_existing_returns_empty_list(product_service_with_sample_data):
    """Test getting products by a non-existing category."""
    results = product_service_with_sample_data.get_products_by_category("Gaming")
    assert len(results) == 0

def test_get_products_by_category_empty_category_returns_no_matches(product_service_with_sample_data):
    """Test getting products by an empty category string, should not match any valid category."""
    results = product_service_with_sample_data.get_products_by_category("")
    assert len(results) == 0

def test_get_products_by_category_error_handling_returns_empty_list_and_logs(product_service_with_sample_data, caplog):
    """Test error handling in get_products_by_category, ensuring empty list and logs."""
    caplog.set_level(logging.ERROR)
    with patch.object(product_service_with_sample_data, 'products', new_callable=MagicMock) as mock_products:
        mock_products.__iter__.side_effect = Exception("Simulated iteration error")
        results = product_service_with_sample_data.get_products_by_category("Smartphone")
        assert results == []
        assert "Error getting products by category: Simulated iteration error" in caplog.text

# --- Test get_products_by_brand ---
def test_get_products_by_brand_existing_returns_matches(product_service_with_sample_data):
    """Test getting products by an existing brand."""
    results = product_service_with_sample_data.get_products_by_brand("TestBrand")
    assert len(results) == 1
    assert results[0]['id'] == '1'

def test_get_products_by_brand_case_insensitive_match(product_service_with_sample_data):
    """Test getting products by brand with case-insensitive match."""
    results = product_service_with_sample_data.get_products_by_brand("testbrand")
    assert len(results) == 1
    assert results[0]['id'] == '1'

def test_get_products_by_brand_non_existing_returns_empty_list(product_service_with_sample_data):
    """Test getting products by a non-existing brand."""
    results = product_service_with_sample_data.get_products_by_brand("Nokia")
    assert len(results) == 0

def test_get_products_by_brand_empty_brand_returns_no_matches(product_service_with_sample_data):
    """Test getting products by an empty brand string, should not match any valid brand."""
    results = product_service_with_sample_data.get_products_by_brand("")
    assert len(results) == 0

def test_get_products_by_brand_error_handling_returns_empty_list_and_logs(product_service_with_sample_data, caplog):
    """Test error handling in get_products_by_brand, ensuring empty list and logs."""
    caplog.set_level(logging.ERROR)
    with patch.object(product_service_with_sample_data, 'products', new_callable=MagicMock) as mock_products:
        mock_products.__iter__.side_effect = Exception("Simulated iteration error")
        results = product_service_with_sample_data.get_products_by_brand("TestBrand")
        assert results == []
        assert "Error getting products by brand: Simulated iteration error" in caplog.text

# --- Test get_top_rated_products ---
def test_get_top_rated_products_returns_sorted_by_rating(product_service_with_sample_data):
    """Test getting top-rated products, sorted correctly."""
    # Ratings: P1: 4.5, P2: 4.0, P3: 3.8, P4: 0 (default for missing)
    results = product_service_with_sample_data.get_top_rated_products(limit=2)
    assert len(results) == 2
    assert results[0]['id'] == '1' # Rating 4.5
    assert results[1]['id'] == '2' # Rating 4.0

def test_get_top_rated_products_limit_exceeds_available_returns_all(product_service_with_sample_data):
    """Test get_top_rated_products with limit exceeding available products."""
    results = product_service_with_sample_data.get_top_rated_products(limit=10)
    assert len(results) == 4
    # Ensure correct order based on rating (P4 has default 0 rating)
    assert [p['id'] for p in results] == ['1', '2', '3', '4']

def test_get_top_rated_products_empty_products_list_returns_empty_list(mock_path_chain):
    """Test get_top_rated_products with an empty product list."""
    with patch.object(LocalProductService, '_load_local_products', return_value=[]):
        service = LocalProductService()
        results = service.get_top_rated_products()
        assert results == []

def test_get_top_rated_products_error_handling_returns_empty_list_and_logs(product_service_with_sample_data, caplog):
    """Test error handling in get_top_rated_products, ensuring empty list and logs."""
    caplog.set_level(logging.ERROR)
    with patch.object(product_service_with_sample_data, 'products', new_callable=MagicMock) as mock_products:
        mock_products.__iter__.side_effect = Exception("Simulated iteration error")
        results = product_service_with_sample_data.get_top_rated_products()
        assert results == []
        assert "Error getting top rated products: Simulated iteration error" in caplog.text

# --- Test get_best_selling_products ---
def test_get_best_selling_products_returns_sorted_by_sold_count_and_logs(product_service_with_sample_data, caplog):
    """Test getting best-selling products, sorted correctly by mocked sold count."""
    # Sold count is mocked to 1000 for all products during load
    # This means they will be sorted by their original order (stable sort for equal keys)
    caplog.set_level(logging.INFO)
    results = product_service_with_sample_data.get_best_selling_products(limit=2)
    assert len(results) == 2
    assert results[0]['id'] == '1' # P1 has 1000 sold (mocked)
    assert results[1]['id'] == '2' # P2 has 1000 sold (mocked)
    assert "Getting best selling products, limit: 2" in caplog.text
    assert "Returning 2 best selling products" in caplog.text

def test_get_best_selling_products_limit_exceeds_available_returns_all(product_service_with_sample_data):
    """Test get_best_selling_products with limit exceeding available products."""
    results = product_service_with_sample_data.get_best_selling_products(limit=10)
    assert len(results) == 4
    # All mocked to 1000 sold, so original order
    assert [p['id'] for p in results] == ['1', '2', '3', '4']

def test_get_best_selling_products_empty_products_list_returns_empty_list(mock_path_chain):
    """Test get_best_selling_products with an empty product list."""
    with patch.object(LocalProductService, '_load_local_products', return_value=[]):
        service = LocalProductService()
        results = service.get_best_selling_products()
        assert results == []

def test_get_best_selling_products_error_handling_returns_empty_list_and_logs(product_service_with_sample_data, caplog):
    """Test error handling in get_best_selling_products, ensuring empty list and logs."""
    caplog.set_level(logging.ERROR)
    with patch.object(product_service_with_sample_data, 'products', new_callable=MagicMock) as mock_products:
        mock_products.__iter__.side_effect = Exception("Simulated iteration error")
        results = product_service_with_sample_data.get_best_selling_products()
        assert results == []
        assert "Error getting best selling products: Simulated iteration error" in caplog.text

# --- Test get_products ---
def test_get_products_returns_all_within_limit_and_logs(product_service_with_sample_data, caplog):
    """Test getting all products with a limit and verifies logging."""
    caplog.set_level(logging.INFO)
    results = product_service_with_sample_data.get_products(limit=2)
    assert len(results) == 2
    assert results[0]['id'] == '1'
    assert results[1]['id'] == '2'
    assert "Getting all products, limit: 2" in caplog.text

def test_get_products_limit_exceeds_available_returns_all(product_service_with_sample_data):
    """Test get_products with limit exceeding available products."""
    results = product_service_with_sample_data.get_products(limit=10)
    assert len(results) == 4
    assert [p['id'] for p in results] == ['1', '2', '3', '4']

def test_get_products_empty_products_list_returns_empty_list(mock_path_chain):
    """Test get_products with an empty product list."""
    with patch.object(LocalProductService, '_load_local_products', return_value=[]):
        service = LocalProductService()
        results = service.get_products()
        assert results == []

def test_get_products_error_handling_returns_empty_list_and_logs(product_service_with_sample_data, caplog):
    """Test error handling in get_products, ensuring empty list and logs."""
    caplog.set_level(logging.ERROR)
    with patch.object(product_service_with_sample_data, 'products', new_callable=MagicMock) as mock_products:
        # Mock __getitem__ for slicing operation
        mock_products.__getitem__.side_effect = Exception("Simulated slicing error")
        results = product_service_with_sample_data.get_products()
        assert results == []
        assert "Error getting products: Simulated slicing error" in caplog.text

# --- Test smart_search_products ---
@pytest.fixture
def smart_search_service_custom_data(mock_path_chain):
    """Fixture for LocalProductService with custom data for smart_search_products to ensure predictable sorting."""
    products = [
        {
            "id": "A1", "name": "Best Laptop Pro", "category": "Laptop", "brand": "Tech",
            "price": 20000000, "description": "High-end laptop, great performance.",
            "specifications": {"rating": 4.9, "sold": 1500, "stock": 10}
        },
        {
            "id": "A2", "name": "Budget Smartphone", "category": "Smartphone", "brand": "Mobile",
            "price": 3000000, "description": "Affordable smartphone.",
            "specifications": {"rating": 4.0, "sold": 2000, "stock": 50}
        },
        {
            "id": "A3", "name": "Mid-Range Headphone", "category": "Audio", "brand": "Sound",
            "price": 1000000, "description": "Good quality headphones.",
            "specifications": {"rating": 4.2, "sold": 800, "stock": 30}
        },
        {
            "id": "A4", "name": "Entry-Level Tablet", "category": "Tablet", "brand": "PadCo",
            "price": 2500000, "description": "Simple tablet for basic use.",
            "specifications": {"rating": 3.5, "sold": 1000, "stock": 25}
        },
        {
            "id": "A5", "name": "Ultimate Gaming Laptop", "category": "Laptop", "brand": "GamingPro",
            "price": 25000000, "description": "Top-tier gaming laptop.",
            "specifications": {"rating": 4.8, "sold": 1200, "stock": 5}
        },
        {
            "id": "A6", "name": "Basic Feature Phone", "category": "Phone", "brand": "OldTech",
            "price": 500000, "description": "Very basic phone.",
            "specifications": {"rating": 3.0, "sold": 3000, "stock": 100}
        },
         { # Product to test empty keyword search against
            "id": "A7", "name": "Smart Watch", "category": "Wearable", "brand": "GadgetCo",
            "price": 1000000, "description": "A smart watch.",
            "specifications": {"rating": 4.1, "sold": 700, "stock": 100}
        }
    ]
    with patch.object(LocalProductService, '_load_local_products', return_value=products):
        service = LocalProductService()
        yield service


def test_smart_search_best_no_category_returns_general_top_rated(smart_search_service_custom_data):
    """Test smart search for 'terbaik' without specific category, returning general top-rated."""
    products, message = smart_search_service_custom_data.smart_search_products(keyword="terbaik")
    assert message == "Berikut produk terbaik berdasarkan rating:"
    assert len(products) == 5 # Default limit
    # Expected order: A1 (4.9), A5 (4.8), A3 (4.2), A7 (4.1), A2 (4.0)
    assert [p['id'] for p in products] == ['A1', 'A5', 'A3', 'A7', 'A2']

def test_smart_search_best_with_category_returns_category_top_rated(smart_search_service_custom_data):
    """Test smart search for 'terbaik' with a specific category, returning top-rated for that category."""
    products, message = smart_search_service_custom_data.smart_search_products(keyword="terbaik", category="Laptop")
    assert message == "Berikut Laptop terbaik berdasarkan rating:"
    assert len(products) == 2
    # Expected order: A1 (4.9), A5 (4.8)
    assert [p['id'] for p in products] == ['A1', 'A5']

def test_smart_search_best_with_nonexistent_category_falls_back_to_general_best(smart_search_service_custom_data):
    """Test smart search for 'terbaik' with a non-existent category, falling back to general top-rated."""
    products, message = smart_search_service_custom_data.smart_search_products(keyword="terbaik", category="Smartwatch")
    assert message == "Tidak ada produk kategori Smartwatch, berikut produk terbaik secara umum:"
    assert len(products) == 5
    assert [p['id'] for p in products] == ['A1', 'A5', 'A3', 'A7', 'A2']

def test_smart_search_all_criteria_match_returns_specific_results(smart_search_service_custom_data):
    """Test smart search when all keyword, category, max_price criteria match."""
    products, message = smart_search_service_custom_data.smart_search_products(keyword="phone", category="Smartphone", max_price=5000000)
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."
    assert len(products) == 1
    assert products[0]['id'] == 'A2' # Budget Smartphone

def test_smart_search_keyword_only_returns_matches(smart_search_service_custom_data):
    """Test smart search with only a keyword."""
    products, message = smart_search_service_custom_data.smart_search_products(keyword="laptop")
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."
    assert len(products) == 2
    assert {p['id'] for p in products} == {'A1', 'A5'} # Order based on initial products list

def test_smart_search_category_only_returns_matches(smart_search_service_custom_data):
    """Test smart search with only a category."""
    products, message = smart_search_service_custom_data.smart_search_products(category="Audio")
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."
    assert len(products) == 1
    assert products[0]['id'] == 'A3'

def test_smart_search_max_price_only_returns_matches(smart_search_service_custom_data):
    """Test smart search with only a max_price."""
    products, message = smart_search_service_custom_data.smart_search_products(max_price=2000000)
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."
    assert len(products) == 3 
    # Products <= 2M: A3 (1M), A6 (0.5M), A7 (1M)
    assert {p['id'] for p in products} == {'A3', 'A6', 'A7'}
    # Order preserved from original list: A3, A6, A7
    assert [p['id'] for p in products] == ['A3', 'A6', 'A7']

def test_smart_search_fallback_category_no_budget_match(smart_search_service_custom_data):
    """Test smart search fallback to category if initial keyword+budget criteria fail."""
    # Search for a high-price item (laptop) with a low budget.
    products, message = smart_search_service_custom_data.smart_search_products(keyword="laptop", category="Laptop", max_price=1000000)
    assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."
    assert len(products) == 2
    # Should be laptops sorted by price: A1 (20M), A5 (25M)
    assert [p['id'] for p in products] == ['A1', 'A5']

def test_smart_search_fallback_budget_no_category_match(smart_search_service_custom_data):
    """Test smart search fallback to budget if initial keyword+category criteria fail."""
    products, message = smart_search_service_custom_data.smart_search_products(keyword="phone", category="NonExistentCategory", max_price=5000000)
    assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."
    assert len(products) == 4 
    # Products <= 5M: A2(3M), A3(1M), A4(2.5M), A6(0.5M), A7(1M).
    # The limit of 5 applies to the returned list.
    # Ordered as they appear in the original list from `_load_local_products`: A2, A3, A4, A6, A7
    assert [p['id'] for p in products] == ['A2', 'A3', 'A4', 'A6'] # within the 5 limit

def test_smart_search_fallback_popular_no_match(smart_search_service_custom_data):
    """Test smart search fallback to popular products if all other criteria fail."""
    products, message = smart_search_service_custom_data.smart_search_products(keyword="xyz", category="NonExistent", max_price=10000)
    assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
    assert len(products) == 5
    # Should be sorted by 'sold' count (desc): A6 (3000), A2 (2000), A1 (1500), A5 (1200), A4 (1000)
    assert [p['id'] for p in products] == ['A6', 'A2', 'A1', 'A5', 'A4']

def test_smart_search_empty_product_list_returns_empty_and_fallback_message(mock_path_chain):
    """Test smart search with an empty product list, ensuring empty results and appropriate fallback message."""
    with patch.object(LocalProductService, '_load_local_products', return_value=[]):
        service = LocalProductService()
        products, message = service.smart_search_products(keyword="terbaik")
        assert products == []
        assert message == "Berikut produk terbaik berdasarkan rating:" # Still returns the message, but empty list

        products, message = service.smart_search_products(keyword="any", category="any", max_price=100)
        assert products == []
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

def test_smart_search_limit_parameter_is_respected(smart_search_service_custom_data):
    """Test the limit parameter in smart search."""
    products, message = smart_search_service_custom_data.smart_search_products(keyword="terbaik", limit=1)
    assert len(products) == 1
    assert products[0]['id'] == 'A1' # Highest rated

    products, message = smart_search_service_custom_data.smart_search_products(keyword="laptop", limit=1)
    assert len(products) == 1
    assert products[0]['id'] == 'A1' # First matching laptop in the list (not sorted by smart_search directly)

def test_smart_search_no_keyword_no_category_no_max_price_defaults_to_all_products(smart_search_service_custom_data):
    """Test smart search with no specific criteria, should return all products up to limit."""
    products, message = smart_search_service_custom_data.smart_search_products(limit=3)
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."
    assert len(products) == 3
    assert [p['id'] for p in products] == ['A1', 'A2', 'A3']