import pytest
import json
import random
import builtins
import logging
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

# Adjust import path based on project structure.
# If test file is at `test_services/local_product_service.py`
# and source is at `app/services/local_product_service.py`
# then the import should be relative to the project root.
from app.services.local_product_service import LocalProductService

# --- Fixtures ---

@pytest.fixture
def mock_logger():
    """Mocks the logger to capture log messages for assertions."""
    with patch('app.services.local_product_service.logger') as mock_log:
        yield mock_log

@pytest.fixture
def mock_products_path(tmp_path):
    """
    Mocks the Path object to control the existence and content of 'data/products.json'.
    This fixture ensures that `Path(__file__).parent.parent.parent / "data" / "products.json"`
    points to a controllable temporary path.
    """
    # Simulate the project root path for testing purposes
    mock_project_root = tmp_path / "app" / "services" / ".." / ".."
    mock_data_dir = mock_project_root / "data"
    mock_data_dir.mkdir(parents=True, exist_ok=True)
    mock_products_file = mock_data_dir / "products.json"

    # Patch Path.__init__ and related methods for the specific products.json path
    original_path_init = Path.__init__
    original_path_truediv = Path.__truediv__
    original_path_exists = Path.exists
    original_path_str = Path.__str__

    class MockedPath(Path):
        def __init__(self, *args, **kwargs):
            # Check if this is the specific path we want to mock
            if len(args) >= 3 and str(args[-3]) == 'data' and str(args[-2]) == 'products.json':
                self._mock_path_target = mock_products_file
                original_path_init(self, str(self._mock_path_target)) # Init with the temp path
            else:
                original_path_init(self, *args, **kwargs)

        def exists(self):
            if hasattr(self, '_mock_path_target'):
                return self._mock_path_target.exists()
            return original_path_exists(self)

        def __truediv__(self, other):
            if hasattr(self, '_mock_path_target'):
                return self._mock_path_target / other
            return original_path_truediv(self, other)

        def __str__(self):
            if hasattr(self, '_mock_path_target'):
                return str(self._mock_path_target)
            return original_path_str(self)

    # Patch Path to use our custom MockedPath
    with patch('app.services.local_product_service.Path', new=MockedPath):
        yield mock_products_file


@pytest.fixture
def create_mock_json_file(mock_products_path):
    """Helper to create a mock products.json file with specified content."""
    def _creator(content: str, encoding: str = 'utf-8'):
        with open(mock_products_path, 'w', encoding=encoding) as f:
            f.write(content)
    return _creator

@pytest.fixture(autouse=True)
def mock_random_randint():
    """Mocks random.randint to return a predictable value (500) for 'sold' count, globally."""
    with patch('random.randint', return_value=500) as mock_rand:
        yield mock_rand

@pytest.fixture
def base_test_products_data():
    """Provides a consistent set of product data for testing."""
    return {
        "products": [
            {
                "id": "prod1", "name": "Laptop A", "category": "Laptop", "brand": "BrandX",
                "price": 10000000, "currency": "IDR", "description": "Powerful laptop.",
                "rating": 4.5, "stock_count": 10, "availability": "in_stock", "reviews_count": 50,
                "specifications": {"cpu": "i7", "ram": "16GB"}
            },
            {
                "id": "prod2", "name": "Smartphone B", "category": "Smartphone", "brand": "BrandY",
                "price": 5000000, "currency": "IDR", "description": "Camera focused phone.",
                "rating": 4.0, "stock_count": 20, "availability": "in_stock", "reviews_count": 30,
                "specifications": {"camera": "108MP"}
            },
            {
                "id": "prod3", "name": "Headphones C", "category": "Audio", "brand": "BrandX",
                "price": 1500000, "currency": "IDR", "description": "Noise cancelling.",
                "rating": 4.8, "stock_count": 5, "availability": "out_of_stock", "reviews_count": 80,
                "specifications": {"wireless": True}
            },
            {
                "id": "prod4", "name": "Tablet D", "category": "Tablet", "brand": "BrandZ",
                "price": 7000000, "currency": "IDR", "description": "For creativity.",
                "rating": 4.2, "stock_count": 15, "availability": "in_stock", "reviews_count": 25,
                "specifications": {"screen_size": "10 inch"}
            },
            {
                "id": "prod5", "name": "Gaming PC", "category": "PC", "brand": "BrandX",
                "price": 25000000, "currency": "IDR", "description": "High-end gaming machine.",
                "rating": 4.9, "stock_count": 3, "availability": "in_stock", "reviews_count": 100,
                "specifications": {"gpu": "RTX 4090"}
            },
            {
                "id": "prod6", "name": "Entry Laptop", "category": "Laptop", "brand": "BudgetTech",
                "price": 3000000, "currency": "IDR", "description": "Affordable laptop for students.",
                "rating": 3.5, "stock_count": 50, "availability": "in_stock", "reviews_count": 10
            }
        ]
    }

@pytest.fixture
def local_product_service_instance_with_data(create_mock_json_file, base_test_products_data):
    """Fixture to provide a LocalProductService instance with pre-loaded data."""
    create_mock_json_file(json.dumps(base_test_products_data))
    service = LocalProductService()
    return service, base_test_products_data['products']

@pytest.fixture
def local_product_service_instance_empty_data(create_mock_json_file):
    """Fixture to provide a LocalProductService instance with empty data."""
    create_mock_json_file(json.dumps({"products": []}))
    service = LocalProductService()
    return service

