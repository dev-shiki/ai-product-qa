import pytest
import json
import logging
from pathlib import Path
from unittest.mock import mock_open, patch, MagicMock

# Add the parent directory to the path to allow importing the service
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.local_product_service import LocalProductService

# Suppress actual logging during tests unless specifically testing logging behavior
@pytest.fixture(autouse=True)
def no_logging(caplog):
    """Fixture to silence all logs during tests by default."""
    caplog.set_level(logging.CRITICAL)
    yield

@pytest.fixture
def sample_products_data_raw():
    """Returns a raw dictionary representing the content of products.json."""
    return {
        "products": [
            {"id": "p1", "name": "Laptop A", "category": "Electronics", "brand": "BrandX", "price": 10000000, "description": "Powerful laptop with great performance.", "rating": 4.5, "stock_count": 10, "specifications": {"ram": "16GB", "storage": "512GB SSD"}},
            {"id": "p2", "name": "Smartphone B", "category": "Mobile", "brand": "BrandY", "price": 5000000, "description": "Latest smartphone with a vibrant display.", "rating": 4.0, "stock_count": 20},
            {"id": "p3", "name": "Tablet C", "category": "Electronics", "brand": "BrandX", "price": 7000000, "description": "Lightweight tablet for productivity.", "rating": 4.2, "stock_count": 5},
            {"id": "p4", "name": "Headphones D", "category": "Audio", "brand": "BrandZ", "price": 2000000, "description": "Noise cancelling headphones for immersive sound.", "rating": 3.8, "stock_count": 15},
            {"id": "p5", "name": "Smartwatch E", "category": "Wearables", "brand": "BrandY", "price": 3000000, "description": "Fitness tracker with heart rate monitor.", "rating": 4.1, "stock_count": 8},
            {"id": "p6", "name": "Mouse F", "category": "Accessories", "brand": "BrandX", "price": 500000, "description": "Gaming mouse with high DPI.", "rating": 4.7, "stock_count": 50, "specifications": {"dpi": "16000", "buttons": "8"}},
            {"id": "p7", "name": "Keyboard G", "category": "Accessories", "brand": "BrandZ", "price": 1500000, "description": "Mechanical keyboard for typing enthusiasts.", "rating": 4.6, "stock_count": 30},
            {"id": "p8", "name": "Oven H", "category": "Home Appliances", "brand": "BrandA", "price": 3000000, "description": "Electric oven for baking and grilling.", "rating": 4.0, "stock_count": 5},
        ]
    }

@pytest.fixture
def mock_path_exists_true(mocker):
    """Mocks Path.exists to always return True for the products.json path."""
    mocker.patch('pathlib.Path.exists', return_value=True)

@pytest.fixture
def mock_path_exists_false(mocker):
    """Mocks Path.exists to always return False for the products.json path."""
    mocker.patch('pathlib.Path.exists', return_value=False)

