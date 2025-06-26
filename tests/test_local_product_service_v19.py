import pytest
import logging
import json
import random
import re
from typing import List, Dict, Optional
from pathlib import Path
from unittest.mock import mock_open, patch

# Adjust sys.path to allow importing from the app directory
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app.services.local_product_service import LocalProductService
sys.path.pop(0) # Clean up path after import

# --- Fixtures ---

@pytest.fixture
def caplog_level(caplog):
    """Set the logging level for tests to INFO to capture relevant messages."""
    caplog.set_level(logging.INFO)
    return caplog

@pytest.fixture
def mock_random_randint(mocker):
    """Mocks random.randint to return a predictable value (1234) for 'sold' count."""
    mocker.patch('random.randint', return_value=1234)

@pytest.fixture
def mock_products_data():
    """Provides a consistent set of products for testing service methods."""
    return [
        {
            "id": "1", "name": "Test iPhone 15 Pro", "category": "Smartphone", "brand": "Apple",
            "price": 25000000, "currency": "IDR", "description": "Powerful phone by Apple.",
            "specifications": {"rating": 4.8, "sold": 1250, "stock": 50},
            "availability": "in_stock", "reviews_count": 100,
            "images": ["url1"], "url": "product_url_1"
        },
        {
            "id": "2", "name": "Samsung Galaxy S24", "category": "Smartphone", "brand": "Samsung",
            "price": 15000000, "currency": "IDR", "description": "Android flagship with AI features.",
            "specifications": {"rating": 4.5, "sold": 900, "stock": 30},
            "availability": "in_stock", "reviews_count": 80,
            "images": ["url2"], "url": "product_url_2"
        },
        {
            "id": "3", "name": "MacBook Air M3", "category": "Laptop", "brand": "Apple",
            "price": 20000000, "currency": "IDR", "description": "Thin and light laptop for professionals.",
            "specifications": {"rating": 4.9, "sold": 500, "stock": 20},
            "availability": "in_stock", "reviews_count": 50,
            "images": ["url3"], "url": "product_url_3"
        },
        {
            "id": "4", "name": "Sony Headphones XM4", "category": "Audio", "brand": "Sony",
            "price": 3000000, "currency": "IDR", "description": "Industry-leading noise cancelling headphones.",
            "specifications": {"rating": 4.7, "sold": 2000, "stock": 100},
            "availability": "in_stock", "reviews_count": 120,
            "images": ["url4"], "url": "product_url_4"
        },
        {
            "id": "5", "name": "HP Pavilion Gaming", "category": "Laptop", "brand": "HP",
            "price": 12000000, "currency": "IDR", "description": "Budget gaming laptop.",
            "specifications": {"rating": 4.2, "sold": 700, "stock": 15},
            "availability": "in_stock", "reviews_count": 40,
            "images": ["url5"], "url": "product_url_5"
        },
        { # Product with missing keys for transformation test, and empty category/brand for tests
            "id": "6", "name": "Product Missing Keys", "category": "", "brand": "",
            "price": 100000,
            "specifications": {"stock_count": 5} # missing brand, description, rating
        },
        { # Product for specific specs test and high sold count
            "id": "7", "name": "Smart Watch", "category": "Wearable", "brand": "Xiaomi",
            "price": 500000, "description": "Budget smart watch with heart rate sensor.",
            "specifications": {"rating": 4.0, "sold": 3000, "stock": 200, "features": "heart rate"},
            "availability": "in_stock"
        }
    ]

@pytest.fixture
def mock_load_success(mocker, mock_products_data):
    """Mocks _load_local_products to return a predefined list of products,
    bypassing file system interactions for most tests."""
    mocker.patch.object(LocalProductService, '_load_local_products', return_value=mock_products_data)

