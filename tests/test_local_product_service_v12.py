import pytest
from unittest.mock import mock_open, patch, MagicMock
import json
import logging
import random
from typing import List, Dict, Optional
from pathlib import Path

# Adjust path for import based on the provided file structure
# The file is app/services/local_product_service.py
# If the test is in test_services/local_product_service.py,
# it needs to import from app.services.local_product_service
from app.services.local_product_service import LocalProductService

# --- Fixtures and Test Data ---

@pytest.fixture
def mock_logger(mocker):
    """Mocks the logger to capture calls and prevent actual logging during tests."""
    return mocker.patch('app.services.local_product_service.logger')

@pytest.fixture
def mock_path(mocker):
    """
    Mocks pathlib.Path to control file existence and path construction within the service.
    This fixture ensures that any Path() instantiation within the LocalProductService
    returns a controlled mock object, allowing us to simulate file system behavior.
    """
    mock_file_path_instance = MagicMock(spec=Path)
    # Default behavior: exists returns True, __truediv__ allows chaining path parts
    mock_file_path_instance.exists.return_value = True
    # Simulate the __truediv__ (/) operator for path joining.
    # It returns 'self' to allow method chaining like path / "data" / "file.json"
    mock_file_path_instance.__truediv__.return_value = mock_file_path_instance
    # Make the mock Path object represent a string for logging/assertions
    mock_file_path_instance.__str__.return_value = "/mock/path/to/data/products.json"
    mock_file_path_instance.__repr__.return_value = "PosixPath('/mock/path/to/data/products.json')"

    # Patch Path's __new__ so that any Path() call returns our controlled mock
    mocker.patch('pathlib.Path.__new__', return_value=mock_file_path_instance)
    return mock_file_path_instance

@pytest.fixture
def mock_random_randint(mocker):
    """Mocks random.randint for deterministic 'sold' counts in product transformation."""
    return mocker.patch('app.services.local_product_service.random.randint', return_value=500) # Consistent sold count

@pytest.fixture
def valid_json_content():
    """Returns valid JSON content simulating data/products.json."""
    return json.dumps({
        "products": [
            {"id": "prod1", "name": "Laptop XYZ", "category": "Laptop", "brand": "BrandA", "price": 10000000, "description": "Powerful laptop", "rating": 4.5, "stock_count": 10, "specifications": {"processor": "Intel i7"}},
            {"id": "prod2", "name": "Smartphone ABC", "category": "Smartphone", "brand": "BrandB", "price": 5000000, "description": "Latest smartphone", "rating": 4.0, "stock_count": 20, "specifications": {"storage": "128GB"}},
            {"id": "prod3", "name": "Headphones PQR", "category": "Audio", "brand": "BrandA", "price": 1500000, "description": "Noise cancelling headphones", "rating": 4.8, "stock_count": 5, "reviews_count": 100},
            {"id": "prod4", "name": "Smartwatch DEF", "category": "Wearable", "brand": "BrandC", "price": 2500000, "description": "Fitness tracker", "rating": 3.9, "stock_count": 15},
            {"id": "prod5", "name": "Budget Laptop", "category": "Laptop", "brand": "BrandD", "price": 3000000, "description": "Affordable laptop for daily use", "rating": 3.5, "stock_count": 8, "specifications": {"ram": "8GB"}}
        ]
    })

@pytest.fixture
def valid_json_content_with_bom():
    """Returns valid JSON content with a UTF-8 Byte Order Mark (BOM) prefix."""
    return '\ufeff' + json.dumps({
        "products": [
            {"id": "bom1", "name": "BOM Product", "category": "Test", "brand": "TestBrand", "price": 100, "rating": 4.0, "stock_count": 1}
        ]
    })

@pytest.fixture
def empty_products_json_content():
    """Returns JSON content where the 'products' key is an empty list."""
    return json.dumps({"products": []})

@pytest.fixture
def json_content_no_products_key():
    """Returns JSON content that is valid but lacks the 'products' key."""
    return json.dumps({"other_data": "value"})

@pytest.fixture
def malformed_json_content():
    """Returns malformed JSON content to simulate JSONDecodeError."""
    return "{products: [ {id: 'bad'} " # Malformed JSON

@pytest.fixture
def setup_local_product_service_with_data(mocker, mock_logger, mock_path, mock_random_randint, valid_json_content):
    """Fixture to set up LocalProductService with mocked file operations returning valid data."""
    mock_path.exists.return_value = True # Ensure the mocked file path exists
    mocker.patch("builtins.open", mock_open(read_data=valid_json_content))
    service = LocalProductService()
    return service

