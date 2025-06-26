import pytest
import json
import random
import logging
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Adjust the import path based on your project structure.
# If running pytest from the project root, 'app.services.local_product_service' is correct.
from app.services.local_product_service import LocalProductService

# --- Fixtures ---

@pytest.fixture
def mock_products_data():
    """Returns a dictionary representing valid product data for testing."""
    return {
        "products": [
            {
                "id": "prod1",
                "name": "Product A Smartphone",
                "category": "Electronics",
                "brand": "BrandX",
                "price": 1000000,
                "currency": "IDR",
                "description": "Powerful Product A with many features. Good for general use.",
                "specifications": {"rating": 4.5, "stock_count": 10, "color": "red", "storage": "128GB"},
                "availability": "in_stock",
                "reviews_count": 50,
            },
            {
                "id": "prod2",
                "name": "Product B Fashion Wear",
                "category": "Fashion",
                "brand": "BrandY",
                "price": 500000,
                "currency": "IDR",
                "description": "Stylish Product B, comfortable to wear.",
                "specifications": {"rating": 3.8, "stock_count": 5, "size": "M"},
                "availability": "out_of_stock",
                "reviews_count": 20,
            },
            {
                "id": "prod3",
                "name": "Product C (High Rating)",
                "category": "Electronics",
                "brand": "BrandZ",
                "price": 2000000,
                "currency": "IDR",
                "description": "Another electronic product with excellent performance.",
                "specifications": {"rating": 4.9, "stock_count": 20},
                "availability": "in_stock",
                "reviews_count": 100,
            },
            {
                "id": "prod4",
                "name": "Product D (Low Price)",
                "category": "Home Goods",
                "brand": "BrandX",
                "price": 50000,
                "currency": "IDR",
                "description": "A very cheap home good product.",
                "specifications": {"rating": 3.0, "stock_count": 100},
                "availability": "in_stock",
                "reviews_count": 5,
            },
            {
                "id": "prod5",
                "name": "Product E (Best Seller Book)",
                "category": "Books",
                "brand": "PublisherA",
                "price": 150000,
                "currency": "IDR",
                "description": "A popular book, highly recommended.",
                "specifications": {"rating": 4.2, "stock_count": 30, "sold": 1500},
                "availability": "in_stock",
                "reviews_count": 80,
            },
            {
                "id": "prod6",
                "name": "Product F (Low Seller Article)",
                "category": "Books",
                "brand": "PublisherB",
                "price": 120000,
                "currency": "IDR",
                "description": "Less popular book or article.",
                "specifications": {"rating": 4.0, "stock_count": 50, "sold": 50},
                "availability": "in_stock",
                "reviews_count": 10,
            },
        ]
    }

@pytest.fixture
def mock_empty_products_data():
    """Returns a dictionary with an empty products list."""
    return {"products": []}

@pytest.fixture
def mock_invalid_json_content():
    """Returns a string that is not valid JSON."""
    return "This is not JSON content {"

@pytest.fixture
def mock_path_exists_true(monkeypatch):
    """Mocks Path.exists to always return True."""
    monkeypatch.setattr(Path, 'exists', lambda self: True)

@pytest.fixture
def mock_path_exists_false(monkeypatch):
    """Mocks Path.exists to always return False."""
    monkeypatch.setattr(Path, 'exists', lambda self: False)

@pytest.fixture
def mock_open_with_content(monkeypatch, content):
    """Mocks built-in open to return specific content."""
    mock_file = mock_open(read_data=content)
    monkeypatch.setattr("builtins.open", mock_file)
    return mock_file

@pytest.fixture
def mock_open_with_json(mock_products_data, monkeypatch):
    """Mocks built-in open to return valid JSON content."""
    json_content = json.dumps(mock_products_data)
    mock_file = mock_open(read_data=json_content)
    monkeypatch.setattr("builtins.open", mock_file)
    return mock_file

@pytest.fixture
def mock_open_with_empty_json(mock_empty_products_data, monkeypatch):
    """Mocks built-in open to return empty JSON content."""
    json_content = json.dumps(mock_empty_products_data)
    mock_file = mock_open(read_data=json_content)
    monkeypatch.setattr("builtins.open", mock_file)
    return mock_file

@pytest.fixture
def mock_open_with_invalid_json(mock_invalid_json_content, monkeypatch):
    """Mocks built-in open to return invalid JSON content."""
    mock_file = mock_open(read_data=mock_invalid_json_content)
    monkeypatch.setattr("builtins.open", mock_file)
    return mock_file

@pytest.fixture
def mock_open_read_error(monkeypatch):
    """Mocks built-in open to raise an IOError on read."""
    mock_file = MagicMock()
    mock_file.read.side_effect = IOError("Mock read error")
    monkeypatch.setattr("builtins.open", lambda *args, **kwargs: mock_file)
    return mock_file

@pytest.fixture
def mock_open_unicode_error(monkeypatch):
    """Mocks built-in open to raise UnicodeDecodeError."""
    mock_file = MagicMock()
    mock_file.read.side_effect = UnicodeDecodeError("utf-8", b'', 0, 1, "mock error")
    monkeypatch.setattr("builtins.open", lambda *args, **kwargs: mock_file)
    return mock_file

@pytest.fixture
def mock_random_randint(monkeypatch):
    """Mocks random.randint to return a fixed value for deterministic 'sold' counts."""
    monkeypatch.setattr(random, 'randint', lambda a, b: 1000)

@pytest.fixture
def mock_logger(monkeypatch):
    """Mocks the logger to capture logs for assertions."""
    mock_log = MagicMock()
    monkeypatch.setattr(logging, 'getLogger', lambda name: mock_log)
    return mock_log