@pytest.fixture
def mock_load_local_products(mocker, sample_products_data_raw):
    """
    Mocks the _load_local_products method to return a specific,
    consistently transformed list of products. This is used for tests
    that need a predictable set of products already loaded into the service.
    """
    transformed_products = []
    # Ensure random.randint is consistent for mocked products
    mocker.patch('random.randint', return_value=500) 
    
    for p in sample_products_data_raw['products']:
        transformed_product = {
            "id": p.get('id', ''),
            "name": p.get('name', ''),
            "category": p.get('category', ''),
            "brand": p.get('brand', ''),
            "price": p.get('price', 0),
            "currency": p.get('currency', 'IDR'),
            "description": p.get('description', ''),
            "specifications": {
                "rating": p.get('rating', 0),
                "sold": 500,  # Consistent random value due to mock
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
        transformed_products.append(transformed_product)
    
    mock = mocker.patch.object(LocalProductService, '_load_local_products', return_value=transformed_products)
    return mock

@pytest.fixture
def local_product_service_with_mocked_products(mock_load_local_products):
    """
    Provides an instance of LocalProductService where products are
    consistently loaded via the mocked `_load_local_products` method.
    """
    service = LocalProductService()
    return service

class TestLocalProductServiceInitialization:
    """Tests related to the initialization and product loading (private method _load_local_products)."""
    
    def test_init_loads_products_successfully(self, mocker, sample_products_data_raw, caplog):
        """
        Test that __init__ calls _load_local_products and successfully loads data
        from a mocked JSON file, logging the success.
        """
        mocker.patch('pathlib.Path.exists', return_value=True)
        json_content = json.dumps(sample_products_data_raw)
        mock_file_open = mock_open(read_data=json_content)
        mocker.patch('builtins.open', mock_file_open)
        mocker.patch('random.randint', return_value=123) # Consistent random for testing

        with caplog.at_level(logging.INFO):
            service = LocalProductService()
            
            assert len(service.products) == len(sample_products_data_raw['products'])
            assert "Loaded 8 local products from JSON file" in caplog.text
            # The first encoding in the list is 'utf-16-le', if it works, it's used.
            assert "Successfully loaded 8 products from JSON file using utf-16-le encoding" in caplog.text
            # Verify transformation and random.randint was used
            assert service.products[0]['specifications']['sold'] == 123
            assert service.products[0]['name'] == "Laptop A"
            assert mock_file_open.call_args[0][0].endswith(str(Path("data") / "products.json"))

    def test_init_uses_fallback_if_file_not_found(self, mocker, mock_path_exists_false, caplog):
        """
        Test that __init__ falls back to default products if products.json
        is not found, and logs the error/warning.
        """
        with caplog.at_level(logging.ERROR): # Capture ERROR and WARNING
            service = LocalProductService()
            assert len(service.products) == 8 # Fallback products count
            assert "Products JSON file not found at:" in caplog.text
            assert "Using fallback products due to JSON file loading error" in caplog.text

    def test_load_local_products_with_bom(self, mocker, sample_products_data_raw, caplog):
        """Test _load_local_products correctly handles JSON files with a BOM."""
        mocker.patch('pathlib.Path.exists', return_value=True)
        json_content_with_bom = '\ufeff' + json.dumps(sample_products_data_raw)
        mock_file_open = mock_open(read_data=json_content_with_bom)
        mocker.patch('builtins.open', mock_file_open)
        mocker.patch('random.randint', return_value=123)

        service = LocalProductService() # This calls _load_local_products
        products = service.products # Access the loaded products

        assert len(products) == len(sample_products_data_raw['products'])
        assert products[0]['name'] == "Laptop A"
        assert products[0]['specifications']['sold'] == 123
        with caplog.at_level(logging.INFO): # Re-check logs specifically for successful load
            service = LocalProductService() # Re-initialize to capture logs for this specific test case
            assert "Successfully loaded" in caplog.text
            # Verify open was called with 'r' mode and first encoding
            mock_file_open.assert_called_with(mocker.ANY, 'r', encoding='utf-16-le')


    def test_load_local_products_invalid_json(self, mocker, mock_path_exists_true, caplog):
        """Test _load_local_products handles malformed JSON content by falling back."""
        mocker.patch('builtins.open', mock_open(read_data='{"products": [invalid_json'))
        
        service = LocalProductService()
        products = service.products # Access loaded products
        
        assert len(products) == 8 # Should fall back
        with caplog.at_level(logging.WARNING): # Check warning for decode error
            # Re-initialize to get a fresh log capture for this specific scenario
            service = LocalProductService()
            assert "Failed to load with utf-16-le encoding: Expecting value: line 1 column 18 (char 17)" in caplog.text
            assert "All encoding attempts failed, using fallback products" in caplog.text
            assert "Using fallback products due to JSON file loading error" in caplog.text

    def test_load_local_products_unicode_decode_error(self, mocker, mock_path_exists_true, caplog):
        """
        Test _load_local_products attempts different encodings if the first
        encodings fail with UnicodeDecodeError, eventually succeeding.
        """
        # Mocking open's read method to simulate encoding failures for initial attempts
        def mock_read_side_effect(*args, **kwargs):
            if kwargs.get('encoding') in ['utf-16-le', 'utf-16']:
                raise UnicodeDecodeError('mock_codec', b'\xfe\xff', 0, 1, 'invalid byte sequence')
            # For 'utf-8', return valid JSON
            return json.dumps({"products": [{"id": "test", "name": "ProductUsingUTF8"}]})

        mock_file_open = mock_open()
        mock_file_open.return_value.read.side_effect = mock_read_side_effect
        mocker.patch('builtins.open', mock_file_open)

        with caplog.at_level(logging.WARNING):
            service = LocalProductService()
            products = service.products
            
            assert len(products) == 1
            assert products[0]['name'] == "ProductUsingUTF8"
            assert "Failed to load with utf-16-le encoding: invalid byte sequence" in caplog.text
            assert "Failed to load with utf-16 encoding: invalid byte sequence" in caplog.text
            assert "Successfully loaded 1 products from JSON file using utf-8 encoding" in caplog.text


    def test_load_local_products_all_encodings_fail(self, mocker, mock_path_exists_true, caplog):
        """Test _load_local_products falls back if all encoding attempts fail."""
        def mock_read_side_effect(*args, **kwargs):
            raise UnicodeDecodeError('mock_codec', b'\xfe\xff', 0, 1, 'mocked error for all encodings')

        mock_file_open = mock_open()
        mock_file_open.return_value.read.side_effect = mock_read_side_effect
        mocker.patch('builtins.open', mock_file_open)
        
        service = LocalProductService()
        products = service.products
        
        assert len(products) == 8 # Fallback products count
        with caplog.at_level(logging.ERROR):
            service = LocalProductService() # Re-initialize to capture logs
            assert "All encoding attempts failed, using fallback products" in caplog.text
            assert "Using fallback products due to JSON file loading error" in caplog.text

    def test_load_local_products_general_exception(self, mocker, mock_path_exists_true, caplog):
        """Test _load_local_products handles general exceptions during file operations (e.g., IOError)."""
        mocker.patch('builtins.open', side_effect=IOError("Permission denied error"))
        
        service = LocalProductService()
        products = service.products
        
        assert len(products) == 8 # Fallback products count
        with caplog.at_level(logging.ERROR):
            service = LocalProductService() # Re-initialize to capture logs
            assert "Error loading products from JSON file: Permission denied error" in caplog.text
            assert "Using fallback products due to JSON file loading error" in caplog.text

    def test_load_local_products_empty_products_list(self, mocker, mock_path_exists_true, caplog):
        """Test _load_local_products handles JSON where 'products' key is an empty list."""
        mocker.patch('builtins.open', mock_open(read_data=json.dumps({"products": []})))
        mocker.patch('random.randint', return_value=1)

        service = LocalProductService()
        products = service.products
        
        assert len(products) == 0
        with caplog.at_level(logging.INFO):
            service = LocalProductService() # Re-initialize to capture logs
            assert "Successfully loaded 0 products from JSON file" in caplog.text

    def test_load_local_products_missing_products_key(self, mocker, mock_path_exists_true, caplog):
        """Test _load_local_products handles JSON where the 'products' key is missing."""
        mocker.patch('builtins.open', mock_open(read_data=json.dumps({"data": []})))
        mocker.patch('random.randint', return_value=1)

        service = LocalProductService()
        products = service.products
        
        assert len(products) == 0
        with caplog.at_level(logging.INFO):
            service = LocalProductService() # Re-initialize to capture logs
            assert "Successfully loaded 0 products from JSON file" in caplog.text

    def test_load_local_products_product_transformation_defaults(self, mocker, caplog):
        """
        Test that _load_local_products applies default values for missing fields
        during product transformation.
        """
        mocker.patch('pathlib.Path.exists', return_value=True)
        raw_product_data = {
            "products": [
                {"id": "p_incomplete", "name": "Incomplete Product", "specifications": {"extra_field": "value"}}
            ]
        }
        mocker.patch('builtins.open', mock_open(read_data=json.dumps(raw_product_data)))
        mocker.patch('random.randint', return_value=999)

        service = LocalProductService()
        products = service.products

        assert len(products) == 1
        product = products[0]
        assert product['id'] == 'p_incomplete'
        assert product['name'] == 'Incomplete Product'
        assert product['category'] == ''
        assert product['price'] == 0
        assert product['currency'] == 'IDR'
        assert product['description'] == ''
        assert product['specifications']['rating'] == 0
        assert product['specifications']['sold'] == 999
        assert product['specifications']['stock'] == 0
        assert product['specifications']['condition'] == 'Baru'
        assert product['specifications']['shop_location'] == 'Indonesia'
        assert product['specifications']['shop_name'] == 'Unknown Store'
        assert product['specifications']['extra_field'] == 'value' # Existing specs merged
        assert product['availability'] == 'in_stock'
        assert product['reviews_count'] == 0
        assert product['images'] == ["https://example.com/p_incomplete.jpg"]
        assert product['url'] == "https://shopee.co.id/p_incomplete"

    def test_get_fallback_products_returns_correct_data(self, local_product_service_with_mocked_products, caplog):
        """Test that _get_fallback_products returns the hardcoded list and logs a warning."""
        with caplog.at_level(logging.WARNING):
            fallback_products = local_product_service_with_mocked_products._get_fallback_products()
            assert len(fallback_products) == 8 # Verify the size of hardcoded list
            assert fallback_products[0]['name'] == "iPhone 15 Pro Max"
            assert "Using fallback products due to JSON file loading error" in caplog.text


class TestLocalProductServiceSearchDetails:
    """Tests related to product search and details retrieval."""

    def test_search_products_by_name(self, local_product_service_with_mocked_products):
        """Test searching products by name keyword."""
        results = local_product_service_with_mocked_products.search_products("Laptop A")
        assert len(results) == 1
        assert results[0]['name'] == "Laptop A"

    def test_search_products_case_insensitive(self, local_product_service_with_mocked_products):
        """Test search is case-insensitive for keywords across fields."""
        results = local_product_service_with_mocked_products.search_products("laptop a")
        assert len(results) == 1
        assert results[0]['name'] == "Laptop A"

        results = local_product_service_with_mocked_products.search_products("electronics")
        assert len(results) == 2
        assert {p['name'] for p in results} == {"Laptop A", "Tablet C"}
        assert results[0]['name'] == "Laptop A" # 'Electronics' in category and name has 'laptop'
        
    def test_search_products_by_description(self, local_product_service_with_mocked_products):
        """Test searching products by description keyword."""
        results = local_product_service_with_mocked_products.search_products("vibrant display")
        assert len(results) == 1
        assert results[0]['name'] == "Smartphone B"

    def test_search_products_by_category_keyword(self, local_product_service_with_mocked_products):
        """Test searching products by category keyword."""
        results = local_product_service_with_mocked_products.search_products("Electronics")
        assert len(results) == 2
        assert {p['name'] for p in results} == {"Laptop A", "Tablet C"}
        # 'Laptop A' matches 'Electronics' in both category field and name/description containing 'laptop'.
        # 'Tablet C' matches 'Electronics' in category.
        # Relevance sorting makes Laptop A first.
        assert results[0]['name'] == "Laptop A" 

    def test_search_products_by_brand_keyword(self, local_product_service_with_mocked_products):
        """Test searching products by brand keyword."""
        results = local_product_service_with_mocked_products.search_products("BrandY")
        assert len(results) == 2
        assert {p['name'] for p in results} == {"Smartphone B", "Smartwatch E"}
        assert results[0]['name'] == "Smartphone B" # 'Smartphone B' matches 'BrandY' in brand field and has more keywords match

    def test_search_products_by_specifications(self, local_product_service_with_mocked_products):
        """Test searching products by specification values."""
        results = local_product_service_with_mocked_products.search_products("16GB RAM")
        assert len(results) == 1
        assert results[0]['name'] == "Laptop A"
        
        results = local_product_service_with_mocked_products.search_products("16000 DPI")
        assert len(results) == 1
        assert results[0]['name'] == "Mouse F"

    def test_search_products_with_limit(self, local_product_service_with_mocked_products):
        """Test search_products with a specified limit."""
        results = local_product_service_with_mocked_products.search_products("BrandX", limit=1)
        assert len(results) == 1
        assert results[0]['name'] == "Laptop A" # Laptop A has higher relevance for BrandX based on default sorting

    def test_search_products_no_match(self, local_product_service_with_mocked_products):
        """Test search_products when no matches are found."""
        results = local_product_service_with_mocked_products.search_products("NonExistentProductKeyword")
        assert len(results) == 0

    def test_search_products_empty_keyword(self, local_product_service_with_mocked_products):
        """Test search_products with an empty keyword, should return all products (up to limit)."""
        results = local_product_service_with_mocked_products.search_products("")
        assert len(results) == 8 # All products match empty string, sorted by score.
        # Based on relevance score, 'Laptop A' and 'Smartphone B' would likely be at the top due to higher prices contributing more score.
        # However, without specific keyword matches, the initial product order combined with general scoring leads to this.
        assert results[0]['name'] == 'Laptop A' 

    def test_search_products_with_price_filter_and_keyword(self, local_product_service_with_mocked_products):
        """
        Test searching with an explicit price filter in keyword,
        where price is a soft filter and relevance factor.
        """
        # Search "laptop 5 juta". Laptop A is 10M. It won't match the price filter initially.
        # But 'laptop' keyword will match 'Laptop A'.
        # The relevance score will boost cheaper items, but Laptop A is the only laptop.
        results = local_product_service_with_mocked_products.search_products("laptop 5 juta") 
        assert len(results) == 1
        assert results[0]['name'] == "Laptop A"

        # Search for products "di bawah 3 juta" (price-only search)
        results = local_product_service_with_mocked_products.search_products("di bawah 3 juta")
        # Products <= 3M: Headphones D (2M), Smartwatch E (3M), Mouse F (0.5M), Keyboard G (1.5M), Oven H (3M)
        assert len(results) == 5
        assert all(p['price'] <= 3000000 for p in results)
        # Sorted by relevance (lower price gets higher score for budget search)
        assert results[0]['name'] == "Mouse F" # 0.5M
        assert results[1]['name'] == "Keyboard G" # 1.5M
        assert results[2]['name'] == "Headphones D" # 2M
        assert results[3]['name'] == "Smartwatch E" # 3M
        assert results[4]['name'] == "Oven H" # 3M

    def test_search_products_with_budget_keyword(self, local_product_service_with_mocked_products):
        """Test searching with budget keywords like 'murah' or 'budget'."""
        results = local_product_service_with_mocked_products.search_products("smartphone murah")
        # Max price for 'murah' is 5jt. Smartphone B is 5jt. It matches 'smartphone' keyword.
        assert len(results) == 1
        assert results[0]['name'] == "Smartphone B"
        
        results = local_product_service_with_mocked_products.search_products("mouse budget")
        # Max price for 'budget' is 5jt. Mouse F is 0.5jt. It matches 'mouse' keyword.
        assert len(results) == 1
        assert results[0]['name'] == "Mouse F"
        
        results = local_product_service_with_mocked_products.search_products("produk terjangkau")
        # Max price for 'terjangkau' is 4jt. "produk" doesn't match anything directly.
        # Products that match price <= 4jt: Headphones D (2M), Smartwatch E (3M), Mouse F (0.5M), Keyboard G (1.5M), Oven H (3M).
        assert len(results) == 5
        assert all(p['price'] <= 4000000 for p in results)
        assert {p['name'] for p in results} == {'Mouse F', 'Keyboard G', 'Headphones D', 'Smartwatch E', 'Oven H'}
        assert results[0]['name'] == "Mouse F" # Sorted by relevance (cheapest first)

    def test_search_products_error_handling(self, local_product_service_with_mocked_products, mocker, caplog):
        """Test error handling in search_products, ensuring it returns an empty list and logs."""
        mocker.patch.object(local_product_service_with_mocked_products, '_extract_price_from_keyword', side_effect=ValueError("Test Error"))
        with caplog.at_level(logging.ERROR):
            results = local_product_service_with_mocked_products.search_products("keyword")
            assert len(results) == 0
            assert "Error searching products: Test Error" in caplog.text

    def test_extract_price_from_keyword_juta(self, local_product_service_with_mocked_products):
        """Test price extraction for 'juta' pattern (e.g., '10 juta')."""
        assert local_product_service_with_mocked_products._extract_price_from_keyword("10 juta") == 10000000
        assert local_product_service_with_mocked_products._extract_price_from_keyword("harga 20 juta") == 20000000
        assert local_product_service_with_mocked_products._extract_price_from_keyword("1juta") == 1000000
        # Note: current regex for 'juta' only matches integer part, not decimal like 5.5 juta.

    def test_extract_price_from_keyword_ribu(self, local_product_service_with_mocked_products):
        """Test price extraction for 'ribu' pattern (e.g., '500 ribu')."""
        assert local_product_service_with_mocked_products._extract_price_from_keyword("500 ribu") == 500000
        assert local_product_service_with_mocked_products._extract_price_from_keyword("harga 100 ribu") == 100000

    def test_extract_price_from_keyword_rp(self, local_product_service_with_mocked_products):
        """Test price extraction for 'rp' pattern (e.g., 'rp 150000')."""
        assert local_product_service_with_mocked_products._extract_price_from_keyword("rp 150000") == 150000
        assert local_product_service_with_mocked_products._extract_price_from_keyword("rp50000") == 50000
        assert local_product_service_with_mocked_products._extract_price_from_keyword("100000 rp") == 100000

    def test_extract_price_from_keyword_k_m(self, local_product_service_with_mocked_products):
        """Test price extraction for 'k' (thousand) and 'm' (million) patterns."""
        assert local_product_service_with_mocked_products._extract_price_from_keyword("200k") == 200000
        assert local_product_service_with_mocked_products._extract_price_from_keyword("5m") == 5000000

    def test_extract_price_from_keyword_budget_keywords(self, local_product_service_with_mocked_products):
        """Test price extraction for budget keywords like 'murah'."""
        assert local_product_service_with_mocked_products._extract_price_from_keyword("murah") == 5000000
        assert local_product_service_with_mocked_products._extract_price_from_keyword("budget laptop") == 5000000
        assert local_product_service_with_mocked_products._extract_price_from_keyword("hemat") == 3000000
        assert local_product_service_with_mocked_products._extract_price_from_keyword("terjangkau") == 4000000
        assert local_product_service_with_mocked_products._extract_price_from_keyword("ekonomis") == 2000000

    def test_extract_price_from_keyword_no_match(self, local_product_service_with_mocked_products):
        """Test price extraction when no recognized price pattern or budget keyword is found."""
        assert local_product_service_with_mocked_products._extract_price_from_keyword("random keyword") is None
        assert local_product_service_with_mocked_products._extract_price_from_keyword("") is None
        assert local_product_service_with_mocked_products._extract_price_from_keyword("5.5 juta") is None # Decimal not matched by current regex

    def test_extract_price_from_keyword_error_handling(self, local_product_service_with_mocked_products, mocker, caplog):
        """Test error handling in _extract_price_from_keyword, ensuring it returns None and logs."""
        mocker.patch('re.search', side_effect=Exception("Regex Processing Error"))
        with caplog.at_level(logging.ERROR):
            result = local_product_service_with_mocked_products._extract_price_from_keyword("1 juta")
            assert result is None
            assert "Error extracting price from keyword: Regex Processing Error" in caplog.text

    def test_get_product_details_found(self, local_product_service_with_mocked_products):
        """Test retrieving product details for an existing ID."""
        product = local_product_service_with_mocked_products.get_product_details("p1")
        assert product is not None
        assert product['name'] == "Laptop A"
        assert product['id'] == "p1"

    def test_get_product_details_not_found(self, local_product_service_with_mocked_products):
        """Test retrieving product details for a non-existent ID."""
        product = local_product_service_with_mocked_products.get_product_details("nonexistent")
        assert product is None

    def test_get_product_details_error_handling(self, local_product_service_with_mocked_products, mocker, caplog):
        """Test error handling in get_product_details, ensuring it returns None and logs."""
        # Simulate an error during iteration over products
        mocker.patch.object(local_product_service_with_mocked_products, 'products', new_callable=MagicMock, side_effect=Exception("List Access Error"))
        with caplog.at_level(logging.ERROR):
            product = local_product_service_with_mocked_products.get_product_details("p1")
            assert product is None
            assert "Error getting product details: List Access Error" in caplog.text


class TestLocalProductServiceCategoriesBrands:
    """Tests related to category and brand retrieval and filtering."""

    def test_get_categories(self, local_product_service_with_mocked_products):
        """Test retrieving unique and sorted product categories."""
        categories = local_product_service_with_mocked_products.get_categories()
        expected_categories = ['Accessories', 'Audio', 'Electronics', 'Home Appliances', 'Mobile', 'Wearables']
        assert categories == sorted(list(set(expected_categories)))

    def test_get_categories_empty_products(self, mocker):
        """Test get_categories when no products are loaded into the service."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        categories = service.get_categories()
        assert categories == []

    def test_get_categories_product_missing_category(self, mocker):
        """Test get_categories when some products miss the 'category' key."""
        mock_products = [
            {"id": "c1", "name": "Cat Product", "category": "CategoryA"},
            {"id": "c2", "name": "No Cat Product"}, # Missing category
            {"id": "c3", "name": "Another Cat Product", "category": "CategoryB"},
        ]
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=mock_products)
        service = LocalProductService()
        categories = service.get_categories()
        assert sorted(categories) == ['', 'CategoryA', 'CategoryB'] # Empty string for missing category

    def test_get_brands(self, local_product_service_with_mocked_products):
        """Test retrieving unique and sorted product brands."""
        brands = local_product_service_with_mocked_products.get_brands()
        expected_brands = ['BrandA', 'BrandX', 'BrandY', 'BrandZ']
        assert brands == sorted(list(set(expected_brands)))

    def test_get_brands_empty_products(self, mocker):
        """Test get_brands when no products are loaded into the service."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        brands = service.get_brands()
        assert brands == []

    def test_get_brands_product_missing_brand(self, mocker):
        """Test get_brands when some products miss the 'brand' key."""
        mock_products = [
            {"id": "b1", "name": "Brand Product", "brand": "BrandA"},
            {"id": "b2", "name": "No Brand Product"}, # Missing brand
            {"id": "b3", "name": "Another Brand Product", "brand": "BrandB"},
        ]
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=mock_products)
        service = LocalProductService()
        brands = service.get_brands()
        assert sorted(brands) == ['', 'BrandA', 'BrandB'] # Empty string for missing brand

    def test_get_products_by_category_found(self, local_product_service_with_mocked_products):
        """Test filtering products by existing category."""
        results = local_product_service_with_mocked_products.get_products_by_category("Electronics")
        assert len(results) == 2
        assert {p['name'] for p in results} == {"Laptop A", "Tablet C"}

    def test_get_products_by_category_case_insensitive(self, local_product_service_with_mocked_products):
        """Test category filter is case-insensitive."""
        results = local_product_service_with_mocked_products.get_products_by_category("electronics")
        assert len(results) == 2
        assert {p['name'] for p in results} == {"Laptop A", "Tablet C"}

    def test_get_products_by_category_no_match(self, local_product_service_with_mocked_products):
        """Test filtering products by a non-existent category."""
        results = local_product_service_with_mocked_products.get_products_by_category("Automotive")
        assert len(results) == 0

    def test_get_products_by_category_error_handling(self, local_product_service_with_mocked_products, mocker, caplog):
        """Test error handling in get_products_by_category, ensuring empty list and logs."""
        mocker.patch.object(local_product_service_with_mocked_products, 'products', new_callable=MagicMock, side_effect=Exception("List Error"))
        with caplog.at_level(logging.ERROR):
            results = local_product_service_with_mocked_products.get_products_by_category("Electronics")
            assert len(results) == 0
            assert "Error getting products by category: List Error" in caplog.text

    def test_get_products_by_brand_found(self, local_product_service_with_mocked_products):
        """Test filtering products by existing brand."""
        results = local_product_service_with_mocked_products.get_products_by_brand("BrandY")
        assert len(results) == 2
        assert {p['name'] for p in results} == {"Smartphone B", "Smartwatch E"}

    def test_get_products_by_brand_case_insensitive(self, local_product_service_with_mocked_products):
        """Test brand filter is case-insensitive."""
        results = local_product_service_with_mocked_products.get_products_by_brand("brandy")
        assert len(results) == 2
        assert {p['name'] for p in results} == {"Smartphone B", "Smartwatch E"}

    def test_get_products_by_brand_no_match(self, local_product_service_with_mocked_products):
        """Test filtering products by a non-existent brand."""
        results = local_product_service_with_mocked_products.get_products_by_brand("BrandXYZ")
        assert len(results) == 0

    def test_get_products_by_brand_error_handling(self, local_product_service_with_mocked_products, mocker, caplog):
        """Test error handling in get_products_by_brand, ensuring empty list and logs."""
        mocker.patch.object(local_product_service_with_mocked_products, 'products', new_callable=MagicMock, side_effect=Exception("List Error"))
        with caplog.at_level(logging.ERROR):
            results = local_product_service_with_mocked_products.get_products_by_brand("BrandX")
            assert len(results) == 0
            assert "Error getting products by brand: List Error" in caplog.text


class TestLocalProductServiceSortingAndGeneral:
    """Tests related to sorting products (top-rated, best-selling) and general product retrieval."""

    def test_get_top_rated_products(self, local_product_service_with_mocked_products):
        """Test retrieving products sorted by highest rating."""
        # Ratings: Mouse F (4.7), Keyboard G (4.6), Laptop A (4.5), Tablet C (4.2), Smartwatch E (4.1),
        # Smartphone B (4.0), Oven H (4.0), Headphones D (3.8)
        # Expected order (descending rating) for limit=5:
        # Mouse F, Keyboard G, Laptop A, Tablet C, Smartwatch E
        results = local_product_service_with_mocked_products.get_top_rated_products(5)
        assert len(results) == 5
        assert results[0]['name'] == "Mouse F"
        assert results[1]['name'] == "Keyboard G"
        assert results[2]['name'] == "Laptop A"
        assert results[3]['name'] == "Tablet C"
        assert results[4]['name'] == "Smartwatch E"
        
        # Test limit parameter
        results_limit_2 = local_product_service_with_mocked_products.get_top_rated_products(2)
        assert len(results_limit_2) == 2
        assert results_limit_2[0]['name'] == "Mouse F"
        assert results_limit_2[1]['name'] == "Keyboard G"

    def test_get_top_rated_products_missing_rating(self, mocker):
        """Test get_top_rated_products handles products missing 'rating' or 'specifications' gracefully."""
        mock_products = [
            {"id": "r1", "name": "Good Product", "specifications": {"rating": 5.0}},
            {"id": "r2", "name": "No Rating Product", "specifications": {}}, # Missing rating (defaults to 0)
            {"id": "r3", "name": "No Specs Product"}, # Missing specifications (defaults to 0 rating)
            {"id": "r4", "name": "Average Product", "specifications": {"rating": 3.0}},
        ]
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=mock_products)
        service = LocalProductService()
        
        results = service.get_top_rated_products(3)
        assert len(results) == 3
        # Products with missing rating/specs default to 0 rating, so they'd be last among rated.
        assert results[0]['name'] == "Good Product"
        assert results[1]['name'] == "Average Product"
        # The order between 'No Rating Product' and 'No Specs Product' depends on their original order
        # in the list, as their default rating (0) is the same.
        assert results[2]['name'] in {"No Rating Product", "No Specs Product"}

    def test_get_top_rated_products_error_handling(self, local_product_service_with_mocked_products, mocker, caplog):
        """Test error handling in get_top_rated_products, ensuring empty list and logs."""
        mocker.patch.object(local_product_service_with_mocked_products, 'products', new_callable=MagicMock, side_effect=Exception("List Error"))
        with caplog.at_level(logging.ERROR):
            results = local_product_service_with_mocked_products.get_top_rated_products()
            assert len(results) == 0
            assert "Error getting top rated products: List Error" in caplog.text

    def test_get_best_selling_products(self, local_product_service_with_mocked_products, caplog):
        """Test retrieving products sorted by highest sold count."""
        # Override the products in the fixture to have distinct sold counts for a meaningful test
        mock_products_for_sold = [
            {"id": "s1", "name": "High Sold Product", "specifications": {"sold": 1000, "rating": 4.0}},
            {"id": "s2", "name": "Medium Sold Product", "specifications": {"sold": 500, "rating": 3.0}},
            {"id": "s3", "name": "Low Sold Product", "specifications": {"sold": 100, "rating": 5.0}},
        ]
        local_product_service_with_mocked_products.products = mock_products_for_sold 

        with caplog.at_level(logging.INFO):
            results = local_product_service_with_mocked_products.get_best_selling_products(3)
            assert len(results) == 3
            assert results[0]['name'] == "High Sold Product"
            assert results[1]['name'] == "Medium Sold Product"
            assert results[2]['name'] == "Low Sold Product"
            assert "Getting best selling products, limit: 3" in caplog.text
            assert "Returning 3 best selling products" in caplog.text

    def test_get_best_selling_products_missing_sold(self, mocker):
        """Test get_best_selling_products handles products missing 'sold' or 'specifications' gracefully."""
        mock_products = [
            {"id": "x1", "name": "ProdX", "specifications": {"sold": 200}},
            {"id": "x2", "name": "ProdY", "specifications": {}}, # Missing sold (defaults to 0)
            {"id": "x3", "name": "ProdZ", "specifications": {"sold": 300}},
            {"id": "x4", "name": "ProdA"}, # Missing specifications (defaults to 0 sold)
        ]
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=mock_products)
        service = LocalProductService()
        
        results = service.get_best_selling_products(3)
        assert len(results) == 3
        # Products with missing sold/specs default to 0 sold, so they'd be last.
        assert results[0]['name'] == "ProdZ"
        assert results[1]['name'] == "ProdX"
        assert results[2]['name'] in {"ProdY", "ProdA"} # Order among 0-sold is arbitrary

    def test_get_best_selling_products_error_handling(self, local_product_service_with_mocked_products, mocker, caplog):
        """Test error handling in get_best_selling_products, ensuring empty list and logs."""
        mocker.patch.object(local_product_service_with_mocked_products, 'products', new_callable=MagicMock, side_effect=Exception("List Error"))
        with caplog.at_level(logging.ERROR):
            results = local_product_service_with_mocked_products.get_best_selling_products()
            assert len(results) == 0
            assert "Error getting best selling products: List Error" in caplog.text

    def test_get_products(self, local_product_service_with_mocked_products, caplog):
        """Test retrieving all products up to a specified limit."""
        with caplog.at_level(logging.INFO):
            all_products = local_product_service_with_mocked_products.get_products()
            assert len(all_products) == 8 # Default limit 10, but only 8 products in sample
            assert "Getting all products, limit: 10" in caplog.text
            
            limited_products = local_product_service_with_mocked_products.get_products(limit=3)
            assert len(limited_products) == 3
            assert limited_products[0]['name'] == "Laptop A" # Order is as loaded
            assert "Getting all products, limit: 3" in caplog.text

    def test_get_products_error_handling(self, local_product_service_with_mocked_products, mocker, caplog):
        """Test error handling in get_products, ensuring empty list and logs."""
        mocker.patch.object(local_product_service_with_mocked_products, 'products', new_callable=MagicMock, side_effect=Exception("List Error"))
        with caplog.at_level(logging.ERROR):
            results = local_product_service_with_mocked_products.get_products()
            assert len(results) == 0
            assert "Error getting products: List Error" in caplog.text