@pytest.fixture
def setup_local_product_service_empty_data(mocker, mock_logger, mock_path, mock_random_randint, empty_products_json_content):
    """Fixture to set up LocalProductService with mocked file operations returning empty products list."""
    mock_path.exists.return_value = True
    mocker.patch("builtins.open", mock_open(read_data=empty_products_json_content))
    service = LocalProductService()
    return service

# --- Test Cases ---

class TestLocalProductServiceInitialization:
    """Tests for the __init__ method and its dependency on _load_local_products."""

    def test_init_loads_products_successfully(self, mock_logger, mock_path, mock_random_randint, valid_json_content, mocker):
        mock_path.exists.return_value = True
        mocker.patch("builtins.open", mock_open(read_data=valid_json_content))
        
        service = LocalProductService()
        
        assert len(service.products) == 5
        mock_logger.info.assert_called_with("Loaded 5 local products from JSON file")
        
        # Verify a sample product's transformation
        prod1 = next(p for p in service.products if p['id'] == 'prod1')
        assert prod1['id'] == 'prod1'
        assert prod1['name'] == 'Laptop XYZ'
        assert prod1['price'] == 10000000
        assert prod1['currency'] == 'IDR'
        assert prod1['images'] == ["https://example.com/prod1.jpg"]
        assert prod1['url'] == "https://shopee.co.id/prod1"
        assert prod1['specifications']['rating'] == 4.5
        assert prod1['specifications']['sold'] == 500 # From mock_random_randint
        assert prod1['specifications']['stock'] == 10
        assert prod1['specifications']['condition'] == 'Baru'
        assert prod1['specifications']['shop_location'] == 'Indonesia'
        assert prod1['specifications']['shop_name'] == 'BrandA Store'
        assert prod1['specifications']['processor'] == 'Intel i7' # Check merged specs
        assert prod1['reviews_count'] == 0 # Default value

    def test_init_falls_back_if_file_not_found(self, mock_logger, mock_path, mock_random_randint):
        mock_path.exists.return_value = False # Simulate file not found
        
        service = LocalProductService()
        
        assert len(service.products) == 8 # Expect fallback products
        mock_logger.error.assert_called_with(f"Products JSON file not found at: {mock_path}")
        mock_logger.warning.assert_called_with("Using fallback products due to JSON file loading error")
        mock_logger.info.assert_called_with("Loaded 8 local products from JSON file")

    def test_init_falls_back_on_json_decode_error_for_all_encodings(self, mock_logger, mock_path, mock_random_randint, malformed_json_content, mocker):
        mock_path.exists.return_value = True
        mocker.patch("builtins.open", mock_open(read_data=malformed_json_content))
        
        service = LocalProductService()
        
        assert len(service.products) == 8 # Expect fallback products
        # There are 6 encodings tried. Each should cause a warning.
        assert mock_logger.warning.call_count == 6 
        mock_logger.error.assert_called_with("All encoding attempts failed, using fallback products")
        mock_logger.warning.assert_called_with("Using fallback products due to JSON file loading error")

    def test_init_falls_back_on_unicode_decode_error_for_all_encodings(self, mock_logger, mock_path, mock_random_randint, mocker):
        mock_path.exists.return_value = True
        
        # Simulate all encoding attempts failing with UnicodeDecodeError
        mock_file_read = MagicMock(side_effect=[
            UnicodeDecodeError("utf-16-le", b'\x00', 0, 1, "simulated error LE"),
            UnicodeDecodeError("utf-16", b'\x00', 0, 1, "simulated error 16"),
            UnicodeDecodeError("utf-8", b'\x00', 0, 1, "simulated error 8"),
            UnicodeDecodeError("utf-8-sig", b'\x00', 0, 1, "simulated error 8-sig"),
            UnicodeDecodeError("latin-1", b'\x00', 0, 1, "simulated error latin-1"),
            UnicodeDecodeError("cp1252", b'\x00', 0, 1, "simulated error cp1252"),
        ])
        # Patch `open` to return a file handle whose `read` method raises the errors
        mocker.patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=mock_file_read)), __exit__=MagicMock(return_value=False))))

        service = LocalProductService()
        
        assert len(service.products) == 8 # Expect fallback products
        assert mock_logger.warning.call_count == 6 # Each encoding attempt should log a warning
        mock_logger.error.assert_called_with("All encoding attempts failed, using fallback products")
        mock_logger.warning.assert_called_with("Using fallback products due to JSON file loading error")

    def test_init_falls_back_on_generic_exception_during_load(self, mock_logger, mock_path, mock_random_randint, mocker):
        mock_path.exists.return_value = True
        mocker.patch("builtins.open", side_effect=Exception("Unexpected file error during open"))

        service = LocalProductService()
        
        assert len(service.products) == 8 # Expect fallback products
        mock_logger.error.assert_called_with("Error loading products from JSON file: Unexpected file error during open")
        mock_logger.warning.assert_called_with("Using fallback products due to JSON file loading error")

    def test_init_handles_empty_products_list_in_json(self, mock_logger, mock_path, mock_random_randint, empty_products_json_content, mocker):
        mock_path.exists.return_value = True
        mocker.patch("builtins.open", mock_open(read_data=empty_products_json_content))
        
        service = LocalProductService()
        
        assert len(service.products) == 0 
        mock_logger.info.assert_called_with(mocker.string_matching(r"Successfully loaded 0 products from JSON file using .* encoding")) 
        mock_logger.info.assert_called_with("Loaded 0 local products from JSON file")
        
    def test_init_handles_json_without_products_key(self, mock_logger, mock_path, mock_random_randint, json_content_no_products_key, mocker):
        mock_path.exists.return_value = True
        mocker.patch("builtins.open", mock_open(read_data=json_content_no_products_key))
        
        service = LocalProductService()
        
        assert len(service.products) == 0 
        mock_logger.info.assert_called_with(mocker.string_matching(r"Successfully loaded 0 products from JSON file using .* encoding")) 
        mock_logger.info.assert_called_with("Loaded 0 local products from JSON file")

    def test_load_local_products_with_bom_content_handled(self, mock_logger, mock_path, mock_random_randint, valid_json_content_with_bom, mocker):
        mock_path.exists.return_value = True
        mocker.patch("builtins.open", mock_open(read_data=valid_json_content_with_bom))

        service = LocalProductService()
        
        assert len(service.products) == 1
        assert service.products[0]['id'] == 'bom1'
        mock_logger.info.assert_called_with(mocker.string_matching(r"Successfully loaded 1 products from JSON file using .* encoding"))

    def test_load_local_products_tries_encodings_and_succeeds_on_second(self, mock_logger, mock_path, mock_random_randint, valid_json_content, mocker):
        mock_path.exists.return_value = True
        
        # Simulate first encoding failing, then succeeding with the second attempt.
        mock_file_read_side_effect = [
            UnicodeDecodeError("utf-16-le", b'', 0, 1, "simulated error"),
            valid_json_content # This content will be read on the second open attempt
        ]
        
        # Use a custom mock for `open` that returns a file handle whose `read` method
        # will yield the `side_effect` list elements sequentially.
        mock_open_func = MagicMock()
        mock_open_func.return_value.__enter__.return_value.read = MagicMock(side_effect=mock_file_read_side_effect)
        mocker.patch("builtins.open", mock_open_func)
        
        service = LocalProductService()

        assert len(service.products) == 5
        mock_logger.warning.assert_called_once_with(mocker.string_matching(r"Failed to load with utf-16-le encoding: .*"))
        mock_logger.info.assert_called_with(mocker.string_matching(r"Successfully loaded 5 products from JSON file using utf-16 encoding"))

    def test_get_fallback_products_direct_call(self, mock_logger):
        """Tests the _get_fallback_products method directly."""
        # Create a dummy instance of LocalProductService to call its private method, bypassing __init__
        service = LocalProductService.__new__(LocalProductService) 
        # Initialize `products` attribute as it would be during normal operation, even though it's unused by this specific method
        service.products = [] 
        
        fallback_products = service._get_fallback_products()
        assert len(fallback_products) == 8
        assert fallback_products[0]['id'] == '1'
        mock_logger.warning.assert_called_with("Using fallback products due to JSON file loading error")

