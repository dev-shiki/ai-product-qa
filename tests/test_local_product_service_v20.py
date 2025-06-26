import pytest
import json
import logging
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import random

# Import the class under test
from app.services.local_product_service import LocalProductService

# Define a base path for mocking, ensuring it's relative to where tests might run
# This will be mocked in the Path object
MOCK_BASE_PATH = Path("/tmp/mock_app_root")

# Sample product data for various tests, especially for fallback and specific scenarios
SAMPLE_PRODUCTS = [
    {
        "id": "prod1",
        "name": "Smartphone X",
        "category": "Electronics",
        "brand": "BrandA",
        "price": 10000000,
        "currency": "IDR",
        "description": "A high-end smartphone.",
        "specifications": {"rating": 4.5, "sold": 500, "stock": 100},
        "availability": "in_stock",
        "reviews_count": 100
    },
    {
        "id": "prod2",
        "name": "Laptop Y",
        "category": "Computers",
        "brand": "BrandB",
        "price": 15000000,
        "currency": "IDR",
        "description": "Powerful laptop for gaming.",
        "specifications": {"rating": 4.8, "sold": 1200, "stock": 50},
        "availability": "in_stock",
        "reviews_count": 250
    },
    {
        "id": "prod3",
        "name": "Headphones Z",
        "category": "Audio",
        "brand": "BrandA",
        "price": 2000000,
        "currency": "IDR",
        "description": "Noise-cancelling headphones.",
        "specifications": {"rating": 4.2, "sold": 800, "stock": 200},
        "availability": "in_stock",
        "reviews_count": 150
    },
    {
        "id": "prod4",
        "name": "Smartwatch A",
        "category": "Wearables",
        "brand": "BrandC",
        "price": 3000000,
        "currency": "IDR",
        "description": "Latest generation smartwatch.",
        "specifications": {"rating": 3.9, "sold": 300, "stock": 70},
        "availability": "out_of_stock",
        "reviews_count": 50
    },
    {
        "id": "prod5",
        "name": "Tablet Pro",
        "category": "Electronics",
        "brand": "BrandB",
        "price": 8000000,
        "currency": "IDR",
        "description": "Lightweight and powerful tablet.",
        "specifications": {"rating": 4.7, "sold": 600, "stock": 80},
        "availability": "in_stock",
        "reviews_count": 120
    }
]