@pytest.fixture
def mock_filesystem_for_load(tmp_path, mocker):
    """
    Sets up a mock filesystem for the _load_local_products method.
    It creates a dummy `data/products.json` inside `tmp_path` and
    mocks `Path(__file__)` so that its parent chain points to `tmp_path`.
    Returns the Path object to the `products.json` file in `tmp_path` for tests to manipulate.
    """
    # Create the dummy file structure: tmp_path/app/services/local_product_service.py
    # This simulates the location of the service file.
    dummy_app_dir = tmp_path / "app" / "services"
    dummy_app_dir.mkdir(parents=True, exist_ok=True)
    (dummy_app_dir / "local_product_service.py").touch()
    
    # Create the data directory for products.json
    products_json_dir = tmp_path / "data"
    products_json_dir.mkdir(exist_ok=True)
    products_json_path = products_json_dir / "products.json"

    # Mock Path(__file__) such that its parent.parent.parent resolves to tmp_path
    # This allows the `current_dir` calculation in LocalProductService to work correctly.
    mock_file_path_instance = mocker.Mock(spec=Path)
    mock_file_path_instance.parent.parent.parent.return_value = tmp_path

    # Patch the Path class constructor:
    # When Path() is called, if it's Path(__file__), return our mock instance.
    # Otherwise, let it behave normally (e.g., for Path.exists on the actual file).
    original_path_init = Path.__init__
    
    def mock_path_constructor(self_obj, *args, **kwargs):
        if len(args) > 0 and Path(args[0]).name == Path(__file__).name: # Check if it's the `__file__` path
            self_obj.__class__ = mock_file_path_instance.__class__ # Make it act like our mock
            self_obj.__dict__ = mock_file_path_instance.__dict__.copy()
        else:
            original_path_init(self_obj, *args, **kwargs)

    mocker.patch('pathlib.Path.__init__', autospec=True, side_effect=mock_path_constructor)
    # Patch the `__new__` method as well for completeness, as Path uses it.
    # This is often safer: mock the `Path` class directly.
    mocker.patch('app.services.local_product_service.Path', wraps=Path)
    
    # Now, configure the mock created by `Path(__file__)`.
    # This needs to be done *after* Path is patched, but *before* LocalProductService is instantiated.
    # The `mocker.patch` calls in a fixture automatically clean up.
    
    # Let's directly mock the specific path variable that `_load_local_products` uses.
    # This is more robust as it doesn't rely on the Path(__file__) logic to be perfectly mirrored.
    # Instead, we just mock the result of `current_dir / "data" / "products.json"`
    
    # Mock the Path class to return specific behavior for the products.json path
    mock_json_file_path_obj = mocker.Mock(spec=Path)
    mock_json_file_path_obj.exists.return_value = True # Default to file existing
    mock_json_file_path_obj.open.return_value.__enter__.return_value.read.return_value = "" # Default to empty content
    
    # Mock Path constructor so that when the specific products.json path is constructed,
    # we return our mock object. This is still tricky.
    
    # BEST APPROACH: Let the real Path object be created, and then mock its methods.
    # We will just manage the actual temp file.
    
    return products_json_path

@pytest.fixture
def service_with_mocked_products(mock_load_success):
    """Provides an instance of LocalProductService with mocked products loaded."""
    return LocalProductService()

# --- Tests for LocalProductService ---