class TestLocalProductServiceSearch:
    """Tests for search_products method."""

    @pytest.fixture(autouse=True)
    def _set_up_service_with_data(self, setup_local_product_service_with_data):
        self.service = setup_local_product_service_with_data

    def test_search_products_by_name(self, mock_logger):
        results = self.service.search_products("laptop")
        assert len(results) == 2
        assert {p['id'] for p in results} == {'prod1', 'prod5'}
        mock_logger.info.assert_called_with("Searching products with keyword: laptop")
        mock_logger.info.assert_called_with("Found 2 products")

    def test_search_products_case_insensitive(self):
        results = self.service.search_products("lAPtoP")
        assert len(results) == 2
        assert {p['id'] for p in results} == {'prod1', 'prod5'}

    def test_search_products_by_description(self):
        results = self.service.search_products("powerful")
        assert len(results) == 1
        assert results[0]['id'] == 'prod1'

    def test_search_products_by_brand(self):
        results = self.service.search_products("BrandA")
        assert len(results) == 2
        assert {p['id'] for p in results} == {'prod1', 'prod3'}

    def test_search_products_by_category(self):
        results = self.service.search_products("Smartphone")
        assert len(results) == 1
        assert results[0]['id'] == 'prod2'

    def test_search_products_by_specifications(self):
        results = self.service.search_products("Intel i7")
        assert len(results) == 1
        assert results[0]['id'] == 'prod1'
        
    def test_search_products_no_match(self, mock_logger):
        results = self.service.search_products("NonExistentProduct")
        assert len(results) == 0
        mock_logger.info.assert_called_with("Searching products with keyword: NonExistentProduct")
        mock_logger.info.assert_called_with("Found 0 products")

    def test_search_products_with_limit(self):
        results = self.service.search_products("product", limit=2)
        assert len(results) == 2 # Should return some products, up to limit

    def test_search_products_empty_keyword(self):
        results = self.service.search_products("", limit=3)
        assert len(results) == 3 # Should return top N products (based on relevance score logic without keyword)
        
    def test_search_products_with_price_keyword_and_text_match(self):
        # "laptop 6 juta" -> max_price = 6,000,000
        # prod1: Laptop, 10M -> (keyword match 'laptop', price > max_price)
        # prod2: Smartphone, 5M -> (no keyword match, price <= max_price)
        # prod3: Headphones, 1.5M -> (no keyword match, price <= max_price)
        # prod4: Smartwatch, 2.5M -> (no keyword match, price <= max_price)
        # prod5: Laptop, 3M -> (keyword match 'laptop', price <= max_price)
        
        # According to code: products matching `max_price` are added and `continue`d
        # Then, if not added by price, check `keyword_lower in searchable_text`.
        # So, prod2,3,4,5 are added because of price. Prod1 is not added by price.
        # Then for prod1 (not added by price), 'laptop' matches text, so it's added.
        # This means all 5 products will be in `filtered_products`.
        # Relevance: prod5 (Laptop+Budget) > prod1 (Laptop) > prod3 (Budget) > prod4 (Budget) > prod2 (Budget)
        results = self.service.search_products("laptop 6 juta")
        assert len(results) == 5
        assert results[0]['id'] == 'prod5'
        assert results[1]['id'] == 'prod1'
        assert results[2]['id'] == 'prod3'
        assert results[3]['id'] == 'prod4'
        assert results[4]['id'] == 'prod2'

    def test_search_products_with_budget_keyword_and_text_match(self):
        # "laptop murah" -> 'murah' -> max_price = 5,000,000
        # Similar logic as above, all 5 products should be included.
        # Relevance: prod5 (Laptop+Budget) > prod1 (Laptop) > prod3 (Budget) > prod4 (Budget) > prod2 (Budget)
        results = self.service.search_products("laptop murah")
        assert len(results) == 5
        assert results[0]['id'] == 'prod5'
        assert results[1]['id'] == 'prod1'
        assert results[2]['id'] == 'prod3'
        assert results[3]['id'] == 'prod4'
        assert results[4]['id'] == 'prod2'

    def test_search_products_error_handling(self, mock_logger, mocker):
        # Temporarily make self.products uniterable to force an exception
        original_products = self.service.products
        self.service.products = mocker.MagicMock(side_effect=Exception("Simulated iteration error"))
        
        results = self.service.search_products("keyword")
        assert len(results) == 0
        mock_logger.error.assert_called_with(mocker.string_matching(r"Error searching products: .*"))
        self.service.products = original_products # Restore for other tests

