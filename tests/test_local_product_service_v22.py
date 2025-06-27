import pytest
import json
import os
import shutil
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import logging

# Ensure the path is correct relative to where pytest might run
# This is typically 'tests/' or 'test_services/'
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.local_product_service import LocalProductService

# Configure logging for tests
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Define a sample product structure for testing transformations
SAMPLE_RAW_PRODUCTS_DATA = {
    "products": [
        {
            "id": "prod1",
            "name": "Laptop XYZ",
            "category": "Laptop",
            "brand": "BrandA",
            "price": 10000000,
            "currency": "IDR",
            "description": "A powerful laptop.",
            "rating": 4.5,
            "stock_count": 50,
            "availability": "in_stock",
            "reviews_count": 100,
            "specifications": {"processor": "Intel i7"},
            "missing_field": "should_be_ignored"
        },
        {
            "id": "prod2",
            "name": "Smartphone ABC",
            "category": "Smartphone",
            "brand": "BrandB",
            "price": 5000000,
            "currency": "IDR",
            "description": "Latest smartphone.",
            "rating": 4.2,
            "stock_count": 30,
            "availability": "out_of_stock",
            "reviews_count": 50,
            "specifications": {"camera": "64MP"},
            "some_other_field": "value"
        },
        {   # Product with minimal fields
            "id": "prod3",
            "name": "Headphones",
            "category": "Audio",
            "brand": "BrandA",
            "price": 1000000,
            "rating": 3.8, # for best selling / top rated tests
            "stock_count": 10,
            "reviews_count": 20,
            "sold": 1500 # Explicitly set for best selling
        },
        {   # Another product for best selling / top rated
            "id": "prod4",
            "name": "Smartwatch",
            "category": "Wearable",
            "brand": "BrandC",
            "price": 2500000,
            "rating": 4.9, # for best selling / top rated tests
            "stock_count": 20,
            "reviews_count": 80,
            "sold": 500 # Explicitly set for best selling
        }
    ]
}

# The expected transformed products (with random.randint mocked to 1000)
EXPECTED_TRANSFORMED_PRODUCTS = [
    {
        "id": "prod1",
        "name": "Laptop XYZ",
        "category": "Laptop",
        "brand": "BrandA",
        "price": 10000000,
        "currency": "IDR",
        "description": "A powerful laptop.",
        "specifications": {
            "rating": 4.5,
            "sold": 1000, # Mocked
            "stock": 50,
            "condition": "Baru",
            "shop_location": "Indonesia",
            "shop_name": "BrandA Store",
            "processor": "Intel i7"
        },
        "availability": "in_stock",
        "reviews_count": 100,
        "images": ["https://example.com/prod1.jpg"],
        "url": "https://shopee.co.id/prod1"
    },
    {
        "id": "prod2",
        "name": "Smartphone ABC",
        "category": "Smartphone",
        "brand": "BrandB",
        "price": 5000000,
        "currency": "IDR",
        "description": "Latest smartphone.",
        "specifications": {
            "rating": 4.2,
            "sold": 1000, # Mocked
            "stock": 30,
            "condition": "Baru",
            "shop_location": "Indonesia",
            "shop_name": "BrandB Store",
            "camera": "64MP"
        },
        "availability": "out_of_stock",
        "reviews_count": 50,
        "images": ["https://example.com/prod2.jpg"],
        "url": "https://shopee.co.id/prod2"
    },
    {
        "id": "prod3",
        "name": "Headphones",
        "category": "Audio",
        "brand": "BrandA",
        "price": 1000000,
        "currency": "IDR", # Defaulted
        "description": "", # Defaulted
        "specifications": {
            "rating": 3.8,
            "sold": 1500, # Explicitly set, not mocked for this one
            "stock": 10,
            "condition": "Baru",
            "shop_location": "Indonesia",
            "shop_name": "BrandA Store"
        },
        "availability": "in_stock", # Defaulted
        "reviews_count": 20,
        "images": ["https://example.com/prod3.jpg"],
        "url": "https://shopee.co.id/prod3"
    },
    {
        "id": "prod4",
        "name": "Smartwatch",
        "category": "Wearable",
        "brand": "BrandC",
        "price": 2500000,
        "currency": "IDR", # Defaulted
        "description": "", # Defaulted
        "specifications": {
            "rating": 4.9,
            "sold": 500, # Explicitly set, not mocked for this one
            "stock": 20,
            "condition": "Baru",
            "shop_location": "Indonesia",
            "shop_name": "BrandC Store"
        },
        "availability": "in_stock", # Defaulted
        "reviews_count": 80,
        "images": ["https://example.com/prod4.jpg"],
        "url": "https://shopee.co.id/prod4"
    }
]

# Fixtures for mocking
@pytest.fixture
def mock_path_exists():
    """Mock Path.exists to control file existence."""
    with patch('pathlib.Path.exists') as mock_exists:
        yield mock_exists