class TestLocalProductServiceInitAndLoad:
    
    # Test __init__ with successful file load
    def test_init_success(self, mock_filesystem_for_load, mock_random_randint, caplog_level):
        json_content = json.dumps({
            "products": [
                {"id": "p1", "name": "Product A", "category": "Cat1", "brand": "BrandX", "price": 100, "stock_count": 10, "rating": 4.0},
                {"id": "p2", "name": "Product B", "category": "Cat2", "brand": "BrandY", "price": 200, "stock_count": 20, "rating": 3.5}
            ]
        })
        # Write content to the actual temporary file
        mock_filesystem_for_load.write_text(json_content, encoding='utf-8')
        
        service = LocalProductService()
        
        assert len(service.products) == 2
        assert service.products[0]['id'] == 'p1'
        assert service.products[0]['specifications']['sold'] == 1234 # From mock_random_randint
        assert "Loaded 2 local products from JSON file" in caplog_level.text
        assert "Successfully loaded 2 products from JSON file using utf-8 encoding" in caplog_level.text

    # Test __init__ when file does not exist
    def test_init_file_not_found(self, mock_filesystem_for_load, caplog_level, mocker):
        mock_filesystem_for_load.unlink(missing_ok=True) # Ensure file doesn't exist
        mocker.spy(LocalProductService, '_get_fallback_products') # Spy on fallback method
        
        service = LocalProductService()
        
        assert len(service.products) == 8 # Should load fallback products (8 from source)
        LocalProductService._get_fallback_products.assert_called_once()
        assert f"Products JSON file not found at: {mock_filesystem_for_load.as_posix()}" in caplog_level.text
        assert "Using fallback products due to JSON file loading error" in caplog_level.text

    # Test __init__ with invalid JSON content (JsonDecodeError)
    def test_init_invalid_json(self, mock_filesystem_for_load, caplog_level, mocker):
        mock_filesystem_for_load.write_text("this is not json", encoding='utf-8')
        mocker.spy(LocalProductService, '_get_fallback_products')
        
        service = LocalProductService()
        
        assert len(service.products) == 8 # Fallback products loaded
        LocalProductService._get_fallback_products.assert_called_once()
        assert "Failed to load with utf-8 encoding: Expecting value: line 1 column 1 (char 0)" in caplog_level.text
        assert "All encoding attempts failed, using fallback products" in caplog_level.text

    # Test __init__ with JSON missing 'products' key
    def test_init_json_missing_products_key(self, mock_filesystem_for_load, mock_random_randint, caplog_level):
        json_content = json.dumps({"items": [{"id": "p1"}]}) # Missing 'products' key
        mock_filesystem_for_load.write_text(json_content, encoding='utf-8')
        
        service = LocalProductService()
        
        assert len(service.products) == 0 # products list should be empty if 'products' key is not found
        assert "Successfully loaded 0 products from JSON file using utf-8 encoding" in caplog_level.text
        assert "Loaded 0 local products from JSON file" in caplog_level.text

    # Test __init__ with UnicodeDecodeError for all encodings
    def test_init_unicode_decode_error(self, mock_filesystem_for_load, caplog_level, mocker):
        # To simulate a file that causes UnicodeDecodeError, we'll write invalid bytes
        # or, more reliably, patch `builtins.open` to raise the error.
        mock_filesystem_for_load.unlink(missing_ok=True) # Ensure no real file interferes
        
        def mock_open_side_effect(file, mode='r', encoding=None, *args, **kwargs):
            # Simulate different errors for different encodings to hit all branches
            if encoding == 'utf-16-le':
                raise UnicodeDecodeError('utf-16-le', b'\xff', 0, 1, 'invalid byte')
            elif encoding == 'utf-16':
                raise UnicodeDecodeError('utf-16', b'\xfe', 0, 1, 'invalid byte')
            elif encoding == 'utf-8':
                raise UnicodeDecodeError('utf-8', b'\xf0\x28\x8c\xbc', 0, 1, 'invalid continuation byte')
            else: # For other encodings like latin-1, cp1252, just return empty content
                mock_file = mocker.mock_open(read_data='')
                return mock_file()
        
        mocker.patch('builtins.open', side_effect=mock_open_side_effect)
        # Ensure the Path.exists returns True so `open` is called
        mocker.patch.object(mock_filesystem_for_load, 'exists', return_value=True) 
        mocker.spy(LocalProductService, '_get_fallback_products')
        
        service = LocalProductService()
        
        assert len(service.products) == 8 # Fallback products loaded
        LocalProductService._get_fallback_products.assert_called_once()
        assert "Failed to load with utf-16-le encoding: " in caplog_level.text
        assert "Failed to load with utf-16 encoding: " in caplog_level.text
        assert "Failed to load with utf-8 encoding: " in caplog_level.text
        assert "All encoding attempts failed, using fallback products" in caplog_level.text

    # Test __init__ with a BOM in UTF-8 file
    def test_init_utf8_bom(self, mock_filesystem_for_load, mock_random_randint, caplog_level):
        json_content = '\ufeff' + json.dumps({ # Add UTF-8 BOM
            "products": [
                {"id": "p1", "name": "Product A", "category": "Cat1", "brand": "BrandX", "price": 100, "stock_count": 10, "rating": 4.0}
            ]
        })
        mock_filesystem_for_load.write_text(json_content, encoding='utf-8')
        
        service = LocalProductService()
        
        assert len(service.products) == 1
        assert "Successfully loaded 1 products from JSON file using utf-8 encoding" in caplog_level.text
        assert service.products[0]['id'] == 'p1'
        assert service.products[0]['name'] == 'Product A'

    # Test __init__ with a generic Exception during loading
    def test_init_generic_exception(self, mock_filesystem_for_load, caplog_level, mocker):
        # Simulate an error when checking file existence (e.g., permissions issues)
        mocker.patch.object(mock_filesystem_for_load, 'exists', side_effect=Exception("Permission denied during exists check"))
        mocker.spy(LocalProductService, '_get_fallback_products')
        
        service = LocalProductService()
        
        assert len(service.products) == 8 # Fallback products loaded
        LocalProductService._get_fallback_products.assert_called_once()
        assert "Error loading products from JSON file: Permission denied during exists check" in caplog_level.text
        assert "Using fallback products due to JSON file loading error" in caplog_level.text

    # Test transformation of product data, including default values and random sold
    def test_product_transformation(self, mock_filesystem_for_load, mock_random_randint, caplog_level):
        json_content = json.dumps({
            "products": [
                { # Fully provided
                    "id": "full1", "name": "Full Product", "category": "Electronics", "brand": "XYZ",
                    "price": 1000, "currency": "USD", "description": "Desc",
                    "stock_count": 50, "rating": 4.5, "specifications": {"color": "red", "weight": "1kg"},
                    "availability": "out_of_stock", "reviews_count": 10
                },
                { # Missing many fields, triggering defaults
                    "id": "missing1", "name": "Missing Product"
                }
            ]
        })
        mock_filesystem_for_load.write_text(json_content, encoding='utf-8')
        
        service = LocalProductService()
        
        assert len(service.products) == 2
        
        full_product = service.products[0]
        assert full_product['id'] == 'full1'
        assert full_product['name'] == 'Full Product'
        assert full_product['category'] == 'Electronics'
        assert full_product['brand'] == 'XYZ'
        assert full_product['price'] == 1000
        assert full_product['currency'] == 'USD'
        assert full_product['description'] == 'Desc'
        assert full_product['specifications']['rating'] == 4.5
        assert full_product['specifications']['sold'] == 1234 # Mocked random value
        assert full_product['specifications']['stock'] == 50
        assert full_product['specifications']['condition'] == 'Baru'
        assert full_product['specifications']['shop_location'] == 'Indonesia'
        assert full_product['specifications']['shop_name'] == 'XYZ Store'
        assert full_product['specifications']['color'] == 'red' # Merged from specifications
        assert full_product['specifications']['weight'] == '1kg'
        assert full_product['availability'] == 'out_of_stock'
        assert full_product['reviews_count'] == 10
        assert full_product['images'] == ["https://example.com/full1.jpg"]
        assert full_product['url'] == "https://shopee.co.id/full1"

        missing_product = service.products[1]
        assert missing_product['id'] == 'missing1'
        assert missing_product['name'] == 'Missing Product'
        assert missing_product['category'] == '' # Default
        assert missing_product['brand'] == '' # Default
        assert missing_product['price'] == 0 # Default
        assert missing_product['currency'] == 'IDR' # Default
        assert missing_product['description'] == '' # Default
        assert missing_product['specifications']['rating'] == 0 # Default
        assert missing_product['specifications']['sold'] == 1234
        assert missing_product['specifications']['stock'] == 0 # Default
        assert missing_product['specifications']['condition'] == 'Baru'
        assert missing_product['specifications']['shop_location'] == 'Indonesia'
        assert missing_product['specifications']['shop_name'] == 'Unknown Store' # Default brand
        assert missing_product['availability'] == 'in_stock' # Default
        assert missing_product['reviews_count'] == 0 # Default
        assert missing_product['images'] == ["https://example.com/missing1.jpg"]
        assert missing_product['url'] == "https://shopee.co.id/missing1"