class TestLocalProductServiceExtractPriceFromKeyword:
    """Tests for _extract_price_from_keyword method."""

    @pytest.fixture(autouse=True)
    def _set_up_service(self, setup_local_product_service_with_data):
        self.service = setup_local_product_service_with_data

    @pytest.mark.parametrize("keyword, expected_price", [
        ("iphone 10 juta", 10000000),
        ("monitor 500 ribu", 500000),
        ("rp 1500000 keyboard", 1500000),
        ("mouse 75000 rp", 75000),
        ("headphone 200k", 200000),
        ("hp 3m", 3000000),
        ("murah", 5000000),
        ("budget gaming pc", 5000000),
        ("hemat", 3000000),
        ("terjangkau", 4000000),
        ("ekonomis", 2000000),
        ("charger", None),
        ("", None),
        ("rp 1234567890", 1234567890), # Large number
        ("1k", 1000),
        ("1m", 1000000),
        ("juta", None), # Only 'juta' without number
        ("ribu", None), # Only 'ribu' without number
        ("murah banget", 5000000), # Should still pick up 'murah'
        ("not a price", None),
        ("1 juta 2 ribu", 1000000), # Should pick up the first pattern match (juta)
    ])
    def test_extract_price_from_keyword(self, keyword, expected_price):
        price = self.service._extract_price_from_keyword(keyword)
        assert price == expected_price

    def test_extract_price_error_handling(self, mock_logger, mocker):
        # Mock re.search to raise an exception to simulate an internal error
        mocker.patch('re.search', side_effect=Exception("Regex error"))
        
        price = self.service._extract_price_from_keyword("some keyword")
        assert price is None
        mock_logger.error.assert_called_with(mocker.string_matching(r"Error extracting price from keyword: Regex error"))