@pytest.fixture
def mock_open_file():
    """Mock open() for file reading."""
    with patch('builtins.open', new_callable=mock_open) as m_open:
        yield m_open

@pytest.fixture
def mock_randint():
    """Mock random.randint to ensure predictable 'sold' values."""
    with patch('random.randint', return_value=1000) as m_randint:
        yield m_randint

@pytest.fixture
def mock_logger_warnings_errors():
    """Fixture to capture log messages for assertions."""
    with patch.object(logging.getLogger(__name__), 'warning') as mock_warning,\
         patch.object(logging.getLogger(__name__), 'error') as mock_error,\
         patch.object(logging.getLogger(__name__), 'info') as mock_info:
        yield mock_warning, mock_error, mock_info

@pytest.fixture
def service_with_mock_products(mock_randint):
    """Provides a LocalProductService instance with predictable products."""
    with patch.object(LocalProductService, '_load_local_products') as mock_load:
        mock_load.return_value = EXPECTED_TRANSFORMED_PRODUCTS
        service = LocalProductService()
        yield service

@pytest.fixture
def service_with_empty_products():
    """Provides a LocalProductService instance with an empty product list."""
    with patch.object(LocalProductService, '_load_local_products') as mock_load:
        mock_load.return_value = []
        service = LocalProductService()
        yield service

