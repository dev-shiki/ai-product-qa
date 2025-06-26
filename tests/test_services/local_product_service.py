import pytest
from unittest.mock import patch, mock_open, MagicMock, call
import logging
import json
import random
from typing import List, Dict
from pathlib import Path
import sys
import builtins # Added for patching open

# Add the parent directory of 'app' to the sys.path
# This allows imports like 'from app.services.local_product_service import LocalProductService'
# to work correctly when tests are run from a different root.
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.local_product_service import LocalProductService

# Mock data for testing
# MOCK_PRODUCTS_RAW_FOR_JSON represents the data structure *read from the JSON file*
MOCK_PRODUCTS_RAW_FOR_JSON = [
    {
        "id": "prod1",
        "name": "Product A",
        "category": "Category1",
        "brand": "BrandX",
        "price": 100000,
        "currency": "IDR",
        "description": "Description A. A very good product.",
        "specifications": {"rating": 4.5, "sold": 500, "stock_count": 100, "extra_spec": "value1"},
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
        "description": "Description B, also Product A related. A moderate product.",
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
        "price": 50000, # Cheapest product, high rating
        "currency": "IDR",
        "description": "Cheapest product, high quality. Very good.",
        "specifications": {"rating": 4.9, "sold": 1200, "stock_count": 200}, # Highest rated
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
        "description": "Expensive gadget. This is a very pricy item.",
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
        "description": "Best seller in Category1. Popular choice.",
        "specifications": {"rating": 4.6, "sold": 15000, "stock_count": 1000}, # Highest sold
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
        "description": "A budget friendly product. Very affordable.",
        "specifications": {"rating": 3.0, "sold": 50, "stock_count": 20},
        "availability": "in_stock",
        "reviews_count": 1,
        "images": ["url_f.jpg"],
        "url": "url_f"
    },
    # Add a product with minimal fields to test defaults in transformation
    {
        "id": "prod7",
        "name": "Minimal Product",
        "description": "This product has minimal details.",
    },
    # Add a product with custom spec that should be merged
    {
        "id": "prod8",
        "name": "Custom Spec Product",
        "category": "Electronics",
        "price": 750000,
        "specifications": {
            "custom_field": "custom_value",
            "rating": 4.2,
            "stock_count": 70,
        },
    }
]