class TestLocalProductServiceGetDetails:
    """Tests for get_product_details method."""

    @pytest.fixture(autouse=True)
    def _set_up_service_with_data(self, setup_local_product_service_with_data):
        self.service = setup_local_product_service_with_data

    def test_get_product_details_existing_id(self):
        product = self.service.get_product_details("prod1")
        assert product is not None
        assert product['id'] == "prod1"
        assert product['name'] == "Laptop XYZ"

    def test_get_product_details_non_existing_id(self):
        product = self.service.get_product_details("nonexistent")
        assert product is None

    def test_get_product_details_empty_product_list(self, setup_local_product_service_empty_data):
        # Use a service instance with an empty product list
        product = setup_local_product_service_empty_data.get_product_details("prod1")
        assert product is None

    def test_get_product_details_error_handling(self, mock_logger, mocker):
        # Temporarily make self.products raise an error on iteration
        original_products = self.service.products
        self.service.products = mocker.MagicMock(side_effect=Exception("Simulated iteration error"))
        
        product = self.service.get_product_details("prod1")
        assert product is None
        mock_logger.error.assert_called_with(mocker.string_matching(r"Error getting product details: Simulated iteration error"))
        self.service.products = original_products # Restore for other tests

class TestLocalProductServiceCategoryAndBrand:
    """Tests for get_categories, get_brands, get_products_by_category, get_products_by_brand methods."""

    @pytest.fixture(autouse=True)
    def _set_up_service_with_data(self, setup_local_product_service_with_data):
        self.service = setup_local_product_service_with_data

    def test_get_categories(self):
        categories = self.service.get_categories()
        expected_categories = ["Audio", "Laptop", "Smartphone", "Wearable"]
        assert sorted(categories) == sorted(expected_categories)
        assert len(categories) == len(expected_categories)

    def test_get_categories_empty_products(self, setup_local_product_service_empty_data):
        categories = setup_local_product_service_empty_data.get_categories()
        assert categories == []

    def test_get_categories_product_without_category_key(self, mocker):
        self.service.products = [{"id": "x", "name": "No Category Name"}]
        categories = self.service.get_categories()
        assert categories == [""] # Empty string for missing category

    def test_get_brands(self):
        brands = self.service.get_brands()
        expected_brands = ["BrandA", "BrandB", "BrandC", "BrandD"]
        assert sorted(brands) == sorted(expected_brands)
        assert len(brands) == len(expected_brands)

    def test_get_brands_empty_products(self, setup_local_product_service_empty_data):
        brands = setup_local_product_service_empty_data.get_brands()
        assert brands == []

    def test_get_brands_product_without_brand_key(self, mocker):
        self.service.products = [{"id": "y", "name": "No Brand Name"}]
        brands = self.service.get_brands()
        assert brands == [""] # Empty string for missing brand

    def test_get_products_by_category(self):
        results = self.service.get_products_by_category("Laptop")
        assert len(results) == 2
        assert {p['id'] for p in results} == {'prod1', 'prod5'}

    def test_get_products_by_category_case_insensitive(self):
        results = self.service.get_products_by_category("smartphone")
        assert len(results) == 1
        assert results[0]['id'] == 'prod2'

    def test_get_products_by_category_no_match(self):
        results = self.service.get_products_by_category("Tablet")
        assert len(results) == 0

    def test_get_products_by_category_empty_products_list(self, setup_local_product_service_empty_data):
        results = setup_local_product_service_empty_data.get_products_by_category("Laptop")
        assert len(results) == 0

    def test_get_products_by_category_error_handling(self, mock_logger, mocker):
        original_products = self.service.products
        self.service.products = mocker.MagicMock(side_effect=Exception("Simulated iteration error"))
        
        results = self.service.get_products_by_category("Laptop")
        assert len(results) == 0
        mock_logger.error.assert_called_with(mocker.string_matching(r"Error getting products by category: Simulated iteration error"))
        self.service.products = original_products

    def test_get_products_by_brand(self):
        results = self.service.get_products_by_brand("BrandA")
        assert len(results) == 2
        assert {p['id'] for p in results} == {'prod1', 'prod3'}

    def test_get_products_by_brand_case_insensitive(self):
        results = self.service.get_products_by_brand("branda")
        assert len(results) == 2
        assert {p['id'] for p in results} == {'prod1', 'prod3'}

    def test_get_products_by_brand_no_match(self):
        results = self.service.get_products_by_brand("BrandE")
        assert len(results) == 0

    def test_get_products_by_brand_empty_products_list(self, setup_local_product_service_empty_data):
        results = setup_local_product_service_empty_data.get_products_by_brand("BrandA")
        assert len(results) == 0

    def test_get_products_by_brand_error_handling(self, mock_logger, mocker):
        original_products = self.service.products
        self.service.products = mocker.MagicMock(side_effect=Exception("Simulated iteration error"))
        
        results = self.service.get_products_by_brand("BrandA")
        assert len(results) == 0
        mock_logger.error.assert_called_with(mocker.string_matching(r"Error getting products by brand: Simulated iteration error"))
        self.service.products = original_products