@pytest.fixture
def local_product_service_instance_missing_file(mock_products_path):
    """Fixture to provide a LocalProductService instance where products.json is missing."""
    if mock_products_path.exists():
        mock_products_path.unlink() # Ensure the file does not exist
    service = LocalProductService()
    return service


# --- Test Class ---

class TestLocalProductService:

    # --- Test __init__ ---
    def test_init_loads_products_successfully(self, local_product_service_instance_with_data, mock_logger, mock_random_randint):
        """Tests that __init__ successfully loads products and logs info."""
        service, _ = local_product_service_instance_with_data
        assert service.products is not None
        assert len(service.products) > 0
        mock_logger.info.assert_called_with(f"Loaded {len(service.products)} local products from JSON file")
        # Ensure random.randint was called for each product during transformation
        assert mock_random_randint.call_count == len(service.products)
        assert service.products[0]['specifications']['sold'] == 500 # From mock_random_randint

    def test_init_uses_fallback_on_file_not_found(self, local_product_service_instance_missing_file, mock_logger, mock_products_path):
        """Tests that __init__ uses fallback products when the JSON file is not found."""
        service = local_product_service_instance_missing_file
        assert len(service.products) == 8 # Fallback products count
        mock_logger.error.assert_any_call(f"Products JSON file not found at: {mock_products_path}")
        mock_logger.warning.assert_called_with("Using fallback products due to JSON file loading error")

    # --- Test _load_local_products ---

    def test_load_local_products_success_utf8(self, create_mock_json_file, mock_logger):
        """Tests successful loading of a UTF-8 encoded JSON file."""
        json_content = """{"products": [{"id": "a", "name": "Test Product", "category": "Test", "price": 1000, "rating": 4.0}]}"""
        create_mock_json_file(json_content, encoding='utf-8')
        service = LocalProductService()
        products = service._load_local_products()
        assert len(products) == 1
        assert products[0]['id'] == 'a'
        assert products[0]['name'] == 'Test Product'
        assert products[0]['price'] == 1000
        assert products[0]['specifications']['rating'] == 4.0
        assert products[0]['specifications']['sold'] == 500 # From mock_random_randint
        assert products[0]['images'] == ["https://example.com/a.jpg"]
        mock_logger.info.assert_any_call(f"Successfully loaded 1 products from JSON file using utf-8 encoding")

    def test_load_local_products_success_with_bom(self, create_mock_json_file, mock_logger):
        """Tests successful loading of a JSON file with a UTF-8 BOM."""
        json_content = "\ufeff" + """{"products": [{"id": "bom_prod", "name": "BOM Product", "price": 500}]}"""
        create_mock_json_file(json_content, encoding='utf-8-sig')
        service = LocalProductService()
        products = service._load_local_products()
        assert len(products) == 1
        assert products[0]['name'] == 'BOM Product'
        mock_logger.info.assert_any_call("Successfully loaded 1 products from JSON file using utf-8-sig encoding")


    def test_load_local_products_missing_file_uses_fallback(self, mock_products_path, mock_logger):
        """Tests _load_local_products using fallback when file is genuinely missing."""
        if mock_products_path.exists():
            mock_products_path.unlink()
        
        service = LocalProductService()
        products = service._load_local_products()
        assert len(products) == 8 # Fallback products count
        mock_logger.error.assert_called_with(f"Products JSON file not found at: {mock_products_path}")
        mock_logger.warning.assert_called_with("Using fallback products due to JSON file loading error")


    def test_load_local_products_invalid_json_uses_fallback(self, create_mock_json_file, mock_logger):
        """Tests _load_local_products using fallback when JSON content is invalid."""
        create_mock_json_file("this is not json", encoding='utf-8')
        service = LocalProductService()
        products = service._load_local_products()
        assert len(products) == 8 # Fallback products
        mock_logger.warning.assert_any_call(f"Failed to load with utf-8 encoding: Expecting value: line 1 column 1 (char 0)")
        mock_logger.error.assert_called_with("All encoding attempts failed, using fallback products")
        mock_logger.warning.assert_called_with("Using fallback products due to JSON file loading error")

    def test_load_local_products_encoding_failure_then_success(self, create_mock_json_file, mock_logger):
        """
        Tests _load_local_products trying multiple encodings, with some failing before a success.
        This requires detailed mocking of `builtins.open`.
        """
        # Content valid for latin-1 but not utf-8
        content_latin1 = b'{"products": [{"id": "enc_prod", "name": "Produkt\xe4", "price": 100}]}'.decode('latin-1')
        
        # Simulate `open` attempts for different encodings
        # It's important to simulate the `read()` call for each `open` attempt.
        mock_open_instance = mock_open()
        mock_open_instance.side_effect = [
            MagicMock(read=MagicMock(side_effect=UnicodeDecodeError('utf-16-le', b'', 0, 1, 'bad byte'))),
            MagicMock(read=MagicMock(side_effect=UnicodeDecodeError('utf-16', b'', 0, 1, 'bad byte'))),
            MagicMock(read=MagicMock(side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'bad byte'))),
            MagicMock(read=MagicMock(side_effect=UnicodeDecodeError('utf-8-sig', b'', 0, 1, 'bad byte'))),
            MagicMock(read=MagicMock(return_value=content_latin1)), # Success with latin-1
            # Add more mocks for cp1252 if it gets this far in sequence
        ]
        
        with patch('builtins.open', new=mock_open_instance):
            # We also need to ensure Path.exists() is true for the file to be opened
            with patch('app.services.local_product_service.Path.exists', return_value=True):
                service = LocalProductService()
                products = service._load_local_products()

                assert len(products) == 1
                assert products[0]['name'] == 'Produktä'
                assert products[0]['id'] == 'enc_prod'
                assert products[0]['price'] == 100
                
                mock_logger.warning.assert_any_call(f"Failed to load with utf-16-le encoding: bad byte")
                mock_logger.warning.assert_any_call(f"Failed to load with utf-16 encoding: bad byte")
                mock_logger.warning.assert_any_call(f"Failed to load with utf-8 encoding: bad byte")
                mock_logger.warning.assert_any_call(f"Failed to load with utf-8-sig encoding: bad byte")
                mock_logger.info.assert_any_call(f"Successfully loaded 1 products from JSON file using latin-1 encoding")

    def test_load_local_products_general_exception_uses_fallback(self, mock_logger):
        """Tests _load_local_products using fallback on a general exception (e.g., IOError)."""
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with patch('app.services.local_product_service.Path.exists', return_value=True):
                service = LocalProductService()
                products = service._load_local_products()
                assert len(products) == 8 # Fallback products
                mock_logger.error.assert_called_with("Error loading products from JSON file: Permission denied")
                mock_logger.warning.assert_called_with("Using fallback products due to JSON file loading error")

    def test_load_local_products_empty_json_file(self, create_mock_json_file, mock_logger):
        """Tests _load_local_products with an empty JSON object."""
        create_mock_json_file('{}')
        service = LocalProductService()
        products = service._load_local_products()
        assert len(products) == 0
        mock_logger.info.assert_called_with(f"Successfully loaded 0 products from JSON file using utf-8 encoding")

    def test_load_local_products_json_missing_products_key(self, create_mock_json_file, mock_logger):
        """Tests _load_local_products with JSON missing the 'products' key."""
        create_mock_json_file('{"data": []}') # No 'products' key
        service = LocalProductService()
        products = service._load_local_products()
        assert len(products) == 0
        mock_logger.info.assert_called_with(f"Successfully loaded 0 products from JSON file using utf-8 encoding")

    def test_load_local_products_product_transformation_defaults(self, create_mock_json_file, mock_random_randint):
        """Tests product transformation with minimal input, checking default values."""
        json_content = """{"products": [{"id": "minimal", "name": "Minimal Prod"}]}"""
        create_mock_json_file(json_content)
        service = LocalProductService()
        products = service._load_local_products()
        assert len(products) == 1
        transformed_product = products[0]
        assert transformed_product['id'] == 'minimal'
        assert transformed_product['name'] == 'Minimal Prod'
        assert transformed_product['category'] == ''
        assert transformed_product['brand'] == ''
        assert transformed_product['price'] == 0
        assert transformed_product['currency'] == 'IDR'
        assert transformed_product['description'] == ''
        assert transformed_product['specifications']['rating'] == 0
        assert transformed_product['specifications']['sold'] == 500 # Mocked
        assert transformed_product['specifications']['stock'] == 0
        assert transformed_product['specifications']['condition'] == 'Baru'
        assert transformed_product['specifications']['shop_location'] == 'Indonesia'
        assert transformed_product['specifications']['shop_name'] == 'Unknown Store'
        assert transformed_product['availability'] == 'in_stock'
        assert transformed_product['reviews_count'] == 0
        assert transformed_product['images'] == ["https://example.com/minimal.jpg"]
        assert transformed_product['url'] == "https://shopee.co.id/minimal"

    def test_load_local_products_product_transformation_with_existing_specs(self, create_mock_json_file):
        """Tests product transformation with existing specifications and brand-derived shop name."""
        json_content = """{"products": [{"id": "full_spec", "name": "Full Spec Prod", "brand": "XYZ", "specifications": {"color": "red", "weight": "1kg"}}]}"""
        create_mock_json_file(json_content)
        service = LocalProductService()
        products = service._load_local_products()
        assert len(products) == 1
        transformed_product = products[0]
        assert transformed_product['specifications']['color'] == 'red'
        assert transformed_product['specifications']['weight'] == '1kg'
        assert transformed_product['specifications']['shop_name'] == 'XYZ Store' # Derived from brand

    # --- Test _get_fallback_products ---
    def test_get_fallback_products(self, mock_logger):
        """Tests that _get_fallback_products returns the hardcoded list and logs a warning."""
        service = LocalProductService() # No file setup needed, it directly calls _get_fallback_products
        fallback_products = service._get_fallback_products()
        assert len(fallback_products) == 8
        assert fallback_products[0]['id'] == '1'
        assert fallback_products[0]['name'] == 'iPhone 15 Pro Max'
        mock_logger.warning.assert_called_with("Using fallback products due to JSON file loading error")

    # --- Test search_products ---
    @pytest.mark.parametrize("keyword, expected_ids, expected_count, description", [
        ("laptop", ["prod1", "prod6"], 2, "Basic keyword match on name/category"),
        ("phone", ["prod2"], 1, "Keyword match on description"),
        ("BrandX", ["prod5", "prod1", "prod3"], 3, "Keyword match on brand, sorted by relevance"),
        ("gaming rtx", ["prod5"], 1, "Multiple keywords on specs"),
        ("Product", [], 0, "No match"),
        ("powerful", ["prod1"], 1, "Keyword match on description"),
        ("camera", ["prod2"], 1, "Keyword match on description"),
        ("noise", ["prod3"], 1, "Keyword match on description"),
        ("creativity", ["prod4"], 1, "Keyword match on description"),
        ("high-end", ["prod5"], 1, "Keyword match on description"),
        ("affordable", ["prod6"], 1, "Keyword match on description"),
        ("BrandY", ["prod2"], 1, "Match by brand"),
        ("BrandZ", ["prod4"], 1, "Match by brand"),
        ("BrandX Powerful", ["prod1"], 1, "Combination of keywords matching multiple fields (name and brand)"),
        ("brandx laptop", ["prod1"], 1, "Combination of brand and category/name"),
        ("audio wireless", ["prod3"], 1, "Combination of category and specification"),
        ("tablet 10 inch", ["prod4"], 1, "Combination of category and specification"),
        ("laptop i7", ["prod1"], 1, "Combination of category and specification"),
        ("smartphone 108mp", ["prod2"], 1, "Combination of category and specification"),
        ("PC RTX", ["prod5"], 1, "Combination of category and specification"),
        ("unknown", [], 0, "Keyword that does not exist"),
    ])
    def test_search_products_basic_keyword_matching(self, local_product_service_instance_with_data, keyword, expected_ids, expected_count, description):
        """Tests basic keyword matching across various product fields."""
        service, _ = local_product_service_instance_with_data
        results = service.search_products(keyword, limit=10)
        assert len(results) == expected_count, f"Failed for keyword '{keyword}': {description}"
        assert [p['id'] for p in results] == expected_ids, f"Failed for keyword '{keyword}': {description}"

    def test_search_products_case_insensitivity(self, local_product_service_instance_with_data):
        """Tests that keyword searches are case-insensitive."""
        service, _ = local_product_service_instance_with_data
        results = service.search_products("LAPTOP")
        assert len(results) == 2
        assert {p['id'] for p in results} == {"prod1", "prod6"}

    def test_search_products_limit(self, local_product_service_instance_with_data):
        """Tests the 'limit' parameter in search_products."""
        service, _ = local_product_service_instance_with_data
        results = service.search_products("BrandX", limit=2)
        assert len(results) == 2
        # Order based on relevance_score: 'BrandX' adds 5, so all are equal score (5).
        # Fallback to internal Python sort stability based on initial product list order.
        # Original: prod1, prod3, prod5
        assert [p['id'] for p in results] == ["prod1", "prod3"] 

    def test_search_products_no_match(self, local_product_service_instance_with_data):
        """Tests search_products returning an empty list when no matches are found."""
        service, _ = local_product_service_instance_with_data
        results = service.search_products("nonexistent_product")
        assert len(results) == 0

    def test_search_products_empty_keyword(self, local_product_service_instance_with_data):
        """Tests search_products with an empty keyword, which should return products based on limit."""
        service, _ = local_product_service_instance_with_data
        results = service.search_products("", limit=3)
        assert len(results) == 3
        # When keyword is empty, relevance score is 0 for all, so order is based on original list slice
        assert [p['id'] for p in results] == ["prod1", "prod2", "prod3"]

    def test_search_products_price_extraction_juta(self, local_product_service_instance_with_data):
        """Tests price extraction for 'juta' (million) and price filtering."""
        service, _ = local_product_service_instance_with_data
        results = service.search_products("laptop 15 juta") # Max price 15,000,000
        # prod1 (10M), prod6 (3M) are <= 15M. prod5 (25M) is excluded.
        assert len(results) == 2
        assert {p['id'] for p in results} == {"prod1", "prod6"}
        
        results_low_budget = service.search_products("hp 6 juta") # Max price 6,000,000
        # prod2 (5M) is <= 6M.
        assert len(results_low_budget) == 1
        assert results_low_budget[0]['id'] == 'prod2'

    def test_search_products_price_extraction_ribu(self, local_product_service_instance_with_data):
        """Tests price extraction for 'ribu' (thousand) and price filtering."""
        service, _ = local_product_service_instance_with_data
        # prod3 is 1.5jt (1,500,000 IDR), so 2000 ribu (2,000,000 IDR) should include it.
        results = service.search_products("headphones 2000 ribu")
        assert len(results) == 1
        assert results[0]['id'] == 'prod3'

    def test_search_products_price_extraction_budget_keywords(self, local_product_service_instance_with_data):
        """Tests price filtering based on budget keywords like 'murah'."""
        service, _ = local_product_service_instance_with_data
        results_murah = service.search_products("laptop murah") # max 5jt
        # prod1 (10jt) is out, prod6 (3jt) is in.
        assert len(results_murah) == 1
        assert results_murah[0]['id'] == 'prod6'

        results_hemat = service.search_products("phone hemat") # max 3jt
        # prod2 (5jt) is out.
        assert len(results_hemat) == 0

    def test_search_products_relevance_scoring_budget(self, local_product_service_instance_with_data):
        """Tests that budget-related keywords influence relevance scoring to prefer lower prices."""
        service, _ = local_product_service_instance_with_data
        # Products: prod1 (10M), prod2 (5M), prod3 (1.5M), prod4 (7M), prod5 (25M), prod6 (3M)
        results = service.search_products("murah", limit=3) # max 5jt, should prioritize lower price
        # Products that match price <= 5jt: prod2 (5M), prod3 (1.5M), prod6 (3M)
        # Scoring: (10M - price) / 1M. Higher score for lower prices.
        # prod3 (1.5M): (10M - 1.5M) / 1M = 8.5
        # prod6 (3M): (10M - 3M) / 1M = 7.0
        # prod2 (5M): (10M - 5M) / 1M = 5.0
        # Expected order: prod3, prod6, prod2
        assert [p['id'] for p in results] == ["prod3", "prod6", "prod2"]

    def test_search_products_error_handling(self, local_product_service_instance_with_data, mock_logger):
        """Tests error handling within search_products."""
        service, _ = local_product_service_instance_with_data
        with patch.object(service, '_extract_price_from_keyword', side_effect=ValueError("Test Error")):
            results = service.search_products("test")
            assert results == []
            mock_logger.error.assert_called_with("Error searching products: Test Error")

    # --- Test _extract_price_from_keyword ---
    @pytest.mark.parametrize("keyword, expected_price", [
        ("laptop 10 juta", 10000000),
        ("handphone 2 juta", 2000000),
        ("mouse 50 ribu", 50000),
        ("keyboard rp 750000", 750000),
        ("tablet 1500k", 1500000),
        ("pc 20m", 20000000),
        ("monitor 1000000rp", 1000000),
        ("murah", 5000000),
        ("budget", 5000000),
        ("hemat", 3000000),
        ("terjangkau", 4000000),
        ("ekonomis", 2000000),
        ("iphone", None), # No price
        ("tidak ada harga", None), # No price
        ("laptop 10.5 juta", 10000000), # regex only captures integer part (r'(\d+)')
    ])
    def test_extract_price_from_keyword_success(self, local_product_service_instance_with_data, keyword, expected_price):
        """Tests successful extraction of price from various keyword patterns."""
        service, _ = local_product_service_instance_with_data
        price = service._extract_price_from_keyword(keyword)
        assert price == expected_price

    def test_extract_price_from_keyword_error_handling(self, local_product_service_instance_with_data, mock_logger):
        """Tests error handling within _extract_price_from_keyword."""
        service, _ = local_product_service_instance_with_data
        with patch('re.search', side_effect=TypeError("Regex error")):
            price = service._extract_price_from_keyword("laptop 10 juta")
            assert price is None
            mock_logger.error.assert_called_with("Error extracting price from keyword: Regex error")

    # --- Test get_product_details ---
    def test_get_product_details_found(self, local_product_service_instance_with_data):
        """Tests finding product details by a valid ID."""
        service, _ = local_product_service_instance_with_data
        product = service.get_product_details("prod1")
        assert product is not None
        assert product['id'] == "prod1"
        assert product['name'] == "Laptop A"

    def test_get_product_details_not_found(self, local_product_service_instance_with_data):
        """Tests getting product details for a non-existent ID."""
        service, _ = local_product_service_instance_with_data
        product = service.get_product_details("nonexistent_id")
        assert product is None

    def test_get_product_details_error_handling(self, local_product_service_instance_with_data, mock_logger):
        """Tests error handling within get_product_details."""
        service, _ = local_product_service_instance_with_data
        with patch.object(service, 'products', new_callable=MagicMock) as mock_products:
            mock_products.__iter__.side_effect = Exception("Iteration error")
            product = service.get_product_details("prod1")
            assert product is None
            mock_logger.error.assert_called_with("Error getting product details: Iteration error")

    # --- Test get_categories ---
    def test_get_categories(self, local_product_service_instance_with_data):
        """Tests retrieving a sorted list of unique product categories."""
        service, _ = local_product_service_instance_with_data
        categories = service.get_categories()
        expected_categories = ["Audio", "Laptop", "PC", "Smartphone", "Tablet"]
        assert sorted(categories) == sorted(expected_categories)
        assert len(categories) == len(expected_categories)

    def test_get_categories_empty_data(self, local_product_service_instance_empty_data):
        """Tests get_categories with no products loaded."""
        service = local_product_service_instance_empty_data
        categories = service.get_categories()
        assert categories == []

    def test_get_categories_with_empty_category_field(self, create_mock_json_file):
        """Tests get_categories correctly handles products with empty category fields."""
        json_with_empty_category = json.dumps({"products": [
            {"id": "a", "name": "Item A", "category": "Electronics"},
            {"id": "b", "name": "Item B", "category": ""},
            {"id": "c", "name": "Item C", "category": "Gadgets"}
        ]})
        create_mock_json_file(json_with_empty_category)
        service = LocalProductService()
        categories = service.get_categories()
        assert sorted(categories) == ['', 'Electronics', 'Gadgets']

    # --- Test get_brands ---
    def test_get_brands(self, local_product_service_instance_with_data):
        """Tests retrieving a sorted list of unique product brands."""
        service, _ = local_product_service_instance_with_data
        brands = service.get_brands()
        expected_brands = ["BrandX", "BrandY", "BrandZ", "BudgetTech"]
        assert sorted(brands) == sorted(expected_brands)
        assert len(brands) == len(expected_brands)

    def test_get_brands_empty_data(self, local_product_service_instance_empty_data):
        """Tests get_brands with no products loaded."""
        service = local_product_service_instance_empty_data
        brands = service.get_brands()
        assert brands == []

    def test_get_brands_with_empty_brand_field(self, create_mock_json_file):
        """Tests get_brands correctly handles products with empty brand fields."""
        json_with_empty_brand = json.dumps({"products": [
            {"id": "a", "name": "Item A", "brand": "Brand1"},
            {"id": "b", "name": "Item B", "brand": ""},
            {"id": "c", "name": "Item C", "brand": "Brand2"}
        ]})
        create_mock_json_file(json_with_empty_brand)
        service = LocalProductService()
        brands = service.get_brands()
        assert sorted(brands) == ['', 'Brand1', 'Brand2']

    # --- Test get_products_by_category ---
    def test_get_products_by_category_found(self, local_product_service_instance_with_data):
        """Tests retrieving products for an existing category."""
        service, _ = local_product_service_instance_with_data
        products = service.get_products_by_category("Laptop")
        assert len(products) == 2
        assert {p['id'] for p in products} == {"prod1", "prod6"}

    def test_get_products_by_category_not_found(self, local_product_service_instance_with_data):
        """Tests retrieving products for a non-existent category."""
        service, _ = local_product_service_instance_with_data
        products = service.get_products_by_category("NonExistentCategory")
        assert len(products) == 0

    def test_get_products_by_category_case_insensitivity(self, local_product_service_instance_with_data):
        """Tests that category search is case-insensitive."""
        service, _ = local_product_service_instance_with_data
        products = service.get_products_by_category("lApToP")
        assert len(products) == 2
        assert {p['id'] for p in products} == {"prod1", "prod6"}

    def test_get_products_by_category_error_handling(self, local_product_service_instance_with_data, mock_logger):
        """Tests error handling within get_products_by_category."""
        service, _ = local_product_service_instance_with_data
        with patch.object(service, 'products', new_callable=MagicMock) as mock_products:
            mock_products.__iter__.side_effect = Exception("Iteration error")
            products = service.get_products_by_category("Laptop")
            assert products == []
            mock_logger.error.assert_called_with("Error getting products by category: Iteration error")

    # --- Test get_products_by_brand ---
    def test_get_products_by_brand_found(self, local_product_service_instance_with_data):
        """Tests retrieving products for an existing brand."""
        service, _ = local_product_service_instance_with_data
        products = service.get_products_by_brand("BrandX")
        assert len(products) == 3
        assert {p['id'] for p in products} == {"prod1", "prod3", "prod5"}

    def test_get_products_by_brand_not_found(self, local_product_service_instance_with_data):
        """Tests retrieving products for a non-existent brand."""
        service, _ = local_product_service_instance_with_data
        products = service.get_products_by_brand("NonExistentBrand")
        assert len(products) == 0

    def test_get_products_by_brand_case_insensitivity(self, local_product_service_instance_with_data):
        """Tests that brand search is case-insensitive."""
        service, _ = local_product_service_instance_with_data
        products = service.get_products_by_brand("bRaNdX")
        assert len(products) == 3
        assert {p['id'] for p in products} == {"prod1", "prod3", "prod5"}

    def test_get_products_by_brand_error_handling(self, local_product_service_instance_with_data, mock_logger):
        """Tests error handling within get_products_by_brand."""
        service, _ = local_product_service_instance_with_data
        with patch.object(service, 'products', new_callable=MagicMock) as mock_products:
            mock_products.__iter__.side_effect = Exception("Iteration error")
            products = service.get_products_by_brand("BrandX")
            assert products == []
            mock_logger.error.assert_called_with("Error getting products by brand: Iteration error")

    # --- Test get_top_rated_products ---
    def test_get_top_rated_products(self, local_product_service_instance_with_data):
        """Tests retrieving products sorted by rating in descending order."""
        service, _ = local_product_service_instance_with_data
        # Product ratings in fixture: prod5 (4.9), prod3 (4.8), prod1 (4.5), prod4 (4.2), prod2 (4.0), prod6 (3.5)
        top_products = service.get_top_rated_products(3)
        assert len(top_products) == 3
        assert top_products[0]['id'] == 'prod5'
        assert top_products[1]['id'] == 'prod3'
        assert top_products[2]['id'] == 'prod1'

    def test_get_top_rated_products_limit_more_than_available(self, local_product_service_instance_with_data):
        """Tests get_top_rated_products when limit exceeds available products."""
        service, _ = local_product_service_instance_with_data
        top_products = service.get_top_rated_products(10)
        assert len(top_products) == 6 # All products

    def test_get_top_rated_products_no_rating(self, create_mock_json_file, mock_random_randint):
        """Tests get_top_rated_products handling products with no explicit rating (defaults to 0)."""
        json_content = """{"products": [{"id": "a", "name": "Prod A"}, {"id": "b", "name": "Prod B", "rating": 3.0}]}"""
        create_mock_json_file(json_content)
        service = LocalProductService()
        top_products = service.get_top_rated_products(2)
        assert len(top_products) == 2
        # 'Prod B' has rating 3.0. 'Prod A' has default 0.0, so Prod B should be first.
        assert top_products[0]['id'] == 'b'
        assert top_products[1]['id'] == 'a'

    def test_get_top_rated_products_error_handling(self, local_product_service_instance_with_data, mock_logger):
        """Tests error handling within get_top_rated_products."""
        service, _ = local_product_service_instance_with_data
        with patch.object(service, 'products', new_callable=MagicMock) as mock_products:
            mock_products.__iter__.side_effect = Exception("Iteration error")
            products = service.get_top_rated_products()
            assert products == []
            mock_logger.error.assert_called_with("Error getting top rated products: Iteration error")

    # --- Test get_best_selling_products ---
    def test_get_best_selling_products(self, local_product_service_instance_with_data, mock_logger):
        """
        Tests retrieving products sorted by sold count.
        Temporarily overrides mock_random_randint to ensure diverse sold counts for sorting.
        """
        service, _ = local_product_service_instance_with_data
        # Override mock_random_randint for this specific test to get diverse sold counts
        with patch('random.randint', side_effect=[1000, 200, 800, 50, 1500, 300]):
            # Re-initialize service to reload products with the new mocked randint values
            service = LocalProductService()
            # The order of products in fixture: prod1, prod2, prod3, prod4, prod5, prod6
            # New sold counts: prod1: 1000, prod2: 200, prod3: 800, prod4: 50, prod5: 1500, prod6: 300
            # Expected order by sold count (desc): prod5 (1500), prod1 (1000), prod3 (800), prod6 (300), prod2 (200), prod4 (50)
            
            best_selling = service.get_best_selling_products(3)
            assert len(best_selling) == 3
            assert best_selling[0]['id'] == 'prod5'
            assert best_selling[1]['id'] == 'prod1'
            assert best_selling[2]['id'] == 'prod3'
            
            mock_logger.info.assert_any_call("Getting best selling products, limit: 3")
            mock_logger.info.assert_any_call("Returning 3 best selling products")

    def test_get_best_selling_products_no_sold_data(self, create_mock_json_file):
        """Tests get_best_selling_products when products have no 'sold' count (defaults to 0)."""
        json_content = """{"products": [{"id": "a", "name": "Prod A"}, {"id": "b", "name": "Prod B"}]}"""
        create_mock_json_file(json_content)
        
        # Patch random.randint to ensure 'sold' defaults to 0 (or a consistent value)
        with patch('random.randint', return_value=0):
             service_no_sold = LocalProductService()
             best_selling = service_no_sold.get_best_selling_products(2)
             assert len(best_selling) == 2
             # Should be in original order if sold count is 0 for all (stable sort)
             assert best_selling[0]['id'] == 'a'
             assert best_selling[1]['id'] == 'b'

    def test_get_best_selling_products_error_handling(self, local_product_service_instance_with_data, mock_logger):
        """Tests error handling within get_best_selling_products."""
        service, _ = local_product_service_instance_with_data
        with patch.object(service, 'products', new_callable=MagicMock) as mock_products:
            mock_products.__iter__.side_effect = Exception("Iteration error")
            products = service.get_best_selling_products()
            assert products == []
            mock_logger.error.assert_called_with("Error getting best selling products: Iteration error")

    # --- Test get_products ---
    def test_get_products(self, local_product_service_instance_with_data):
        """Tests retrieving all loaded products without a specific limit."""
        service, _ = local_product_service_instance_with_data
        all_products = service.get_products()
        assert len(all_products) == 6 # All initial test products from fixture
        assert all_products[0]['id'] == 'prod1' # Check order (should be order in fixture)

    def test_get_products_limit(self, local_product_service_instance_with_data):
        """Tests the 'limit' parameter in get_products."""
        service, _ = local_product_service_instance_with_data
        limited_products = service.get_products(limit=3)
        assert len(limited_products) == 3
        assert limited_products[0]['id'] == 'prod1'
        assert limited_products[1]['id'] == 'prod2'
        assert limited_products[2]['id'] == 'prod3'

    def test_get_products_limit_more_than_available(self, local_product_service_instance_with_data):
        """Tests get_products when limit exceeds available products."""
        service, _ = local_product_service_instance_with_data
        limited_products = service.get_products(limit=10)
        assert len(limited_products) == 6 # All products

    def test_get_products_error_handling(self, local_product_service_instance_with_data, mock_logger):
        """Tests error handling within get_products."""
        service, _ = local_product_service_instance_with_data
        with patch.object(service, 'products', side_effect=Exception("List access error")):
            products = service.get_products()
            assert products == []
            mock_logger.error.assert_called_with("Error getting products: List access error")

    # --- Test smart_search_products ---
    @pytest.fixture
    def smart_search_service_with_diverse_sold(self, local_product_service_instance_with_data):
        """
        Fixture that provides a LocalProductService instance with products having
        diverse 'sold' counts for predictable best-selling results.
        """
        service, _ = local_product_service_instance_with_data
        # Set specific 'sold' values for testing popular fallbacks
        with patch('random.randint', side_effect=[1000, 200, 800, 50, 1500, 300]):
            service._load_local_products() # Re-initialize products with new sold counts
        return service
    
    def test_smart_search_best_general(self, smart_search_service_with_diverse_sold):
        """Tests smart_search_products for 'terbaik' without a specific category."""
        products, message = smart_search_service_with_diverse_sold.smart_search_products(keyword='terbaik', limit=2)
        # Expected order based on rating: prod5 (4.9), prod3 (4.8), prod1 (4.5)
        assert len(products) == 2
        assert products[0]['id'] == 'prod5'
        assert products[1]['id'] == 'prod3'
        assert message == "Berikut produk terbaik berdasarkan rating:"

    def test_smart_search_best_category_found(self, smart_search_service_with_diverse_sold):
        """Tests smart_search_products for 'terbaik' within an existing category."""
        products, message = smart_search_service_with_diverse_sold.smart_search_products(keyword='terbaik', category='Laptop', limit=1)
        # Laptop products: prod1 (4.5), prod6 (3.5). prod1 is better.
        assert len(products) == 1
        assert products[0]['id'] == 'prod1'
        assert message == "Berikut Laptop terbaik berdasarkan rating:"

    def test_smart_search_best_category_not_found_fallback(self, smart_search_service_with_diverse_sold):
        """Tests smart_search_products for 'terbaik' in a non-existent category, falling back to general best."""
        products, message = smart_search_service_with_diverse_sold.smart_search_products(keyword='terbaik', category='Furniture', limit=2)
        # Fallback to general best products
        assert len(products) == 2
        assert products[0]['id'] == 'prod5'
        assert products[1]['id'] == 'prod3'
        assert message == "Tidak ada produk kategori Furniture, berikut produk terbaik secara umum:"

    def test_smart_search_full_match(self, smart_search_service_with_diverse_sold):
        """Tests smart_search_products when all criteria (keyword, category, max_price) are met."""
        products, message = smart_search_service_with_diverse_sold.smart_search_products(
            keyword='powerful', category='Laptop', max_price=12000000, limit=1
        )
        # prod1: Laptop A (10M, powerful description, category Laptop) - matches all
        assert len(products) == 1
        assert products[0]['id'] == 'prod1'
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_no_full_match_category_fallback(self, smart_search_service_with_diverse_sold):
        """Tests smart_search_products falling back to category search when full criteria not met."""
        # Keyword 'superfast' doesn't match anything.
        # Max_price 5M excludes prod1 (10M).
        # Fallback to category 'Laptop': prod1 (10M), prod6 (3M). Sorts by price (ascending).
        products, message = smart_search_service_with_diverse_sold.smart_search_products(
            keyword='superfast', category='Laptop', max_price=5000000, limit=2
        )
        assert len(products) == 2
        assert products[0]['id'] == 'prod6' # 3M (cheaper)
        assert products[1]['id'] == 'prod1' # 10M
        assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."

    def test_smart_search_no_full_match_budget_fallback(self, smart_search_service_with_diverse_sold):
        """Tests smart_search_products falling back to budget-only search."""
        # Keyword 'nonexistent', category 'nonexistent'.
        # Max_price 6M is applicable.
        products, message = smart_search_service_with_diverse_sold.smart_search_products(
            keyword='nonexistent', category='NonExistentCategory', max_price=6000000, limit=2
        )
        # Products <= 6M: prod2 (5M), prod3 (1.5M), prod6 (3M)
        # Order based on original `self.products` iteration (stable): prod2, prod3, prod6
        assert len(products) == 2
        assert {p['id'] for p in products} == {"prod2", "prod3"}
        assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

    def test_smart_search_no_match_popular_fallback(self, smart_search_service_with_diverse_sold):
        """Tests smart_search_products falling back to popular products when no other criteria are met."""
        products, message = smart_search_service_with_diverse_sold.smart_search_products(
            keyword='xyz', category='abc', max_price=100, limit=2
        )
        # Fallback to popular (best selling) products based on diverse sold counts
        # prod5 (1500), prod1 (1000)
        assert len(products) == 2
        assert products[0]['id'] == 'prod5'
        assert products[1]['id'] == 'prod1'
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_empty_input_falls_back_to_popular(self, smart_search_service_with_diverse_sold):
        """Tests smart_search_products with no explicit search criteria, leading to popular fallback."""
        products, message = smart_search_service_with_diverse_sold.smart_search_products(limit=2)
        # Defaults for keyword, category, max_price are None or '', leading to popular fallback.
        assert len(products) == 2
        assert products[0]['id'] == 'prod5'
        assert products[1]['id'] == 'prod1'
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_keyword_only(self, smart_search_service_with_diverse_sold):
        """Tests smart_search_products with only a keyword provided."""
        products, message = smart_search_service_with_diverse_sold.smart_search_products(keyword='camera', limit=1)
        # prod2: "Camera focused phone."
        assert len(products) == 1
        assert products[0]['id'] == 'prod2'
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_category_only(self, smart_search_service_with_diverse_sold):
        """Tests smart_search_products with only a category provided."""
        products, message = smart_search_service_with_diverse_sold.smart_search_products(category='Smartphone', limit=1)
        # prod2: Smartphone B
        assert len(products) == 1
        assert products[0]['id'] == 'prod2'
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_max_price_only(self, smart_search_service_with_diverse_sold):
        """Tests smart_search_products with only a maximum price provided."""
        products, message = smart_search_service_with_diverse_sold.smart_search_products(max_price=2000000, limit=1)
        # Products <= 2M: prod3 (1.5M).
        assert len(products) == 1
        assert products[0]['id'] == 'prod3'
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_combination_no_keyword_no_category_but_price_hit(self, smart_search_service_with_diverse_sold):
        """Tests smart_search_products with only a maximum price, no keyword or category."""
        products, message = smart_search_service_with_diverse_sold.smart_search_products(max_price=6000000, limit=3)
        # Products <= 6M: prod2 (5M), prod3 (1.5M), prod6 (3M)
        # Order based on original product list iteration: prod2, prod3, prod6
        assert len(products) == 3
        assert [p['id'] for p in products] == ['prod2', 'prod3', 'prod6']
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_empty_string_inputs_should_be_treated_as_none(self, smart_search_service_with_diverse_sold):
        """Tests that empty string inputs for keyword/category are treated as None."""
        products, message = smart_search_service_with_diverse_sold.smart_search_products(keyword='', category='', max_price=None, limit=2)
        # Should fallback to popular products
        assert len(products) == 2
        assert products[0]['id'] == 'prod5'
        assert products[1]['id'] == 'prod1'
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_no_products_at_all(self, local_product_service_instance_empty_data):
        """Tests smart_search_products when the service has no products loaded."""
        service = local_product_service_instance_empty_data
        products, message = service.smart_search_products(keyword='any', category='any', max_price=1000000)
        assert products == []
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." # Still returns this message, but with an empty list.