import pytest
from unittest.mock import patch, mock_open, MagicMock
import logging
import json
from pathlib import Path
import sys
import builtins # Added for patching open

# Add the parent directory of 'app' to the sys.path
# This allows imports like 'from app.services.local_product_service import LocalProductService'
# to work correctly when tests are run from a different root.
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.local_product_service import LocalProductService

# Mock data for testing
MOCK_PRODUCTS_DATA = [
    {
        "id": "prod1",
        "name": "Product A",
        "category": "Category1",
        "brand": "BrandX",
        "price": 100000,
        "currency": "IDR",
        "description": "Description A",
        "specifications": {"rating": 4.5, "sold": 500, "stock_count": 100},
        "availability": "in_stock",
        "reviews_count": 10,
        "images": ["url_a.jpg"],
        "url": "url_a"
    },
    {
        "id": "prod2",
        "name": "Product B",
        "category": "Category2",
        "brand": "BrandY",
        "price": 200000,
        "currency": "IDR",
        "description": "Description B, also Product A related.",
        "specifications": {"rating": 3.8, "sold": 300, "stock_count": 50},
        "availability": "out_of_stock",
        "reviews_count": 5,
        "images": ["url_b.jpg"],
        "url": "url_b"
    },
    {
        "id": "prod3",
        "name": "Product C",
        "category": "Category1",
        "brand": "BrandX",
        "price": 50000,
        "currency": "IDR",
        "description": "Cheapest product.",
        "specifications": {"rating": 4.9, "sold": 1200, "stock_count": 200},
        "availability": "in_stock",
        "reviews_count": 20,
        "images": ["url_c.jpg"],
        "url": "url_c"
    },
    {
        "id": "prod4",
        "name": "Product D",
        "category": "Category3",
        "brand": "BrandZ",
        "price": 5000000, # 5 juta
        "currency": "IDR",
        "description": "Expensive gadget.",
        "specifications": {"rating": 4.0, "sold": 100, "stock_count": 10},
        "availability": "in_stock",
        "reviews_count": 2,
        "images": ["url_d.jpg"],
        "url": "url_d"
    },
    {
        "id": "prod5",
        "name": "Product E (Best Seller)",
        "category": "Category1",
        "brand": "BrandX",
        "price": 150000,
        "currency": "IDR",
        "description": "Best seller in Category1.",
        "specifications": {"rating": 4.6, "sold": 15000, "stock_count": 1000},
        "availability": "in_stock",
        "reviews_count": 150,
        "images": ["url_e.jpg"],
        "url": "url_e"
    },
    {
        "id": "prod6",
        "name": "Product F (Budget)",
        "category": "Category2",
        "brand": "BrandY",
        "price": 4000000, # 4 juta
        "currency": "IDR",
        "description": "A budget friendly product.",
        "specifications": {"rating": 3.0, "sold": 50, "stock_count": 20},
        "availability": "in_stock",
        "reviews_count": 1,
        "images": ["url_f.jpg"],
        "url": "url_f"
    },
]