class TestLocalProductServiceSmartSearch:
    """Tests for the complex smart_search_products method and its various fallback scenarios."""

    def test_smart_search_best_general(self, local_product_service_with_mocked_products):
        """Test smart_search_products for 'terbaik' or 'best' without specific category (general best by rating)."""
        # Mouse F (4.7), Keyboard G (4.6), Laptop A (4.5), Tablet C (4.2), Smartwatch E (4.1)
        results, msg = local_product_service_with_mocked_products.smart_search_products(keyword="produk terbaik")
        assert len(results) == 5
        assert results[0]['name'] == "Mouse F"
        assert results[1]['name'] == "Keyboard G"
        assert "Berikut produk terbaik berdasarkan rating:" in msg

    def test_smart_search_best_category_found(self, local_product_service_with_mocked_products):
        """Test smart_search_products for 'terbaik' within an existing category."""
        results, msg = local_product_service_with_mocked_products.smart_search_products(keyword="laptop terbaik", category="Electronics")
        # Electronics products: Laptop A (4.5), Tablet C (4.2)
        assert len(results) == 2
        assert results[0]['name'] == "Laptop A"
        assert results[1]['name'] == "Tablet C"
        assert "Berikut Electronics terbaik berdasarkan rating:" in msg

    def test_smart_search_best_category_not_found(self, local_product_service_with_mocked_products):
        """Test smart_search_products for 'terbaik' within a non-existent category (falls back to general best)."""
        results, msg = local_product_service_with_mocked_products.smart_search_products(keyword="mobil terbaik", category="Automotive")
        # Should fallback to general best products (Mouse F, Keyboard G, etc.)
        assert len(results) == 5
        assert results[0]['name'] == "Mouse F"
        assert "Tidak ada produk kategori Automotive, berikut produk terbaik secara umum:" in msg

    def test_smart_search_combined_match(self, local_product_service_with_mocked_products):
        """Test smart_search_products with keyword, category, and max_price all matching."""
        # Search for a specific laptop within budget.
        # Laptop A: name 'Laptop A', category 'Electronics', price 10M.
        results, msg = local_product_service_with_mocked_products.smart_search_products(keyword="powerful laptop", category="Electronics", max_price=12000000)
        assert len(results) == 1
        assert results[0]['name'] == "Laptop A"
        assert "Berikut produk yang sesuai dengan kriteria Anda." in msg

    def test_smart_search_no_exact_match_fallback_category(self, local_product_service_with_mocked_products):
        """
        Test smart_search_products fallback 4: no exact match with all criteria,
        but category matches (and returns products sorted by price).
        """
        # Scenario: Search for "expensive monitor" (no keyword match), in "Electronics" category (matches),
        # with a very low max_price (e.g., 100k) so no product matches price filter.
        # This should then fall back to showing products in "Electronics" sorted by price.
        results, msg = local_product_service_with_mocked_products.smart_search_products(keyword="expensive monitor", category="Electronics", max_price=100000)
        # Electronics products: Tablet C (7M), Laptop A (10M). Sorted by price.
        assert len(results) == 2
        assert results[0]['name'] == "Tablet C" 
        assert results[1]['name'] == "Laptop A"
        assert "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut." in msg

    def test_smart_search_no_exact_match_fallback_budget(self, local_product_service_with_mocked_products):
        """
        Test smart_search_products fallback 5: no exact/category match,
        but products within the max_price range exist.
        """
        # Search "non-existent item" (no keyword match), no category, max_price 2.5M.
        # Products <= 2.5M: Headphones D (2M), Mouse F (0.5M), Keyboard G (1.5M).
        results, msg = local_product_service_with_mocked_products.smart_search_products(keyword="xyz", category=None, max_price=2500000)
        assert len(results) == 3
        assert {p['name'] for p in results} == {"Headphones D", "Mouse F", "Keyboard G"}
        # The order is based on the initial filtered list order, then limited.
        assert "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda." in msg

    def test_smart_search_no_match_fallback_popular(self, local_product_service_with_mocked_products):
        """
        Test smart_search_products fallback 6: no criteria matches,
        returns popular products (sorted by sold count).
        """
        # Override products to have varied 'sold' counts for a meaningful 'popular' test.
        mock_products_for_popular_test = [
            {"id": "pop1", "name": "Popular A", "specifications": {"sold": 2000, "rating": 4.0}},
            {"id": "pop2", "name": "Popular B", "specifications": {"sold": 500, "rating": 3.0}},
            {"id": "pop3", "name": "Popular C", "specifications": {"sold": 1500, "rating": 5.0}},
            {"id": "pop4", "name": "Popular D", "specifications": {"sold": 100, "rating": 2.0}},
            {"id": "pop5", "name": "Popular E", "specifications": {"sold": 2500, "rating": 4.5}},
            {"id": "pop6", "name": "Popular F", "specifications": {"sold": 0, "rating": 1.0}},
        ]
        local_product_service_with_mocked_products.products = mock_products_for_popular_test

        results, msg = local_product_service_with_mocked_products.smart_search_products(keyword="completely unrelated phrase", category="nonexistent type", max_price=1)
        assert len(results) == 5
        assert results[0]['name'] == "Popular E" # 2500 sold
        assert results[1]['name'] == "Popular A" # 2000 sold
        assert results[2]['name'] == "Popular C" # 1500 sold
        assert results[3]['name'] == "Popular B" # 500 sold
        assert results[4]['name'] == "Popular D" # 100 sold
        assert "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in msg

    def test_smart_search_empty_keyword_no_other_filters(self, local_product_service_with_mocked_products):
        """
        Test smart_search_products with an empty keyword and no other specific filters,
        should default to the popular products fallback.
        """
        # Override products to have varied 'sold' counts.
        mock_products_for_popular_test = [
            {"id": "pop1", "name": "Popular A", "specifications": {"sold": 2000, "rating": 4.0}},
            {"id": "pop2", "name": "Popular B", "specifications": {"sold": 500, "rating": 3.0}},
            {"id": "pop3", "name": "Popular C", "specifications": {"sold": 1500, "rating": 5.0}},
            {"id": "pop4", "name": "Popular D", "specifications": {"sold": 100, "rating": 2.0}},
            {"id": "pop5", "name": "Popular E", "specifications": {"sold": 2500, "rating": 4.5}},
            {"id": "pop6", "name": "Popular F", "specifications": {"sold": 0, "rating": 1.0}},
        ]
        local_product_service_with_mocked_products.products = mock_products_for_popular_test
        
        results, msg = local_product_service_with_mocked_products.smart_search_products(keyword='')
        assert len(results) == 5
        assert results[0]['name'] == "Popular E"
        assert "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in msg

    def test_smart_search_limit_parameter(self, local_product_service_with_mocked_products):
        """Test smart_search_products respects the limit parameter."""
        results, msg = local_product_service_with_mocked_products.smart_search_products(keyword="produk terbaik", limit=2)
        assert len(results) == 2
        assert results[0]['name'] == "Mouse F"
        assert results[1]['name'] == "Keyboard G"
        assert "Berikut produk terbaik berdasarkan rating:" in msg

    def test_smart_search_no_params(self, local_product_service_with_mocked_products):
        """Test smart_search_products called with no parameters (should fallback to popular)."""
        # Override products to have varied 'sold' counts.
        mock_products_for_popular_test = [
            {"id": "pop1", "name": "Popular A", "specifications": {"sold": 2000, "rating": 4.0}},
            {"id": "pop2", "name": "Popular B", "specifications": {"sold": 500, "rating": 3.0}},
            {"id": "pop3", "name": "Popular C", "specifications": {"sold": 1500, "rating": 5.0}},
            {"id": "pop4", "name": "Popular D", "specifications": {"sold": 100, "rating": 2.0}},
            {"id": "pop5", "name": "Popular E", "specifications": {"sold": 2500, "rating": 4.5}},
            {"id": "pop6", "name": "Popular F", "specifications": {"sold": 0, "rating": 1.0}},
        ]
        local_product_service_with_mocked_products.products = mock_products_for_popular_test

        results, msg = local_product_service_with_mocked_products.smart_search_products()
        assert len(results) == 5
        assert results[0]['name'] == "Popular E"
        assert "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in msg

    def test_smart_search_with_none_inputs(self, local_product_service_with_mocked_products):
        """Test smart_search_products with explicit None values for all filters (should fallback to popular)."""
        # Override products to have varied 'sold' counts.
        mock_products_for_popular_test = [
            {"id": "pop1", "name": "Popular A", "specifications": {"sold": 2000, "rating": 4.0}},
            {"id": "pop2", "name": "Popular B", "specifications": {"sold": 500, "rating": 3.0}},
            {"id": "pop3", "name": "Popular C", "specifications": {"sold": 1500, "rating": 5.0}},
            {"id": "pop4", "name": "Popular D", "specifications": {"sold": 100, "rating": 2.0}},
            {"id": "pop5", "name": "Popular E", "specifications": {"sold": 2500, "rating": 4.5}},
            {"id": "pop6", "name": "Popular F", "specifications": {"sold": 0, "rating": 1.0}},
        ]
        local_product_service_with_mocked_products.products = mock_products_for_popular_test

        results, msg = local_product_service_with_mocked_products.smart_search_products(keyword=None, category=None, max_price=None)
        assert len(results) == 5
        assert results[0]['name'] == "Popular E"
        assert "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in msg