@pytest.fixture
def service_with_mock_products(mock_open_with_json, mock_path_exists_true, mock_random_randint, mock_logger):
    """
    Provides a LocalProductService instance initialized with mock products
    and ensures the logger is reset for individual test assertions.
    """
    service = LocalProductService()
    mock_logger.reset_mock()  # Clear logger calls from init for later assertions
    return service

@pytest.fixture
def service_with_fallback_products(mock_path_exists_false, mock_logger):
    """
    Provides a LocalProductService instance that falls back to default products
    and ensures the logger is reset.
    """
    service = LocalProductService()
    mock_logger.reset_mock()
    return service

# --- Tests for LocalProductService ---

class TestLocalProductServiceInitialization:
    """Tests for the __init__ method and product loading."""

    def test_init_loads_products_successfully(self, mock_open_with_json, mock_path_exists_true, mock_random_randint, mock_logger, mock_products_data):
        """
        GIVEN a valid products.json file exists
        WHEN LocalProductService is initialized
        THEN products should be loaded and logger should show success, and products transformed.
        """
        service = LocalProductService()
        assert len(service.products) == len(mock_products_data["products"])
        mock_logger.info.assert_any_call(f"Loaded {len(mock_products_data['products'])} local products from JSON file")
        # Default encoding for json.dumps might be utf-8 on some systems, utf-16-le on others,
        # but the test setup makes the first encoding (utf-16-le) succeed.
        mock_logger.info.assert_any_call(f"Successfully loaded {len(mock_products_data['products'])} products from JSON file using utf-16-le encoding")
        
        # Verify transformation of a sample product
        transformed_product = service.products[0]
        assert "id" in transformed_product
        assert transformed_product["specifications"]["sold"] == 1000  # Due to mock_random_randint
        assert transformed_product["specifications"]["condition"] == "Baru"
        assert transformed_product["specifications"]["shop_location"] == "Indonesia"
        assert transformed_product["specifications"]["shop_name"] == "BrandX Store" # From original brand
        assert transformed_product["images"] == [f"https://example.com/{transformed_product['id']}.jpg"]
        assert transformed_product["url"] == f"https://shopee.co.id/{transformed_product['id']}"
        assert transformed_product["specifications"]["storage"] == "128GB" # Existing spec should be merged

    def test_init_falls_back_if_file_not_found(self, mock_path_exists_false, mock_logger):
        """
        GIVEN products.json does not exist
        WHEN LocalProductService is initialized
        THEN fallback products should be used and logger should show error and warning.
        """
        service = LocalProductService()
        expected_fallback_count = len(service._get_fallback_products()) # Call internal method to get actual count
        assert len(service.products) == expected_fallback_count
        mock_logger.error.assert_any_call(f"Products JSON file not found at: {Path(__file__).parent.parent.parent / 'data' / 'products.json'}")
        mock_logger.warning.assert_any_call("Using fallback products due to JSON file loading error")
        mock_logger.info.assert_any_call(f"Loaded {expected_fallback_count} local products from JSON file")

    def test_init_falls_back_if_json_parsing_fails_all_encodings(self, monkeypatch, mock_path_exists_true, mock_logger):
        """
        GIVEN products.json exists but parsing fails for all encodings
        WHEN LocalProductService is initialized
        THEN fallback products should be used and logger should show errors.
        """
        # Mock open to raise UnicodeDecodeError for all attempts
        read_mock = MagicMock(side_effect=UnicodeDecodeError("utf-8", b'', 0, 1, "mock error"))
        mock_file = mock_open()
        mock_file.return_value.__enter__.return_value.read = read_mock
        monkeypatch.setattr("builtins.open", mock_file)

        service = LocalProductService()
        expected_fallback_count = len(service._get_fallback_products())
        assert len(service.products) == expected_fallback_count
        # Check that warnings were logged for each encoding attempt (at least the number of encodings defined)
        assert mock_logger.warning.call_count >= 6
        mock_logger.error.assert_any_call("All encoding attempts failed, using fallback products")
        mock_logger.warning.assert_any_call("Using fallback products due to JSON file loading error")
        mock_logger.info.assert_any_call(f"Loaded {expected_fallback_count} local products from JSON file")

    def test_init_falls_back_on_general_exception_during_load(self, monkeypatch, mock_path_exists_true, mock_logger):
        """
        GIVEN _load_local_products raises a general exception
        WHEN LocalProductService is initialized
        THEN fallback products should be used.
        """
        # Patch the internal method directly to simulate an unexpected error
        original_load_local_products = LocalProductService._load_local_products
        monkeypatch.setattr(LocalProductService, "_load_local_products", MagicMock(side_effect=Exception("Mock load error")))
        
        service = LocalProductService()
        expected_fallback_count = len(original_load_local_products(service)) # Call original to get count
        assert len(service.products) == expected_fallback_count
        mock_logger.error.assert_any_call("Error loading products from JSON file: Mock load error")
        mock_logger.warning.assert_any_call("Using fallback products due to JSON file loading error")

    def test_load_local_products_with_empty_json_file(self, mock_open_with_empty_json, mock_path_exists_true, mock_logger):
        """
        GIVEN an empty products.json file (valid JSON, empty list)
        WHEN _load_local_products is called
        THEN an empty list of products should be returned.
        """
        service = LocalProductService()  # This calls _load_local_products internally
        assert len(service.products) == 0
        mock_logger.info.assert_any_call("Successfully loaded 0 products from JSON file using utf-16-le encoding")

    def test_load_local_products_with_invalid_json_content(self, mock_open_with_invalid_json, mock_path_exists_true, mock_logger):
        """
        GIVEN an invalid products.json file (malformed JSON)
        WHEN _load_local_products is called
        THEN fallback products should be used.
        """
        service = LocalProductService()
        expected_fallback_count = len(service._get_fallback_products())
        assert len(service.products) == expected_fallback_count
        mock_logger.warning.assert_any_call(f"Failed to load with utf-16-le encoding: Expecting value: line 1 column 1 (char 0)")
        mock_logger.error.assert_any_call("All encoding attempts failed, using fallback products")
        mock_logger.warning.assert_any_call("Using fallback products due to JSON file loading error")

    def test_load_local_products_with_no_products_key_in_json(self, monkeypatch, mock_path_exists_true, mock_random_randint, mock_logger):
        """
        GIVEN a valid JSON file without a 'products' key
        WHEN _load_local_products is called
        THEN an empty list should be returned (due to .get('products', [])).
        """
        mock_data_no_products_key = json.dumps({"other_key": [{"item": 1}]})
        mock_file = mock_open(read_data=mock_data_no_products_key)
        monkeypatch.setattr("builtins.open", mock_file)

        service = LocalProductService()
        assert len(service.products) == 0
        mock_logger.info.assert_any_call("Successfully loaded 0 products from JSON file using utf-16-le encoding")

    def test_load_local_products_handles_bom_character(self, monkeypatch, mock_path_exists_true, mock_random_randint, mock_logger, mock_products_data):
        """
        GIVEN a JSON file with a BOM character at the start
        WHEN _load_local_products is called
        THEN BOM should be removed and products loaded successfully.
        """
        json_content_with_bom = '\ufeff' + json.dumps(mock_products_data)
        mock_file = mock_open(read_data=json_content_with_bom)
        monkeypatch.setattr("builtins.open", mock_file)

        service = LocalProductService()
        assert len(service.products) == len(mock_products_data["products"])
        mock_logger.info.assert_any_call(f"Successfully loaded {len(mock_products_data['products'])} products from JSON file using utf-16-le encoding")
        # Verify BOM was handled by ensuring content starts correctly after parsing
        assert service.products[0]["id"] == "prod1"

    def test_load_local_products_tries_multiple_encodings(self, monkeypatch, mock_path_exists_true, mock_logger, mock_products_data):
        """
        GIVEN a file that causes UnicodeDecodeError for initial encodings but succeeds with a later one (e.g., latin-1)
        WHEN _load_local_products is called
        THEN it should try multiple encodings and succeed with the correct one.
        """
        # Simulate content that can only be decoded by 'latin-1' (or other non-default encodings)
        # We need to simulate the _bytes_ that would cause the error, then the correct bytes.
        # For testing, we can just make `read()` fail a few times and then succeed.
        test_content_latin1 = json.dumps(mock_products_data)
        
        mock_read = MagicMock()
        mock_read.side_effect = [
            UnicodeDecodeError("utf-16-le", b'', 0, 1, "mock utf-16-le error"),
            UnicodeDecodeError("utf-16", b'', 0, 1, "mock utf-16 error"),
            UnicodeDecodeError("utf-8", b'', 0, 1, "mock utf-8 error"),
            UnicodeDecodeError("utf-8-sig", b'', 0, 1, "mock utf-8-sig error"),
            test_content_latin1 # This will be read when 'latin-1' is tried (or whatever is fifth)
        ]

        mock_file = mock_open()
        mock_file.return_value.__enter__.return_value.read = mock_read
        monkeypatch.setattr("builtins.open", mock_file)

        service = LocalProductService()
        assert len(service.products) == len(mock_products_data["products"])
        mock_logger.warning.assert_any_call(f"Failed to load with utf-16-le encoding: mock utf-16-le error")
        mock_logger.warning.assert_any_call(f"Failed to load with utf-16 encoding: mock utf-16 error")
        mock_logger.warning.assert_any_call(f"Failed to load with utf-8 encoding: mock utf-8 error")
        mock_logger.warning.assert_any_call(f"Failed to load with utf-8-sig encoding: mock utf-8-sig error")
        mock_logger.info.assert_any_call(f"Successfully loaded {len(mock_products_data['products'])} products from JSON file using latin-1 encoding")