# Configure logging for tests
@pytest.fixture(autouse=True)
def setup_logging():
    """Capture logs for assertions."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    yield
    logger.removeHandler(handler)


@pytest.fixture
def mock_path_and_open(mocker):
    """
    Fixture to mock Path operations and the open() function.
    It simulates the existence of 'products.json' and its content.
    Returns a dict with control mocks.
    """
    mock_path_instance = mocker.MagicMock(spec=Path)
    mock_path_instance.parent = MagicMock(return_value=MOCK_BASE_PATH / "app" / "services")
    mock_path_instance.__truediv__.side_effect = lambda other: MOCK_BASE_PATH / "data" / "products.json" if other == "data" else Path(MOCK_BASE_PATH / "data" / "products.json") / other
    mock_path_instance.exists.return_value = True

    mocker.patch('pathlib.Path', return_value=mock_path_instance)
    
    mock_file_content = json.dumps({"products": SAMPLE_PRODUCTS})
    mock_open_patch = mocker.patch('builtins.open', mock_open(read_data=mock_file_content))
    
    # Mock random.randint for consistent "sold" count
    mocker.patch('random.randint', return_value=1234)

    return {
        "path_mock": mock_path_instance,
        "open_mock": mock_open_patch,
        "set_file_content": lambda content: mock_open_patch.side_effect(
            lambda *args, **kwargs: mock_open(read_data=content)(*args, **kwargs)
        ),
        "set_file_exists": lambda exists: mock_path_instance.exists.return_value == exists
    }


@pytest.fixture
def local_product_service(mock_path_and_open):
    """
    Fixture to provide a LocalProductService instance with mocked dependencies.
    By default, it will load SAMPLE_PRODUCTS.
    """
    service = LocalProductService()
    return service


@pytest.fixture
def fallback_products():
    """Provides the hardcoded fallback product list."""
    service = LocalProductService() # We don't care about init's side effects here
    return service._get_fallback_products()


class TestLocalProductService:

    def test_init_success(self, local_product_service, caplog):
        """Test successful initialization and product loading."""
        caplog.set_level(logging.INFO)
        assert len(local_product_service.products) == len(SAMPLE_PRODUCTS)
        assert f"Loaded {len(SAMPLE_PRODUCTS)} local products from JSON file" in caplog.text
        assert local_product_service.products[0]['specifications']['sold'] == 1234 # From random mock

    def test_init_file_not_found(self, mock_path_and_open, caplog, fallback_products):
        """Test initialization when products.json is not found."""
        caplog.set_level(logging.ERROR)
        mock_path_and_open["set_file_exists"](False)
        service = LocalProductService()
        assert service.products == fallback_products
        assert "Products JSON file not found at:" in caplog.text
        assert "Using fallback products due to JSON file loading error" in caplog.text

    def test_init_json_decode_error(self, mock_path_and_open, caplog, fallback_products):
        """Test initialization when JSON file content is invalid."""
        caplog.set_level(logging.WARNING)
        mock_path_and_open["set_file_content"]("this is not json {")
        service = LocalProductService()
        assert service.products == fallback_products
        assert "Failed to load with utf-16-le encoding: " in caplog.text
        assert "Failed to load with utf-16 encoding: " in caplog.text
        assert "Failed to load with utf-8 encoding: " in caplog.text
        assert "All encoding attempts failed, using fallback products" in caplog.text

    def test_init_unicode_decode_error(self, mock_path_and_open, caplog, fallback_products):
        """Test initialization when UnicodeDecodeError occurs for all encodings."""
        caplog.set_level(logging.WARNING)
        # Simulate a sequence of errors for each encoding
        def mock_open_side_effect(*args, **kwargs):
            if kwargs.get('encoding') in ['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                raise UnicodeDecodeError("encoding", b'\xed\xa0\x80', 0, 1, "bad data")
            return mock_open(read_data=json.dumps({"products": []}))(*args, **kwargs) # Fallback to valid for subsequent calls

        mock_path_and_open["open_mock"].side_effect = mock_open_side_effect
        
        service = LocalProductService()
        assert service.products == fallback_products
        assert "Failed to load with utf-16-le encoding: " in caplog.text
        assert "All encoding attempts failed, using fallback products" in caplog.text

    @pytest.mark.parametrize("encoding", ['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252'])
    def test_load_local_products_various_encodings(self, mock_path_and_open, encoding, caplog):
        """Test _load_local_products with different valid encodings."""
        caplog.set_level(logging.INFO)
        products_data = json.dumps({"products": [{"id": "enc_test", "name": f"Product ({encoding})", "price": 100}]})
        
        # Manually create a file mock that pretends to be a specific encoding
        mock_file_obj = MagicMock()
        mock_file_obj.read.return_value = products_data # We're letting the Python's open handle actual decoding

        def open_side_effect(*args, **kwargs):
            if kwargs.get('encoding') == encoding:
                # For the target encoding, return a file object that provides the data
                return mock_file_obj
            else:
                # For other encodings, simulate a failure to force the loop to continue
                raise UnicodeDecodeError("encoding", b'bad', 0, 1, "simulated error")

        mock_path_and_open["open_mock"].side_effect = open_side_effect
        
        service = LocalProductService()
        # Call _load_local_products directly to isolate this method's behavior
        loaded_products = service._load_local_products()
        assert len(loaded_products) == 1
        assert loaded_products[0]['name'] == f"Product ({encoding})"
        assert f"Successfully loaded 1 products from JSON file using {encoding} encoding" in caplog.text

    def test_load_local_products_with_bom(self, mock_path_and_open, caplog):
        """Test _load_local_products handles JSON with BOM."""
        caplog.set_level(logging.INFO)
        products_data = json.dumps({"products": [{"id": "bom_test", "name": "BOM Product", "price": 100}]})
        mock_path_and_open["set_file_content"]('\ufeff' + products_data) # Add BOM prefix
        
        service = LocalProductService()
        loaded_products = service._load_local_products()
        assert len(loaded_products) == 1
        assert loaded_products[0]['name'] == "BOM Product"
        assert "Successfully loaded 1 products from JSON file using utf-8 encoding" in caplog.text # BOM implies UTF-8 for many systems

    def test_load_local_products_missing_products_key(self, mock_path_and_open, caplog):
        """Test _load_local_products when 'products' key is missing in JSON."""
        caplog.set_level(logging.INFO)
        mock_path_and_open["set_file_content"](json.dumps({"items": SAMPLE_PRODUCTS}))
        service = LocalProductService()
        assert len(service.products) == 0 # Should return empty list if 'products' key is not found
        assert "Successfully loaded 0 products from JSON file" in caplog.text

    def test_load_local_products_empty_products_list(self, mock_path_and_open, caplog):
        """Test _load_local_products when 'products' list is empty in JSON."""
        caplog.set_level(logging.INFO)
        mock_path_and_open["set_file_content"](json.dumps({"products": []}))
        service = LocalProductService()
        assert len(service.products) == 0
        assert "Successfully loaded 0 products from JSON file" in caplog.text

    def test_load_local_products_partial_product_data(self, mock_path_and_open, caplog):
        """Test _load_local_products handles products with missing fields and applies defaults."""
        caplog.set_level(logging.INFO)
        partial_data = [{"id": "partial1", "name": "Partial Product"}, {"id": "partial2", "price": 500000}]
        mock_path_and_open["set_file_content"](json.dumps({"products": partial_data}))
        service = LocalProductService()
        products = service.products
        assert len(products) == 2
        
        # Check defaults
        assert products[0]['price'] == 0
        assert products[0]['currency'] == 'IDR'
        assert products[0]['specifications']['rating'] == 0
        assert products[0]['images'] == ["https://example.com/partial1.jpg"]
        assert products[1]['name'] == ''
        assert products[1]['category'] == ''

    def test_load_local_products_general_exception(self, mock_path_and_open, caplog, fallback_products):
        """Test _load_local_products handles general exceptions."""
        caplog.set_level(logging.ERROR)
        mock_path_and_open["open_mock"].side_effect = Exception("Simulated general error")
        service = LocalProductService()
        assert service.products == fallback_products
        assert "Error loading products from JSON file: Simulated general error" in caplog.text

    def test_get_fallback_products(self, fallback_products):
        """Test _get_fallback_products returns the expected hardcoded list."""
        service = LocalProductService() # Create a clean instance to call directly
        products = service._get_fallback_products()
        assert len(products) == 8 # Based on the provided code
        assert products[0]['id'] == '1'
        assert products[0]['name'] == 'iPhone 15 Pro Max'
        assert products[7]['id'] == '8'
        assert products[7]['name'] == 'Samsung Galaxy Tab S9'

    def test_search_products_by_name(self, local_product_service):
        """Test searching products by name keyword."""
        results = local_product_service.search_products("smartphone")
        assert len(results) == 1
        assert results[0]['id'] == "prod1"

    def test_search_products_case_insensitive(self, local_product_service):
        """Test searching products with case-insensitive keywords."""
        results = local_product_service.search_products("SmArTpHoNe")
        assert len(results) == 1
        assert results[0]['id'] == "prod1"

    def test_search_products_by_category(self, local_product_service):
        """Test searching products by category keyword."""
        results = local_product_service.search_products("Electronics")
        assert len(results) == 2
        assert any(p['id'] == 'prod1' for p in results)
        assert any(p['id'] == 'prod5' for p in results)

    def test_search_products_by_brand(self, local_product_service):
        """Test searching products by brand keyword."""
        results = local_product_service.search_products("BrandA")
        assert len(results) == 2
        assert any(p['id'] == 'prod1' for p in results)
        assert any(p['id'] == 'prod3' for p in results)

    def test_search_products_by_description(self, local_product_service):
        """Test searching products by description keyword."""
        results = local_product_service.search_products("gaming")
        assert len(results) == 1
        assert results[0]['id'] == "prod2"

    def test_search_products_by_specifications(self, local_product_service):
        """Test searching products by specifications (converted to string)."""
        results = local_product_service.search_products("4.8") # rating for Laptop Y
        assert len(results) == 1
        assert results[0]['id'] == "prod2"

    def test_search_products_no_results(self, local_product_service):
        """Test searching with a keyword that yields no results."""
        results = local_product_service.search_products("NonExistentProduct")
        assert len(results) == 0

    def test_search_products_with_limit(self, local_product_service):
        """Test search results limited by the 'limit' parameter."""
        results = local_product_service.search_products("Brand", limit=1)
        assert len(results) == 1
        # The exact product might vary based on default sorting if many match, but count is key.

    def test_search_products_empty_keyword(self, local_product_service):
        """Test searching with an empty keyword, should return nothing or be handled gracefully."""
        # The current implementation will search for an empty string, which matches everything.
        # It then applies sorting. It's effectively `get_products` with sorting.
        results = local_product_service.search_products("", limit=3)
        assert len(results) == 3
        # Should return the top 3 based on relevance score (which would be 0 for all on empty keyword, then sorted by internal order)
        # For this test, just check the limit.

    def test_search_products_price_range_exact_match(self, local_product_service):
        """Test searching with a price range keyword."""
        # prod1: 10M, prod2: 15M, prod3: 2M, prod4: 3M, prod5: 8M
        results = local_product_service.search_products("dibawah 9 juta")
        assert len(results) == 3
        assert any(p['id'] == 'prod3' for p in results) # 2M
        assert any(p['id'] == 'prod4' for p in results) # 3M
        assert any(p['id'] == 'prod5' for p in results) # 8M

    def test_search_products_price_range_and_keyword(self, local_product_service):
        """Test searching with both keyword and price range."""
        results = local_product_service.search_products("electronics 9 juta")
        assert len(results) == 1
        assert results[0]['id'] == "prod5" # Tablet Pro (8M)

    def test_search_products_budget_keywords(self, local_product_service):
        """Test searching with 'budget' keywords."""
        # 'murah' -> 5M
        results = local_product_service.search_products("smartphone murah")
        assert len(results) == 1 # Only Smartphone X is 10M, but 'murah' applies max_price 5M
        assert results[0]['id'] == "prod4" # Smartwatch A (3M) is filtered by max_price
        
        # Test 'murah' directly
        results = local_product_service.search_products("murah")
        assert len(results) == 3 # prod3 (2M), prod4 (3M), prod5 (8M)
        assert all(p['price'] <= 5000000 for p in results)

    def test_search_products_relevance_scoring(self, local_product_service):
        """Test products are sorted by relevance score."""
        # Prod1: Smartphone X (BrandA, Electronics)
        # Prod3: Headphones Z (BrandA, Audio)
        results = local_product_service.search_products("BrandA")
        # Both Prod1 and Prod3 have "BrandA". Prod1 is "Smartphone X", Prod3 is "Headphones Z".
        # If no other keyword, it's just sorted by default.
        # Let's use a keyword where name match gets higher score
        results = local_product_service.search_products("Smartphone")
        assert results[0]['id'] == "prod1" # Exact name match
        
        results = local_product_service.search_products("BrandA")
        # Both have BrandA. Check current sorting. Prod1 (10M), Prod3 (2M). No budget keyword.
        # Relevance: score from brand match (5)
        # Order is based on creation order for equal scores. Prod1 came first.
        assert results[0]['id'] == "prod1" 
        assert results[1]['id'] == "prod3"


    def test_search_products_error_handling(self, local_product_service, caplog, mocker):
        """Test error handling in search_products."""
        caplog.set_level(logging.ERROR)
        # Temporarily make self.products unusable
        mocker.patch.object(local_product_service, 'products', side_effect=Exception("Simulated search error"))
        results = local_product_service.search_products("test")
        assert results == []
        assert "Error searching products: Simulated search error" in caplog.text

    def test_extract_price_from_keyword_juta(self, local_product_service):
        """Test price extraction for 'juta' keyword."""
        assert local_product_service._extract_price_from_keyword("10 juta") == 10000000
        assert local_product_service._extract_price_from_keyword("25juta") == 25000000

    def test_extract_price_from_keyword_ribu(self, local_product_service):
        """Test price extraction for 'ribu' keyword."""
        assert local_product_service._extract_price_from_keyword("50 ribu") == 50000
        assert local_product_service._extract_price_from_keyword("20000ribu") == 20000000

    def test_extract_price_from_keyword_rp_prefix(self, local_product_service):
        """Test price extraction for 'rp' prefix."""
        assert local_product_service._extract_price_from_keyword("rp 1500000") == 1500000

    def test_extract_price_from_keyword_rp_suffix(self, local_product_service):
        """Test price extraction for 'rp' suffix."""
        assert local_product_service._extract_price_from_keyword("12345 rp") == 12345

    def test_extract_price_from_keyword_k(self, local_product_service):
        """Test price extraction for 'k' suffix."""
        assert local_product_service._extract_price_from_keyword("100k") == 100000
        assert local_product_service._extract_price_from_keyword("500 k") == 500000

    def test_extract_price_from_keyword_m(self, local_product_service):
        """Test price extraction for 'm' suffix."""
        assert local_product_service._extract_price_from_keyword("5m") == 5000000
        assert local_product_service._extract_price_from_keyword("10 m") == 10000000

    def test_extract_price_from_keyword_budget_keywords(self, local_product_service):
        """Test price extraction for budget keywords."""
        assert local_product_service._extract_price_from_keyword("laptop murah") == 5000000
        assert local_product_service._extract_price_from_keyword("budget hp") == 5000000
        assert local_product_service._extract_price_from_keyword("terjangkau") == 4000000
        assert local_product_service._extract_price_from_keyword("ekonomis") == 2000000
        assert local_product_service._extract_price_from_keyword("hemat") == 3000000

    def test_extract_price_from_keyword_no_match(self, local_product_service):
        """Test price extraction returns None when no price/budget keyword is found."""
        assert local_product_service._extract_price_from_keyword("random keyword search") is None

    def test_extract_price_from_keyword_error_handling(self, local_product_service, caplog, mocker):
        """Test error handling in _extract_price_from_keyword."""
        caplog.set_level(logging.ERROR)
        # Simulate an error within the method, e.g., bad regex
        mocker.patch('re.search', side_effect=Exception("Simulated regex error"))
        result = local_product_service._extract_price_from_keyword("10 juta")
        assert result is None
        assert "Error extracting price from keyword: Simulated regex error" in caplog.text

    def test_get_product_details_existing_id(self, local_product_service):
        """Test getting details for an existing product ID."""
        product = local_product_service.get_product_details("prod1")
        assert product is not None
        assert product['id'] == "prod1"
        assert product['name'] == "Smartphone X"

    def test_get_product_details_non_existent_id(self, local_product_service):
        """Test getting details for a non-existent product ID."""
        product = local_product_service.get_product_details("nonexistent")
        assert product is None

    def test_get_product_details_error_handling(self, local_product_service, caplog, mocker):
        """Test error handling in get_product_details."""
        caplog.set_level(logging.ERROR)
        mocker.patch.object(local_product_service, 'products', side_effect=Exception("Simulated details error"))
        result = local_product_service.get_product_details("prod1")
        assert result is None
        assert "Error getting product details: Simulated details error" in caplog.text

    def test_get_categories(self, local_product_service):
        """Test getting unique product categories."""
        categories = local_product_service.get_categories()
        expected_categories = sorted(['Electronics', 'Computers', 'Audio', 'Wearables'])
        assert categories == expected_categories

    def test_get_categories_empty_products(self, mocker):
        """Test getting categories when product list is empty."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        categories = service.get_categories()
        assert categories == []

    def test_get_categories_with_empty_category_field(self, mocker):
        """Test getting categories when some products have empty category field."""
        products_with_empty_category = [
            {"id": "c1", "category": "A"},
            {"id": "c2", "category": ""},
            {"id": "c3", "category": "B"}
        ]
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=products_with_empty_category)
        service = LocalProductService()
        categories = service.get_categories()
        assert categories == ["", "A", "B"] # Empty string is a valid category value

    def test_get_brands(self, local_product_service):
        """Test getting unique product brands."""
        brands = local_product_service.get_brands()
        expected_brands = sorted(['BrandA', 'BrandB', 'BrandC'])
        assert brands == expected_brands

    def test_get_brands_empty_products(self, mocker):
        """Test getting brands when product list is empty."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        brands = service.get_brands()
        assert brands == []

    def test_get_brands_with_empty_brand_field(self, mocker):
        """Test getting brands when some products have empty brand field."""
        products_with_empty_brand = [
            {"id": "b1", "brand": "X"},
            {"id": "b2", "brand": ""},
            {"id": "b3", "brand": "Y"}
        ]
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=products_with_empty_brand)
        service = LocalProductService()
        brands = service.get_brands()
        assert brands == ["", "X", "Y"]

    def test_get_products_by_category_existing(self, local_product_service):
        """Test getting products for an existing category."""
        results = local_product_service.get_products_by_category("Electronics")
        assert len(results) == 2
        assert all(p['category'] == "Electronics" for p in results)

    def test_get_products_by_category_case_insensitive(self, local_product_service):
        """Test getting products for category with case-insensitive search."""
        results = local_product_service.get_products_by_category("eLeCtRoNiCs")
        assert len(results) == 2
        assert all(p['category'] == "Electronics" for p in results)

    def test_get_products_by_category_non_existent(self, local_product_service):
        """Test getting products for a non-existent category."""
        results = local_product_service.get_products_by_category("NonExistentCategory")
        assert len(results) == 0

    def test_get_products_by_category_error_handling(self, local_product_service, caplog, mocker):
        """Test error handling in get_products_by_category."""
        caplog.set_level(logging.ERROR)
        mocker.patch.object(local_product_service, 'products', side_effect=Exception("Simulated category error"))
        results = local_product_service.get_products_by_category("Electronics")
        assert results == []
        assert "Error getting products by category: Simulated category error" in caplog.text

    def test_get_products_by_brand_existing(self, local_product_service):
        """Test getting products for an existing brand."""
        results = local_product_service.get_products_by_brand("BrandA")
        assert len(results) == 2
        assert all(p['brand'] == "BrandA" for p in results)

    def test_get_products_by_brand_case_insensitive(self, local_product_service):
        """Test getting products for brand with case-insensitive search."""
        results = local_product_service.get_products_by_brand("bRaNdA")
        assert len(results) == 2
        assert all(p['brand'] == "BrandA" for p in results)

    def test_get_products_by_brand_non_existent(self, local_product_service):
        """Test getting products for a non-existent brand."""
        results = local_product_service.get_products_by_brand("NonExistentBrand")
        assert len(results) == 0

    def test_get_products_by_brand_error_handling(self, local_product_service, caplog, mocker):
        """Test error handling in get_products_by_brand."""
        caplog.set_level(logging.ERROR)
        mocker.patch.object(local_product_service, 'products', side_effect=Exception("Simulated brand error"))
        results = local_product_service.get_products_by_brand("BrandA")
        assert results == []
        assert "Error getting products by brand: Simulated brand error" in caplog.text

    def test_get_top_rated_products(self, local_product_service):
        """Test getting top rated products."""
        # prod2 (4.8), prod5 (4.7), prod1 (4.5), prod3 (4.2), prod4 (3.9)
        results = local_product_service.get_top_rated_products(limit=3)
        assert len(results) == 3
        assert results[0]['id'] == "prod2"
        assert results[1]['id'] == "prod5"
        assert results[2]['id'] == "prod1"

    def test_get_top_rated_products_limit_exceeds(self, local_product_service):
        """Test getting top rated products when limit exceeds total products."""
        results = local_product_service.get_top_rated_products(limit=100)
        assert len(results) == len(SAMPLE_PRODUCTS)

    def test_get_top_rated_products_empty_products(self, mocker):
        """Test getting top rated products when product list is empty."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        results = service.get_top_rated_products()
        assert results == []

    def test_get_top_rated_products_missing_rating(self, mocker):
        """Test getting top rated products when some products miss rating."""
        products_no_rating = [
            {"id": "r1", "specifications": {"sold": 10}},
            {"id": "r2", "specifications": {"rating": 5.0}},
            {"id": "r3", "specifications": {"rating": 2.0}},
            {"id": "r4", "specifications": {}} # No specs at all
        ]
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=products_no_rating)
        service = LocalProductService()
        results = service.get_top_rated_products(limit=3)
        assert len(results) == 3
        # Products with missing rating get 0, so they are at the bottom.
        assert results[0]['id'] == "r2"
        assert results[1]['id'] == "r3"
        assert results[2]['id'] == "r1" # r1 and r4 both have 0 rating, r1 before r4 due to original order
        # The specific order of 0-rated items depends on Python's sort stability.

    def test_get_top_rated_products_error_handling(self, local_product_service, caplog, mocker):
        """Test error handling in get_top_rated_products."""
        caplog.set_level(logging.ERROR)
        mocker.patch.object(local_product_service, 'products', side_effect=Exception("Simulated rating error"))
        results = local_product_service.get_top_rated_products()
        assert results == []
        assert "Error getting top rated products: Simulated rating error" in caplog.text

    def test_get_best_selling_products(self, local_product_service, caplog):
        """Test getting best selling products."""
        caplog.set_level(logging.INFO)
        # prod2 (1200), prod3 (800), prod5 (600), prod1 (500), prod4 (300)
        results = local_product_service.get_best_selling_products(limit=3)
        assert len(results) == 3
        assert results[0]['id'] == "prod2"
        assert results[1]['id'] == "prod3"
        assert results[2]['id'] == "prod5"
        assert "Getting best selling products, limit: 3" in caplog.text
        assert "Returning 3 best selling products" in caplog.text

    def test_get_best_selling_products_limit_exceeds(self, local_product_service):
        """Test getting best selling products when limit exceeds total products."""
        results = local_product_service.get_best_selling_products(limit=100)
        assert len(results) == len(SAMPLE_PRODUCTS)

    def test_get_best_selling_products_empty_products(self, mocker):
        """Test getting best selling products when product list is empty."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        results = service.get_best_selling_products()
        assert results == []

    def test_get_best_selling_products_missing_sold(self, mocker):
        """Test getting best selling products when some products miss sold count."""
        products_no_sold = [
            {"id": "s1", "specifications": {"rating": 5.0}},
            {"id": "s2", "specifications": {"sold": 100}},
            {"id": "s3", "specifications": {"sold": 50}},
            {"id": "s4", "specifications": {}} # No specs at all
        ]
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=products_no_sold)
        service = LocalProductService()
        results = service.get_best_selling_products(limit=3)
        assert len(results) == 3
        # Products with missing sold get 0, so they are at the bottom.
        assert results[0]['id'] == "s2"
        assert results[1]['id'] == "s3"
        assert results[2]['id'] == "s1" # s1 and s4 both have 0 sold, s1 before s4 due to original order

    def test_get_best_selling_products_error_handling(self, local_product_service, caplog, mocker):
        """Test error handling in get_best_selling_products."""
        caplog.set_level(logging.ERROR)
        mocker.patch.object(local_product_service, 'products', side_effect=Exception("Simulated selling error"))
        results = local_product_service.get_best_selling_products()
        assert results == []
        assert "Error getting best selling products: Simulated selling error" in caplog.text

    def test_get_products(self, local_product_service, caplog):
        """Test getting all products with default limit."""
        caplog.set_level(logging.INFO)
        results = local_product_service.get_products()
        assert len(results) == 5 # Default limit is 10, but SAMPLE_PRODUCTS has 5
        assert results == SAMPLE_PRODUCTS
        assert "Getting all products, limit: 10" in caplog.text

    def test_get_products_with_custom_limit(self, local_product_service):
        """Test getting all products with a custom limit."""
        results = local_product_service.get_products(limit=2)
        assert len(results) == 2
        assert results == SAMPLE_PRODUCTS[:2]

    def test_get_products_limit_exceeds(self, local_product_service):
        """Test getting all products when limit exceeds total products."""
        results = local_product_service.get_products(limit=100)
        assert len(results) == len(SAMPLE_PRODUCTS)

    def test_get_products_empty_products(self, mocker):
        """Test getting products when product list is empty."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        results = service.get_products()
        assert results == []

    def test_get_products_error_handling(self, local_product_service, caplog, mocker):
        """Test error handling in get_products."""
        caplog.set_level(logging.ERROR)
        mocker.patch.object(local_product_service, 'products', side_effect=Exception("Simulated get all products error"))
        results = local_product_service.get_products()
        assert results == []
        assert "Error getting products: Simulated get all products error" in caplog.text

    # --- smart_search_products tests ---
    def test_smart_search_products_best_general(self, local_product_service):
        """Test smart search for 'best' products without specific category."""
        products, msg = local_product_service.smart_search_products(keyword="terbaik")
        # Should return top 5 rated from SAMPLE_PRODUCTS
        # prod2 (4.8), prod5 (4.7), prod1 (4.5), prod3 (4.2), prod4 (3.9)
        assert len(products) == 5
        assert products[0]['id'] == 'prod2'
        assert msg == "Berikut produk terbaik berdasarkan rating:"

    def test_smart_search_products_best_with_category(self, local_product_service):
        """Test smart search for 'best' products within a specific category."""
        products, msg = local_product_service.smart_search_products(keyword="terbaik", category="Electronics")
        # Electronics: prod1 (4.5), prod5 (4.7)
        assert len(products) == 2
        assert products[0]['id'] == 'prod5'
        assert products[1]['id'] == 'prod1'
        assert msg == "Berikut Electronics terbaik berdasarkan rating:"

    def test_smart_search_products_best_with_non_existent_category_fallback(self, local_product_service):
        """Test smart search for 'best' products in non-existent category, falling back to general best."""
        products, msg = local_product_service.smart_search_products(keyword="terbaik", category="NonExistent")
        # Should fallback to general top 5 rated
        assert len(products) == 5
        assert products[0]['id'] == 'prod2'
        assert msg == "Tidak ada produk kategori NonExistent, berikut produk terbaik secara umum:"

    def test_smart_search_products_all_criteria_match(self, local_product_service):
        """Test smart search where all keyword, category, and max_price criteria match."""
        # prod5: Tablet Pro, Electronics, 8M
        products, msg = local_product_service.smart_search_products(
            keyword="tablet", category="Electronics", max_price=8000000, limit=1
        )
        assert len(products) == 1
        assert products[0]['id'] == 'prod5'
        assert msg == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_products_keyword_only(self, local_product_service):
        """Test smart search with only a keyword."""
        products, msg = local_product_service.smart_search_products(keyword="Laptop")
        assert len(products) == 1
        assert products[0]['id'] == 'prod2'
        assert msg == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_products_category_only(self, local_product_service):
        """Test smart search with only a category."""
        products, msg = local_product_service.smart_search_products(category="Audio")
        assert len(products) == 1
        assert products[0]['id'] == 'prod3'
        assert msg == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_products_max_price_only(self, local_product_service):
        """Test smart search with only a max price."""
        # prod3 (2M), prod4 (3M), prod5 (8M)
        products, msg = local_product_service.smart_search_products(max_price=8000000)
        assert len(products) == 3
        assert msg == "Berikut produk yang sesuai dengan kriteria Anda."
        assert all(p['price'] <= 8000000 for p in products)

    def test_smart_search_products_no_criteria_match_category_fallback(self, local_product_service):
        """Test smart search fallback to category-only if keyword/price fail."""
        # Search for "xyz" in "Electronics" below "1M" (no match)
        # Should fallback to all "Electronics" products, sorted by price (prod5 then prod1)
        products, msg = local_product_service.smart_search_products(
            keyword="nonexistent", category="Electronics", max_price=1000000
        )
        assert len(products) == 2
        assert products[0]['id'] == 'prod5' # 8M, cheapest in Electronics category
        assert products[1]['id'] == 'prod1' # 10M
        assert msg == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."

    def test_smart_search_products_no_criteria_match_budget_fallback(self, local_product_service):
        """Test smart search fallback to budget-only if keyword/category fail."""
        # Search for "xyz" in "NonExistentCategory" below "4M" (no match for first 3 paths)
        # Should fallback to products <= 4M
        # prod3 (2M), prod4 (3M)
        products, msg = local_product_service.smart_search_products(
            keyword="nonexistent", category="NonExistentCategory", max_price=4000000
        )
        assert len(products) == 2
        assert any(p['id'] == 'prod3' for p in products)
        assert any(p['id'] == 'prod4' for p in products)
        assert msg == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

    def test_smart_search_products_complete_fallback_to_popular(self, local_product_service):
        """Test smart search falling back to popular products if no criteria match any path."""
        # Search for completely non-existent criteria
        products, msg = local_product_service.smart_search_products(
            keyword="totally unrelated", category="AnotherCategory", max_price=100
        )
        # Should fallback to best selling (popular)
        # prod2 (1200), prod3 (800), prod5 (600), prod1 (500), prod4 (300)
        assert len(products) == 5
        assert products[0]['id'] == 'prod2'
        assert msg == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_products_empty_keyword_all_none(self, local_product_service):
        """Test smart search with all parameters None/empty, should behave like get_products."""
        products, msg = local_product_service.smart_search_products(keyword='', category=None, max_price=None, limit=3)
        assert len(products) == 3
        # Should return all products, limited, and the default message "Berikut produk yang sesuai..."
        assert products == SAMPLE_PRODUCTS[:3]
        assert msg == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_products_limit_applied(self, local_product_service):
        """Test smart search correctly applies the limit."""
        products, msg = local_product_service.smart_search_products(category="Electronics", limit=1)
        assert len(products) == 1
        assert msg == "Berikut produk yang sesuai dengan kriteria Anda."
        assert products[0]['id'] == 'prod5' # cheapest in Electronics for this path

        products, msg = local_product_service.smart_search_products(keyword="terbaik", limit=2)
        assert len(products) == 2
        assert msg == "Berikut produk terbaik berdasarkan rating:"
        assert products[0]['id'] == 'prod2'
        assert products[1]['id'] == 'prod5'