# Test cases for __init__ and _load_local_products
class TestLocalProductServiceInitializationAndLoading:

    def test_init_loads_products_successfully(self, mock_path_exists, mock_open_file, mock_randint, mock_logger_warnings_errors):
        """
        Test that __init__ correctly calls _load_local_products and logs info.
        """
        mock_exists = mock_path_exists
        mock_exists.return_value = True
        mock_open_file.return_value.read.return_value = json.dumps(SAMPLE_RAW_PRODUCTS_DATA)
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors

        service = LocalProductService()

        assert len(service.products) == len(EXPECTED_TRANSFORMED_PRODUCTS)
        mock_info.assert_any_call(f"Loaded {len(EXPECTED_TRANSFORMED_PRODUCTS)} local products from JSON file")
        mock_info.assert_any_call(f"Successfully loaded {len(EXPECTED_TRANSFORMED_PRODUCTS)} products from JSON file using utf-16-le encoding") # Default first successful encoding

    def test_init_falls_back_on_load_error(self, mock_path_exists, mock_open_file, mock_randint, mock_logger_warnings_errors):
        """
        Test that __init__ falls back to default products if _load_local_products fails.
        """
        mock_exists = mock_path_exists
        mock_exists.return_value = True # File exists
        mock_open_file.side_effect = Exception("Simulated file read error") # Simulate error during open/read
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors

        service = LocalProductService()

        # Check if fallback products are loaded
        fallback_service = LocalProductService() # Create a temporary instance to get fallback products
        expected_fallback_products = fallback_service._get_fallback_products()

        assert service.products == expected_fallback_products
        mock_error.assert_called_with("Error loading products from JSON file: Simulated file read error")
        mock_warning.assert_called_with("Using fallback products due to JSON file loading error")
        mock_info.assert_any_call(f"Loaded {len(expected_fallback_products)} local products from JSON file")


    def test_load_local_products_file_not_found(self, mock_path_exists, mock_logger_warnings_errors):
        """
        Test _load_local_products when the JSON file does not exist.
        """
        mock_exists = mock_path_exists
        mock_exists.return_value = False
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors

        service = LocalProductService() # Instantiates, calls _load_local_products
        service._load_local_products() # Directly call to test behavior more explicitly

        # Check if fallback products are loaded
        fallback_service = LocalProductService() # Create a temporary instance to get fallback products
        expected_fallback_products = fallback_service._get_fallback_products()

        assert service.products == expected_fallback_products
        mock_error.assert_called_once() # Path should be in the error message
        assert "Products JSON file not found at:" in mock_error.call_args[0][0]
        mock_warning.assert_called_with("Using fallback products due to JSON file loading error")

    def test_load_local_products_json_decode_error(self, mock_path_exists, mock_open_file, mock_logger_warnings_errors):
        """
        Test _load_local_products when JSON content is invalid.
        """
        mock_path_exists.return_value = True
        mock_open_file.return_value.read.return_value = "{invalid json"
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors

        service = LocalProductService()
        service._load_local_products()

        # All encoding attempts should fail and fallback
        assert mock_warning.call_count == len(LocalProductService._load_local_products.__defaults__[0]) # Check warnings for all encodings
        assert "Failed to load with utf-16-le encoding: Expecting property name enclosed in double quotes" in mock_warning.call_args_list[0].args[0]
        mock_error.assert_called_with("All encoding attempts failed, using fallback products")
        mock_warning.assert_called_with("Using fallback products due to JSON file loading error")


    def test_load_local_products_unicode_decode_error_and_fallback(self, mock_path_exists, mock_open_file, mock_logger_warnings_errors):
        """
        Test _load_local_products when initial encodings fail but a later one succeeds.
        """
        mock_path_exists.return_value = True
        
        # Simulate an encoding failure for the first few attempts, then success
        def mock_read_side_effect(*args, **kwargs):
            encoding = kwargs.get('encoding')
            if encoding == 'utf-16-le':
                raise UnicodeDecodeError('utf-16-le', b'\x00\x00', 0, 1, 'invalid start byte')
            elif encoding == 'utf-16':
                raise UnicodeDecodeError('utf-16', b'\x00\x00', 0, 1, 'invalid start byte')
            elif encoding == 'utf-8': # This one succeeds
                return json.dumps(SAMPLE_RAW_PRODUCTS_DATA)
            else:
                return json.dumps(SAMPLE_RAW_PRODUCTS_DATA) # Should not reach here

        mock_open_file.return_value.read.side_effect = mock_read_side_effect
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors

        service = LocalProductService()
        service._load_local_products()

        assert len(service.products) == len(EXPECTED_TRANSFORMED_PRODUCTS)
        assert mock_warning.call_count == 2 # For utf-16-le and utf-16
        mock_info.assert_any_call(f"Successfully loaded {len(EXPECTED_TRANSFORMED_PRODUCTS)} products from JSON file using utf-8 encoding")
        mock_error.assert_not_called()

    def test_load_local_products_with_bom(self, mock_path_exists, mock_open_file, mock_randint, mock_logger_warnings_errors):
        """
        Test _load_local_products handling of BOM character.
        """
        mock_path_exists.return_value = True
        json_content_with_bom = '\ufeff' + json.dumps(SAMPLE_RAW_PRODUCTS_DATA)
        mock_open_file.return_value.read.return_value = json_content_with_bom
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors

        service = LocalProductService()
        service._load_local_products()

        assert len(service.products) == len(EXPECTED_TRANSFORMED_PRODUCTS)
        mock_info.assert_any_call(f"Successfully loaded {len(EXPECTED_TRANSFORMED_PRODUCTS)} products from JSON file using utf-16-le encoding") # First successful encoding
        mock_open_file.assert_called_with(ANY, 'r', encoding='utf-16-le') # Check that it tried the encodings

    def test_load_local_products_empty_products_array_in_json(self, mock_path_exists, mock_open_file, mock_randint, mock_logger_warnings_errors):
        """
        Test _load_local_products when the 'products' array in JSON is empty.
        """
        mock_path_exists.return_value = True
        mock_open_file.return_value.read.return_value = json.dumps({"products": []})
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors

        service = LocalProductService()
        service._load_local_products()

        assert service.products == []
        mock_info.assert_any_call("Successfully loaded 0 products from JSON file using utf-16-le encoding")

    def test_load_local_products_missing_products_key_in_json(self, mock_path_exists, mock_open_file, mock_randint, mock_logger_warnings_errors):
        """
        Test _load_local_products when the 'products' key is missing in JSON.
        """
        mock_path_exists.return_value = True
        mock_open_file.return_value.read.return_value = json.dumps({"other_key": []})
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors

        service = LocalProductService()
        service._load_local_products()

        assert service.products == []
        mock_info.assert_any_call("Successfully loaded 0 products from JSON file using utf-16-le encoding")

    @patch('app.services.local_product_service.Path')
    def test_load_local_products_general_exception_handling(self, mock_Path, mock_logger_warnings_errors):
        """
        Test _load_local_products for general exceptions during processing.
        """
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.__truediv__.return_value = mock_path_instance # For chain .parent.parent / "data" / "products.json"
        mock_Path.return_value = mock_path_instance

        # Simulate an unexpected error, e.g., during transformation or other logic
        mock_open_file = mock_open(read_data=json.dumps(SAMPLE_RAW_PRODUCTS_DATA))
        mock_open_file.side_effect = Exception("Unexpected error during file processing")

        mock_warning, mock_error, mock_info = mock_logger_warnings_errors

        service = LocalProductService()
        service._load_local_products()

        # Check if fallback products are loaded
        fallback_service = LocalProductService()
        expected_fallback_products = fallback_service._get_fallback_products()

        assert service.products == expected_fallback_products
        mock_error.assert_called_with("Error loading products from JSON file: Unexpected error during file processing")
        mock_warning.assert_called_with("Using fallback products due to JSON file loading error")

    def test_get_fallback_products(self, mock_logger_warnings_errors):
        """
        Test _get_fallback_products returns the hardcoded list.
        """
        service = LocalProductService() # Create instance to access method
        products = service._get_fallback_products()
        
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors
        mock_warning.assert_called_with("Using fallback products due to JSON file loading error")
        assert len(products) == 8 # Based on the provided code
        assert products[0]['id'] == "1"
        assert products[0]['name'] == "iPhone 15 Pro Max"


# Helper for patching Path and open in search_products tests
ANY = object() # A sentinel for arguments we don't care to assert