class TestLocalProductServiceSortingAndRetrieval:
    """Tests for get_top_rated_products, get_best_selling_products, and get_products methods."""

    @pytest.fixture(autouse=True)
    def _set_up_service_with_data(self, setup_local_product_service_with_data):
        self.service = setup_local_product_service_with_data
        # Override products with a custom set for clearer sorting tests
        self.service.products = [
            {"id": "p1", "name": "High Rated", "category": "A", "brand": "X", "price": 100, "specifications": {"rating": 5.0, "sold": 1000}},
            {"id": "p2", "name": "Medium Rated", "category": "A", "brand": "Y", "price": 200, "specifications": {"rating": 4.0, "sold": 500}},
            {"id": "p3", "name": "Low Rated", "category": "B", "brand": "X", "price": 300, "specifications": {"rating": 3.0, "sold": 2000}},
            {"id": "p4", "name": "No Rating", "category": "B", "brand": "Y", "price": 400, "specifications": {"sold": 1500}}, # No rating (defaults to 0)
            {"id": "p5", "name": "Another Medium", "category": "A", "brand": "Z", "price": 50, "specifications": {"rating": 4.2, "sold": 750}}
        ]

    def test_get_top_rated_products(self):
        results = self.service.get_top_rated_products()
        assert len(results) == 5
        # Expected order by rating (desc): p1(5.0), p5(4.2), p2(4.0), p3(3.0), p4(0.0 default)
        assert results[0]['id'] == 'p1'
        assert results[1]['id'] == 'p5'
        assert results[2]['id'] == 'p2'
        assert results[3]['id'] == 'p3'
        assert results[4]['id'] == 'p4'

    def test_get_top_rated_products_with_limit(self):
        results = self.service.get_top_rated_products(limit=2)
        assert len(results) == 2
        assert results[0]['id'] == 'p1'
        assert results[1]['id'] == 'p5'

    def test_get_top_rated_products_empty_list(self, setup_local_product_service_empty_data):
        results = setup_local_product_service_empty_data.get_top_rated_products()
        assert results == []

    def test_get_top_rated_products_limit_zero(self):
        results = self.service.get_top_rated_products(limit=0)
        assert results == []
    
    def test_get_top_rated_products_error_handling(self, mock_logger, mocker):
        original_products = self.service.products
        self.service.products = mocker.MagicMock(side_effect=Exception("Simulated sorting error"))
        
        results = self.service.get_top_rated_products()
        assert results == []
        mock_logger.error.assert_called_with(mocker.string_matching(r"Error getting top rated products: Simulated sorting error"))
        self.service.products = original_products

    def test_get_best_selling_products(self, mock_logger):
        results = self.service.get_best_selling_products()
        assert len(results) == 5
        # Expected order by sold count (desc): p3(2000), p4(1500), p1(1000), p5(750), p2(500)
        assert results[0]['id'] == 'p3'
        assert results[1]['id'] == 'p4'
        assert results[2]['id'] == 'p1'
        assert results[3]['id'] == 'p5'
        assert results[4]['id'] == 'p2'
        mock_logger.info.assert_called_with("Getting best selling products, limit: 5")
        mock_logger.info.assert_called_with("Returning 5 best selling products")

    def test_get_best_selling_products_with_limit(self):
        results = self.service.get_best_selling_products(limit=2)
        assert len(results) == 2
        assert results[0]['id'] == 'p3'
        assert results[1]['id'] == 'p4'

    def test_get_best_selling_products_empty_list(self, setup_local_product_service_empty_data):
        results = setup_local_product_service_empty_data.get_best_selling_products()
        assert results == []

    def test_get_best_selling_products_limit_zero(self):
        results = self.service.get_best_selling_products(limit=0)
        assert results == []

    def test_get_best_selling_products_error_handling(self, mock_logger, mocker):
        original_products = self.service.products
        self.service.products = mocker.MagicMock(side_effect=Exception("Simulated sorting error"))
        
        results = self.service.get_best_selling_products()
        assert results == []
        mock_logger.error.assert_called_with(mocker.string_matching(r"Error getting best selling products: Simulated sorting error"))
        self.service.products = original_products

    def test_get_products(self):
        results = self.service.get_products()
        assert len(results) == 5
        # Order is as defined in fixture (initial load order)
        assert results[0]['id'] == 'p1' 
        
    def test_get_products_with_limit(self):
        results = self.service.get_products(limit=3)
        assert len(results) == 3
        assert results[0]['id'] == 'p1'
        assert results[1]['id'] == 'p2'
        assert results[2]['id'] == 'p3'

    def test_get_products_empty_list(self, setup_local_product_service_empty_data):
        results = setup_local_product_service_empty_data.get_products()
        assert results == []

    def test_get_products_limit_zero(self):
        results = self.service.get_products(limit=0)
        assert results == []

    def test_get_products_error_handling(self, mock_logger, mocker):
        original_products = self.service.products
        self.service.products = mocker.MagicMock(side_effect=Exception("Simulated retrieval error"))
        
        results = self.service.get_products()
        assert results == []
        mock_logger.error.assert_called_with(mocker.string_matching(r"Error getting products: Simulated retrieval error"))
        self.service.products = original_products