# TRANSFORMED_MOCK_PRODUCTS_DATA represents the data structure *stored internally* by the service
# after loading and applying transformations (e.g., random sold count, default fields).
# The 'sold' count will be mocked to 1000 for deterministic tests in the fixture.
TRANSFORMED_MOCK_PRODUCTS_DATA = [
    {
        "id": "prod1", "name": "Product A", "category": "Category1", "brand": "BrandX", "price": 100000, "currency": "IDR", "description": "Description A. A very good product.",
        "specifications": {"rating": 4.5, "sold": 1000, "stock": 100, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandX Store", "extra_spec": "value1"},
        "availability": "in_stock", "reviews_count": 10, "images": ["https://example.com/prod1.jpg"], "url": "https://shopee.co.id/prod1"
    },
    {
        "id": "prod2", "name": "Product B", "category": "Category2", "brand": "BrandY", "price": 200000, "currency": "IDR", "description": "Description B, also Product A related. A moderate product.",
        "specifications": {"rating": 3.8, "sold": 1000, "stock": 50, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandY Store"},
        "availability": "out_of_stock", "reviews_count": 5, "images": ["https://example.com/prod2.jpg"], "url": "https://shopee.co.id/prod2"
    },
    {
        "id": "prod3", "name": "Product C", "category": "Category1", "brand": "BrandX", "price": 50000, "currency": "IDR", "description": "Cheapest product, high quality. Very good.",
        "specifications": {"rating": 4.9, "sold": 1000, "stock": 200, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandX Store"},
        "availability": "in_stock", "reviews_count": 20, "images": ["https://example.com/prod3.jpg"], "url": "https://shopee.co.id/prod3"
    },
    {
        "id": "prod4", "name": "Product D", "category": "Category3", "brand": "BrandZ", "price": 5000000, "currency": "IDR", "description": "Expensive gadget. This is a very pricy item.",
        "specifications": {"rating": 4.0, "sold": 1000, "stock": 10, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandZ Store"},
        "availability": "in_stock", "reviews_count": 2, "images": ["https://example.com/prod4.jpg"], "url": "https://shopee.co.id/prod4"
    },
    {
        "id": "prod5", "name": "Product E (Best Seller)", "category": "Category1", "brand": "BrandX", "price": 150000, "currency": "IDR", "description": "Best seller in Category1. Popular choice.",
        "specifications": {"rating": 4.6, "sold": 1000, "stock": 1000, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandX Store"},
        "availability": "in_stock", "reviews_count": 150, "images": ["https://example.com/prod5.jpg"], "url": "https://shopee.co.id/prod5"
    },
    {
        "id": "prod6", "name": "Product F (Budget)", "category": "Category2", "brand": "BrandY", "price": 4000000, "currency": "IDR", "description": "A budget friendly product. Very affordable.",
        "specifications": {"rating": 3.0, "sold": 1000, "stock": 20, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandY Store"},
        "availability": "in_stock", "reviews_count": 1, "images": ["https://example.com/prod6.jpg"], "url": "https://shopee.co.id/prod6"
    },
    {   # prod7 - minimal fields
        "id": "prod7", "name": "Minimal Product", "category": "", "brand": "", "price": 0, "currency": "IDR", "description": "This product has minimal details.",
        "specifications": {"rating": 0, "sold": 1000, "stock": 0, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "Unknown Store"},
        "availability": "in_stock", "reviews_count": 0, "images": ["https://example.com/prod7.jpg"], "url": "https://shopee.co.id/prod7"
    },
    {   # prod8 - custom spec
        "id": "prod8", "name": "Custom Spec Product", "category": "Electronics", "brand": "", "price": 750000, "currency": "IDR", "description": "",
        "specifications": {"rating": 4.2, "sold": 1000, "stock": 70, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "Unknown Store", "custom_field": "custom_value"},
        "availability": "in_stock", "reviews_count": 0, "images": ["https://example.com/prod8.jpg"], "url": "https://shopee.co.id/prod8"
    }
]


@pytest.fixture
def mock_local_product_service_instance():
    """
    Fixture to provide a LocalProductService instance with pre-defined mock products,
    bypassing the file loading mechanism for most tests.
    Also mocks random.randint for deterministic 'sold' values during transformation.
    """
    with patch('random.randint', return_value=1000), \
         patch('app.services.local_product_service.LocalProductService._load_local_products',
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
    with patch('random.randint', return_value=1000), \
         patch('app.services.local_product_service.LocalProductService._load_local_products',
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
        # This mocks the entire path construction: Path(__file__).parent.parent.parent / "data" / "products.json"
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path
        
        # Create an instance to call the internal method
        # Note: We need a real instance to call _load_local_products, not a mock of the class.
        service = LocalProductService() 
        result = service._load_local_products()
        
        mock_logger.error.assert_called_once()
        assert "Products JSON file not found at:" in mock_logger.error.call_args[0][0]
        mock_fallback.assert_called_once()
        assert result == mock_fallback.return_value # Ensure fallback products are returned

def test_load_local_products_valid_json_utf8(mock_logger):
    """
    Test _load_local_products with a valid UTF-8 JSON file.
    """
    mock_json_content = json.dumps({"products": MOCK_PRODUCTS_RAW_FOR_JSON})
    
    with patch('app.services.local_product_service.Path') as MockPath, \
         patch('builtins.open', mock_open(read_data=mock_json_content)), \
         patch('random.randint', return_value=1000): # Mock random.randint for predictable sold count
        
        # Simulate the Path resolution
        mock_file_path = MagicMock(spec=Path)
        mock_file_path.exists.return_value = True
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path

        # Create an instance to call the internal method
        service = LocalProductService() 
        products = service._load_local_products()
        
        assert len(products) == len(TRANSFORMED_MOCK_PRODUCTS_DATA)
        # Compare to the TRANSFORMED_MOCK_PRODUCTS_DATA
        assert products == TRANSFORMED_MOCK_PRODUCTS_DATA
        mock_logger.info.assert_any_call(f"Successfully loaded {len(TRANSFORMED_MOCK_PRODUCTS_DATA)} products from JSON file using utf-8 encoding")
        
        # Verify that open was called with utf-8 encoding (and potentially others if previous ones failed)
        # It's important to check the *last* successful call's encoding.
        assert builtins.open.call_args.kwargs['encoding'] == 'utf-8'

def test_load_local_products_valid_json_utf16le_with_bom(mock_logger):
    """
    Test _load_local_products with a valid UTF-16-LE JSON file containing a BOM.
    """
    mock_json_content_str = json.dumps({"products": MOCK_PRODUCTS_RAW_FOR_JSON})
    
    # Create a mock for Path that points to a file that exists
    mock_file_path = MagicMock(spec=Path)
    mock_file_path.exists.return_value = True
    
    # Define a side_effect function for mock_open to control encoding attempts
    # This simulates trying encodings in order and one succeeding.
    def open_side_effect(file_path_arg, mode, encoding):
        m_file = MagicMock()
        if encoding == 'utf-16-le':
            # This simulates reading a file that *was* UTF-16-LE with BOM,
            # and `file.read()` returns the decoded string (which still has the BOM char at start).
            m_file.read.return_value = '\ufeff' + mock_json_content_str
        elif encoding == 'utf-16': # Make it fail so utf-16-le is tested
            raise UnicodeDecodeError("mockcodec", b"", 0, 1, "mock reason for utf-16")
        else:
            # For other encodings, return content that will cause JSONDecodeError
            # (they shouldn't be reached if utf-16-le succeeds)
            m_file.read.return_value = "invalid json"
        return m_file

    with patch('app.services.local_product_service.Path') as MockPath, \
         patch('builtins.open', side_effect=open_side_effect), \
         patch('random.randint', return_value=1000):
        
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path

        service = LocalProductService()
        products = service._load_local_products()
        
        assert len(products) == len(TRANSFORMED_MOCK_PRODUCTS_DATA)
        assert products == TRANSFORMED_MOCK_PRODUCTS_DATA
        
        # Verify open was called with 'utf-16-le' and succeeded, and it was the first attempt.
        assert builtins.open.call_args_list[0].kwargs['encoding'] == 'utf-16-le'
        mock_logger.info.assert_any_call(f"Successfully loaded {len(TRANSFORMED_MOCK_PRODUCTS_DATA)} products from JSON file using utf-16-le encoding")
        mock_logger.warning.assert_not_called() # No warnings if first attempt succeeds

def test_load_local_products_valid_json_utf8_sig_succeeds_after_utf8_fails(mock_logger):
    """
    Test _load_local_products where utf-8 fails with UnicodeDecodeError, but utf-8-sig succeeds.
    """
    mock_json_content_str = json.dumps({"products": MOCK_PRODUCTS_RAW_FOR_JSON})
    
    mock_file_path = MagicMock(spec=Path)
    mock_file_path.exists.return_value = True

    def open_side_effect(file_path_arg, mode, encoding):
        m_file = MagicMock()
        if encoding == 'utf-16-le':
            raise UnicodeDecodeError("mockcodec", b"", 0, 1, "mock reason for utf-16-le")
        elif encoding == 'utf-16':
            raise UnicodeDecodeError("mockcodec", b"", 0, 1, "mock reason for utf-16")
        elif encoding == 'utf-8':
            raise UnicodeDecodeError("mockcodec", b"", 0, 1, "mock reason for utf-8")
        elif encoding == 'utf-8-sig': # This one succeeds
            m_file.read.return_value = '\ufeff' + mock_json_content_str # Simulate BOM for utf-8-sig
            return m_file
        else:
            pytest.fail(f"Open called with unexpected encoding: {encoding}")

    with patch('app.services.local_product_service.Path') as MockPath, \
         patch('builtins.open', side_effect=open_side_effect), \
         patch('random.randint', return_value=1000):
        
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path

        service = LocalProductService() 
        products = service._load_local_products()
        
        assert len(products) == len(TRANSFORMED_MOCK_PRODUCTS_DATA)
        assert products == TRANSFORMED_MOCK_PRODUCTS_DATA
        
        mock_logger.info.assert_any_call(f"Successfully loaded {len(TRANSFORMED_MOCK_PRODUCTS_DATA)} products from JSON file using utf-8-sig encoding")
        # Verify warnings for previous failed attempts
        mock_logger.warning.assert_any_call(f"Failed to load with utf-16-le encoding: mockcodec: mock reason for utf-16-le")
        mock_logger.warning.assert_any_call(f"Failed to load with utf-16 encoding: mockcodec: mock reason for utf-16")
        mock_logger.warning.assert_any_call(f"Failed to load with utf-8 encoding: mockcodec: mock reason for utf-8")
        
        # Verify `open` calls order and count
        assert builtins.open.call_count == 4
        assert builtins.open.call_args_list[0].kwargs['encoding'] == 'utf-16-le'
        assert builtins.open.call_args_list[1].kwargs['encoding'] == 'utf-16'
        assert builtins.open.call_args_list[2].kwargs['encoding'] == 'utf-8'
        assert builtins.open.call_args_list[3].kwargs['encoding'] == 'utf-8-sig'

def test_load_local_products_valid_json_latin1_succeeds_after_others_fail(mock_logger):
    """
    Test _load_local_products where earlier encodings fail, but latin-1 succeeds.
    """
    mock_json_content_str = json.dumps({"products": MOCK_PRODUCTS_RAW_FOR_JSON})
    
    mock_file_path = MagicMock(spec=Path)
    mock_file_path.exists.return_value = True

    def open_side_effect(file_path_arg, mode, encoding):
        m_file = MagicMock()
        if encoding in ['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig']:
            raise UnicodeDecodeError("mockcodec", b"", 0, 1, f"mock reason for {encoding}")
        elif encoding == 'latin-1': # This one succeeds
            m_file.read.return_value = mock_json_content_str
            return m_file
        else:
            pytest.fail(f"Open called with unexpected encoding: {encoding}")

    with patch('app.services.local_product_service.Path') as MockPath, \
         patch('builtins.open', side_effect=open_side_effect), \
         patch('random.randint', return_value=1000):
        
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path

        service = LocalProductService() 
        products = service._load_local_products()
        
        assert len(products) == len(TRANSFORMED_MOCK_PRODUCTS_DATA)
        assert products == TRANSFORMED_MOCK_PRODUCTS_DATA
        
        mock_logger.info.assert_any_call(f"Successfully loaded {len(TRANSFORMED_MOCK_PRODUCTS_DATA)} products from JSON file using latin-1 encoding")
        # Verify warnings for previous failed attempts
        assert mock_logger.warning.call_count == 4
        assert any(f"Failed to load with {e} encoding" in call_args[0][0] for e in ['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig'] for call_args in mock_logger.warning.call_args_list)
        
        # Verify `open` calls order and count
        assert builtins.open.call_count == 5
        assert builtins.open.call_args_list[4].kwargs['encoding'] == 'latin-1'


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
        assert builtins.open.call_count == len(encodings)


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
        assert builtins.open.call_count == len(encodings)

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
        assert builtins.open.call_count == 1 # Only one call before IOError

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

def test_load_local_products_json_products_key_not_list(mock_logger):
    """
    Test _load_local_products with a valid JSON file where 'products' key is not a list.
    Should result in an empty list after .get('products', []).
    """
    mock_json_content = json.dumps({"products": "not_a_list"}) # 'products' key exists but is not a list
    
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

def test_load_local_products_transformation_minimal_fields(mock_logger):
    """
    Test _load_local_products transformation with a product having only minimal fields.
    Ensures default values are correctly applied.
    """
    minimal_product_raw = {
        "id": "minimal_prod",
        "name": "Minimal Product",
        "description": "This product has minimal details."
    }
    expected_transformed = {
        "id": "minimal_prod",
        "name": "Minimal Product",
        "category": "",
        "brand": "",
        "price": 0,
        "currency": "IDR",
        "description": "This product has minimal details.",
        "specifications": {
            "rating": 0,
            "sold": 1000, # Mocked random.randint value
            "stock": 0,
            "condition": "Baru",
            "shop_location": "Indonesia",
            "shop_name": "Unknown Store",
        },
        "availability": "in_stock",
        "reviews_count": 0,
        "images": ["https://example.com/minimal_prod.jpg"],
        "url": "https://shopee.co.id/minimal_prod"
    }
    mock_json_content = json.dumps({"products": [minimal_product_raw]})

    with patch('app.services.local_product_service.Path') as MockPath, \
         patch('builtins.open', mock_open(read_data=mock_json_content)), \
         patch('random.randint', return_value=1000):
        
        mock_file_path = MagicMock(spec=Path)
        mock_file_path.exists.return_value = True
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path

        service = LocalProductService()
        products = service._load_local_products()
        
        assert len(products) == 1
        assert products[0] == expected_transformed

def test_load_local_products_transformation_with_extra_spec_fields(mock_logger):
    """
    Test _load_local_products transformation ensures extra fields in 'specifications' are preserved.
    """
    product_with_custom_specs_raw = {
        "id": "custom_spec_prod",
        "name": "Product with Custom Specs",
        "specifications": {
            "rating": 4.2,
            "stock_count": 70,
            "custom_field": "custom_value",
            "another_custom": True,
        },
        "brand": "CustomBrand"
    }
    expected_transformed_spec = {
        "rating": 4.2,
        "sold": 1000,
        "stock": 70,
        "condition": "Baru",
        "shop_location": "Indonesia",
        "shop_name": "CustomBrand Store",
        "custom_field": "custom_value",
        "another_custom": True,
    }
    mock_json_content = json.dumps({"products": [product_with_custom_specs_raw]})

    with patch('app.services.local_product_service.Path') as MockPath, \
         patch('builtins.open', mock_open(read_data=mock_json_content)), \
         patch('random.randint', return_value=1000):
        
        mock_file_path = MagicMock(spec=Path)
        mock_file_path.exists.return_value = True
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path

        service = LocalProductService()
        products = service._load_local_products()
        
        assert len(products) == 1
        assert products[0]['id'] == 'custom_spec_prod'
        assert products[0]['specifications'] == expected_transformed_spec

def test_load_local_products_transformation_product_not_dict_causes_error(mock_logger):
    """
    Test _load_local_products when a product entry in the JSON list is not a dictionary.
    This should cause an AttributeError during transformation and be caught by the general exception handler.
    """
    malformed_products_raw = [
        MOCK_PRODUCTS_RAW_FOR_JSON[0],
        "this is not a product dict", # Malformed entry
        MOCK_PRODUCTS_RAW_FOR_JSON[1]
    ]
    mock_json_content = json.dumps({"products": malformed_products_raw})

    with patch('app.services.local_product_service.Path') as MockPath, \
         patch('builtins.open', mock_open(read_data=mock_json_content)), \
         patch('random.randint', return_value=1000), \
         patch('app.services.local_product_service.LocalProductService._get_fallback_products') as mock_fallback:
        
        mock_file_path = MagicMock(spec=Path)
        mock_file_path.exists.return_value = True
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path

        service = LocalProductService()
        products = service._load_local_products()
        
        # The transformation loop will try to call .get() on a string, which raises AttributeError.
        # This will be caught by the outer 'except Exception as e:'.
        mock_logger.error.assert_called_once()
        assert "Error loading products from JSON file: 'str' object has no attribute 'get'" in mock_logger.error.call_args[0][0]
        mock_fallback.assert_called_once()
        assert products == mock_fallback.return_value

def test_load_local_products_first_encoding_succeeds_others_not_tried(mock_logger):
    """
    Test that once an encoding succeeds, no further encoding attempts are made.
    """
    mock_json_content = json.dumps({"products": MOCK_PRODUCTS_RAW_FOR_JSON})
    
    mock_file_path = MagicMock(spec=Path)
    mock_file_path.exists.return_value = True

    # Simulate utf-8 succeeding immediately
    def open_side_effect(file_path_arg, mode, encoding):
        if encoding == 'utf-16-le': # First attempt, fail
            raise UnicodeDecodeError("mockcodec", b"", 0, 1, "mock reason")
        elif encoding == 'utf-16': # Second attempt, fail
            raise UnicodeDecodeError("mockcodec", b"", 0, 1, "mock reason")
        elif encoding == 'utf-8': # Third attempt, succeed
            m_file = MagicMock()
            m_file.read.return_value = mock_json_content
            return m_file
        else: # Should not be called
            pytest.fail(f"Open called with unexpected encoding: {encoding}")

    with patch('app.services.local_product_service.Path') as MockPath, \
         patch('builtins.open', side_effect=open_side_effect), \
         patch('random.randint', return_value=1000):
        
        MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file_path

        service = LocalProductService() 
        products = service._load_local_products()
        
        assert len(products) == len(TRANSFORMED_MOCK_PRODUCTS_DATA)
        mock_logger.info.assert_any_call(f"Successfully loaded {len(TRANSFORMED_MOCK_PRODUCTS_DATA)} products from JSON file using utf-8 encoding")
        mock_logger.warning.assert_any_call("Failed to load with utf-16-le encoding: mockcodec: mock reason")
        mock_logger.warning.assert_any_call("Failed to load with utf-16 encoding: mockcodec: mock reason")
        assert mock_logger.warning.call_count == 2
        
        # Verify open was called exactly 3 times (utf-16-le, utf-16, utf-8)
        assert builtins.open.call_count == 3
        assert builtins.open.call_args_list[0].kwargs['encoding'] == 'utf-16-le'
        assert builtins.open.call_args_list[1].kwargs['encoding'] == 'utf-16'
        assert builtins.open.call_args_list[2].kwargs['encoding'] == 'utf-8'


def test_get_fallback_products(mock_logger):
    """
    Test the _get_fallback_products method directly.
    """
    # Create a LocalProductService instance, but patch its __init__ to avoid file system interaction
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
        service = LocalProductService()
        products = service._get_fallback_products()
        
        assert isinstance(products, list)
        assert len(products) == 8 # Fallback products list should contain 8 items
        assert "iPhone 15 Pro Max" in [p['name'] for p in products]
        mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error")

# --- Tests for search_products and _extract_price_from_keyword ---

def test_search_products_basic_keyword_match(mock_local_product_service_instance):
    """
    Test search_products with a basic keyword matching product names/descriptions.
    """
    service = mock_local_product_service_instance
    results = service.search_products("product a")
    assert len(results) == 2 # Product A and Product B (due to 'Product A related.')
    assert results[0]['id'] == 'prod1' # Should be ranked higher due to exact name match

def test_search_products_case_insensitivity(mock_local_product_service_instance):
    """
    Test search_products with case-insensitive keyword.
    """
    service = mock_local_product_service_instance
    results = service.search_products("product b")
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
    assert results[0]['id'] == 'prod1' # First ranked product (Product A)

def test_search_products_limit_zero(mock_local_product_service_instance):
    """
    Test search_products with a limit of 0.
    """
    service = mock_local_product_service_instance
    results = service.search_products("product", limit=0)
    assert len(results) == 0

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

    results = service.search_products("value1") # Product A (extra_spec: value1)
    assert len(results) == 1
    assert results[0]['id'] == 'prod1'

def test_search_products_price_extraction_juta(mock_local_product_service_instance):
    """
    Test search_products with price extraction from keyword (e.g., "juta").
    """
    service = mock_local_product_service_instance
    results = service.search_products("product 1 juta") # Should include products <= 1,000,000
    product_ids = {p['id'] for p in results}
    expected_ids = {'prod1', 'prod2', 'prod3', 'prod5', 'prod8', 'prod7'} # Product D, F are > 1 juta
    assert product_ids == expected_ids
    assert all(p['price'] <= 1000000 for p in results)
    
    # Check sorting for relevance with price filter
    # Prod1, prod2, prod3, prod5 contain "product" in name/desc. prod7, prod8 don't.
    # Among prod1,prod2,prod3,prod5, prod1 has highest score due to "Product A" exact match
    assert results[0]['id'] == 'prod1' # "Product A" match
    
    # After Prod1, Prod2, Prod3, Prod5.prod7 (price 0) and prod3 (price 50k) would be high due to budget score.
    # The order of products with same score is stable but not guaranteed based on attributes.

def test_search_products_price_extraction_ribu(mock_local_product_service_instance):
    """
    Test search_products with price extraction from keyword (e.g., "ribu").
    """
    service = mock_local_product_service_instance
    results = service.search_products("product 200 ribu") # Should include products <= 200,000
    product_ids = {p['id'] for p in results}
    expected_ids = {'prod1', 'prod2', 'prod3', 'prod5', 'prod7'}
    assert product_ids == expected_ids
    assert all(p['price'] <= 200000 for p in results)

def test_search_products_price_extraction_rp(mock_local_product_service_instance):
    """
    Test search_products with price extraction from keyword (e.g., "Rp X").
    """
    service = mock_local_product_service_instance
    results = service.search_products("product Rp 150000")
    product_ids = {p['id'] for p in results}
    expected_ids = {'prod1', 'prod3', 'prod5', 'prod7'}
    assert product_ids == expected_ids
    assert all(p['price'] <= 150000 for p in results)

def test_search_products_price_extraction_k_m(mock_local_product_service_instance):
    """
    Test search_products with price extraction from keyword (e.g., "Xk", "Xm").
    """
    service = mock_local_product_service_instance
    results = service.search_products("product 300k") # Should include products <= 300,000
    product_ids = {p['id'] for p in results}
    expected_ids = {'prod1', 'prod2', 'prod3', 'prod5', 'prod7'}
    assert product_ids == expected_ids
    assert all(p['price'] <= 300000 for p in results)

    results = service.search_products("gadget 5M") # Should include products <= 5,000,000
    product_ids = {p['id'] for p in results}
    expected_ids = {'prod1', 'prod2', 'prod3', 'prod4', 'prod5', 'prod6', 'prod7', 'prod8'}
    assert product_ids == expected_ids
    assert all(p['price'] <= 5000000 for p in results)

def test_search_products_price_extraction_budget_keyword(mock_local_product_service_instance):
    """
    Test search_products with a budget keyword (e.g., "murah").
    The 'murah' keyword itself affects the relevance score by adding a price preference.
    """
    service = mock_local_product_service_instance
    results = service.search_products("gadget murah") 
    # 'murah' corresponds to 5_000_000 max_price.
    # Prod4 contains 'gadget' in description.
    # All products have price <= 5M.
    # Sorting by relevance: score based on keyword match + price preference.
    
    # We expect 'prod4' (gadget match) and 'prod7', 'prod3' (cheapest) to be among top results.
    # Exact ordering can depend on tie-breaking in sort, so we check for presence among top.
    
    product_ids = {p['id'] for p in results}
    expected_ids = {'prod1', 'prod2', 'prod3', 'prod4', 'prod5', 'prod6', 'prod7', 'prod8'}
    assert product_ids == expected_ids
    assert all(p['price'] <= 5000000 for p in results)

    # Specific check for top elements to reflect sorting by relevance
    # Prod4 has keyword "gadget" and is within budget.
    # Prod7 and Prod3 are very cheap, giving them high budget score.
    top_ids = {p['id'] for p in results[:3]}
    assert 'prod4' in top_ids
    assert 'prod7' in top_ids
    assert 'prod3' in top_ids

def test_search_products_price_and_keyword_combined_without_budget_keyword(mock_local_product_service_instance):
    """
    Test search_products with a numerical price limit and a keyword,
    ensuring price filtering applies and sorting is by relevance (keyword first).
    """
    service = mock_local_product_service_instance
    results = service.search_products("Product A 100 ribu") # Max price 100,000
    
    assert len(results) == 2 # Only prod1 (price 100k) and prod7 (price 0) should match price
    
    # Both 'prod1' (100k) and 'prod7' (0k) are <= 100k.
    # 'prod1' has "Product A" in name (score 10). 'prod7' has no relevant keyword match.
    assert results[0]['id'] == 'prod1' # Higher relevance score due to keyword
    assert results[1]['id'] == 'prod7' # Lower relevance score, only price match


def test_search_products_relevance_sorting_exact_match(mock_local_product_service_instance):
    """
    Verify that exact name matches give higher relevance scores.
    """
    service = mock_local_product_service_instance
    results = service.search_products("good") # Prod1 ('good product'), Prod3 ('Very good')

    assert len(results) == 2
    # The order depends on how 'good' exactly matches. 'Very good' and 'A very good product'
    # Prod1 description: "Description A. A very good product."
    # Prod3 description: "Cheapest product, high quality. Very good."
    # Both should get score from description match. Prod3 also has rating 4.9.
    # The default tie-breaking is stable. Let's just check both are present.
    assert {p['id'] for p in results} == {'prod1', 'prod3'}
    # The order might not be strictly predictable without more refined scoring or tie-breaking logic.
    # For now, asserting presence is sufficient.

def test_search_products_relevance_sorting_budget_preference(mock_local_product_service_instance):
    """
    Verify that for budget searches, lower priced items get a higher relevance score.
    """
    service = mock_local_product_service_instance
    results = service.search_products("product murah") # "murah" implies max_price 5M, and activates budget scoring
    
    # All products have "Product" in name/description.
    # They all get +10 or so for 'product' keyword match.
    # Then budget score is added: (10M - price) / 1M.
    # Prod7 (price 0) should get a huge boost: (10M - 0) / 1M = 10.
    # Prod3 (price 50k) should get a high boost: (10M - 50k) / 1M = 9.95.
    # Prod1 (price 100k) should get: (10M - 100k) / 1M = 9.9.
    
    assert len(results) == len(TRANSFORMED_MOCK_PRODUCTS_DATA) # All products match "product" and are <= 5M
    assert results[0]['id'] == 'prod7' # Cheapest, highest budget score
    assert results[1]['id'] == 'prod3' # Second cheapest
    assert results[2]['id'] == 'prod1' # Third cheapest (among those matching 'product')

def test_search_products_empty_keyword(mock_local_product_service_instance):
    """
    Test search_products with an empty keyword. Should return products up to limit, in default order (which is based on the internal list order).
    """
    service = mock_local_product_service_instance
    results = service.search_products("", limit=3)
    assert len(results) == 3
    # When keyword is empty, the `if keyword_lower in searchable_text` condition is essentially always true.
    # All products get added to `filtered_products`.
    # The relevance_score function for empty keyword_lower will just be based on price if budget keyword is present,
    # otherwise it will be 0 for all, and the order will be original list order due to stable sort.
    # In this case, no budget keyword, so order should be original.
    assert results[0]['id'] == 'prod1'
    assert results[1]['id'] == 'prod2'
    assert results[2]['id'] == 'prod3'


def test_search_products_error_handling(mock_local_product_service_instance, mock_logger):
    """
    Test error handling in search_products.
    """
    service = mock_local_product_service_instance
    # Simulate an error by modifying products list to cause an exception during iteration or access
    with patch.object(service, 'products', new=[{'id': 'bad_data', 'price': 'invalid'}]):
        results = service.search_products("test")
        assert results == []
        mock_logger.error.assert_called_once()
        assert "Error searching products:" in mock_logger.error.call_args[0][0]

def test_extract_price_from_keyword_juta():
    service = LocalProductService() # No need for mocked products for this method
    assert service._extract_price_from_keyword("harga 2 juta") == 2000000
    assert service._extract_price_from_keyword("10 juta") == 10000000
    assert service._extract_price_from_keyword("5.5 juta") is None # Only integer part extracted by regex
    assert service._extract_price_from_keyword("2Juta") == 2000000 # Case insensitive

def test_extract_price_from_keyword_ribu():
    service = LocalProductService()
    assert service._extract_price_from_keyword("maksimal 500 ribu") == 500000
    assert service._extract_price_from_keyword("Rp 100 ribu") == 100000
    assert service._extract_price_from_keyword("250Ribu") == 250000 # Case insensitive

def test_extract_price_from_keyword_rp():
    service = LocalProductService()
    assert service._extract_price_from_keyword("rp 250000") == 250000
    assert service._extract_price_from_keyword("150000 rp") == 150000
    assert service._extract_price_from_keyword("RP. 500000") == 500000 # Test with dot and different casing

def test_extract_price_from_keyword_k_m():
    service = LocalProductService()
    assert service._extract_price_from_keyword("300k") == 300000
    assert service._extract_price_from_keyword("5m") == 5000000
    assert service._extract_price_from_keyword("2.5m") is None # Only integer part extracted by regex
    assert service._extract_price_from_keyword("10K") == 10000 # Case insensitive

def test_extract_price_from_keyword_budget_keywords():
    service = LocalProductService()
    assert service._extract_price_from_keyword("hp murah") == 5000000
    assert service._extract_price_from_keyword("laptop budget") == 5000000
    assert service._extract_price_from_keyword("headset hemat") == 3000000
    assert service._extract_price_from_keyword("monitor terjangkau") == 4000000
    assert service._extract_price_from_keyword("mouse ekonomis") == 2000000
    assert service._extract_price_from_keyword("Harga Murah Banget") == 5000000 # Multiple words

def test_extract_price_from_keyword_no_match():
    service = LocalProductService()
    assert service._extract_price_from_keyword("no price here") is None
    assert service._extract_price_from_keyword("just a keyword") is None
    assert service._extract_price_from_keyword("10 dolar") is None # Unrecognized currency

def test_extract_price_from_keyword_multiple_patterns_first_match_wins():
    service = LocalProductService()
    # "1 juta" comes first in regex patterns than "murah" keyword.
    assert service._extract_price_from_keyword("laptop 1 juta murah") == 1000000
    # "500 ribu" is parsed by regex before "hemat" keyword.
    assert service._extract_price_from_keyword("mouse 500 ribu hemat") == 500000
    # "rp 20000" should match before "murah"
    assert service._extract_price_from_keyword("hp rp 20000 murah") == 20000

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
    assert sorted(categories) == sorted(['Category1', 'Category2', 'Category3', 'Electronics', '']) # '' for prod7, prod8 missing category

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
    assert sorted(brands) == sorted(['BrandX', 'BrandY', 'BrandZ', 'CustomBrand', '']) # '' for prod7, prod8 missing brand

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
    # Based on TRANSFORMED_MOCK_PRODUCTS_DATA ratings:
    # prod3 (4.9), prod5 (4.6), prod1 (4.5), prod8 (4.2), prod4 (4.0), prod2 (3.8), prod6 (3.0), prod7 (0)
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

def test_get_top_rated_products_limit_zero(mock_local_product_service_instance):
    """
    Test get_top_rated_products with a limit of 0.
    """
    service = mock_local_product_service_instance
    products = service.get_top_rated_products(limit=0)
    assert len(products) == 0

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
        {"id": "2", "specifications": {}}, # Missing rating (defaults to 0)
        {"id": "3", "specifications": {"rating": 4.0}},
        {"id": "4"}, # Missing 'specifications' dict entirely (defaults to 0 rating)
    ]
    # Create a LocalProductService instance, but patch its __init__ to avoid file system interaction
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=products_with_missing_rating):
        service = LocalProductService()
        products = service.get_top_rated_products(limit=3)
        assert len(products) == 3
        # Products with missing rating should default to 0 and be at the bottom
        assert products[0]['id'] == '1' # Rating 5.0
        assert products[1]['id'] == '3' # Rating 4.0
        # The third product should be either '2' or '4' (both have 0 rating). Order depends on stable sort.
        assert products[2]['id'] in {'2', '4'}

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
    Since `random.randint` is mocked in the fixture, all products in `service.products`
    will have a 'sold' count of 1000. To properly test sorting by 'sold' for
    `get_best_selling_products`, we temporarily override `service.products` with
    a list where 'sold' values are varied.
    """
    products_for_sold_test = [
        dict(p, specifications=dict(p['specifications'], sold=p['specifications'].get('sold', 0)))
        for p in TRANSFORMED_MOCK_PRODUCTS_DATA # Start with base transformed data
    ]
    # Manually adjust 'sold' values for deterministic testing of sorting by 'sold'
    for p in products_for_sold_test:
        if p['id'] == 'prod5': p['specifications']['sold'] = 15000 # Highest
        elif p['id'] == 'prod3': p['specifications']['sold'] = 1200 # Second highest
        elif p['id'] == 'prod1': p['specifications']['sold'] = 500 # Third highest
        elif p['id'] == 'prod2': p['specifications']['sold'] = 300
        elif p['id'] == 'prod4': p['specifications']['sold'] = 100
        elif p['id'] == 'prod6': p['specifications']['sold'] = 50
        elif p['id'] == 'prod7': p['specifications']['sold'] = 10 # Lowest
        elif p['id'] == 'prod8': p['specifications']['sold'] = 200 # In between

    service = mock_local_product_service_instance
    with patch.object(service, 'products', products_for_sold_test):
        products = service.get_best_selling_products(limit=3)
        assert len(products) == 3
        # Expected order based on adjusted sold counts
        assert products[0]['id'] == 'prod5' # sold=15000
        assert products[1]['id'] == 'prod3' # sold=1200
        assert products[2]['id'] == 'prod1' # sold=500
        mock_logger.info.assert_any_call("Getting best selling products, limit: 3")
        mock_logger.info.assert_any_call("Returning 3 best selling products")

def test_get_best_selling_products_limit_greater_than_available(mock_local_product_service_instance):
    """
    Test get_best_selling_products when limit is greater than available products.
    """
    products_for_sold_test = [
        dict(p, specifications=dict(p['specifications'], sold=p['specifications'].get('sold', 0)))
        for p in TRANSFORMED_MOCK_PRODUCTS_DATA
    ]
    for p in products_for_sold_test:
        if p['id'] == 'prod5': p['specifications']['sold'] = 15000
        elif p['id'] == 'prod3': p['specifications']['sold'] = 1200
        elif p['id'] == 'prod1': p['specifications']['sold'] = 500
        elif p['id'] == 'prod2': p['specifications']['sold'] = 300
        elif p['id'] == 'prod4': p['specifications']['sold'] = 100
        elif p['id'] == 'prod6': p['specifications']['sold'] = 50
        elif p['id'] == 'prod7': p['specifications']['sold'] = 10
        elif p['id'] == 'prod8': p['specifications']['sold'] = 200

    service = mock_local_product_service_instance
    with patch.object(service, 'products', products_for_sold_test):
        products = service.get_best_selling_products(limit=100)
        assert len(products) == len(TRANSFORMED_MOCK_PRODUCTS_DATA)
        # Still sorted by sold count
        assert products[0]['id'] == 'prod5'

def test_get_best_selling_products_limit_zero(mock_local_product_service_instance):
    """
    Test get_best_selling_products with a limit of 0.
    """
    service = mock_local_product_service_instance
    products = service.get_best_selling_products(limit=0)
    assert len(products) == 0

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
        {"id": "2", "specifications": {}}, # Missing sold (defaults to 0)
        {"id": "3", "specifications": {"sold": 500}},
        {"id": "4"}, # Missing 'specifications' dict entirely (defaults to 0 sold)
    ]
    # Create a LocalProductService instance, but patch its __init__ to avoid file system interaction
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=products_with_missing_sold):
        service = LocalProductService()
        products = service.get_best_selling_products(limit=3)
        assert len(products) == 3
        # Products with missing sold should default to 0 and be at the bottom
        assert products[0]['id'] == '1' # Sold 1000
        assert products[1]['id'] == '3' # Sold 500
        # The third product should be either '2' or '4' (both have 0 sold). Order depends on stable sort.
        assert products[2]['id'] in {'2', '4'}

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

def test_get_products_limit_zero(mock_local_product_service_instance):
    """
    Test get_products with a limit of 0.
    """
    service = mock_local_product_service_instance
    products = service.get_products(limit=0)
    assert len(products) == 0

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
    # Based on TRANSFORMED_MOCK_PRODUCTS_DATA ratings: prod3 (4.9), prod5 (4.6)
    assert products[0]['id'] == 'prod3' 
    assert products[1]['id'] == 'prod5' 
    assert message == "Berikut produk terbaik berdasarkan rating:"

def test_smart_search_products_best_request_english_keyword(mock_local_product_service_instance):
    """
    Test smart_search_products for general "best" request (English keyword).
    Should return top-rated products overall.
    """
    service = mock_local_product_service_instance
    products, message = service.smart_search_products(keyword="best", limit=2)
    assert len(products) == 2
    assert products[0]['id'] == 'prod3' 
    assert products[1]['id'] == 'prod5' 
    assert message == "Berikut produk terbaik berdasarkan rating:"


def test_smart_search_products_best_request_specific_category_found(mock_local_product_service_instance):
    """
    Test smart_search_products for "terbaik" request within a specific category that exists.
    """
    service = mock_local_product_service_instance
    products, message = service.smart_search_products(keyword="terbaik Category1", category="Category1", limit=2)
    assert len(products) == 2
    # Products in Category1: prod1 (4.5), prod3 (4.9), prod5 (4.6)
    assert products[0]['id'] == 'prod3' 
    assert products[1]['id'] == 'prod5' 
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
    The primary search path should be taken.
    """
    service = mock_local_product_service_instance
    products, message = service.smart_search_products(keyword="Product A", category="Category1", max_price=150000, limit=2)
    assert len(products) == 2
    # Products matching: prod1 (100k, Category1), prod5 (150k, Category1)
    # The internal search algorithm will filter first, then sort by relevance.
    # Keyword "Product A" matches prod1.
    expected_ids = {'prod1', 'prod5'}
    actual_ids = {p['id'] for p in products}
    assert actual_ids == expected_ids
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_products_no_exact_match_fallback_to_category(mock_local_product_service_instance):
    """
    Test smart_search_products when initial search has no results, but category match is found.
    Should sort by price within category.
    """
    service = mock_local_product_service_instance
    # "NonExistingKeyword" will not match, but "Category2" will. Max_price too low for initial match.
    products, message = service.smart_search_products(keyword="NonExistingKeyword", category="Category2", max_price=50000, limit=2)
    assert len(products) == 2
    # Products in Category2: prod2 (200k), prod6 (4M). Sorted by price: prod2, prod6
    assert products[0]['id'] == 'prod2' # Cheapest in Category2
    assert products[1]['id'] == 'prod6' # Next cheapest in Category2
    assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."

def test_smart_search_products_no_category_match_fallback_to_budget(mock_local_product_service_instance):
    """
    Test smart_search_products when no exact match and no category match, but budget match is found.
    """
    service = mock_local_product_service_instance
    # "NonExistingKeyword" and "NonExistingCategory" won't match. max_price will.
    products, message = service.smart_search_products(keyword="NonExistingKeyword", category="NonExistingCategory", max_price=150000, limit=2)
    assert len(products) == 2
    # Products within 150k: prod1 (100k), prod3 (50k), prod5 (150k), prod7 (0k)
    expected_ids_candidates = {'prod1', 'prod3', 'prod5', 'prod7'}
    actual_ids = {p['id'] for p in products}
    assert actual_ids.issubset(expected_ids_candidates) and len(actual_ids) == 2
    assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

def test_smart_search_products_no_match_all_fallbacks_popular(mock_local_product_service_instance):
    """
    Test smart_search_products when no criteria match and all fallbacks lead to no results,
    should return popular products.
    """
    service = mock_local_product_service_instance
    # Max price 10 will ensure no products match price criteria, and no keywords/categories match.
    # To test best-selling correctly, we need to inject products with varied 'sold' counts.
    products_for_sold_test = [
        dict(p, specifications=dict(p['specifications'], sold=p['specifications'].get('sold', 0)))
        for p in TRANSFORMED_MOCK_PRODUCTS_DATA
    ]
    for p in products_for_sold_test:
        if p['id'] == 'prod5': p['specifications']['sold'] = 15000
        elif p['id'] == 'prod3': p['specifications']['sold'] = 1200
        elif p['id'] == 'prod1': p['specifications']['sold'] = 500
        elif p['id'] == 'prod2': p['specifications']['sold'] = 300
        elif p['id'] == 'prod4': p['specifications']['sold'] = 100
        elif p['id'] == 'prod6': p['specifications']['sold'] = 50
        elif p['id'] == 'prod7': p['specifications']['sold'] = 10
        elif p['id'] == 'prod8': p['specifications']['sold'] = 200

    with patch.object(service, 'products', products_for_sold_test):
        products, message = service.smart_search_products(keyword="CompletelyUniqueKeyword", category="UnknownCategory", max_price=10, limit=2)
        assert len(products) == 2
        assert products[0]['id'] == 'prod5' # sold=15000
        assert products[1]['id'] == 'prod3' # sold=1200
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

def test_smart_search_products_empty_keyword_only_category(mock_local_product_service_instance):
    """
    Test smart_search_products with empty keyword, only category specified.
    Should go to the primary search path and filter by category, then return message.
    """
    service = mock_local_product_service_instance
    products, message = service.smart_search_products(keyword="", category="Category1", limit=2)
    assert len(products) == 2
    # Should find all products in Category1, limit 2. These are prod1, prod3, prod5.
    # The actual order might vary based on default sorting if keyword isn't active.
    # When keyword is empty, and no max_price, score is 0. So original list order applies due to stable sort.
    # prod1, prod3, prod5 are in Category1. Original order is prod1, then prod3, then prod5.
    assert products[0]['id'] == 'prod1'
    assert products[1]['id'] == 'prod3'
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_products_empty_keyword_only_max_price(mock_local_product_service_instance):
    """
    Test smart_search_products with empty keyword, only max_price specified.
    Should go to primary search path and filter by price.
    """
    service = mock_local_product_service_instance
    products, message = service.smart_search_products(keyword="", max_price=150000, limit=2)
    assert len(products) == 2
    # Should find products <= 150k: prod1, prod3, prod5, prod7
    # With empty keyword and max_price, price relevance is active.
    # prod7 (0k) -> prod3 (50k) -> prod1 (100k) -> prod5 (150k)
    assert products[0]['id'] == 'prod7'
    assert products[1]['id'] == 'prod3'
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_products_empty_all_filters(mock_local_product_service_instance):
    """
    Test smart_search_products with no filters (empty keyword, no category, no max_price).
    Should default to returning the first `limit` products from the loaded list (primary path).
    """
    service = mock_local_product_service_instance
    products, message = service.smart_search_products(keyword="", category=None, max_price=None, limit=2)
    assert len(products) == 2
    # Should return first `limit` products as all products match empty criteria.
    assert products == TRANSFORMED_MOCK_PRODUCTS_DATA[:2]
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_products_limit_zero(mock_local_product_service_instance):
    """
    Test smart_search_products with a limit of 0.
    """
    service = mock_local_product_service_instance
    products, message = service.smart_search_products(keyword="Product", limit=0)
    assert len(products) == 0
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    products, message = service.smart_search_products(keyword="terbaik", limit=0)
    assert len(products) == 0
    assert message == "Berikut produk terbaik berdasarkan rating:"

def test_smart_search_products_negative_limit(mock_local_product_service_instance):
    """
    Test smart_search_products with a negative limit. Python slicing handles this by returning an empty list.
    """
    service = mock_local_product_service_instance
    products, message = service.smart_search_products(keyword="Product", limit=-1)
    assert len(products) == 0
    assert message == "Berikut produk yang sesuai dengan kriteria Anda." # Message should still be primary success one

def test_smart_search_products_no_products_loaded(mock_logger):
    """
    Test smart_search_products when the internal products list is empty.
    Should return an empty list and a message indicating no products found.
    """
    # Create a LocalProductService instance with an empty products list
    with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
        service = LocalProductService()
        products, message = service.smart_search_products(keyword="any", category="any", max_price=100000)
        assert products == []
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
        # No error logged, as empty list is a valid state
        mock_logger.error.assert_not_called()