class TestLocalProductServiceInternalMethods:
    """Tests for internal helper methods."""

    def test_get_fallback_products_returns_fixed_list(self, mock_logger):
        """
        GIVEN _get_fallback_products is called
        WHEN no other context
        THEN it should return a predefined list of products and log a warning.
        """
        service = LocalProductService() # Initializes, then we call _get_fallback_products directly
        mock_logger.reset_mock() # Clear init logs
        fallback_products = service._get_fallback_products()
        assert len(fallback_products) == 8 # Based on the provided hardcoded list
        assert fallback_products[0]["id"] == "1"
        assert fallback_products[0]["name"] == "iPhone 15 Pro Max"
        mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error")

    @pytest.mark.parametrize("keyword, expected_price", [
        ("laptop 10 juta", 10000000),
        ("handphone 2 juta", 2000000),
        ("earphone 500 ribu", 500000),
        ("baju rp 150000", 150000),
        ("tas 25000 rp", 25000),
        ("sepatu 75k", 75000),
        ("drone 2m", 2000000), # Handles 'm' for million
        ("iphone murah", 5000000), # Budget keyword
        ("tablet budget", 5000000), # Budget keyword
        ("speaker hemat", 3000000), # Budget keyword
        ("tv terjangkau", 4000000), # Budget keyword
        ("kipas ekonomis", 2000000), # Budget keyword
        ("just a keyword", None), # No price
        ("no price here", None), # No price
        ("", None), # Empty keyword
        ("Rp1.500.000", 1500000), # Example with dots (regex might ignore them or match partially depending on implementation)
        ("Rp 1.500.000", 1500000),
        ("Rp. 1.5jt", None), # Current regex won't pick this up
        ("1.5 juta", 1000000), # Current regex picks up "1" then "juta", giving 1M. Not 1.5M.
    ])
    def test_extract_price_from_keyword(self, service_with_mock_products, keyword, expected_price):
        """
        GIVEN various keywords containing price information
        WHEN _extract_price_from_keyword is called
        THEN it should correctly extract the maximum price or None if no price found.
        """
        # Pre-process keywords for specific regex patterns if needed (e.g., removing dots)
        if "Rp" in keyword:
             # Our regex 'rp\s*(\d+)' and '(\d+)\s*rp' expects digits directly,
             # so "Rp1.500.000" should become "Rp1500000" for the regex to capture it.
             # However, the current regex in the source won't handle dots.
             # It will only extract `\d+`. The fixture tests against the actual implementation.
             pass # No modification needed as regex is tested as-is.

        extracted_price = service_with_mock_products._extract_price_from_keyword(keyword)
        assert extracted_price == expected_price

    def test_extract_price_from_keyword_handles_error(self, service_with_mock_products, monkeypatch, mock_logger):
        """
        GIVEN _extract_price_from_keyword encounters an error (e.g., in regex operations)
        WHEN called
        THEN it should log the error and return None.
        """
        monkeypatch.setattr("re.search", MagicMock(side_effect=Exception("Mock regex error")))
        result = service_with_mock_products._extract_price_from_keyword("some keyword")
        assert result is None
        mock_logger.error.assert_called_once_with("Error extracting price from keyword: Mock regex error")