class TestLocalProductServiceMethods:

    def test_search_products_by_name_case_insensitive(self, service_with_mock_products):
        """
        Test search_products by name, case-insensitive.
        """
        service = service_with_mock_products
        results = service.search_products("laptop xyz")
        assert len(results) == 1
        assert results[0]['id'] == "prod1"

    def test_search_products_by_description(self, service_with_mock_products):
        """
        Test search_products by description.
        """
        service = service_with_mock_products
        results = service.search_products("powerful laptop")
        assert len(results) == 1
        assert results[0]['id'] == "prod1"

    def test_search_products_by_category(self, service_with_mock_products):
        """
        Test search_products by category.
        """
        service = service_with_mock_products
        results = service.search_products("smartphone")
        assert len(results) == 1
        assert results[0]['id'] == "prod2"

    def test_search_products_by_brand(self, service_with_mock_products):
        """
        Test search_products by brand.
        """
        service = service_with_mock_products
        results = service.search_products("BrandA")
        assert len(results) == 2
        assert {p['id'] for p in results} == {"prod1", "prod3"}

    def test_search_products_by_specifications(self, service_with_mock_products):
        """
        Test search_products by specifications.
        """
        service = service_with_mock_products
        results = service.search_products("Intel i7")
        assert len(results) == 1
        assert results[0]['id'] == "prod1"

    def test_search_products_with_limit(self, service_with_mock_products):
        """
        Test search_products with limit.
        """
        service = service_with_mock_products
        # Search for a keyword that returns multiple products
        results = service.search_products("Brand", limit=1)
        assert len(results) == 1
        assert results[0]['id'] == "prod1" # Highest relevance for 'BrandA' in name/brand

    def test_search_products_no_keyword_match(self, service_with_mock_products):
        """
        Test search_products when no keyword matches.
        """
        service = service_with_mock_products
        results = service.search_products("nonexistent product")
        assert len(results) == 0

    def test_search_products_empty_keyword(self, service_with_mock_products):
        """
        Test search_products with an empty keyword.
        Should return all products up to limit, sorted by some default relevance (e.g., name/brand relevance of empty string is effectively random or stable sort).
        Currently, the implementation will return all products and sort by relevance score, which will mostly be price-based for empty keyword.
        """
        service = service_with_mock_products
        results = service.search_products("")
        assert len(results) == len(EXPECTED_TRANSFORMED_PRODUCTS)
        # Verify sorting based on price for empty keyword (lower price = higher score)
        assert results[0]['id'] == 'prod3' # 1M
        assert results[1]['id'] == 'prod4' # 2.5M

    def test_search_products_price_extraction_juta(self, service_with_mock_products):
        """
        Test search_products with price extraction (juta).
        """
        service = service_with_mock_products
        results = service.search_products("laptop 6 juta")
        assert len(results) == 2 # prod2 (5M), prod3 (1M) - prod1 (10M) is excluded
        assert {p['id'] for p in results} == {"prod2", "prod3"}
        results = service.search_products("prod 15 juta") # All products should be under 15M
        assert len(results) == 4
        assert {p['id'] for p in results} == {"prod1", "prod2", "prod3", "prod4"}


    def test_search_products_price_extraction_ribu(self, service_with_mock_products):
        """
        Test search_products with price extraction (ribu).
        """
        service = service_with_mock_products
        # Test a price that's within the range of smaller products
        results = service.search_products("earphone 2000 ribu") # 2M
        assert len(results) == 2 # prod3 (1M) and prod4 (2.5M) will be excluded because 2M is too low. Let's adjust expected transformed products or the search.
        # Let's adjust. prod3 (1M), prod4 (2.5M). Search 2000 ribu (2M). Should only get prod3.
        results = service.search_products("any item 2000 ribu") # should get prod3 (1M)
        assert len(results) == 1
        assert results[0]['id'] == "prod3"

    def test_search_products_price_extraction_k_m(self, service_with_mock_products):
        """
        Test search_products with price extraction (k/m).
        """
        service = service_with_mock_products
        results = service.search_products("phone 5m") # 5,000,000
        assert len(results) == 2 # prod2 (5M), prod3 (1M)
        assert {p['id'] for p in results} == {"prod2", "prod3"}

        results = service.search_products("item 1000k") # 1,000,000
        assert len(results) == 1
        assert results[0]['id'] == "prod3"


    def test_search_products_budget_keywords(self, service_with_mock_products):
        """
        Test search_products with budget keywords.
        """
        service = service_with_mock_products
        # 'murah' defaults to 5,000,000
        results = service.search_products("laptop murah")
        assert len(results) == 2 # prod2 (5M), prod3 (1M)
        assert {p['id'] for p in results} == {"prod2", "prod3"}

        # 'hemat' defaults to 3,000,000
        results = service.search_products("smartphone hemat")
        assert len(results) == 2 # prod3 (1M), prod4 (2.5M)
        assert {p['id'] for p in results} == {"prod3", "prod4"}


    def test_search_products_relevance_scoring(self, service_with_mock_products):
        """
        Test search_products sorting by relevance score.
        """
        service = service_with_mock_products
        # "BrandA" is in name, brand, category (Laptop) and (Audio)
        results = service.search_products("BrandA")
        # prod1 (name: Laptop XYZ, brand: BrandA)
        # prod3 (name: Headphones, brand: BrandA)
        # prod1 contains "Laptop" keyword more strongly, and "BrandA" in brand.
        # For "BrandA", both prod1 and prod3 have BrandA as brand.
        # If both have the keyword in brand, the one with keyword in name (Laptop) might score higher.
        # Let's ensure prod1 is higher than prod3 because it's a stronger keyword match "Laptop XYZ" contains "Laptop"
        # The relevance is 'Brand' related. Both 'BrandA'. prod1 in name 'Laptop XYZ'. prod3 in name 'Headphones'.
        # Both will get brand score. No name score. If there is price score (no price in keyword)
        # prod1 (10M), prod3 (1M). So prod3 (1M) will have higher price score.
        # This means prod3 should be first.
        assert results[0]['id'] == "prod3"
        assert results[1]['id'] == "prod1"

    def test_search_products_relevance_scoring_with_price_preference(self, service_with_mock_products):
        """
        Test search_products sorting by relevance score with price preference.
        """
        service = service_with_mock_products
        # Search "headphones murah". Headphones matches prod3. Murah adds price preference.
        results = service.search_products("headphones murah")
        assert len(results) == 1
        assert results[0]['id'] == "prod3" # 1M, should be preferred due to 'murah'

    def test_search_products_error_handling(self, service_with_mock_products, mock_logger_warnings_errors):
        """
        Test error handling in search_products.
        """
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors
        service = service_with_mock_products
        # Manipulate products to cause an error (e.g., non-dict item)
        service.products = [None] # This will cause an AttributeError or TypeError
        results = service.search_products("test")
        assert results == []
        mock_error.assert_called_once()
        assert "Error searching products:" in mock_error.call_args[0][0]

    def test_extract_price_from_keyword_various_patterns(self):
        """
        Test _extract_price_from_keyword for various price patterns.
        """
        service = LocalProductService() # Does not need products loaded
        assert service._extract_price_from_keyword("laptop 10 juta") == 10000000
        assert service._extract_price_from_keyword("smartphone 500 ribu") == 500000
        assert service._extract_price_from_keyword("rp 250000") == 250000
        assert service._extract_price_from_keyword("1000000 rp") == 1000000
        assert service._extract_price_from_keyword("headset 50k") == 50000
        assert service._extract_price_from_keyword("pc gaming 20m") == 20000000
        assert service._extract_price_from_keyword("laptop 15m") == 15000000
        assert service._extract_price_from_keyword("iphone 25.000.000") == None # Current regex doesn't support dots/commas for separators

    def test_extract_price_from_keyword_budget_keywords(self):
        """
        Test _extract_price_from_keyword for budget keywords.
        """
        service = LocalProductService()
        assert service._extract_price_from_keyword("laptop murah") == 5000000
        assert service._extract_price_from_keyword("budget hp") == 5000000
        assert service._extract_price_from_keyword("tv hemat") == 3000000
        assert service._extract_price_from_keyword("monitor terjangkau") == 4000000
        assert service._extract_price_from_keyword("mouse ekonomis") == 2000000

    def test_extract_price_from_keyword_no_match(self):
        """
        Test _extract_price_from_keyword when no price or budget keyword is found.
        """
        service = LocalProductService()
        assert service._extract_price_from_keyword("random keyword search") is None
        assert service._extract_price_from_keyword("no price here") is None
        assert service._extract_price_from_keyword("") is None

    def test_extract_price_from_keyword_error_handling(self, mock_logger_warnings_errors):
        """
        Test error handling in _extract_price_from_keyword.
        """
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors
        service = LocalProductService()
        with patch('re.search', side_effect=Exception("Regex error")):
            result = service._extract_price_from_keyword("some keyword")
            assert result is None
            mock_error.assert_called_once()
            assert "Error extracting price from keyword: Regex error" in mock_error.call_args[0][0]

    def test_get_product_details_found(self, service_with_mock_products):
        """
        Test get_product_details when product is found.
        """
        service = service_with_mock_products
        product = service.get_product_details("prod1")
        assert product is not None
        assert product['id'] == "prod1"
        assert product['name'] == "Laptop XYZ"

    def test_get_product_details_not_found(self, service_with_mock_products):
        """
        Test get_product_details when product is not found.
        """
        service = service_with_mock_products
        product = service.get_product_details("nonexistent")
        assert product is None

    def test_get_product_details_empty_products(self, service_with_empty_products):
        """
        Test get_product_details with an empty product list.
        """
        service = service_with_empty_products
        product = service.get_product_details("prod1")
        assert product is None

    def test_get_product_details_error_handling(self, service_with_mock_products, mock_logger_warnings_errors):
        """
        Test error handling in get_product_details.
        """
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors
        service = service_with_mock_products
        service.products = [None] # Induce error
        result = service.get_product_details("prod1")
        assert result is None
        mock_error.assert_called_once()
        assert "Error getting product details:" in mock_error.call_args[0][0]

    def test_get_categories(self, service_with_mock_products):
        """
        Test get_categories returns unique, sorted categories.
        """
        service = service_with_mock_products
        categories = service.get_categories()
        assert categories == ['Audio', 'Laptop', 'Smartphone', 'Wearable']

    def test_get_categories_empty_products(self, service_with_empty_products):
        """
        Test get_categories with an empty product list.
        """
        service = service_with_empty_products
        categories = service.get_categories()
        assert categories == []

    def test_get_categories_with_missing_category_field(self):
        """
        Test get_categories when some products are missing the 'category' field.
        """
        with patch.object(LocalProductService, '_load_local_products') as mock_load:
            mock_load.return_value = [
                {"id": "c1", "name": "Prod1", "category": "CategoryA"},
                {"id": "c2", "name": "Prod2", "brand": "BrandX"}, # Missing category
                {"id": "c3", "name": "Prod3", "category": "CategoryB"}
            ]
            service = LocalProductService()
            categories = service.get_categories()
            assert categories == ['', 'CategoryA', 'CategoryB'] # Missing category becomes empty string

    def test_get_brands(self, service_with_mock_products):
        """
        Test get_brands returns unique, sorted brands.
        """
        service = service_with_mock_products
        brands = service.get_brands()
        assert brands == ['BrandA', 'BrandB', 'BrandC']

    def test_get_brands_empty_products(self, service_with_empty_products):
        """
        Test get_brands with an empty product list.
        """
        service = service_with_empty_products
        brands = service.get_brands()
        assert brands == []

    def test_get_products_by_category_found(self, service_with_mock_products):
        """
        Test get_products_by_category when products are found.
        """
        service = service_with_mock_products
        results = service.get_products_by_category("Laptop")
        assert len(results) == 1
        assert results[0]['id'] == "prod1"

    def test_get_products_by_category_not_found(self, service_with_mock_products):
        """
        Test get_products_by_category when no products match.
        """
        service = service_with_mock_products
        results = service.get_products_by_category("NonExistentCategory")
        assert len(results) == 0

    def test_get_products_by_category_case_insensitive(self, service_with_mock_products):
        """
        Test get_products_by_category is case-insensitive.
        """
        service = service_with_mock_products
        results = service.get_products_by_category("smartphone")
        assert len(results) == 1
        assert results[0]['id'] == "prod2"

    def test_get_products_by_category_error_handling(self, service_with_mock_products, mock_logger_warnings_errors):
        """
        Test error handling in get_products_by_category.
        """
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors
        service = service_with_mock_products
        service.products = [None] # Induce error
        results = service.get_products_by_category("Laptop")
        assert results == []
        mock_error.assert_called_once()
        assert "Error getting products by category:" in mock_error.call_args[0][0]

    def test_get_products_by_brand_found(self, service_with_mock_products):
        """
        Test get_products_by_brand when products are found.
        """
        service = service_with_mock_products
        results = service.get_products_by_brand("BrandA")
        assert len(results) == 2
        assert {p['id'] for p in results} == {"prod1", "prod3"}

    def test_get_products_by_brand_not_found(self, service_with_mock_products):
        """
        Test get_products_by_brand when no products match.
        """
        service = service_with_mock_products
        results = service.get_products_by_brand("NonExistentBrand")
        assert len(results) == 0

    def test_get_products_by_brand_case_insensitive(self, service_with_mock_products):
        """
        Test get_products_by_brand is case-insensitive.
        """
        service = service_with_mock_products
        results = service.get_products_by_brand("branda")
        assert len(results) == 2
        assert {p['id'] for p in results} == {"prod1", "prod3"}

    def test_get_products_by_brand_error_handling(self, service_with_mock_products, mock_logger_warnings_errors):
        """
        Test error handling in get_products_by_brand.
        """
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors
        service = service_with_mock_products
        service.products = [None] # Induce error
        results = service.get_products_by_brand("BrandA")
        assert results == []
        mock_error.assert_called_once()
        assert "Error getting products by brand:" in mock_error.call_args[0][0]

    def test_get_top_rated_products(self, service_with_mock_products):
        """
        Test get_top_rated_products returns correctly sorted products with limit.
        """
        service = service_with_mock_products
        # prod4 (4.9), prod1 (4.5), prod2 (4.2), prod3 (3.8)
        results = service.get_top_rated_products(limit=2)
        assert len(results) == 2
        assert results[0]['id'] == "prod4"
        assert results[1]['id'] == "prod1"

    def test_get_top_rated_products_no_limit(self, service_with_mock_products):
        """
        Test get_top_rated_products without a specific limit.
        """
        service = service_with_mock_products
        results = service.get_top_rated_products(limit=10) # More than total products
        assert len(results) == len(EXPECTED_TRANSFORMED_PRODUCTS)
        assert results[0]['id'] == "prod4" # Highest rated

    def test_get_top_rated_products_empty_products(self, service_with_empty_products):
        """
        Test get_top_rated_products with an empty product list.
        """
        service = service_with_empty_products
        results = service.get_top_rated_products()
        assert results == []

    def test_get_top_rated_products_error_handling(self, service_with_mock_products, mock_logger_warnings_errors):
        """
        Test error handling in get_top_rated_products.
        """
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors
        service = service_with_mock_products
        service.products = [None] # Induce error
        results = service.get_top_rated_products()
        assert results == []
        mock_error.assert_called_once()
        assert "Error getting top rated products:" in mock_error.call_args[0][0]

    def test_get_best_selling_products(self, service_with_mock_products, mock_logger_warnings_errors):
        """
        Test get_best_selling_products returns correctly sorted products with limit.
        """
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors
        service = service_with_mock_products
        # prod3 (1500 sold), prod1 (1000 sold, mocked), prod2 (1000 sold, mocked), prod4 (500 sold)
        results = service.get_best_selling_products(limit=2)
        assert len(results) == 2
        assert results[0]['id'] == "prod3"
        assert results[1]['id'] in ["prod1", "prod2"] # Order might be arbitrary between ties
        mock_info.assert_any_call("Getting best selling products, limit: 2")
        mock_info.assert_any_call("Returning 2 best selling products")


    def test_get_best_selling_products_no_limit(self, service_with_mock_products):
        """
        Test get_best_selling_products without a specific limit.
        """
        service = service_with_mock_products
        results = service.get_best_selling_products(limit=10) # More than total products
        assert len(results) == len(EXPECTED_TRANSFORMED_PRODUCTS)
        assert results[0]['id'] == "prod3" # Highest sold

    def test_get_best_selling_products_empty_products(self, service_with_empty_products):
        """
        Test get_best_selling_products with an empty product list.
        """
        service = service_with_empty_products
        results = service.get_best_selling_products()
        assert results == []

    def test_get_best_selling_products_error_handling(self, service_with_mock_products, mock_logger_warnings_errors):
        """
        Test error handling in get_best_selling_products.
        """
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors
        service = service_with_mock_products
        service.products = [None] # Induce error
        results = service.get_best_selling_products()
        assert results == []
        mock_error.assert_called_once()
        assert "Error getting best selling products:" in mock_error.call_args[0][0]

    def test_get_products(self, service_with_mock_products, mock_logger_warnings_errors):
        """
        Test get_products returns all products with limit.
        """
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors
        service = service_with_mock_products
        results = service.get_products(limit=2)
        assert len(results) == 2
        assert results == EXPECTED_TRANSFORMED_PRODUCTS[:2]
        mock_info.assert_any_call("Getting all products, limit: 2")

    def test_get_products_no_limit(self, service_with_mock_products):
        """
        Test get_products without a specific limit (default 10).
        """
        service = service_with_mock_products
        results = service.get_products()
        assert len(results) == len(EXPECTED_TRANSFORMED_PRODUCTS)
        assert results == EXPECTED_TRANSFORMED_PRODUCTS # All products, as 4 < 10

    def test_get_products_empty_products(self, service_with_empty_products):
        """
        Test get_products with an empty product list.
        """
        service = service_with_empty_products
        results = service.get_products()
        assert results == []

    def test_get_products_error_handling(self, service_with_mock_products, mock_logger_warnings_errors):
        """
        Test error handling in get_products.
        """
        mock_warning, mock_error, mock_info = mock_logger_warnings_errors
        service = service_with_mock_products
        service.products = [None] # Induce error
        results = service.get_products()
        assert results == []
        mock_error.assert_called_once()
        assert "Error getting products:" in mock_error.call_args[0][0]

    # Smart Search Tests
    def test_smart_search_products_best_general_request(self, service_with_mock_products):
        """
        Test smart_search_products for general "best" request (top rated overall).
        """
        service = service_with_mock_products
        # prod4 (4.9), prod1 (4.5), prod2 (4.2), prod3 (3.8)
        products, message = service.smart_search_products(keyword="best", limit=2)
        assert len(products) == 2
        assert products[0]['id'] == "prod4"
        assert products[1]['id'] == "prod1"
        assert message == "Berikut produk terbaik berdasarkan rating:"

    def test_smart_search_products_best_category_request(self, service_with_mock_products):
        """
        Test smart_search_products for "best" in a specific category.
        """
        service = service_with_mock_products
        # "Smartphone": prod2 (4.2)
        products, message = service.smart_search_products(keyword="terbaik", category="Smartphone")
        assert len(products) == 1
        assert products[0]['id'] == "prod2"
        assert message == "Berikut Smartphone terbaik berdasarkan rating:"

        # "Laptop": prod1 (4.5)
        products, message = service.smart_search_products(keyword="top", category="Laptop")
        assert len(products) == 1
        assert products[0]['id'] == "prod1"
        assert message == "Berikut Laptop terbaik berdasarkan rating:"

    def test_smart_search_products_best_non_existent_category_fallback(self, service_with_mock_products):
        """
        Test smart_search_products "best" request with non-existent category falls back to general best.
        """
        service = service_with_mock_products
        # prod4 (4.9), prod1 (4.5)
        products, message = service.smart_search_products(keyword="terbaik", category="NonExistentCategory", limit=2)
        assert len(products) == 2
        assert products[0]['id'] == "prod4"
        assert products[1]['id'] == "prod1"
        assert message == "Tidak ada produk kategori NonExistentCategory, berikut produk terbaik secara umum:"

    def test_smart_search_products_full_criteria_match(self, service_with_mock_products):
        """
        Test smart_search_products for a full match on keyword, category, and max_price.
        """
        service = service_with_mock_products
        products, message = service.smart_search_products(
            keyword="phone", category="Smartphone", max_price=6000000, limit=1
        )
        assert len(products) == 1
        assert products[0]['id'] == "prod2" # Smartphone ABC, 5M
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_products_fallback_to_category_only(self, service_with_mock_products):
        """
        Test smart_search_products fallback: keyword+max_price fail, but category matches.
        Should return cheapest in category.
        """
        service = service_with_mock_products
        # Only prod1 (10M) in Laptop. Max price 5M will fail.
        products, message = service.smart_search_products(
            keyword="expensive", category="Laptop", max_price=5000000
        )
        assert len(products) == 1
        assert products[0]['id'] == "prod1" # Only Laptop, so it returns it
        assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."

    def test_smart_search_products_fallback_to_budget_only(self, service_with_mock_products):
        """
        Test smart_search_products fallback: keyword+category fail, but max_price matches.
        """
        service = service_with_mock_products
        # No 'gaming' in "Audio" category. Find products <= 2M. Prod3 (1M).
        products, message = service.smart_search_products(
            keyword="gaming", category="Audio", max_price=2000000
        )
        assert len(products) == 1
        assert products[0]['id'] == "prod3" # Headphones, 1M
        assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

    def test_smart_search_products_fallback_to_popular(self, service_with_mock_products):
        """
        Test smart_search_products fallback: all filters fail, falls back to popular.
        """
        service = service_with_mock_products
        # No products will match this combination
        products, message = service.smart_search_products(
            keyword="xyz123", category="NonExistentCategory", max_price=100
        )
        assert len(products) == len(EXPECTED_TRANSFORMED_PRODUCTS)
        assert products[0]['id'] == "prod3" # Best selling (1500)
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_products_empty_parameters_fallback_to_popular(self, service_with_mock_products):
        """
        Test smart_search_products with empty parameters should return popular products.
        """
        service = service_with_mock_products
        products, message = service.smart_search_products()
        assert len(products) == len(EXPECTED_TRANSFORMED_PRODUCTS) # Limit is 5 by default, but we have 4.
        assert products[0]['id'] == "prod3" # Best selling (1500)
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_products_only_keyword_match(self, service_with_mock_products):
        """
        Test smart_search_products with only keyword and it matches.
        """
        service = service_with_mock_products
        products, message = service.smart_search_products(keyword="laptop")
        assert len(products) == 1
        assert products[0]['id'] == "prod1"
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_products_only_category_match(self, service_with_mock_products):
        """
        Test smart_search_products with only category and it matches.
        """
        service = service_with_mock_products
        products, message = service.smart_search_products(category="Smartphone")
        assert len(products) == 1
        assert products[0]['id'] == "prod2"
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_products_only_max_price_match(self, service_with_mock_products):
        """
        Test smart_search_products with only max_price and it matches.
        """
        service = service_with_mock_products
        products, message = service.smart_search_products(max_price=3000000)
        assert len(products) == 2 # prod3 (1M), prod4 (2.5M)
        assert {p['id'] for p in products} == {"prod3", "prod4"}
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_products_empty_product_list(self, service_with_empty_products):
        """
        Test smart_search_products when the internal product list is empty.
        """
        service = service_with_empty_products
        products, message = service.smart_search_products(keyword="any")
        assert products == []
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." # Still returns this message, but with an empty list

    def test_smart_search_products_limit_applied(self, service_with_mock_products):
        """
        Test smart_search_products applies the limit parameter.
        """
        service = service_with_mock_products
        # General best request, should return top 2
        products, message = service.smart_search_products(keyword="best", limit=2)
        assert len(products) == 2
        assert products[0]['id'] == "prod4" # 4.9
        assert products[1]['id'] == "prod1" # 4.5

        # Fallback to popular (all 4 products, but limit 1)
        products, message = service.smart_search_products(keyword="no match", limit=1)
        assert len(products) == 1
        assert products[0]['id'] == "prod3" # Highest sold

# You might need to add a cleanup for test files if you were creating actual files.
# But for now, mocking Path.exists and open is sufficient to avoid file system interaction.