# Transformed version of MOCK_PRODUCTS_DATA for comparison with _load_local_products output
# The 'sold' count will be mocked to 1000 for deterministic tests
TRANSFORMED_MOCK_PRODUCTS_DATA = [
    {
        "id": "prod1", "name": "Product A", "category": "Category1", "brand": "BrandX", "price": 100000, "currency": "IDR", "description": "Description A",
        "specifications": {"rating": 4.5, "sold": 1000, "stock": 100, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandX Store"},
        "availability": "in_stock", "reviews_count": 10, "images": ["https://example.com/prod1.jpg"], "url": "https://shopee.co.id/prod1"
    },
    {
        "id": "prod2", "name": "Product B", "category": "Category2", "brand": "BrandY", "price": 200000, "currency": "IDR", "description": "Description B, also Product A related.",
        "specifications": {"rating": 3.8, "sold": 1000, "stock": 50, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandY Store"},
        "availability": "out_of_stock", "reviews_count": 5, "images": ["https://example.com/prod2.jpg"], "url": "https://shopee.co.id/prod2"
    },
    {
        "id": "prod3", "name": "Product C", "category": "Category1", "brand": "BrandX", "price": 50000, "currency": "IDR", "description": "Cheapest product.",
        "specifications": {"rating": 4.9, "sold": 1000, "stock": 200, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandX Store"},
        "availability": "in_stock", "reviews_count": 20, "images": ["https://example.com/prod3.jpg"], "url": "https://shopee.co.id/prod3"
    },
    {
        "id": "prod4", "name": "Product D", "category": "Category3", "brand": "BrandZ", "price": 5000000, "currency": "IDR", "description": "Expensive gadget.",
        "specifications": {"rating": 4.0, "sold": 1000, "stock": 10, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandZ Store"},
        "availability": "in_stock", "reviews_count": 2, "images": ["https://example.com/prod4.jpg"], "url": "https://shopee.co.id/prod4"
    },
    {
        "id": "prod5", "name": "Product E (Best Seller)", "category": "Category1", "brand": "BrandX", "price": 150000, "currency": "IDR", "description": "Best seller in Category1.",
        "specifications": {"rating": 4.6, "sold": 1000, "stock": 1000, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandX Store"},
        "availability": "in_stock", "reviews_count": 150, "images": ["https://example.com/prod5.jpg"], "url": "https://shopee.co.id/prod5"
    },
    {
        "id": "prod6", "name": "Product F (Budget)", "category": "Category2", "brand": "BrandY", "price": 4000000, "currency": "IDR", "description": "A budget friendly product.",
        "specifications": {"rating": 3.0, "sold": 1000, "stock": 20, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandY Store"},
        "availability": "in_stock", "reviews_count": 1, "images": ["https://example.com/prod6.jpg"], "url": "https://shopee.co.id/prod6"
    },
]


@pytest.fixture
def mock_local_product_service_instance():
    """
    Fixture to provide a LocalProductService instance with pre-defined mock products,
    bypassing the file loading mechanism for most tests.
    """
    # Patch _load_local_products to return deterministic, transformed mock data
    with patch('app.services.local_product_service.LocalProductService._load_local_products',
               return_value=TRANSFORMED_MOCK_PRODUCTS_DATA) as mock_load:
        service = LocalProductService()
        mock_load.assert_called_once() # Ensure init calls _load_local_products
        yield service

@pytest.fixture
def mock_logger():
    """Fixture to mock the logger to capture log messages."""
    with patch('app.services.local_product_service.logger') as mock_log:
        yield mock_log

# --- Tests for __init__ and _load_local_products ---

def test_init_success(mock_logger):
    """
    Test that LocalProductService initializes successfully by loading products.
    """
    # Mock _load_local_products to return a specific list
    with patch('app.services.local_product_service.LocalProductService._load_local_products',
               return_value=TRANSFORMED_MOCK_PRODUCTS_DATA) as mock_load:
        service = LocalProductService()
        mock_load.assert_called_once()
        assert service.products == TRANSFORMED_MOCK_PRODUCTS_DATA
        mock_logger.info.assert_called_with(f"Loaded {len(TRANSFORMED_MOCK_PRODUCTS_DATA)} local products from JSON file")

def test_load_local_products_file_not_found(mock_logger):
    """
    Test _load_local_products when the JSON file does not exist.
    It should log an error and return fallback products.
    """
    # Mock Path.exists to return False, and mock Path constructor to return a mock object
    with patch('app.services.local_product_service.Path.exists', return_value=False), \
         patch('app.services.local_product_service.LocalProductService._get_fallback_products') as mock_fallback, \
         patch('app.services.local_product_service.Path') as MockPath:
        
        # Configure MockPath to simulate the file path construction
        mock_file_path = MagicMock(spec=Path) # Use spec=Path to ensure Path methods exist
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path
        
        service = LocalProductService() # Initialize to access the method
        result = service._load_local_products()
        
        mock_logger.error.assert_called_once()
        assert "Products JSON file not found at:" in mock_logger.error.call_args[0][0]
        mock_fallback.assert_called_once()
        assert result == mock_fallback.return_value # Ensure fallback products are returned

def test_load_local_products_valid_json_utf8(mock_logger):
    """
    Test _load_local_products with a valid UTF-8 JSON file.
    """
    mock_json_content = json.dumps({"products": MOCK_PRODUCTS_DATA})
    
    with patch('app.services.local_product_service.Path') as MockPath, \
         patch('builtins.open', mock_open(read_data=mock_json_content)), \
         patch('random.randint', return_value=1000): # Mock random.randint for predictable sold count
        
        # Simulate the Path resolution
        mock_file_path = MagicMock(spec=Path)
        mock_file_path.exists.return_value = True
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path

        service = LocalProductService() # Initialize to access the method
        products = service._load_local_products()
        
        assert len(products) == len(TRANSFORMED_MOCK_PRODUCTS_DATA)
        # Compare a few key attributes to ensure transformation happened correctly
        assert products[0]['id'] == TRANSFORMED_MOCK_PRODUCTS_DATA[0]['id']
        assert products[0]['price'] == TRANSFORMED_MOCK_PRODUCTS_DATA[0]['price']
        assert products[0]['specifications']['sold'] == 1000 # Verify mocked random.randint
        assert products[0]['images'][0] == f"https://example.com/{TRANSFORMED_MOCK_PRODUCTS_DATA[0]['id']}.jpg"
        mock_logger.info.assert_any_call(f"Successfully loaded {len(TRANSFORMED_MOCK_PRODUCTS_DATA)} products from JSON file using utf-8 encoding")
        # Ensure open was called with various encodings before finding success with utf-8
        # The first call might be utf-16-le which might fail or succeed depending on mock_open's internal behavior.
        # But utf-8 should be the one leading to the info log.
        assert any(call.kwargs['encoding'] == 'utf-8' for call in builtins.open.call_args_list)

def test_load_local_products_valid_json_utf16le_with_bom(mock_logger):
    """
    Test _load_local_products with a valid UTF-16-LE JSON file containing a BOM.
    """
    mock_json_content_str = json.dumps({"products": MOCK_PRODUCTS_DATA})
    
    # Create a mock for Path that points to a file that exists
    mock_file_path = MagicMock(spec=Path)
    mock_file_path.exists.return_value = True
    
    def open_side_effect(file_path_arg, mode, encoding):
        m_file = MagicMock()
        if encoding == 'utf-16-le':
            # This simulates reading a file that *was* UTF-16-LE with BOM,
            # and `file.read()` returns the decoded string (which still has the BOM char at start).
            m_file.read.return_value = '\ufeff' + mock_json_content_str
        else:
            # Simulate failure for other encodings to ensure utf-16-le is picked
            raise UnicodeDecodeError("mockcodec", b"", 0, 1, "mock reason") # This will make other encodings fail
        return m_file

    with patch('app.services.local_product_service.Path') as MockPath, \
         patch('builtins.open', side_effect=open_side_effect), \
         patch('random.randint', return_value=1000):
        
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path

        service = LocalProductService()
        products = service._load_local_products()
        
        assert len(products) == len(TRANSFORMED_MOCK_PRODUCTS_DATA)
        assert products[0]['id'] == TRANSFORMED_MOCK_PRODUCTS_DATA[0]['id']
        assert products[0]['specifications']['sold'] == 1000
        
        # Verify open was called with 'utf-16-le' first and succeeded
        builtins.open.assert_called_with(mock_file_path, 'r', encoding='utf-16-le')
        mock_logger.info.assert_any_call(f"Successfully loaded {len(TRANSFORMED_MOCK_PRODUCTS_DATA)} products from JSON file using utf-16-le encoding")
        mock_logger.warning.assert_not_called()

def test_load_local_products_invalid_json_all_encodings_fail(mock_logger):
    """
    Test _load_local_products when the JSON content is invalid for all encoding attempts.
    It should log warnings and return fallback products.
    """
    invalid_json_content = "this is not json {"
    
    # Create a mock for Path that points to a file that exists
    mock_file_path = MagicMock(spec=Path)
    mock_file_path.exists.return_value = True

    # Configure mock_open to always return invalid content, causing JSONDecodeError
    def open_side_effect_invalid_json(file_path_arg, mode, encoding):
        m_file = MagicMock()
        m_file.read.return_value = invalid_json_content
        return m_file

    with patch('app.services.local_product_service.Path') as MockPath, \
         patch('builtins.open', side_effect=open_side_effect_invalid_json), \
         patch('app.services.local_product_service.LocalProductService._get_fallback_products') as mock_fallback:
        
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path

        service = LocalProductService()
        result = service._load_local_products()
        
        # Check that warnings were logged for each encoding attempt
        encodings = ['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        for encoding in encodings:
            mock_logger.warning.assert_any_call(f"Failed to load with {encoding} encoding: json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)")
        
        mock_logger.error.assert_called_with("All encoding attempts failed, using fallback products")
        mock_fallback.assert_called_once()
        assert result == mock_fallback.return_value

def test_load_local_products_unicode_decode_error_all_encodings_fail(mock_logger):
    """
    Test _load_local_products when all encoding attempts result in UnicodeDecodeError.
    It should log warnings and return fallback products.
    """
    # Create a mock for Path that points to a file that exists
    mock_file_path = MagicMock(spec=Path)
    mock_file_path.exists.return_value = True

    # Create a mock for builtins.open that always raises UnicodeDecodeError
    def mock_open_side_effect(file_path_arg, mode, encoding):
        raise UnicodeDecodeError("mockcodec", b"", 0, 1, "mock reason")

    with patch('app.services.local_product_service.Path') as MockPath, \
         patch('builtins.open', side_effect=mock_open_side_effect), \
         patch('app.services.local_product_service.LocalProductService._get_fallback_products') as mock_fallback:
        
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path

        service = LocalProductService()
        result = service._load_local_products()
        
        # Check that warnings were logged for each encoding attempt
        encodings = ['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        for encoding in encodings:
            mock_logger.warning.assert_any_call(f"Failed to load with {encoding} encoding: mockcodec: mock reason")
        
        mock_logger.error.assert_called_with("All encoding attempts failed, using fallback products")
        mock_fallback.assert_called_once()
        assert result == mock_fallback.return_value

def test_load_local_products_generic_exception(mock_logger):
    """
    Test _load_local_products when a generic exception occurs (e.g., during file reading or JSON parsing).
    It should log an error and return fallback products.
    """
    # Create a mock for Path that points to a file that exists
    mock_file_path = MagicMock(spec=Path)
    mock_file_path.exists.return_value = True

    with patch('app.services.local_product_service.Path') as MockPath, \
         patch('builtins.open', side_effect=IOError("Mock IO Error")), \
         patch('app.services.local_product_service.LocalProductService._get_fallback_products') as mock_fallback:
        
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path

        service = LocalProductService()
        result = service._load_local_products()
        
        mock_logger.error.assert_called_with("Error loading products from JSON file: Mock IO Error")
        mock_fallback.assert_called_once()
        assert result == mock_fallback.return_value

def test_load_local_products_empty_products_list_in_json(mock_logger):
    """
    Test _load_local_products with a valid JSON file but an empty 'products' list.
    """
    mock_json_content = json.dumps({"products": []}) # Empty products list
    
    with patch('app.services.local_product_service.Path') as MockPath, \
         patch('builtins.open', mock_open(read_data=mock_json_content)), \
         patch('random.randint', return_value=1000):
        
        mock_file_path = MagicMock(spec=Path)
        mock_file_path.exists.return_value = True
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path

        service = LocalProductService()
        products = service._load_local_products()
        
        assert len(products) == 0
        mock_logger.info.assert_any_call("Successfully loaded 0 products from JSON file using utf-8 encoding")
        mock_logger.warning.assert_not_called()

def test_load_local_products_json_missing_products_key(mock_logger):
    """
    Test _load_local_products with a valid JSON file but missing the 'products' key.
    """
    mock_json_content = json.dumps({"some_other_key": "value"}) # Missing 'products' key
    
    with patch('app.services.local_product_service.Path') as MockPath, \
         patch('builtins.open', mock_open(read_data=mock_json_content)), \
         patch('random.randint', return_value=1000):
        
        mock_file_path = MagicMock(spec=Path)
        mock_file_path.exists.return_value = True
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path

        service = LocalProductService()
        products = service._load_local_products()
        
        assert len(products) == 0 # Should fallback to empty list due to .get('products', [])
        mock_logger.info.assert_any_call("Successfully loaded 0 products from JSON file using utf-8 encoding")
        mock_logger.warning.assert_not_called()

def test_get_fallback_products(mock_logger):
    """
    Test the _get_fallback_products method directly.
    """
    # Create a LocalProductService instance, but patch its __init__ to avoid file system interaction
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
        service = LocalProductService()
        products = service._get_fallback_products()
        
        assert isinstance(products, list)
        assert len(products) > 0 # Fallback products list should not be empty
        assert "iPhone 15 Pro Max" in [p['name'] for p in products]
        mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error")

# --- Tests for search_products and _extract_price_from_keyword ---

def test_search_products_basic_keyword_match(mock_local_product_service_instance):
    """
    Test search_products with a basic keyword matching product names/descriptions.
    """
    service = mock_local_product_service_instance
    results = service.search_products("product a")
    assert len(results) == 2 # Product A and Product B (due to 'Product A related')
    assert results[0]['id'] == 'prod1' # Should be ranked higher due to exact name match

def test_search_products_case_insensitivity(mock_local_product_service_instance):
    """
    Test search_products with case-insensitive keyword.
    """
    service = mock_local_product_service_instance
    results = service.search_products("product B")
    assert len(results) == 1
    assert results[0]['id'] == 'prod2'

def test_search_products_no_match(mock_local_product_service_instance):
    """
    Test search_products with a keyword that doesn't match any product.
    """
    service = mock_local_product_service_instance
    results = service.search_products("nonexistent product")
    assert len(results) == 0

def test_search_products_with_limit(mock_local_product_service_instance):
    """
    Test search_products with a limit parameter.
    """
    service = mock_local_product_service_instance
    results = service.search_products("product", limit=1)
    assert len(results) == 1
    assert results[0]['id'] == 'prod1' # First ranked product

def test_search_products_keyword_in_category_brand_specs(mock_local_product_service_instance):
    """
    Test search_products finding keywords in category, brand, and specifications.
    """
    service = mock_local_product_service_instance
    results = service.search_products("BrandY") # Product B, Product F
    assert len(results) == 2
    assert 'prod2' in [p['id'] for p in results]
    assert 'prod6' in [p['id'] for p in results]
    
    results = service.search_products("Category3") # Product D
    assert len(results) == 1
    assert results[0]['id'] == 'prod4'

def test_search_products_price_extraction_juta(mock_local_product_service_instance):
    """
    Test search_products with price extraction from keyword (e.g., "juta").
    """
    service = mock_local_product_service_instance
    results = service.search_products("product 1 juta") # Should include products <= 1,000,000
    product_ids = {p['id'] for p in results}
    expected_ids = {'prod1', 'prod2', 'prod3', 'prod5'} # Product D, F are > 1 juta
    assert product_ids == expected_ids
    assert all(p['price'] <= 1000000 for p in results)

def test_search_products_price_extraction_ribu(mock_local_product_service_instance):
    """
    Test search_products with price extraction from keyword (e.g., "ribu").
    """
    service = mock_local_product_service_instance
    results = service.search_products("product 200 ribu") # Should include products <= 200,000
    product_ids = {p['id'] for p in results}
    expected_ids = {'prod1', 'prod2', 'prod3', 'prod5'}
    assert product_ids == expected_ids
    assert all(p['price'] <= 200000 for p in results)

def test_search_products_price_extraction_rp(mock_local_product_service_instance):
    """
    Test search_products with price extraction from keyword (e.g., "Rp X").
    """
    service = mock_local_product_service_instance
    results = service.search_products("product Rp 150000")
    product_ids = {p['id'] for p in results}
    expected_ids = {'prod1', 'prod3', 'prod5'}
    assert product_ids == expected_ids
    assert all(p['price'] <= 150000 for p in results)

def test_search_products_price_extraction_budget_keyword(mock_local_product_service_instance):
    """
    Test search_products with a budget keyword (e.g., "murah").
    """
    service = mock_local_product_service_instance
    results = service.search_products("gadget murah") # 'murah' corresponds to 5_000_000
    # Product D (5M), Product F (4M) - both match budget.
    # Product D also contains 'gadget' in description.
    product_ids = {p['id'] for p in results}
    expected_ids = {'prod1', 'prod2', 'prod3', 'prod4', 'prod5', 'prod6'} # all products are <= 5M
    assert product_ids == expected_ids
    assert all(p['price'] <= 5000000 for p in results)
    # Check sorting preference for budget searches
    # Prod3 (50k) should rank high due to lower price within budget
    assert results[0]['id'] == 'prod3' # Cheapest product, gets highest budget score

def test_search_products_error_handling(mock_local_product_service_instance, mock_logger):
    """
    Test error handling in search_products.
    """
    service = mock_local_product_service_instance
    # Simulate an error by modifying products list to cause an exception
    with patch.object(service, 'products', new=[{'id': 'bad_data', 'price': 'invalid'}]):
        results = service.search_products("test")
        assert results == []
        mock_logger.error.assert_called_once()
        assert "Error searching products:" in mock_logger.error.call_args[0][0]

def test_extract_price_from_keyword_juta():
    service = LocalProductService() # No need for mocked products for this method
    assert service._extract_price_from_keyword("harga 2 juta") == 2000000
    assert service._extract_price_from_keyword("10 juta") == 10000000

def test_extract_price_from_keyword_ribu():
    service = LocalProductService()
    assert service._extract_price_from_keyword("maksimal 500 ribu") == 500000
    assert service._extract_price_from_keyword("Rp 100 ribu") == 100000

def test_extract_price_from_keyword_rp():
    service = LocalProductService()
    assert service._extract_price_from_keyword("rp 250000") == 250000
    assert service._extract_price_from_keyword("150000 rp") == 150000

def test_extract_price_from_keyword_k_m():
    service = LocalProductService()
    assert service._extract_price_from_keyword("300k") == 300000
    assert service._extract_price_from_keyword("5m") == 5000000

def test_extract_price_from_keyword_budget_keywords():
    service = LocalProductService()
    assert service._extract_price_from_keyword("hp murah") == 5000000
    assert service._extract_price_from_keyword("laptop budget") == 5000000
    assert service._extract_price_from_keyword("headset hemat") == 3000000
    assert service._extract_price_from_keyword("monitor terjangkau") == 4000000
    assert service._extract_price_from_keyword("mouse ekonomis") == 2000000

def test_extract_price_from_keyword_no_match():
    service = LocalProductService()
    assert service._extract_price_from_keyword("no price here") is None
    assert service._extract_price_from_keyword("just a keyword") is None

def test_extract_price_from_keyword_error_handling(mock_logger):
    service = LocalProductService()
    with patch('re.search', side_effect=Exception("Regex error")):
        assert service._extract_price_from_keyword("1 juta") is None
        mock_logger.error.assert_called_once()
        assert "Error extracting price from keyword:" in mock_logger.error.call_args[0][0]

# --- Tests for get_product_details, get_categories, get_brands ---

def test_get_product_details_found(mock_local_product_service_instance):
    """
    Test retrieving details for an existing product ID.
    """
    service = mock_local_product_service_instance
    product = service.get_product_details("prod1")
    assert product is not None
    assert product['id'] == 'prod1'
    assert product['name'] == 'Product A'

def test_get_product_details_not_found(mock_local_product_service_instance):
    """
    Test retrieving details for a non-existent product ID.
    """
    service = mock_local_product_service_instance
    product = service.get_product_details("nonexistent_id")
    assert product is None

def test_get_product_details_empty_products_list(mock_logger):
    """
    Test get_product_details when the products list is empty.
    """
    # Create a LocalProductService instance, but patch its __init__ to avoid file system interaction
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
        service = LocalProductService()
        product = service.get_product_details("prod1")
        assert product is None
        mock_logger.error.assert_not_called() # No error should be logged

def test_get_product_details_error_handling(mock_local_product_service_instance, mock_logger):
    """
    Test error handling in get_product_details.
    """
    service = mock_local_product_service_instance
    # Simulate an error by making products attribute raise an exception on access
    with patch.object(service, 'products', new=MagicMock(side_effect=Exception("List iteration error"))):
        product = service.get_product_details("prod1")
        assert product is None
        mock_logger.error.assert_called_once()
        assert "Error getting product details:" in mock_logger.error.call_args[0][0]


def test_get_categories(mock_local_product_service_instance):
    """
    Test retrieving unique product categories.
    """
    service = mock_local_product_service_instance
    categories = service.get_categories()
    assert sorted(categories) == sorted(['Category1', 'Category2', 'Category3'])

def test_get_categories_empty_products_list():
    """
    Test get_categories when the products list is empty.
    """
    # Create a LocalProductService instance, but patch its __init__ to avoid file system interaction
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
        service = LocalProductService()
        categories = service.get_categories()
        assert categories == []

def test_get_categories_with_missing_category_key():
    """
    Test get_categories when some products are missing the 'category' key.
    """
    # Create a LocalProductService instance, but patch its __init__ to avoid file system interaction
    products_with_missing_cat = [
        {"id": "1", "name": "ProdA", "category": "Cat1"},
        {"id": "2", "name": "ProdB"}, # Missing category
        {"id": "3", "name": "ProdC", "category": "Cat2"},
    ]
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=products_with_missing_cat):
        service = LocalProductService()
        categories = service.get_categories()
        # An empty string is added if 'category' is missing, then sorted
        assert sorted(categories) == ['', 'Cat1', 'Cat2']

def test_get_brands(mock_local_product_service_instance):
    """
    Test retrieving unique product brands.
    """
    service = mock_local_product_service_instance
    brands = service.get_brands()
    assert sorted(brands) == sorted(['BrandX', 'BrandY', 'BrandZ'])

def test_get_brands_empty_products_list():
    """
    Test get_brands when the products list is empty.
    """
    # Create a LocalProductService instance, but patch its __init__ to avoid file system interaction
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
        service = LocalProductService()
        brands = service.get_brands()
        assert brands == []

def test_get_brands_with_missing_brand_key():
    """
    Test get_brands when some products are missing the 'brand' key.
    """
    # Create a LocalProductService instance, but patch its __init__ to avoid file system interaction
    products_with_missing_brand = [
        {"id": "1", "name": "ProdA", "brand": "Brand1"},
        {"id": "2", "name": "ProdB"}, # Missing brand
        {"id": "3", "name": "ProdC", "brand": "Brand2"},
    ]
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=products_with_missing_brand):
        service = LocalProductService()
        brands = service.get_brands()
        # An empty string is added if 'brand' is missing, then sorted
        assert sorted(brands) == ['', 'Brand1', 'Brand2']

# --- Tests for get_products_by_category/brand ---

def test_get_products_by_category_found(mock_local_product_service_instance):
    """
    Test retrieving products by an existing category.
    """
    service = mock_local_product_service_instance
    products = service.get_products_by_category("Category1")
    assert len(products) == 3
    assert all(p['category'] == 'Category1' for p in products)
    assert {'prod1', 'prod3', 'prod5'} == {p['id'] for p in products}

def test_get_products_by_category_case_insensitivity(mock_local_product_service_instance):
    """
    Test retrieving products by category with case-insensitivity.
    """
    service = mock_local_product_service_instance
    products = service.get_products_by_category("category1")
    assert len(products) == 3
    assert all(p['category'] == 'Category1' for p in products)

def test_get_products_by_category_not_found(mock_local_product_service_instance):
    """
    Test retrieving products by a non-existent category.
    """
    service = mock_local_product_service_instance
    products = service.get_products_by_category("NonExistentCategory")
    assert products == []

def test_get_products_by_category_empty_products_list(mock_logger):
    """
    Test get_products_by_category when the products list is empty.
    """
    # Create a LocalProductService instance, but patch its __init__ to avoid file system interaction
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
        service = LocalProductService()
        products = service.get_products_by_category("Category1")
        assert products == []
        mock_logger.error.assert_not_called()

def test_get_products_by_category_error_handling(mock_local_product_service_instance, mock_logger):
    """
    Test error handling in get_products_by_category.
    """
    service = mock_local_product_service_instance
    with patch.object(service, 'products', new=MagicMock(side_effect=Exception("List iteration error"))):
        products = service.get_products_by_category("Category1")
        assert products == []
        mock_logger.error.assert_called_once()
        assert "Error getting products by category:" in mock_logger.error.call_args[0][0]

def test_get_products_by_brand_found(mock_local_product_service_instance):
    """
    Test retrieving products by an existing brand.
    """
    service = mock_local_product_service_instance
    products = service.get_products_by_brand("BrandX")
    assert len(products) == 3
    assert all(p['brand'] == 'BrandX' for p in products)
    assert {'prod1', 'prod3', 'prod5'} == {p['id'] for p in products}

def test_get_products_by_brand_case_insensitivity(mock_local_product_service_instance):
    """
    Test retrieving products by brand with case-insensitivity.
    """
    service = mock_local_product_service_instance
    products = service.get_products_by_brand("brandx")
    assert len(products) == 3
    assert all(p['brand'] == 'BrandX' for p in products)

def test_get_products_by_brand_not_found(mock_local_product_service_instance):
    """
    Test retrieving products by a non-existent brand.
    """
    service = mock_local_product_service_instance
    products = service.get_products_by_brand("NonExistentBrand")
    assert products == []

def test_get_products_by_brand_empty_products_list(mock_logger):
    """
    Test get_products_by_brand when the products list is empty.
    """
    # Create a LocalProductService instance, but patch its __init__ to avoid file system interaction
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
        service = LocalProductService()
        products = service.get_products_by_brand("BrandX")
        assert products == []
        mock_logger.error.assert_not_called()

def test_get_products_by_brand_error_handling(mock_local_product_service_instance, mock_logger):
    """
    Test error handling in get_products_by_brand.
    """
    service = mock_local_product_service_instance
    with patch.object(service, 'products', new=MagicMock(side_effect=Exception("List iteration error"))):
        products = service.get_products_by_brand("BrandX")
        assert products == []
        mock_logger.error.assert_called_once()
        assert "Error getting products by brand:" in mock_logger.error.call_args[0][0]

# --- Tests for get_top_rated_products, get_best_selling_products, get_products ---

def test_get_top_rated_products(mock_local_product_service_instance):
    """
    Test retrieving top-rated products.
    """
    service = mock_local_product_service_instance
    products = service.get_top_rated_products(limit=3)
    assert len(products) == 3
    # Prod3 (4.9), Prod5 (4.6), Prod1 (4.5)
    assert products[0]['id'] == 'prod3'
    assert products[1]['id'] == 'prod5'
    assert products[2]['id'] == 'prod1'

def test_get_top_rated_products_limit_greater_than_available(mock_local_product_service_instance):
    """
    Test get_top_rated_products when limit is greater than available products.
    """
    service = mock_local_product_service_instance
    products = service.get_top_rated_products(limit=100)
    assert len(products) == len(TRANSFORMED_MOCK_PRODUCTS_DATA)
    # Still sorted by rating
    assert products[0]['id'] == 'prod3'

def test_get_top_rated_products_empty_products_list(mock_logger):
    """
    Test get_top_rated_products when the products list is empty.
    """
    # Create a LocalProductService instance, but patch its __init__ to avoid file system interaction
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
        service = LocalProductService()
        products = service.get_top_rated_products()
        assert products == []
        mock_logger.error.assert_not_called()

def test_get_top_rated_products_with_missing_rating_key():
    """
    Test get_top_rated_products when some products are missing the 'rating' key.
    """
    products_with_missing_rating = [
        {"id": "1", "specifications": {"rating": 5.0}},
        {"id": "2", "specifications": {}}, # Missing rating
        {"id": "3", "specifications": {"rating": 4.0}},
        {"id": "4", "specifications": {"sold": 100}}, # Missing specifications and rating
    ]
    # Create a LocalProductService instance, but patch its __init__ to avoid file system interaction
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=products_with_missing_rating):
        service = LocalProductService()
        products = service.get_top_rated_products(limit=3)
        assert len(products) == 3
        # Products with missing rating should default to 0 and be at the bottom
        assert products[0]['id'] == '1' # Rating 5.0
        assert products[1]['id'] == '3' # Rating 4.0
        # The order of '2' and '4' depends on their original order if ratings are equal (0)
        # Using a set to check for presence, or check both possibilities
        assert {products[2]['id'], products[1]['id'], products[0]['id']} == {'1', '3', '2'} or \
               {products[2]['id'], products[1]['id'], products[0]['id']} == {'1', '3', '4'}

def test_get_top_rated_products_error_handling(mock_local_product_service_instance, mock_logger):
    """
    Test error handling in get_top_rated_products.
    """
    service = mock_local_product_service_instance
    with patch.object(service, 'products', new=MagicMock(side_effect=Exception("Sorting error"))):
        products = service.get_top_rated_products()
        assert products == []
        mock_logger.error.assert_called_once()
        assert "Error getting top rated products:" in mock_logger.error.call_args[0][0]

def test_get_best_selling_products(mock_local_product_service_instance, mock_logger):
    """
    Test retrieving best-selling products.
    """
    service = mock_local_product_service_instance
    products = service.get_best_selling_products(limit=3)
    assert len(products) == 3
    # Prod5 (15000), Prod3 (1200), Prod1 (500)
    assert products[0]['id'] == 'prod5'
    assert products[1]['id'] == 'prod3'
    assert products[2]['id'] == 'prod1'
    mock_logger.info.assert_any_call("Getting best selling products, limit: 3")
    mock_logger.info.assert_any_call("Returning 3 best selling products")

def test_get_best_selling_products_limit_greater_than_available(mock_local_product_service_instance):
    """
    Test get_best_selling_products when limit is greater than available products.
    """
    service = mock_local_product_service_instance
    products = service.get_best_selling_products(limit=100)
    assert len(products) == len(TRANSFORMED_MOCK_PRODUCTS_DATA)
    # Still sorted by sold count
    assert products[0]['id'] == 'prod5'

def test_get_best_selling_products_empty_products_list(mock_logger):
    """
    Test get_best_selling_products when the products list is empty.
    """
    # Create a LocalProductService instance, but patch its __init__ to avoid file system interaction
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
        service = LocalProductService()
        products = service.get_best_selling_products()
        assert products == []
        mock_logger.error.assert_not_called()

def test_get_best_selling_products_with_missing_sold_key():
    """
    Test get_best_selling_products when some products are missing the 'sold' key.
    """
    products_with_missing_sold = [
        {"id": "1", "specifications": {"sold": 1000}},
        {"id": "2", "specifications": {}}, # Missing sold
        {"id": "3", "specifications": {"sold": 500}},
        {"id": "4", "specifications": {"rating": 4.0}}, # Missing specifications and sold
    ]
    # Create a LocalProductService instance, but patch its __init__ to avoid file system interaction
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=products_with_missing_sold):
        service = LocalProductService()
        products = service.get_best_selling_products(limit=3)
        assert len(products) == 3
        # Products with missing sold should default to 0 and be at the bottom
        assert products[0]['id'] == '1' # Sold 1000
        assert products[1]['id'] == '3' # Sold 500
        # The order of '2' and '4' depends on their original order if sold are equal (0)
        assert {products[2]['id'], products[1]['id'], products[0]['id']} == {'1', '3', '2'} or \
               {products[2]['id'], products[1]['id'], products[0]['id']} == {'1', '3', '4'}

def test_get_best_selling_products_error_handling(mock_local_product_service_instance, mock_logger):
    """
    Test error handling in get_best_selling_products.
    """
    service = mock_local_product_service_instance
    with patch.object(service, 'products', new=MagicMock(side_effect=Exception("Sorting error"))):
        products = service.get_best_selling_products()
        assert products == []
        mock_logger.error.assert_called_once()
        assert "Error getting best selling products:" in mock_logger.error.call_args[0][0]

def test_get_products(mock_local_product_service_instance, mock_logger):
    """
    Test retrieving all products with a limit.
    """
    service = mock_local_product_service_instance
    products = service.get_products(limit=3)
    assert len(products) == 3
    assert products == TRANSFORMED_MOCK_PRODUCTS_DATA[:3]
    mock_logger.info.assert_any_call("Getting all products, limit: 3")

def test_get_products_limit_greater_than_available(mock_local_product_service_instance):
    """
    Test get_products when limit is greater than available products.
    """
    service = mock_local_product_service_instance
    products = service.get_products(limit=100)
    assert len(products) == len(TRANSFORMED_MOCK_PRODUCTS_DATA)
    assert products == TRANSFORMED_MOCK_PRODUCTS_DATA

def test_get_products_empty_products_list(mock_logger):
    """
    Test get_products when the products list is empty.
    """
    # Create a LocalProductService instance, but patch its __init__ to avoid file system interaction
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
        service = LocalProductService()
        products = service.get_products()
        assert products == []
        mock_logger.error.assert_not_called()

def test_get_products_error_handling(mock_local_product_service_instance, mock_logger):
    """
    Test error handling in get_products.
    """
    service = mock_local_product_service_instance
    with patch.object(service, 'products', new=MagicMock(side_effect=Exception("List slicing error"))):
        products = service.get_products()
        assert products == []
        mock_logger.error.assert_called_once()
        assert "Error getting products:" in mock_logger.error.call_args[0][0]

# --- Tests for smart_search_products ---

def test_smart_search_products_best_request_general(mock_local_product_service_instance):
    """
    Test smart_search_products for general "terbaik" request.
    Should return top-rated products overall.
    """
    service = mock_local_product_service_instance
    products, message = service.smart_search_products(keyword="terbaik", limit=2)
    assert len(products) == 2
    assert products[0]['id'] == 'prod3' # Rating 4.9
    assert products[1]['id'] == 'prod5' # Rating 4.6
    assert message == "Berikut produk terbaik berdasarkan rating:"

def test_smart_search_products_best_request_specific_category_found(mock_local_product_service_instance):
    """
    Test smart_search_products for "terbaik" request within a specific category that exists.
    """
    service = mock_local_product_service_instance
    products, message = service.smart_search_products(keyword="terbaik Category1", category="Category1", limit=2)
    assert len(products) == 2
    # Products in Category1: prod1 (4.5), prod3 (4.9), prod5 (4.6)
    assert products[0]['id'] == 'prod3' # Rating 4.9
    assert products[1]['id'] == 'prod5' # Rating 4.6
    assert message == "Berikut Category1 terbaik berdasarkan rating:"

def test_smart_search_products_best_request_specific_category_not_found_fallback(mock_local_product_service_instance):
    """
    Test smart_search_products for "terbaik" request within a non-existent category.
    Should fallback to general top-rated products.
    """
    service = mock_local_product_service_instance
    products, message = service.smart_search_products(keyword="terbaik NonExistent", category="NonExistent", limit=2)
    assert len(products) == 2
    assert products[0]['id'] == 'prod3' # Rating 4.9 (general best)
    assert products[1]['id'] == 'prod5' # Rating 4.6 (general best)
    assert message == "Tidak ada produk kategori NonExistent, berikut produk terbaik secara umum:"

def test_smart_search_products_all_criteria_match(mock_local_product_service_instance):
    """
    Test smart_search_products where keyword, category, and max_price all match.
    """
    service = mock_local_product_service_instance
    products, message = service.smart_search_products(keyword="Product A", category="Category1", max_price=150000, limit=2)
    assert len(products) == 2
    # Products matching: prod1 (100k), prod5 (150k)
    assert {p['id'] for p in products} == {'prod1', 'prod5'}
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_products_no_exact_match_fallback_to_category(mock_local_product_service_instance):
    """
    Test smart_search_products when initial search has no results, but category match is found.
    """
    service = mock_local_product_service_instance
    # "NonExistingKeyword" will not match, but "Category2" will. Max_price too low for actual matches.
    products, message = service.smart_search_products(keyword="NonExistingKeyword", category="Category2", max_price=50000, limit=2)
    assert len(products) == 2
    # Products in Category2: prod2 (200k), prod6 (4M)
    assert products[0]['id'] == 'prod2' # Should be cheapest in Category2
    assert products[1]['id'] == 'prod6' # Next cheapest
    assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."

def test_smart_search_products_no_category_match_fallback_to_budget(mock_local_product_service_instance):
    """
    Test smart_search_products when no exact match and no category match, but budget match is found.
    """
    service = mock_local_product_service_instance
    # "NonExistingKeyword" and "NonExistingCategory" won't match. max_price will.
    products, message = service.smart_search_products(keyword="NonExistingKeyword", category="NonExistingCategory", max_price=150000, limit=2)
    assert len(products) == 2
    # Products within 150k: prod1 (100k), prod3 (50k), prod5 (150k)
    assert {p['id'] for p in products} == {'prod1', 'prod3', 'prod5'} # Should contain 2 of these
    assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

def test_smart_search_products_no_match_all_fallbacks_popular(mock_local_product_service_instance):
    """
    Test smart_search_products when no criteria match and all fallbacks lead to no results,
    should return popular products.
    """
    service = mock_local_product_service_instance
    products, message = service.smart_search_products(keyword="CompletelyUniqueKeyword", category="UnknownCategory", max_price=10, limit=2)
    assert len(products) == 2
    # Should be best-selling products: prod5 (15000), prod3 (1200)
    assert products[0]['id'] == 'prod5'
    assert products[1]['id'] == 'prod3'
    assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

def test_smart_search_products_empty_keyword_only_category(mock_local_product_service_instance):
    """
    Test smart_search_products with empty keyword, only category.
    """
    service = mock_local_product_service_instance
    products, message = service.smart_search_products(keyword="", category="Category1", limit=2)
    assert len(products) == 2
    # Should find all products in Category1, limit 2.
    assert {p['id'] for p in products} == {'prod1', 'prod3', 'prod5'} # Should contain 2 of these
    assert message == "Berikut produk yang sesuai dengan kriteria Anda." # Matches all criteria

def test_smart_search_products_empty_keyword_only_max_price(mock_local_product_service_instance):
    """
    Test smart_search_products with empty keyword, only max_price.
    """
    service = mock_local_product_service_instance
    products, message = service.smart_search_products(keyword="", max_price=150000, limit=2)
    assert len(products) == 2
    # Should find products <= 150k: prod1, prod3, prod5
    assert {p['id'] for p in products} == {'prod1', 'prod3', 'prod5'} # Should contain 2 of these
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_products_empty_all_filters(mock_local_product_service_instance):
    """
    Test smart_search_products with no filters (empty keyword, no category, no max_price).
    Should default to returning the first `limit` products from the loaded list.
    """
    service = mock_local_product_service_instance
    products, message = service.smart_search_products(keyword="", category=None, max_price=None, limit=2)
    assert len(products) == 2
    # Should return results based on initial filter criteria if any, else popular.
    # In this case, empty keyword, no category, no max_price means all products match.
    # So it should return the first `limit` products from `self.products`
    assert products == TRANSFORMED_MOCK_PRODUCTS_DATA[:2]
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."