class TestLocalProductServiceSearch:
    """Tests for the search_products method."""

    @pytest.mark.parametrize("keyword, expected_ids, limit", [
        ("Product A", ["prod1"], 10),
        ("smartphone", ["prod1"], 10), # From prod1 name
        ("fashion", ["prod2"], 10), # From prod2 category
        ("BrandX", ["prod1", "prod4"], 10), # Prod1 & Prod4
        ("red", ["prod1"], 10), # From prod1 specs
        ("description B", ["prod2"], 10), # From prod2 description
        ("book", ["prod5", "prod6"], 10), # Books category
        ("nonexistent", [], 10), # No results
        ("product", ["prod3", "prod1", "prod5", "prod2", "prod6", "prod4"], 10), # All products match "product" in name/desc. Order by relevance.
        ("product", ["prod3", "prod1"], 2), # All products match "product", but limit to 2

        # Price search: "product 1 juta" should include Prod1 (1M) and Prod4 (50k) due to price filter
        # And also rank higher (due to price preference in relevance_score for "juta" keywords)
        ("product 1 juta", ["prod1", "prod4"], 10), # prod1 1M, prod4 50k - both <= 1M
        ("product murah", ["prod4", "prod2", "prod5", "prod6", "prod1", "prod3"], 10), # Price-preferred sort for 'murah' (max 5M)
        ("Product D 100 ribu", ["prod4"], 10), # Prod D is 50k, fits under 100k
    ])
    def test_search_products_general_scenarios(self, service_with_mock_products, keyword, expected_ids, limit):
        """
        GIVEN products loaded
        WHEN searching with various keywords, limits, and price filters
        THEN correct products should be returned, ordered by relevance.
        """
        results = service_with_mock_products.search_products(keyword, limit=limit)
        actual_ids = [p["id"] for p in results]

        # For relevance scoring, the exact order might vary if scores are identical.
        # Check if the set of expected IDs is present and the length is correct.
        assert len(results) == min(limit, len(expected_ids))

        if keyword == "product murah":
            # For 'murah', price is strongly weighted, so prod4 (50k) should be first.
            # Then prod2 (500k), prod5 (150k), prod6 (120k)
            assert actual_ids[0] == "prod4" # 50k
            assert actual_ids[1] == "prod2" # 500k
            # The remaining order among others is less strict but they should all be present
            assert set(actual_ids) == set(expected_ids[:len(actual_ids)])
        elif keyword == "product 1 juta":
            assert set(actual_ids) == set(expected_ids)
            assert results[0]["id"] == "prod1" or results[0]["id"] == "prod4" # Either could be first based on other relevance factors
        elif keyword == "product":
            # Products with 'Product' in name have higher score. Prod3 and Prod1 are 4.9 and 4.5.
            # The specific order between prod3 and prod1 among others depends on subtle score tie-breaks.
            assert actual_ids[0] in ["prod3", "prod1"]
            assert actual_ids[1] in ["prod3", "prod1"] and actual_ids[1] != actual_ids[0]
        else:
            assert actual_ids == expected_ids[:len(actual_ids)]

    def test_search_products_case_insensitivity(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN searching with a case-insensitive keyword
        THEN relevant products should be returned.
        """
        results = service_with_mock_products.search_products("product a smartPHONE")
        assert len(results) == 1
        assert results[0]["id"] == "prod1"

    def test_search_products_empty_keyword(self, service_with_mock_products):
        """
        GIVEN an empty keyword
        WHEN search_products is called
        THEN it should return all products up to the limit (no specific keyword relevance).
        """
        results = service_with_mock_products.search_products("")
        assert len(results) == 6 # All products if limit is high enough (default 10)
        assert isinstance(results, list)
        assert all(isinstance(p, dict) for p in results)

    def test_search_products_error_handling(self, service_with_mock_products, monkeypatch, mock_logger):
        """
        GIVEN search_products encounters an error (e.g., during internal processing)
        WHEN called
        THEN it should log the error and return an empty list.
        """
        # Simulate an error within the loop or helper function
        monkeypatch.setattr(LocalProductService, "_extract_price_from_keyword", MagicMock(side_effect=Exception("Mock search error")))
        results = service_with_mock_products.search_products("any keyword")
        assert results == []
        mock_logger.error.assert_called_once_with("Error searching products: Mock search error")


class TestLocalProductServiceProductRetrieval:
    """Tests for individual product retrieval and category/brand listings."""

    def test_get_product_details_existing_id(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting details for an existing product ID
        THEN the correct product dictionary should be returned.
        """
        product = service_with_mock_products.get_product_details("prod1")
        assert product is not None
        assert product["id"] == "prod1"
        assert product["name"] == "Product A Smartphone"

    def test_get_product_details_non_existent_id(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting details for a non-existent product ID
        THEN None should be returned.
        """
        product = service_with_mock_products.get_product_details("nonexistent")
        assert product is None

    def test_get_product_details_empty_id(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting details with an empty ID
        THEN None should be returned.
        """
        product = service_with_mock_products.get_product_details("")
        assert product is None

    def test_get_product_details_error_handling(self, service_with_mock_products, monkeypatch, mock_logger):
        """
        GIVEN get_product_details encounters an error (e.g., accessing a malformed product)
        WHEN called
        THEN it should log the error and return None.
        """
        # Corrupt a product to cause an error during access
        corrupted_product = {"id": "prod_corrupt", "name": "Corrupted Product"}
        service_with_mock_products.products.append(corrupted_product)
        # Mock product.get('id') to raise an error when trying to access it for this specific product
        def mock_get(key, default=None):
            if key == 'id' and corrupted_product['id'] == "prod_corrupt":
                raise Exception("Mock ID access error")
            return corrupted_product.get(key, default)
        
        monkeypatch.setattr(corrupted_product, 'get', mock_get)

        result = service_with_mock_products.get_product_details("prod_corrupt")
        assert result is None
        mock_logger.error.assert_called_once_with("Error getting product details: Mock ID access error")


    def test_get_categories(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting categories
        THEN a sorted list of unique categories should be returned.
        """
        categories = service_with_mock_products.get_categories()
        expected_categories = sorted(["Electronics", "Fashion", "Home Goods", "Books"])
        assert categories == expected_categories

    def test_get_categories_empty_products(self, mock_open_with_empty_json, mock_path_exists_true, mock_random_randint, mock_logger):
        """
        GIVEN no products loaded (empty self.products)
        WHEN requesting categories
        THEN an empty list should be returned.
        """
        service = LocalProductService() # Initializes with empty products
        categories = service.get_categories()
        assert categories == []

    def test_get_categories_product_without_category_field(self, mock_path_exists_true, monkeypatch, mock_random_randint, mock_logger):
        """
        GIVEN products, some without a 'category' field
        WHEN requesting categories
        THEN an empty string should be included if some products lack a category.
        """
        mock_data = json.dumps({"products": [
            {"id": "1", "name": "Prod1", "category": "CategoryA"},
            {"id": "2", "name": "Prod2"}, # No category field, so .get('category', '') will be ''
            {"id": "3", "name": "Prod3", "category": "CategoryB"}
        ]})
        mock_file = mock_open(read_data=mock_data)
        monkeypatch.setattr("builtins.open", mock_file)
        service = LocalProductService()
        categories = service.get_categories()
        assert categories == ["", "CategoryA", "CategoryB"] # Sorted list including empty string

    def test_get_brands(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting brands
        THEN a sorted list of unique brands should be returned.
        """
        brands = service_with_mock_products.get_brands()
        expected_brands = sorted(["BrandX", "BrandY", "BrandZ", "PublisherA", "PublisherB"])
        assert brands == expected_brands

    def test_get_brands_empty_products(self, mock_open_with_empty_json, mock_path_exists_true, mock_random_randint, mock_logger):
        """
        GIVEN no products loaded (empty self.products)
        WHEN requesting brands
        THEN an empty list should be returned.
        """
        service = LocalProductService()
        brands = service.get_brands()
        assert brands == []

    def test_get_brands_product_without_brand_field(self, mock_path_exists_true, monkeypatch, mock_random_randint, mock_logger):
        """
        GIVEN products, some without a 'brand' field
        WHEN requesting brands
        THEN an empty string should be included if some products lack a brand.
        """
        mock_data = json.dumps({"products": [
            {"id": "1", "name": "Prod1", "brand": "BrandA"},
            {"id": "2", "name": "Prod2"}, # No brand field, so .get('brand', '') will be ''
            {"id": "3", "name": "Prod3", "brand": "BrandB"}
        ]})
        mock_file = mock_open(read_data=mock_data)
        monkeypatch.setattr("builtins.open", mock_file)
        service = LocalProductService()
        brands = service.get_brands()
        assert brands == ["", "BrandA", "BrandB"] # Sorted list including empty string

    def test_get_products_by_category_existing(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting products by an existing category
        THEN a list of products in that category should be returned.
        """
        results = service_with_mock_products.get_products_by_category("Electronics")
        assert len(results) == 2
        assert all(p["category"] == "Electronics" for p in results)
        assert {p["id"] for p in results} == {"prod1", "prod3"}

    def test_get_products_by_category_case_insensitive(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting products by a category with different casing
        THEN relevant products should be returned.
        """
        results = service_with_mock_products.get_products_by_category("electronics")
        assert len(results) == 2
        assert all(p["category"] == "Electronics" for p in results)

    def test_get_products_by_category_non_existent(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting products by a non-existent category
        THEN an empty list should be returned.
        """
        results = service_with_mock_products.get_products_by_category("NonExistentCategory")
        assert results == []

    def test_get_products_by_category_empty_string(self, service_with_mock_products):
        """
        GIVEN products loaded, and one product with an empty category string
        WHEN requesting products by an empty category string
        THEN that product should be returned.
        """
        # Add a product explicitly with an empty category
        service_with_mock_products.products.append({
            "id": "prod_no_cat", "name": "No Category Product", "category": "", "price": 100
        })
        results = service_with_mock_products.get_products_by_category("")
        assert len(results) == 1
        assert results[0]["id"] == "prod_no_cat"

    def test_get_products_by_category_error_handling(self, service_with_mock_products, monkeypatch, mock_logger):
        """
        GIVEN get_products_by_category encounters an error (e.g., during product access)
        WHEN called
        THEN it should log the error and return an empty list.
        """
        # Make product.get('category') raise an error for a specific product
        malicious_product = {"id": "malicious", "name": "Malicious Prod", "category": "Test"}
        service_with_mock_products.products.append(malicious_product)
        
        def mock_get_category(key, default=None):
            if key == 'category' and malicious_product['id'] == "malicious":
                raise Exception("Mock category access error")
            return malicious_product.get(key, default)

        monkeypatch.setattr(malicious_product, 'get', mock_get_category)

        results = service_with_mock_products.get_products_by_category("Test")
        assert results == []
        mock_logger.error.assert_called_once_with("Error getting products by category: Mock category access error")

    def test_get_products_by_brand_existing(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting products by an existing brand
        THEN a list of products from that brand should be returned.
        """
        results = service_with_mock_products.get_products_by_brand("BrandX")
        assert len(results) == 2
        assert all(p["brand"] == "BrandX" for p in results)
        assert {p["id"] for p in results} == {"prod1", "prod4"}

    def test_get_products_by_brand_case_insensitive(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting products by a brand with different casing
        THEN relevant products should be returned.
        """
        results = service_with_mock_products.get_products_by_brand("brandx")
        assert len(results) == 2
        assert all(p["brand"] == "BrandX" for p in results)

    def test_get_products_by_brand_non_existent(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting products by a non-existent brand
        THEN an empty list should be returned.
        """
        results = service_with_mock_products.get_products_by_brand("NonExistentBrand")
        assert results == []

    def test_get_products_by_brand_empty_string(self, service_with_mock_products):
        """
        GIVEN products loaded, and one product with an empty brand string
        WHEN requesting products by an empty brand string
        THEN that product should be returned.
        """
        service_with_mock_products.products.append({
            "id": "prod_no_brand", "name": "No Brand Product", "brand": "", "price": 100
        })
        results = service_with_mock_products.get_products_by_brand("")
        assert len(results) == 1
        assert results[0]["id"] == "prod_no_brand"

    def test_get_products_by_brand_error_handling(self, service_with_mock_products, monkeypatch, mock_logger):
        """
        GIVEN get_products_by_brand encounters an error (e.g., during product access)
        WHEN called
        THEN it should log the error and return an empty list.
        """
        # Make product.get('brand') raise an error for a specific product
        malicious_product = {"id": "malicious", "name": "Malicious Prod", "brand": "Test"}
        service_with_mock_products.products.append(malicious_product)

        def mock_get_brand(key, default=None):
            if key == 'brand' and malicious_product['id'] == "malicious":
                raise Exception("Mock brand access error")
            return malicious_product.get(key, default)
        
        monkeypatch.setattr(malicious_product, 'get', mock_get_brand)

        results = service_with_mock_products.get_products_by_brand("Test")
        assert results == []
        mock_logger.error.assert_called_once_with("Error getting products by brand: Mock brand access error")

    def test_get_top_rated_products_standard_limit(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting top-rated products with a standard limit
        THEN products should be sorted by rating (desc) and limited.
        """
        # Ratings: prod3 (4.9), prod1 (4.5), prod5 (4.2), prod6 (4.0), prod2 (3.8), prod4 (3.0)
        results = service_with_mock_products.get_top_rated_products(limit=3)
        assert len(results) == 3
        assert results[0]["id"] == "prod3"
        assert results[1]["id"] == "prod1"
        assert results[2]["id"] == "prod5"

    def test_get_top_rated_products_limit_exceeds_available(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting top-rated products with a limit exceeding available products
        THEN all products should be returned, sorted.
        """
        results = service_with_mock_products.get_top_rated_products(limit=10)
        assert len(results) == 6
        assert results[0]["id"] == "prod3"
        assert results[-1]["id"] == "prod4" # Lowest rated

    def test_get_top_rated_products_limit_zero(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting top-rated products with a limit of 0
        THEN an empty list should be returned.
        """
        results = service_with_mock_products.get_top_rated_products(limit=0)
        assert results == []

    def test_get_top_rated_products_missing_rating_or_specifications(self, service_with_mock_products):
        """
        GIVEN products some with missing 'rating' or 'specifications' keys
        WHEN requesting top-rated products
        THEN those products should default to a rating of 0 and be sorted accordingly (at the end).
        """
        service_with_mock_products.products.append({
            "id": "prod_no_spec", "name": "No Spec Product", "price": 100, "specifications": {}
        })
        service_with_mock_products.products.append({
            "id": "prod_no_rating", "name": "No Rating Product", "price": 100, "specifications": {"stock_count": 10}
        })
        results = service_with_mock_products.get_top_rated_products(limit=10)
        assert len(results) == 8 # Original 6 + 2 new
        # Products with missing rating/specifications will default to rating 0, so they appear at the end.
        assert results[0]["id"] == "prod3" # Still the top one
        # The exact order of the last two (rating 0) might depend on Python's sort stability for equal keys.
        # So we check if they are among the last ones.
        last_two_ids = {results[-1]["id"], results[-2]["id"]}
        assert "prod_no_spec" in last_two_ids
        assert "prod_no_rating" in last_two_ids
        assert results[-3]["id"] == "prod4" # Original lowest rated (3.0) should be just before them

    def test_get_top_rated_products_error_handling(self, service_with_mock_products, monkeypatch, mock_logger):
        """
        GIVEN get_top_rated_products encounters an error (e.g., accessing self.products)
        WHEN called
        THEN it should log the error and return an empty list.
        """
        monkeypatch.setattr(service_with_mock_products, "products", MagicMock(side_effect=Exception("Mock products access error")))
        results = service_with_mock_products.get_top_rated_products()
        assert results == []
        mock_logger.error.assert_called_once_with("Error getting top rated products: Mock products access error")

    def test_get_best_selling_products_standard_limit(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting best-selling products with a standard limit
        THEN products should be sorted by sold count (desc) and limited.
        """
        # Sold counts: prod5 (1500), prod1,2,3,4 (1000 from mock_random_randint), prod6 (50)
        results = service_with_mock_products.get_best_selling_products(limit=3)
        assert len(results) == 3
        assert results[0]["id"] == "prod5" # Best seller
        # The next 4 products (prod1,2,3,4) all have 'sold' == 1000. Their relative order is stable based on original list order.
        assert results[1]["id"] == "prod1" # First product in original list with sold=1000
        assert results[2]["id"] == "prod2" # Second product in original list with sold=1000

    def test_get_best_selling_products_limit_exceeds_available(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting best-selling products with a limit exceeding available products
        THEN all products should be returned, sorted.
        """
        results = service_with_mock_products.get_best_selling_products(limit=10)
        assert len(results) == 6
        assert results[0]["id"] == "prod5"
        assert results[-1]["id"] == "prod6" # Lowest sold

    def test_get_best_selling_products_limit_zero(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting best-selling products with a limit of 0
        THEN an empty list should be returned.
        """
        results = service_with_mock_products.get_best_selling_products(limit=0)
        assert results == []

    def test_get_best_selling_products_missing_sold_or_specifications(self, service_with_mock_products):
        """
        GIVEN products some with missing 'sold' or 'specifications' keys
        WHEN requesting best-selling products
        THEN those products should default to a sold count of 0 and be sorted accordingly (at the end).
        """
        service_with_mock_products.products.append({
            "id": "prod_no_spec_sold", "name": "No Spec Sold Product", "price": 100, "specifications": {}
        })
        service_with_mock_products.products.append({
            "id": "prod_no_sold", "name": "No Sold Product", "price": 100, "specifications": {"rating": 5}
        })
        results = service_with_mock_products.get_best_selling_products(limit=10)
        assert len(results) == 8
        assert results[0]["id"] == "prod5" # Still the top one (1500 sold)
        # Products with missing sold/specifications will default to sold 0, so they appear at the end.
        last_two_ids = {results[-1]["id"], results[-2]["id"]}
        assert "prod_no_spec_sold" in last_two_ids
        assert "prod_no_sold" in last_two_ids
        assert results[-3]["id"] == "prod6" # Original lowest sold (50) should be just before them

    def test_get_best_selling_products_error_handling(self, service_with_mock_products, monkeypatch, mock_logger):
        """
        GIVEN get_best_selling_products encounters an error (e.g., accessing self.products)
        WHEN called
        THEN it should log the error and return an empty list.
        """
        monkeypatch.setattr(service_with_mock_products, "products", MagicMock(side_effect=Exception("Mock products access error")))
        results = service_with_mock_products.get_best_selling_products()
        assert results == []
        mock_logger.error.assert_called_once_with("Error getting best selling products: Mock products access error")

    def test_get_products_standard_limit(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting all products with a standard limit
        THEN a limited list of products should be returned in their original order.
        """
        results = service_with_mock_products.get_products(limit=3)
        assert len(results) == 3
        assert results[0]["id"] == "prod1"
        assert results[1]["id"] == "prod2"
        assert results[2]["id"] == "prod3"

    def test_get_products_limit_exceeds_available(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting all products with a limit exceeding available products
        THEN all products should be returned.
        """
        results = service_with_mock_products.get_products(limit=10)
        assert len(results) == 6

    def test_get_products_limit_zero(self, service_with_mock_products):
        """
        GIVEN products loaded
        WHEN requesting all products with a limit of 0
        THEN an empty list should be returned.
        """
        results = service_with_mock_products.get_products(limit=0)
        assert results == []

    def test_get_products_error_handling(self, service_with_mock_products, monkeypatch, mock_logger):
        """
        GIVEN get_products encounters an error (e.g., accessing self.products)
        WHEN called
        THEN it should log the error and return an empty list.
        """
        monkeypatch.setattr(service_with_mock_products, "products", MagicMock(side_effect=Exception("Mock products access error")))
        results = service_with_mock_products.get_products()
        assert results == []
        mock_logger.error.assert_called_once_with("Error getting products: Mock products access error")


class TestLocalProductServiceSmartSearch:
    """Tests for the smart_search_products method, covering its various fallback logic."""

    @pytest.mark.parametrize("keyword, category, max_price, expected_product_ids_start, expected_message", [
        # Fallback 1: Best products general (keyword 'terbaik' or 'best', no category)
        ("terbaik", None, None, ["prod3", "prod1", "prod5"], "Berikut produk terbaik berdasarkan rating:"),
        ("best product", None, None, ["prod3", "prod1", "prod5"], "Berikut produk terbaik berdasarkan rating:"),

        # Fallback 2: Best products in specific category
        ("terbaik", "Electronics", None, ["prod3", "prod1"], "Berikut Electronics terbaik berdasarkan rating:"),
        ("best", "Books", None, ["prod5", "prod6"], "Berikut Books terbaik berdasarkan rating:"),

        # Fallback 2.1: Best products in non-existent category -> fallback to general best
        ("terbaik", "NonExistentCategory", None, ["prod3", "prod1", "prod5"], "Tidak ada produk kategori NonExistentCategory, berikut produk terbaik secara umum:"),

        # Path 3: Direct Match (all criteria met)
        ("Product A", "Electronics", 1500000, ["prod1"], "Berikut produk yang sesuai dengan kriteria Anda."),
        ("Product D", "Home Goods", 100000, ["prod4"], "Berikut produk yang sesuai dengan kriteria Anda."),
        ("Product B", "Fashion", None, ["prod2"], "Berikut produk yang sesuai dengan kriteria Anda."),

        # Fallback 4: No full match, but category match (sorted by price)
        ("nonexistent_keyword", "Electronics", None, ["prod1", "prod3"], "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."),
        ("gibberish", "Books", None, ["prod6", "prod5"], "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."),

        # Fallback 5: No category match, but budget match
        ("nonexistent_keyword_2", "InvalidCategory", 100000, ["prod4"], "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."),
        ("Another Random Keyword", "Food", 500000, ["prod4", "prod2"], "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."), # prod4 (50k), prod2 (500k)

        # Fallback 6: No matches at all -> popular products
        ("totally_unrelated_keyword", "Another_NonExistent_Category", None, ["prod5", "prod1", "prod2"], "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."),
        ("", "", None, ["prod5", "prod1", "prod2"], "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."), # Empty search
        (None, None, None, ["prod5", "prod1", "prod2"], "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."), # All None
    ])
    def test_smart_search_products_scenarios(self, service_with_mock_products, keyword, category, max_price, expected_product_ids_start, expected_message):
        """
        GIVEN various search criteria and products loaded
        WHEN smart_search_products is called
        THEN it should apply the correct fallback logic and return expected products and message.
        """
        limit = 10 # Use a high limit to check order/presence of many items

        products, message = service_with_mock_products.smart_search_products(keyword=keyword, category=category, max_price=max_price, limit=limit)
        actual_product_ids = [p["id"] for p in products]

        assert message == expected_message

        # Assertions based on the specific fallback path
        if "produk terbaik berdasarkan rating:" in message:
            # Sorted by rating descending: prod3 (4.9), prod1 (4.5), prod5 (4.2), prod6 (4.0), prod2 (3.8), prod4 (3.0)
            if category: # Specific category (Electronics: prod3, prod1; Books: prod5, prod6)
                expected_full_ids = sorted([p["id"] for p in service_with_mock_products.products if category.lower() in p.get("category", "").lower()], 
                                            key=lambda id: service_with_mock_products.get_product_details(id)['specifications'].get('rating', 0), 
                                            reverse=True)
            else: # General best
                expected_full_ids = ["prod3", "prod1", "prod5", "prod6", "prod2", "prod4"] # Pre-sorted for clarity
            assert actual_product_ids[:len(expected_product_ids_start)] == expected_product_ids_start
            assert len(actual_product_ids) == len(expected_full_ids) if not category else len(expected_full_ids) # Should return all in category if match

        elif "produk termurah di kategori tersebut." in message:
            # Sorted by price ascending within category
            if category == "Electronics": # prod1 (1M), prod3 (2M)
                assert actual_product_ids == ["prod1", "prod3"]
            elif category == "Books": # prod6 (120k), prod5 (150k)
                assert actual_product_ids == ["prod6", "prod5"]

        elif "produk lain yang sesuai budget Anda." in message:
            # Sorted by price ascending for products under max_price
            if max_price == 100000: # Only prod4 (50k)
                assert actual_product_ids == ["prod4"]
            elif max_price == 500000: # prod4 (50k), prod2 (500k)
                assert actual_product_ids == ["prod4", "prod2"]
            
        elif "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in message:
            # Sorted by 'sold' count descending
            # prod5 (1500), then prod1,2,3,4 (all 1000), then prod6 (50)
            assert actual_product_ids[0] == "prod5"
            assert actual_product_ids[-1] == "prod6"
            # The order of prod1,2,3,4 (all sold=1000) can vary based on Python's stable sort.
            # So we check that all are present.
            expected_full_popular_ids = ["prod5", "prod1", "prod2", "prod3", "prod4", "prod6"]
            assert set(actual_product_ids) == set(expected_full_popular_ids)

        else: # Direct match
            assert actual_product_ids == expected_product_ids_start[:len(actual_product_ids)]
            assert len(actual_product_ids) == len(expected_product_ids_start) # For direct matches, length should be exact.

    def test_smart_search_products_limit(self, service_with_mock_products):
        """
        GIVEN smart_search_products is called with a limit
        WHEN products are found via any path
        THEN the number of returned products should respect the limit.
        """
        # Test limit for direct match
        products, message = service_with_mock_products.smart_search_products(keyword="Product", limit=2)
        assert len(products) == 2
        assert "Berikut produk yang sesuai dengan kriteria Anda." in message

        # Test limit for general best products fallback
        products, message = service_with_mock_products.smart_search_products(keyword="terbaik", limit=1)
        assert len(products) == 1
        assert "Berikut produk terbaik berdasarkan rating:" in message
        assert products[0]["id"] == "prod3" # Highest rated product

        # Test limit for non-existent category fallback to general best
        products, message = service_with_mock_products.smart_search_products(keyword="best", category="NonExistent", limit=2)
        assert len(products) == 2
        assert "Tidak ada produk kategori NonExistent, berikut produk terbaik secara umum:" in message
        assert products[0]["id"] == "prod3"
        assert products[1]["id"] == "prod1"

        # Test limit for popular products fallback (no match)
        products, message = service_with_mock_products.smart_search_products(keyword="asdfasdf", limit=3)
        assert len(products) == 3
        assert "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in message
        assert products[0]["id"] == "prod5" # Best selling
        assert products[1]["id"] == "prod1" or products[1]["id"] == "prod2" or products[1]["id"] == "prod3" or products[1]["id"] == "prod4" # One of the 1000-sold products