class TestLocalProductServiceSmartSearch:
    """Tests for the smart_search_products method, covering various fallback scenarios."""

    @pytest.fixture(autouse=True)
    def _set_up_service_with_data(self, setup_local_product_service_with_data):
        self.service = setup_local_product_service_with_data
        # Use a more diverse set of products for comprehensive smart search tests
        self.service.products = [
            {"id": "s1", "name": "Gaming Laptop Pro", "category": "Laptop", "brand": "Alienware", "price": 20000000, "specifications": {"rating": 4.9, "sold": 500, "ram": "32GB"}},
            {"id": "s2", "name": "Ultra Slim Laptop", "category": "Laptop", "brand": "Dell", "price": 10000000, "specifications": {"rating": 4.5, "sold": 300}},
            {"id": "s3", "name": "Budget Smartphone", "category": "Smartphone", "brand": "Xiaomi", "price": 2000000, "specifications": {"rating": 3.8, "sold": 1500}},
            {"id": "s4", "name": "Pro Camera", "category": "Camera", "brand": "Sony", "price": 15000000, "specifications": {"rating": 4.7, "sold": 200}},
            {"id": "s5", "name": "Best Bluetooth Speaker", "category": "Audio", "brand": "JBL", "price": 1000000, "specifications": {"rating": 4.2, "sold": 800}},
            {"id": "s6", "name": "Headphones Terbaik", "category": "Audio", "brand": "Bose", "price": 3000000, "specifications": {"rating": 4.8, "sold": 1200}},
            {"id": "s7", "name": "Value Tablet", "category": "Tablet", "brand": "Lenovo", "price": 4000000, "specifications": {"rating": 4.0, "sold": 600}},
            {"id": "s8", "name": "Premium Keyboard", "category": "Accessories", "brand": "Razer", "price": 800000, "specifications": {"rating": 4.6, "sold": 900}},
            {"id": "s9", "name": "Monitor Ultrawide", "category": "Monitor", "brand": "LG", "price": 7000000, "specifications": {"rating": 4.1, "sold": 400}}
        ]

    def test_smart_search_case_1_best_general_products(self):
        # Case 1: is_best_request and no specific category. Returns top-rated general products.
        products, message = self.service.smart_search_products(keyword="produk terbaik", limit=2)
        assert len(products) == 2
        # s1 (4.9), s6 (4.8) are the top 2 rated
        assert products[0]['id'] == 's1' 
        assert products[1]['id'] == 's6' 
        assert message == "Berikut produk terbaik berdasarkan rating:"

    def test_smart_search_case_2_best_in_existing_category(self):
        # Case 2: is_best_request and category exists. Returns top-rated in that category.
        products, message = self.service.smart_search_products(keyword="laptop terbaik", category="Laptop", limit=1)
        assert len(products) == 1
        assert products[0]['id'] == 's1' # Gaming Laptop Pro (4.9)
        assert message == "Berikut Laptop terbaik berdasarkan rating:"

    def test_smart_search_case_2_5_best_with_non_existing_category_fallback_to_general(self):
        # Case 2.5: is_best_request and category not found. Fallback to general top-rated.
        products, message = self.service.smart_search_products(keyword="tv terbaik", category="TV", limit=2)
        assert len(products) == 2
        assert products[0]['id'] == 's1' # Gaming Laptop Pro (4.9)
        assert products[1]['id'] == 's6' # Headphones Terbaik (4.8)
        assert message == "Tidak ada produk kategori TV, berikut produk terbaik secara umum:"

    def test_smart_search_case_3_all_criteria_match(self):
        # Case 3: All criteria met (`keyword`, `category`, `max_price`). Returns filtered products.
        products, message = self.service.smart_search_products(keyword="laptop", category="Laptop", max_price=15000000, limit=1)
        assert len(products) == 1
        assert products[0]['id'] == 's2' # Ultra Slim Laptop (10M), s1 is 20M
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."
        
        products, message = self.service.smart_search_products(keyword="premium", category="Accessories", max_price=1000000)
        assert len(products) == 1
        assert products[0]['id'] == 's8'
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_case_4_no_full_match_category_fallback(self):
        # Case 4: No products meeting all criteria, but category matches. Fallback to cheapest in category.
        # Search for "keyboard laptop 5 juta" -> (keyword "keyboard", category "Laptop", max_price 5M)
        # No actual product will match all three.
        # It should fallback to all products in 'Laptop' category, sorted by price.
        products, message = self.service.smart_search_products(keyword="keyboard", category="Laptop", max_price=5000000, limit=2)
        assert len(products) == 2
        # s2 (10M) and s1 (20M) are both laptops. s2 is cheaper.
        assert products[0]['id'] == 's2' 
        assert products[1]['id'] == 's1'
        assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."
        
    def test_smart_search_case_5_no_category_match_budget_fallback(self):
        # Case 5: No products meeting specific keyword+category, but max_price matches. Fallback to products within budget.
        # Search for "monitor game 1 juta" -> (keyword "monitor", category "Gaming", max_price 1M)
        # No "Gaming" category. Monitor (s9) is 7M (too expensive for 1M).
        # Fallback to products <= 1M.
        products, message = self.service.smart_search_products(keyword="monitor", category="Gaming", max_price=1000000, limit=2)
        assert len(products) == 2
        # s8 (0.8M), s5 (1M) are the cheapest within budget
        assert products[0]['id'] == 's8' 
        assert products[1]['id'] == 's5'
        assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

    def test_smart_search_case_6_no_match_popular_fallback(self):
        # Case 6: No products for any criteria. Fallback to best-selling products.
        products, message = self.service.smart_search_products(keyword="xyz non existent", category="NonCat", max_price=10000, limit=2)
        assert len(products) == 2
        # Best selling: s3 (1500), s6 (1200), s8 (900), s5 (800)...
        assert products[0]['id'] == 's3' 
        assert products[1]['id'] == 's6' 
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
        
    def test_smart_search_no_parameters(self):
        # No keyword, category, max_price specified. Should return first N products (from general search)
        # This falls into Case 3 where all filters are `None` initially.
        products, message = self.service.smart_search_products(limit=3)
        assert len(products) == 3
        # The default sorting behavior of search_products when no keyword means it returns all products up to limit,
        # sorted by the relevance score, which would be 0 for all if no price/keyword criteria apply.
        # But `smart_search_products` calls `search_products` and then applies its own sorting, so products
        # are returned in their original order.
        assert {p['id'] for p in products} == {'s1', 's2', 's3'}
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_empty_products_list(self, setup_local_product_service_empty_data):
        # Test smart search with an empty internal product list
        products, message = setup_local_product_service_empty_data.smart_search_products(keyword="laptop")
        assert len(products) == 0
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." # Fallback msg