class TestLocalProductServiceMethods:
    
    # Test _get_fallback_products
    def test_get_fallback_products(self, caplog_level):
        # Instantiate service, but then replace its products to ensure _get_fallback_products
        # is tested in isolation, as its normal call is from __init__.
        service = LocalProductService() 
        # To test _get_fallback_products directly without __init__ side effects,
        # we can temporarily replace the products list or test a new instance with a mocked `_load_local_products`.
        # More direct:
        fallback_products = service._get_fallback_products()
        assert len(fallback_products) == 8 # Based on the source code's fallback data
        assert fallback_products[0]['id'] == '1'
        assert "Using fallback products due to JSON file loading error" in caplog_level.text

    # Test search_products
    def test_search_products_by_name(self, service_with_mocked_products):
        results = service_with_mocked_products.search_products("iPhone")
        assert len(results) == 1
        assert results[0]['id'] == '1'

    def test_search_products_case_insensitive(self, service_with_mocked_products):
        results = service_with_mocked_products.search_products("iphone")
        assert len(results) == 1
        assert results[0]['id'] == '1'
        
    def test_search_products_by_brand(self, service_with_mocked_products):
        results = service_with_mocked_products.search_products("Samsung")
        assert len(results) == 1
        assert results[0]['id'] == '2'

    def test_search_products_by_category(self, service_with_mocked_products):
        results = service_with_mocked_products.search_products("Laptop")
        assert len(results) == 2
        assert {p['id'] for p in results} == {'3', '5'} # MacBook Air, HP Pavilion

    def test_search_products_by_description(self, service_with_mocked_products):
        results = service_with_mocked_products.search_products("flagship")
        assert len(results) == 1
        assert results[0]['id'] == '2' # Samsung Galaxy S24

    def test_search_products_by_specifications_content(self, service_with_mocked_products):
        results = service_with_mocked_products.search_products("heart rate")
        assert len(results) == 1
        assert results[0]['id'] == '7' # Smart Watch

    def test_search_products_no_match(self, service_with_mocked_products):
        results = service_with_mocked_products.search_products("NonExistentProduct")
        assert len(results) == 0

    def test_search_products_empty_keyword_returns_all_up_to_limit(self, service_with_mocked_products):
        # When keyword is empty, `keyword_lower in searchable_text` is always true.
        # Products are sorted by relevance, which will be 0 for all products if no keyword or price.
        # So it should return the first `limit` products in the original list.
        results = service_with_mocked_products.search_products("", limit=3)
        assert len(results) == 3
        # Assuming mock_products_data order is preserved in the absence of relevance.
        assert results[0]['id'] == '1' 
        assert results[1]['id'] == '2'
        assert results[2]['id'] == '3'
        
    def test_search_products_with_limit(self, service_with_mocked_products):
        results = service_with_mocked_products.search_products("Pro", limit=1) # iPhone 15 Pro, MacBook Air M3, HP Pavilion Gaming
        assert len(results) == 1
        assert results[0]['id'] == '1' # iPhone 15 Pro (highest relevance for "Pro" in name)
        
    def test_search_products_with_price_limit_juta(self, service_with_mocked_products):
        # Products <= 15M: Samsung S24 (15M), HP Pavilion (12M), Sony Headphones (3M), Smart Watch (0.5M), Prod Missing (0.1M)
        results = service_with_mocked_products.search_products("phone 15 juta") 
        assert len(results) == 2 # Samsung Galaxy S24 and HP Pavilion Gaming because of price limit
        # The price filter is applied first, then keyword search on remaining.
        # Both "Samsung Galaxy S24" and "HP Pavilion Gaming" have 'phone' or 'gaming' related text,
        # but the price filter applies to all products before keyword filtering for relevance.
        assert {p['id'] for p in results} == {'2', '5'} # Samsung Galaxy S24, HP Pavilion

    def test_search_products_with_price_limit_ribu_k(self, service_with_mocked_products):
        results = service_with_mocked_products.search_products("watch 500k") # Smart Watch (500k)
        assert len(results) == 1
        assert results[0]['id'] == '7'

    def test_search_products_with_budget_keyword(self, service_with_mocked_products):
        # 'murah' implies max_price 5M
        results = service_with_mocked_products.search_products("headphones murah")
        # Products <= 5M: Sony Headphones (3M), Smart Watch (0.5M), Product Missing Keys (0.1M)
        assert len(results) == 3
        # Ensure sorting prioritizes 'headphones' keyword then lower price for budget search
        assert results[0]['id'] == '4' # Sony Headphones (exact match for headphones, within budget, highest relevance from keyword score)
        assert results[1]['id'] == '7' # Smart Watch (within budget, lower price)
        assert results[2]['id'] == '6' # Product Missing Keys (within budget, lowest price)

    def test_search_products_error_handling(self, service_with_mocked_products, caplog_level, mocker):
        mocker.patch.object(service_with_mocked_products, '_extract_price_from_keyword', side_effect=Exception("Price extraction error"))
        results = service_with_mocked_products.search_products("any keyword")
        assert results == []
        assert "Error searching products: Price extraction error" in caplog_level.text

    # Test _extract_price_from_keyword
    def test_extract_price_juta(self, service_with_mocked_products):
        assert service_with_mocked_products._extract_price_from_keyword("harga 20 juta") == 20000000
        assert service_with_mocked_products._extract_price_from_keyword("1juta") == 1000000
        assert service_with_mocked_products._extract_price_from_keyword("5 m") == 5000000 # 'm' for million

    def test_extract_price_ribu(self, service_with_mocked_products):
        assert service_with_mocked_products._extract_price_from_keyword("di bawah 500 ribu") == 500000
        assert service_with_mocked_products._extract_price_from_keyword("100 k") == 100000

    def test_extract_price_rp_format(self, service_with_mocked_products):
        assert service_with_mocked_products._extract_price_from_keyword("maks rp 1500000") == 1500000
        assert service_with_mocked_products._extract_price_from_keyword("500000 rp") == 500000

    def test_extract_price_budget_keywords(self, service_with_mocked_products):
        assert service_with_mocked_products._extract_price_from_keyword("laptop murah") == 5000000
        assert service_with_mocked_products._extract_price_from_keyword("hp budget") == 5000000
        assert service_with_mocked_products._extract_price_from_keyword("earphone hemat") == 3000000
        assert service_with_mocked_products._extract_price_from_keyword("tablet terjangkau") == 4000000
        assert service_with_mocked_products._extract_price_from_keyword("speaker ekonomis") == 2000000

    def test_extract_price_no_match(self, service_with_mocked_products):
        assert service_with_mocked_products._extract_price_from_keyword("gaming pc") is None
        assert service_with_mocked_products._extract_price_from_keyword("") is None

    def test_extract_price_error_handling(self, service_with_mocked_products, caplog_level, mocker):
        mocker.patch('re.search', side_effect=Exception("Regex search failed"))
        result = service_with_mocked_products._extract_price_from_keyword("10 juta")
        assert result is None
        assert "Error extracting price from keyword: Regex search failed" in caplog_level.text

    # Test get_product_details
    def test_get_product_details_existing(self, service_with_mocked_products):
        product = service_with_mocked_products.get_product_details("1")
        assert product is not None
        assert product['name'] == 'Test iPhone 15 Pro'

    def test_get_product_details_non_existent(self, service_with_mocked_products):
        product = service_with_mocked_products.get_product_details("999")
        assert product is None

    def test_get_product_details_empty_id(self, service_with_mocked_products):
        product = service_with_mocked_products.get_product_details("")
        assert product is None

    def test_get_product_details_error_handling(self, service_with_mocked_products, caplog_level, mocker):
        # Simulate an error during iteration over self.products
        mocker.patch.object(service_with_mocked_products, 'products', side_effect=Exception("Data access error"))
        product = service_with_mocked_products.get_product_details("1")
        assert product is None
        assert "Error getting product details: Data access error" in caplog_level.text

    # Test get_categories
    def test_get_categories(self, service_with_mocked_products):
        categories = service_with_mocked_products.get_categories()
        expected_categories = sorted(['Smartphone', 'Laptop', 'Audio', 'Misc', 'Wearable', '']) # '' from missing keys product
        assert categories == expected_categories

    def test_get_categories_empty_products(self):
        service = LocalProductService() # Instantiate normally
        service.products = [] # Manually clear products for this test
        assert service.get_categories() == []

    def test_get_categories_missing_category_key(self, mocker):
        service = LocalProductService()
        service.products = [{"id": "p_nocat", "name": "No Category Product"}] # No 'category' key
        categories = service.get_categories()
        assert categories == [''] # Default empty string category should be collected

    # Test get_brands
    def test_get_brands(self, service_with_mocked_products):
        brands = service_with_mocked_products.get_brands()
        expected_brands = sorted(['Apple', 'Samsung', 'Sony', 'HP', 'Xiaomi', '']) # '' from missing keys product
        assert brands == expected_brands

    def test_get_brands_empty_products(self):
        service = LocalProductService()
        service.products = []
        assert service.get_brands() == []

    def test_get_brands_missing_brand_key(self, mocker):
        service = LocalProductService()
        service.products = [{"id": "p_nobrand", "name": "No Brand Product"}] # No 'brand' key
        brands = service.get_brands()
        assert brands == [''] # Default empty string brand should be collected

    # Test get_products_by_category
    def test_get_products_by_category_existing(self, service_with_mocked_products):
        results = service_with_mocked_products.get_products_by_category("Smartphone")
        assert len(results) == 2
        assert {p['id'] for p in results} == {'1', '2'}

    def test_get_products_by_category_case_insensitive(self, service_with_mocked_products):
        results = service_with_mocked_products.get_products_by_category("smartphone")
        assert len(results) == 2
        assert {p['id'] for p in results} == {'1', '2'}

    def test_get_products_by_category_non_existent(self, service_with_mocked_products):
        results = service_with_mocked_products.get_products_by_category("Furniture")
        assert len(results) == 0

    def test_get_products_by_category_empty_string(self, service_with_mocked_products):
        # Product Missing Keys has empty category
        results = service_with_mocked_products.get_products_by_category("")
        assert len(results) == 1
        assert results[0]['id'] == '6'

    def test_get_products_by_category_error_handling(self, service_with_mocked_products, caplog_level, mocker):
        mocker.patch.object(service_with_mocked_products, 'products', side_effect=Exception("Iteration error"))
        results = service_with_mocked_products.get_products_by_category("Smartphone")
        assert results == []
        assert "Error getting products by category: Iteration error" in caplog_level.text

    # Test get_products_by_brand
    def test_get_products_by_brand_existing(self, service_with_mocked_products):
        results = service_with_mocked_products.get_products_by_brand("Apple")
        assert len(results) == 2
        assert {p['id'] for p in results} == {'1', '3'}

    def test_get_products_by_brand_case_insensitive(self, service_with_mocked_products):
        results = service_with_mocked_products.get_products_by_brand("apple")
        assert len(results) == 2
        assert {p['id'] for p in results} == {'1', '3'}

    def test_get_products_by_brand_non_existent(self, service_with_mocked_products):
        results = service_with_mocked_products.get_products_by_brand("Google")
        assert len(results) == 0

    def test_get_products_by_brand_empty_string(self, service_with_mocked_products):
        # Product Missing Keys has empty brand
        results = service_with_mocked_products.get_products_by_brand("")
        assert len(results) == 1
        assert results[0]['id'] == '6'

    def test_get_products_by_brand_error_handling(self, service_with_mocked_products, caplog_level, mocker):
        mocker.patch.object(service_with_mocked_products, 'products', side_effect=Exception("Iteration error"))
        results = service_with_mocked_products.get_products_by_brand("Apple")
        assert results == []
        assert "Error getting products by brand: Iteration error" in caplog_level.text

    # Test get_top_rated_products
    def test_get_top_rated_products(self, service_with_mocked_products):
        # Ratings: MacBook Air (4.9), iPhone (4.8), Sony (4.7), Samsung (4.5), HP (4.2), Smart Watch (4.0), Missing (0)
        results = service_with_mocked_products.get_top_rated_products(limit=3)
        assert len(results) == 3
        assert results[0]['id'] == '3' # MacBook Air (4.9)
        assert results[1]['id'] == '1' # iPhone (4.8)
        assert results[2]['id'] == '4' # Sony (4.7)

    def test_get_top_rated_products_limit_exceeds(self, service_with_mocked_products):
        results = service_with_mocked_products.get_top_rated_products(limit=100)
        assert len(results) == len(service_with_mocked_products.products)

    def test_get_top_rated_products_zero_limit(self, service_with_mocked_products):
        results = service_with_mocked_products.get_top_rated_products(limit=0)
        assert len(results) == 0

    def test_get_top_rated_products_error_handling(self, service_with_mocked_products, caplog_level, mocker):
        mocker.patch.object(service_with_mocked_products, 'products', side_effect=Exception("Sort error"))
        results = service_with_mocked_products.get_top_rated_products()
        assert results == []
        assert "Error getting top rated products: Sort error" in caplog_level.text

    # Test get_best_selling_products
    def test_get_best_selling_products(self, service_with_mocked_products, caplog_level):
        # Sold: Smart Watch (3000), Sony (2000), iPhone (1250), Samsung (900), HP (700), MacBook (500), Missing (0)
        results = service_with_mocked_products.get_best_selling_products(limit=3)
        assert len(results) == 3
        assert results[0]['id'] == '7' # Smart Watch (3000)
        assert results[1]['id'] == '4' # Sony (2000)
        assert results[2]['id'] == '1' # iPhone (1250)
        assert "Getting best selling products, limit: 3" in caplog_level.text
        assert "Returning 3 best selling products" in caplog_level.text

    def test_get_best_selling_products_limit_exceeds(self, service_with_mocked_products):
        results = service_with_mocked_products.get_best_selling_products(limit=100)
        assert len(results) == len(service_with_mocked_products.products)

    def test_get_best_selling_products_zero_limit(self, service_with_mocked_products):
        results = service_with_mocked_products.get_best_selling_products(limit=0)
        assert len(results) == 0

    def test_get_best_selling_products_error_handling(self, service_with_mocked_products, caplog_level, mocker):
        mocker.patch.object(service_with_mocked_products, 'products', side_effect=Exception("Sort error"))
        results = service_with_mocked_products.get_best_selling_products()
        assert results == []
        assert "Error getting best selling products: Sort error" in caplog_level.text

    # Test get_products (all products)
    def test_get_products(self, service_with_mocked_products, caplog_level):
        results = service_with_mocked_products.get_products(limit=3)
        assert len(results) == 3
        # Order is preserved as no sorting logic is applied beyond slicing
        assert results[0]['id'] == '1' 
        assert "Getting all products, limit: 3" in caplog_level.text

    def test_get_products_limit_exceeds(self, service_with_mocked_products):
        results = service_with_mocked_products.get_products(limit=100)
        assert len(results) == len(service_with_mocked_products.products)

    def test_get_products_zero_limit(self, service_with_mocked_products):
        results = service_with_mocked_products.get_products(limit=0)
        assert len(results) == 0

    def test_get_products_error_handling(self, service_with_mocked_products, caplog_level, mocker):
        mocker.patch.object(service_with_mocked_products, 'products', side_effect=Exception("List slice error"))
        results = service_with_mocked_products.get_products()
        assert results == []
        assert "Error getting products: List slice error" in caplog_level.text

    # Test smart_search_products (most complex method)
    def test_smart_search_best_general(self, service_with_mocked_products):
        # Scenario 1: "terbaik" or "best" without specific category
        # Expected: top-rated general products (MacBook Air 4.9, iPhone 4.8)
        products, message = service_with_mocked_products.smart_search_products(keyword="terbaik", limit=2)
        assert len(products) == 2
        assert products[0]['id'] == '3' # MacBook Air (4.9)
        assert products[1]['id'] == '1' # iPhone (4.8)
        assert message == "Berikut produk terbaik berdasarkan rating:"

    def test_smart_search_best_category_found(self, service_with_mocked_products):
        # Scenario 2: "terbaik" with existing category
        # Laptops: MacBook Air (4.9), HP Pavilion (4.2)
        products, message = service_with_mocked_products.smart_search_products(keyword="terbaik", category="Laptop", limit=1)
        assert len(products) == 1
        assert products[0]['id'] == '3' # MacBook Air
        assert message == "Berikut Laptop terbaik berdasarkan rating:"

    def test_smart_search_best_category_not_found_fallback_general(self, service_with_mocked_products):
        # Scenario 2: "terbaik" with non-existent category, should fallback to general best
        products, message = service_with_mocked_products.smart_search_products(keyword="best", category="Furniture", limit=2)
        assert len(products) == 2
        assert products[0]['id'] == '3' # MacBook Air (general best)
        assert products[1]['id'] == '1' # iPhone (general best)
        assert message == "Tidak ada produk kategori Furniture, berikut produk terbaik secara umum:"

    def test_smart_search_all_criteria_match(self, service_with_mocked_products):
        # Scenario 3: All criteria met
        products, message = service_with_mocked_products.smart_search_products(
            keyword="galaxy", category="Smartphone", max_price=16000000, limit=1
        )
        assert len(products) == 1
        assert products[0]['id'] == '2' # Samsung Galaxy S24 (15M)
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_fallback_to_category_only(self, service_with_mocked_products):
        # Scenario 4: Keyword/price don't match, but category does. Returns cheapest in category.
        # Products: [MacBook Air (20M), HP Pavilion (12M)]
        products, message = service_with_mocked_products.smart_search_products(
            keyword="nonexistent-keyword", category="Laptop", max_price=None, limit=2
        )
        assert len(products) == 2
        assert products[0]['id'] == '5' # HP Pavilion (12M) - cheaper
        assert products[1]['id'] == '3' # MacBook Air (20M)
        assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."

    def test_smart_search_fallback_to_budget_only(self, service_with_mocked_products):
        # Scenario 5: No category match, but max_price matches. Returns products within budget.
        # Products within 4M: Sony (3M), Smart Watch (0.5M), Product Missing Keys (0.1M)
        products, message = service_with_mocked_products.smart_search_products(
            keyword="nonexistent-keyword", category="NonExistentCategory", max_price=4000000, limit=2
        )
        assert len(products) == 2
        # Sorting is not explicitly defined here, but they should be from the budget results
        # Order might depend on original list or dict iteration order.
        # Let's verify by ID and assume order doesn't matter for this general fallback.
        assert {p['id'] for p in products} == {'4', '7'} # Sony, Smart Watch

        assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

    def test_smart_search_fallback_to_popular(self, service_with_mocked_products):
        # Scenario 6: No criteria match, fallback to best-selling products.
        # Sold: Smart Watch (3000), Sony (2000), iPhone (1250)
        products, message = service_with_mocked_products.smart_search_products(
            keyword="nothing_matches", category="NonExistentCategory", max_price=1, limit=2
        )
        assert len(products) == 2
        assert products[0]['id'] == '7' # Smart Watch (top sold)
        assert products[1]['id'] == '4' # Sony Headphones (2nd top sold)
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_empty_keyword_no_other_filters(self, service_with_mocked_products):
        # When keyword is empty, and category/max_price are None, it should hit Scenario 3
        # (all criteria match because filters are effectively off)
        # Then it just returns the first `limit` products from the internal list.
        products, message = service_with_mocked_products.smart_search_products(keyword="", category=None, max_price=None, limit=3)
        assert len(products) == 3
        assert {p['id'] for p in products} == {'1', '2', '3'} # First 3 from mock_products_data
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_keyword_only_no_match_popular_fallback(self, service_with_mocked_products):
        # Keyword doesn't match any product, category and max_price are None.
        # Should fall through all checks to Scenario 6: popular products.
        products, message = service_with_mocked_products.smart_search_products(keyword="nonexistent_product_xyz", limit=2)
        assert len(products) == 2
        assert products[0]['id'] == '7'
        assert products[1]['id'] == '4'
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_product_with_no_rating_or_sold_data(self, service_with_mocked_products):
        # Ensure products with missing 'rating' or 'sold' keys don't break sorting
        # Product '6' has rating 0 and sold 0
        products, message = service_with_mocked_products.smart_search_products(keyword="terbaik", limit=10)
        # '6' should be at the very end when sorting by rating (0.0)
        assert products[-1]['id'] == '6'
        
        products, message = service_with_mocked_products.smart_search_products(keyword="popular", limit=10)
        # '6' should be at the very end when sorting by sold (0)
        assert products[-1]['id'] == '6'