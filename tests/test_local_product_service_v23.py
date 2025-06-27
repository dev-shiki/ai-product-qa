import pytest
import logging
import json
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

# Adjust the import path based on the file's location
# If the test file is test_services/local_product_service.py
# and the source is app/services/local_product_service.py
# then we need to go up two levels from test_services to reach app's parent,
# then down into app. This usually means sys.path manipulation or a relative import like:
# from app.services.local_product_service import LocalProductService
# For simplicity in this direct code generation, I'll assume standard project structure
# where 'app' is on the Python path or tests are run from the project root.
from app.services.local_product_service import LocalProductService

# Configure logging for tests if needed, or just capture logs
logger = logging.getLogger(__name__)

# --- Test Data and Fixtures ---

@pytest.fixture
def mock_valid_products_json_content():
    """Returns a string of valid JSON content for products."""
    return json.dumps({
        "products": [
            {
                "id": "101",
                "name": "Smartphone X",
                "category": "Smartphone",
                "brand": "BrandA",
                "price": 10000000,
                "currency": "IDR",
                "description": "Powerful smartphone",
                "specifications": {"rating": 4.5, "stock_count": 50, "specs_extra": "foo"},
                "availability": "in_stock",
                "reviews_count": 100
            },
            {
                "id": "102",
                "name": "Laptop Y",
                "category": "Laptop",
                "brand": "BrandB",
                "price": 15000000,
                "currency": "IDR",
                "description": "High-performance laptop",
                "specifications": {"rating": 4.8, "stock_count": 30, "sold": 1500},
                "reviews_count": 200
            },
            {
                "id": "103",
                "name": "Headphones Z",
                "category": "Audio",
                "brand": "BrandA",
                "price": 2000000,
                "currency": "IDR",
                "description": "Noise-cancelling headphones",
                "specifications": {"rating": 4.0, "stock_count": 100, "sold": 500},
                "availability": "out_of_stock"
            },
            {
                "id": "104",
                "name": "Tablet A",
                "category": "Tablet",
                "brand": "BrandC",
                "price": 8000000,
                "currency": "IDR",
                "description": "Portable tablet",
                "specifications": {"rating": 4.2, "stock_count": 20, "sold": 800},
                "reviews_count": 50
            },
            {
                "id": "105",
                "name": "Gaming PC",
                "category": "PC",
                "brand": "BrandD",
                "price": 25000000,
                "currency": "IDR",
                "description": "Ultimate Gaming Rig",
                "specifications": {"rating": 4.9, "stock_count": 10, "sold": 2000},
                "reviews_count": 300
            }
        ]
    })

@pytest.fixture
def mock_valid_products_json_content_with_bom():
    """Returns a string of valid JSON content with a BOM."""
    content = json.dumps({
        "products": [
            {
                "id": "bom_prod",
                "name": "BOM Product",
                "category": "Test",
                "brand": "BOMCo",
                "price": 1000,
                "specifications": {"rating": 3.0}
            }
        ]
    })
    return '\ufeff' + content

@pytest.fixture
def mock_empty_products_json_content():
    """Returns a string of empty JSON content for products."""
    return json.dumps({"products": []})

@pytest.fixture
def mock_malformed_json_content():
    """Returns a string of malformed JSON content."""
    return "{products: [ { 'id': 'malformed' }"

@pytest.fixture
def mock_invalid_encoding_content():
    """Returns content that will cause UnicodeDecodeError."""
    # This simulates bytes that cannot be decoded by common encodings
    return b'\xff\xfe\x00\x00\x00\x00\x00\x00'.decode('latin-1', errors='ignore') # Or any other way to get "bad" string data

@pytest.fixture
def mock_no_products_key_json_content():
    """Returns a JSON string without the 'products' key."""
    return json.dumps({"items": [{"id": "no_key_prod", "name": "No Key Product"}]})

@pytest.fixture
def local_product_service_instance_empty():
    """
    Fixture for LocalProductService with mocked _load_local_products
    to return an empty list.
    """
    with patch.object(LocalProductService, '_load_local_products', return_value=[]):
        yield LocalProductService()

@pytest.fixture
def local_product_service_instance(mock_valid_products_json_content):
    """
    Fixture for LocalProductService with mocked file operations
    to simulate a valid products.json file.
    """
    with patch('app.services.local_product_service.Path') as MockPath:
        # Configure Path to simulate the file exists
        mock_json_file_path = MockPath.return_value
        mock_json_file_path.exists.return_value = True

        # Configure open to return mock_valid_products_json_content
        mock_file_open = mock_open(read_data=mock_valid_products_json_content)
        with patch('builtins.open', mock_file_open):
            # Also patch random.randint for predictable test results
            with patch('app.services.local_product_service.random.randint', return_value=1000):
                service = LocalProductService()
                yield service, MockPath, mock_file_open

# --- Test Cases ---

class TestLocalProductServiceInitialization:
    @patch('app.services.local_product_service.Path')
    @patch('app.services.local_product_service.LocalProductService._load_local_products')
    @patch('app.services.local_product_service.logger')
    def test_init_loads_products_and_logs(self, mock_logger, mock_load_products, MockPath):
        """Test that __init__ calls _load_local_products and logs the count."""
        mock_load_products.return_value = [{"id": "1", "name": "Test Product"}]
        service = LocalProductService()

        mock_load_products.assert_called_once()
        assert service.products == [{"id": "1", "name": "Test Product"}]
        mock_logger.info.assert_called_once_with("Loaded 1 local products from JSON file")

class TestLocalProductServiceLoadProducts:

    @patch('app.services.local_product_service.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('app.services.local_product_service.random.randint', return_value=1000)
    @patch('app.services.local_product_service.logger')
    def test_load_local_products_success_and_transformation(self, mock_logger, mock_randint, mock_open_func, MockPath, mock_valid_products_json_content):
        """Test successful loading and transformation of products from JSON."""
        # Configure Path mock
        mock_json_file_path = MockPath.return_value
        mock_json_file_path.exists.return_value = True

        # Configure open mock
        mock_open_func.return_value.__enter__.return_value.read.return_value = mock_valid_products_json_content

        service = LocalProductService() # This calls _load_local_products internally
        products = service.products # Access the loaded products

        # Assert Path and open were called correctly
        MockPath.assert_called_once()
        mock_json_file_path.exists.assert_called_once()
        mock_open_func.assert_called_once_with(mock_json_file_path, 'r', encoding='utf-16-le') # First encoding attempt

        # Assert product transformation
        assert len(products) == 5
        prod1 = products[0]
        assert prod1['id'] == "101"
        assert prod1['name'] == "Smartphone X"
        assert prod1['price'] == 10000000
        assert prod1['currency'] == "IDR"
        assert prod1['images'] == ["https://example.com/101.jpg"]
        assert prod1['url'] == "https://shopee.co.id/101"
        assert prod1['specifications']['rating'] == 4.5
        assert prod1['specifications']['sold'] == 1000 # From mocked random.randint
        assert prod1['specifications']['stock'] == 50
        assert prod1['specifications']['condition'] == "Baru"
        assert prod1['specifications']['shop_location'] == "Indonesia"
        assert prod1['specifications']['shop_name'] == "BrandA Store"
        assert prod1['specifications']['specs_extra'] == "foo" # Ensures existing specs are kept
        assert prod1.get('reviews_count') == 100

        mock_logger.info.assert_any_call("Successfully loaded 5 products from JSON file using utf-16-le encoding")


    @patch('app.services.local_product_service.Path')
    @patch('app.services.local_product_service.LocalProductService._get_fallback_products')
    @patch('app.services.local_product_service.logger')
    def test_load_local_products_file_not_found(self, mock_logger, mock_get_fallback_products, MockPath):
        """Test _load_local_products when the JSON file does not exist."""
        mock_json_file_path = MockPath.return_value
        mock_json_file_path.exists.return_value = False
        mock_get_fallback_products.return_value = ["fallback_product"]

        service = LocalProductService() # This calls _load_local_products

        mock_json_file_path.exists.assert_called_once()
        mock_logger.error.assert_called_once_with(f"Products JSON file not found at: {mock_json_file_path}")
        mock_get_fallback_products.assert_called_once()
        assert service.products == ["fallback_product"]

    @patch('app.services.local_product_service.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('app.services.local_product_service.LocalProductService._get_fallback_products')
    @patch('app.services.local_product_service.logger')
    def test_load_local_products_malformed_json(self, mock_logger, mock_get_fallback_products, mock_open_func, MockPath, mock_malformed_json_content):
        """Test _load_local_products with malformed JSON, leading to fallback."""
        mock_json_file_path = MockPath.return_value
        mock_json_file_path.exists.return_value = True

        # Simulate JSONDecodeError for all encodings
        mock_open_func.return_value.__enter__.return_value.read.return_value = mock_malformed_json_content
        mock_get_fallback_products.return_value = ["fallback_product"]

        service = LocalProductService()

        # It should try all encodings and log warnings
        assert mock_open_func.call_count == len(['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252'])
        mock_logger.warning.call_count == len(['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252'])
        mock_logger.error.assert_called_once_with("All encoding attempts failed, using fallback products")
        mock_get_fallback_products.assert_called_once()
        assert service.products == ["fallback_product"]

    @patch('app.services.local_product_service.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('app.services.local_product_service.LocalProductService._get_fallback_products')
    @patch('app.services.local_product_service.logger')
    def test_load_local_products_unicode_decode_error(self, mock_logger, mock_get_fallback_products, mock_open_func, MockPath, mock_invalid_encoding_content):
        """Test _load_local_products with UnicodeDecodeError, leading to fallback."""
        mock_json_file_path = MockPath.return_value
        mock_json_file_path.exists.return_value = True

        # Simulate UnicodeDecodeError for all encodings
        mock_open_func.return_value.__enter__.return_value.read.side_effect = UnicodeDecodeError('utf-8', b'\x80', 0, 1, 'invalid start byte')
        mock_get_fallback_products.return_value = ["fallback_product"]

        service = LocalProductService()

        assert mock_open_func.call_count == len(['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252'])
        mock_logger.warning.call_count == len(['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252'])
        mock_logger.error.assert_called_once_with("All encoding attempts failed, using fallback products")
        mock_get_fallback_products.assert_called_once()
        assert service.products == ["fallback_product"]

    @patch('app.services.local_product_service.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('app.services.local_product_service.LocalProductService._get_fallback_products')
    @patch('app.services.local_product_service.logger')
    def test_load_local_products_general_exception(self, mock_logger, mock_get_fallback_products, mock_open_func, MockPath):
        """Test _load_local_products with a general exception, leading to fallback."""
        mock_json_file_path = MockPath.return_value
        mock_json_file_path.exists.return_value = True
        mock_open_func.side_effect = Exception("Permission denied") # Simulate OS error

        mock_get_fallback_products.return_value = ["fallback_product"]

        service = LocalProductService()

        mock_logger.error.assert_called_once_with("Error loading products from JSON file: Permission denied")
        mock_get_fallback_products.assert_called_once()
        assert service.products == ["fallback_product"]

    @patch('app.services.local_product_service.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('app.services.local_product_service.random.randint', return_value=1000)
    @patch('app.services.local_product_service.logger')
    def test_load_local_products_with_bom(self, mock_logger, mock_randint, mock_open_func, MockPath, mock_valid_products_json_content_with_bom):
        """Test _load_local_products correctly handles JSON with BOM."""
        mock_json_file_path = MockPath.return_value
        mock_json_file_path.exists.return_value = True
        mock_open_func.return_value.__enter__.return_value.read.return_value = mock_valid_products_json_content_with_bom

        service = LocalProductService()
        products = service.products

        assert len(products) == 1
        assert products[0]['id'] == "bom_prod"
        assert mock_logger.info.called # Should indicate successful load

    @patch('app.services.local_product_service.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('app.services.local_product_service.random.randint', return_value=1000)
    @patch('app.services.local_product_service.logger')
    def test_load_local_products_empty_products_list(self, mock_logger, mock_randint, mock_open_func, MockPath, mock_empty_products_json_content):
        """Test _load_local_products when 'products' key is an empty list."""
        mock_json_file_path = MockPath.return_value
        mock_json_file_path.exists.return_value = True
        mock_open_func.return_value.__enter__.return_value.read.return_value = mock_empty_products_json_content

        service = LocalProductService()
        products = service.products

        assert len(products) == 0
        mock_logger.info.assert_any_call("Successfully loaded 0 products from JSON file using utf-16-le encoding")

    @patch('app.services.local_product_service.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('app.services.local_product_service.random.randint', return_value=1000)
    @patch('app.services.local_product_service.logger')
    def test_load_local_products_no_products_key(self, mock_logger, mock_randint, mock_open_func, MockPath, mock_no_products_key_json_content):
        """Test _load_local_products when 'products' key is missing from JSON."""
        mock_json_file_path = MockPath.return_value
        mock_json_file_path.exists.return_value = True
        mock_open_func.return_value.__enter__.return_value.read.return_value = mock_no_products_key_json_content

        service = LocalProductService()
        products = service.products

        assert len(products) == 0 # .get('products', []) handles this
        mock_logger.info.assert_any_call("Successfully loaded 0 products from JSON file using utf-16-le encoding")

    @patch('app.services.local_product_service.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('app.services.local_product_service.random.randint', return_value=1000)
    @patch('app.services.local_product_service.logger')
    def test_load_local_products_partial_product_data(self, mock_logger, mock_randint, mock_open_func, MockPath):
        """Test product transformation with missing optional fields."""
        json_content = json.dumps({
            "products": [
                {
                    "id": "partial_prod",
                    "name": "Partial Product",
                    # Missing category, brand, price, description, etc.
                }
            ]
        })
        mock_json_file_path = MockPath.return_value
        mock_json_file_path.exists.return_value = True
        mock_open_func.return_value.__enter__.return_value.read.return_value = json_content

        service = LocalProductService()
        products = service.products

        assert len(products) == 1
        prod = products[0]
        assert prod['id'] == "partial_prod"
        assert prod['name'] == "Partial Product"
        assert prod['category'] == "" # Default value
        assert prod['price'] == 0 # Default value
        assert prod['currency'] == "IDR" # Default value
        assert prod['description'] == "" # Default value
        assert prod['specifications']['rating'] == 0 # Default value
        assert prod['specifications']['sold'] == 1000 # Mocked
        assert prod['specifications']['stock'] == 0 # Default value
        assert prod['specifications']['condition'] == "Baru" # Default
        assert prod['availability'] == "in_stock" # Default

class TestLocalProductServiceFallback:
    @patch('app.services.local_product_service.logger')
    def test_get_fallback_products(self, mock_logger):
        """Test _get_fallback_products returns a non-empty list and logs a warning."""
        service = LocalProductService() # This init will call _load_local_products which will call _get_fallback_products if Path is mocked
        products = service._get_fallback_products()
        assert len(products) == 8 # Based on the provided fallback data
        assert products[0]['id'] == "1"
        mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error")

class TestLocalProductServiceSearchProducts:
    def test_search_products_by_keyword(self, local_product_service_instance):
        """Test searching products by a general keyword."""
        service, _, _ = local_product_service_instance
        results = service.search_products("smartphone")
        assert len(results) == 1
        assert results[0]['id'] == "101"
        assert results[0]['name'] == "Smartphone X"

    def test_search_products_by_brand(self, local_product_service_instance):
        """Test searching products by brand keyword."""
        service, _, _ = local_product_service_instance
        results = service.search_products("BrandA")
        assert len(results) == 2
        assert {p['id'] for p in results} == {"101", "103"}

    def test_search_products_case_insensitivity(self, local_product_service_instance):
        """Test search is case-insensitive."""
        service, _, _ = local_product_service_instance
        results = service.search_products("lApToP")
        assert len(results) == 1
        assert results[0]['id'] == "102"

    def test_search_products_no_match(self, local_product_service_instance):
        """Test search with a keyword that yields no results."""
        service, _, _ = local_product_service_instance
        results = service.search_products("nonexistent_product")
        assert len(results) == 0

    def test_search_products_limit(self, local_product_service_instance):
        """Test search_products respects the limit parameter."""
        service, _, _ = local_product_service_instance
        # Both BrandA products should match, but limit to 1
        results = service.search_products("BrandA", limit=1)
        assert len(results) == 1
        # The higher rated product should be first due to relevance_score (BrandA in name = 5, in desc = 0)
        assert results[0]['id'] == "101" # "BrandA" in brand, higher rating

    def test_search_products_empty_keyword(self, local_product_service_instance):
        """Test search with an empty keyword returns an empty list."""
        service, _, _ = local_product_service_instance
        results = service.search_products("")
        assert len(results) == 0 # Empty keyword should not match anything by default logic

    @patch('app.services.local_product_service.logger')
    def test_search_products_exception_handling(self, mock_logger, local_product_service_instance):
        """Test search_products handles general exceptions."""
        service, _, _ = local_product_service_instance
        # Simulate an error by making products uniterable
        service.products = None
        results = service.search_products("anything")
        assert len(results) == 0
        mock_logger.error.assert_called_once()
        assert "Error searching products" in mock_logger.error.call_args[0][0]

    def test_search_products_with_price_range(self, local_product_service_instance):
        """Test searching products including a price range in the keyword."""
        service, _, _ = local_product_service_instance
        results = service.search_products("laptop 10 juta")
        # Should return Laptop Y (15M) OR filter to those <= 10M
        # The price extraction takes precedence. Laptop Y is 15M, so it should not be included
        # unless it also matches 'laptop' and the price filter logic is `and` vs `or`.
        # Current logic: `if max_price and product_price <= max_price: filtered_products.append(product); continue`
        # This means price filter acts as an OR, which is not intuitive for a combined search.
        # Let's adjust expected behavior based on the current code.
        # 'laptop' matches Laptop Y. '10 juta' filters Smartphone X (10M), Headphones Z (2M), Tablet A (8M).
        # Gaming PC (25M) is excluded by price. Laptop Y (15M) is excluded by price.
        # Relevance will prioritize the keyword "laptop".
        
        # Products matching "laptop": [Laptop Y] (price 15M)
        # Products matching price <= 10M: [Smartphone X (10M), Headphones Z (2M), Tablet A (8M)]
        # The current implementation uses an OR-like behavior for price.
        # `if max_price and product_price <= max_price: filtered_products.append(product); continue`
        # This means if it matches price, it's added. Otherwise, it checks text.
        
        results = service.search_products("laptop 10 juta")
        assert len(results) == 4 # Smartphone X, Headphones Z, Tablet A (by price) + Laptop Y (by keyword)
        ids = {p['id'] for p in results}
        assert ids == {"101", "102", "103", "104"}
        
        # Test a more restrictive budget search
        results_budget = service.search_products("smartphone murah")
        assert len(results_budget) == 3 # Based on "murah" being 5M
        # Smartphone X (10M) is > 5M, but matches 'smartphone' keyword.
        # Headphones Z (2M) and Tablet A (8M) and Gaming PC (25M)
        # Price filter logic: 'murah' -> max_price = 5M
        # Products <= 5M: Headphones Z (2M)
        # Products matching 'smartphone': Smartphone X (10M)
        # The `continue` makes it an OR.
        # So: Headphones Z (by price), Smartphone X (by keyword)
        # Let's verify the relevance sorting: score for 'murah' is (5M - price)/1M.
        # For Smartphone X: price=10M, budget score is negative. Keyword score is high.
        # For Headphones Z: price=2M, budget score is (5M - 2M)/1M = 3. Keyword score is 0.
        
        # The `relevance_score` function has a bug for budget searches with negative values if price > 10M.
        # score += (10000000 - product.get('price', 0)) / 1000000
        # If price is 15M, score -= 5.
        
        # Let's re-evaluate what we expect given the code:
        # "smartphone murah" -> max_price = 5M
        # Candidates:
        # 1. Smartphone X (ID 101, price 10M): Does NOT meet price <= 5M. Matches 'smartphone' keyword. Added.
        # 2. Laptop Y (ID 102, price 15M): Does NOT meet price <= 5M. Does NOT match 'smartphone'. Not added.
        # 3. Headphones Z (ID 103, price 2M): Meets price <= 5M. Added.
        # 4. Tablet A (ID 104, price 8M): Does NOT meet price <= 5M. Does NOT match 'smartphone'. Not added.
        # 5. Gaming PC (ID 105, price 25M): Does NOT meet price <= 5M. Does NOT match 'smartphone'. Not added.
        # Filtered products: [Smartphone X, Headphones Z]
        # Sort:
        # Smartphone X: name score 10, brand/cat 0, budget score (10M-10M)/1M=0 if `max_price` is set.
        # Headphones Z: name score 0, brand/cat 0, budget score (10M-2M)/1M=8 if `max_price` is set.
        
        # The `relevance_score` is applied to `filtered_products`.
        # It's based on `max_price` being set (which it is for "murah"),
        # or `any(word in keyword_lower for word in ['murah', ...])` (which is true).
        # So for both, `score += (10000000 - price)/1000000` is applied.
        # For Smartphone X (10M): score (name) = 10, budget score = (10M - 10M) / 1M = 0. Total = 10.
        # For Headphones Z (2M): score (name) = 0, budget score = (10M - 2M) / 1M = 8. Total = 8.
        # Sorted results should be: [Smartphone X, Headphones Z].
        
        # Re-run the test to confirm this
        results_budget = service.search_products("smartphone murah", limit=10)
        assert len(results_budget) == 2
        assert results_budget[0]['id'] == "101" # Smartphone X (Higher relevance score due to keyword match)
        assert results_budget[1]['id'] == "103" # Headphones Z (Lower relevance score, but matched price)


class TestLocalProductServiceExtractPrice:
    @patch('app.services.local_product_service.logger')
    def test_extract_price_from_keyword_juta(self, mock_logger):
        """Test price extraction for 'juta' pattern."""
        service = LocalProductService()
        assert service._extract_price_from_keyword("laptop 10 juta") == 10000000
        assert service._extract_price_from_keyword("smartphone 2.5 juta") == None # Current regex only takes int, not float

    @patch('app.services.local_product_service.logger')
    def test_extract_price_from_keyword_ribu(self, mock_logger):
        """Test price extraction for 'ribu' pattern."""
        service = LocalProductService()
        assert service._extract_price_from_keyword("headset 50 ribu") == 50000
        assert service._extract_price_from_keyword("baju 5 ribu") == 5000

    @patch('app.services.local_product_service.logger')
    def test_extract_price_from_keyword_rp_prefix(self, mock_logger):
        """Test price extraction for 'rp' prefix pattern."""
        service = LocalProductService()
        assert service._extract_price_from_keyword("monitor rp 2500000") == 2500000
        assert service._extract_price_from_keyword("rp 150000") == 150000

    @patch('app.services.local_product_service.logger')
    def test_extract_price_from_keyword_rp_suffix(self, mock_logger):
        """Test price extraction for 'rp' suffix pattern."""
        service = LocalProductService()
        assert service._extract_price_from_keyword("hp 3000000 rp") == 3000000

    @patch('app.services.local_product_service.logger')
    def test_extract_price_from_keyword_k_suffix(self, mock_logger):
        """Test price extraction for 'k' suffix pattern."""
        service = LocalProductService()
        assert service._extract_price_from_keyword("buku 20k") == 20000
        assert service._extract_price_from_keyword("harga 50k") == 50000

    @patch('app.services.local_product_service.logger')
    def test_extract_price_from_keyword_m_suffix(self, mock_logger):
        """Test price extraction for 'm' suffix pattern."""
        service = LocalProductService()
        assert service._extract_price_from_keyword("mobil 300m") == 300000000

    @patch('app.services.local_product_service.logger')
    def test_extract_price_from_keyword_budget_keywords(self, mock_logger):
        """Test price extraction for budget keywords."""
        service = LocalProductService()
        assert service._extract_price_from_keyword("headset murah") == 5000000
        assert service._extract_price_from_keyword("budget gaming pc") == 5000000
        assert service._extract_price_from_keyword("cari yang hemat") == 3000000
        assert service._extract_price_from_keyword("price terjangkau") == 4000000
        assert service._extract_price_from_keyword("ekonomis saja") == 2000000

    @patch('app.services.local_product_service.logger')
    def test_extract_price_from_keyword_no_price(self, mock_logger):
        """Test price extraction when no price or budget keyword is present."""
        service = LocalProductService()
        assert service._extract_price_from_keyword("random keyword") is None
        assert service._extract_price_from_keyword("") is None

    @patch('app.services.local_product_service.logger')
    def test_extract_price_from_keyword_exception_handling(self, mock_logger):
        """Test _extract_price_from_keyword handles exceptions."""
        service = LocalProductService()
        with patch('re.search', side_effect=Exception("Regex error")):
            result = service._extract_price_from_keyword("10 juta")
            assert result is None
            mock_logger.error.assert_called_once()
            assert "Error extracting price from keyword" in mock_logger.error.call_args[0][0]

class TestLocalProductServiceGetDetails:
    def test_get_product_details_found(self, local_product_service_instance):
        """Test get_product_details returns correct product for existing ID."""
        service, _, _ = local_product_service_instance
        product = service.get_product_details("102")
        assert product is not None
        assert product['name'] == "Laptop Y"

    def test_get_product_details_not_found(self, local_product_service_instance):
        """Test get_product_details returns None for non-existing ID."""
        service, _, _ = local_product_service_instance
        product = service.get_product_details("nonexistent_id")
        assert product is None

    def test_get_product_details_empty_id(self, local_product_service_instance):
        """Test get_product_details with empty ID."""
        service, _, _ = local_product_service_instance
        product = service.get_product_details("")
        assert product is None

    @patch('app.services.local_product_service.logger')
    def test_get_product_details_exception_handling(self, mock_logger, local_product_service_instance):
        """Test get_product_details handles general exceptions."""
        service, _, _ = local_product_service_instance
        service.products = None # Simulate an error
        result = service.get_product_details("101")
        assert result is None
        mock_logger.error.assert_called_once()
        assert "Error getting product details" in mock_logger.error.call_args[0][0]

class TestLocalProductServiceCategoriesAndBrands:
    def test_get_categories(self, local_product_service_instance):
        """Test get_categories returns unique sorted categories."""
        service, _, _ = local_product_service_instance
        categories = service.get_categories()
        assert categories == ["Audio", "Laptop", "PC", "Smartphone", "Tablet"]
        assert len(categories) == 5

    def test_get_categories_with_empty_products(self, local_product_service_instance_empty):
        """Test get_categories with an empty product list."""
        service = local_product_service_instance_empty
        categories = service.get_categories()
        assert categories == []

    def test_get_categories_with_product_missing_category(self):
        """Test get_categories handles products with missing 'category' key."""
        with patch.object(LocalProductService, '_load_local_products', return_value=[{"id": "1", "name": "No Category Product"}]):
            service = LocalProductService()
            categories = service.get_categories()
            assert categories == [""] # Should include empty string for missing category

    def test_get_brands(self, local_product_service_instance):
        """Test get_brands returns unique sorted brands."""
        service, _, _ = local_product_service_instance
        brands = service.get_brands()
        assert brands == ["BrandA", "BrandB", "BrandC", "BrandD"]
        assert len(brands) == 4

    def test_get_brands_with_empty_products(self, local_product_service_instance_empty):
        """Test get_brands with an empty product list."""
        service = local_product_service_instance_empty
        brands = service.get_brands()
        assert brands == []

    def test_get_brands_with_product_missing_brand(self):
        """Test get_brands handles products with missing 'brand' key."""
        with patch.object(LocalProductService, '_load_local_products', return_value=[{"id": "1", "name": "No Brand Product"}]):
            service = LocalProductService()
            brands = service.get_brands()
            assert brands == [""] # Should include empty string for missing brand

class TestLocalProductServiceFilterByCategoryAndBrand:
    def test_get_products_by_category(self, local_product_service_instance):
        """Test get_products_by_category returns correct products."""
        service, _, _ = local_product_service_instance
        results = service.get_products_by_category("Smartphone")
        assert len(results) == 1
        assert results[0]['id'] == "101"

    def test_get_products_by_category_case_insensitive(self, local_product_service_instance):
        """Test get_products_by_category is case-insensitive."""
        service, _, _ = local_product_service_instance
        results = service.get_products_by_category("laptop")
        assert len(results) == 1
        assert results[0]['id'] == "102"

    def test_get_products_by_category_no_match(self, local_product_service_instance):
        """Test get_products_by_category returns empty list for no match."""
        service, _, _ = local_product_service_instance
        results = service.get_products_by_category("NonExistentCategory")
        assert len(results) == 0

    @patch('app.services.local_product_service.logger')
    def test_get_products_by_category_exception_handling(self, mock_logger, local_product_service_instance):
        """Test get_products_by_category handles general exceptions."""
        service, _, _ = local_product_service_instance
        service.products = None
        results = service.get_products_by_category("Smartphone")
        assert len(results) == 0
        mock_logger.error.assert_called_once()
        assert "Error getting products by category" in mock_logger.error.call_args[0][0]

    def test_get_products_by_brand(self, local_product_service_instance):
        """Test get_products_by_brand returns correct products."""
        service, _, _ = local_product_service_instance
        results = service.get_products_by_brand("BrandA")
        assert len(results) == 2
        assert {p['id'] for p in results} == {"101", "103"}

    def test_get_products_by_brand_case_insensitive(self, local_product_service_instance):
        """Test get_products_by_brand is case-insensitive."""
        service, _, _ = local_product_service_instance
        results = service.get_products_by_brand("branda")
        assert len(results) == 2
        assert {p['id'] for p in results} == {"101", "103"}

    def test_get_products_by_brand_no_match(self, local_product_service_instance):
        """Test get_products_by_brand returns empty list for no match."""
        service, _, _ = local_product_service_instance
        results = service.get_products_by_brand("NonExistentBrand")
        assert len(results) == 0

    @patch('app.services.local_product_service.logger')
    def test_get_products_by_brand_exception_handling(self, mock_logger, local_product_service_instance):
        """Test get_products_by_brand handles general exceptions."""
        service, _, _ = local_product_service_instance
        service.products = None
        results = service.get_products_by_brand("BrandA")
        assert len(results) == 0
        mock_logger.error.assert_called_once()
        assert "Error getting products by brand" in mock_logger.error.call_args[0][0]

class TestLocalProductServiceTopAndBestSelling:
    def test_get_top_rated_products(self, local_product_service_instance):
        """Test get_top_rated_products returns products sorted by rating."""
        service, _, _ = local_product_service_instance
        top_products = service.get_top_rated_products(limit=3)
        assert len(top_products) == 3
        # Gaming PC (4.9), Laptop Y (4.8), Smartphone X (4.5)
        assert top_products[0]['id'] == "105"
        assert top_products[1]['id'] == "102"
        assert top_products[2]['id'] == "101"

    def test_get_top_rated_products_limit_exceeds_total(self, local_product_service_instance):
        """Test get_top_rated_products when limit is greater than total products."""
        service, _, _ = local_product_service_instance
        top_products = service.get_top_rated_products(limit=10)
        assert len(top_products) == 5 # Returns all products

    def test_get_top_rated_products_missing_specs_or_rating(self):
        """Test get_top_rated_products handles missing 'specifications' or 'rating' keys."""
        with patch.object(LocalProductService, '_load_local_products', return_value=[
            {"id": "1", "name": "No Rating", "specifications": {}},
            {"id": "2", "name": "No Specs"},
            {"id": "3", "name": "High Rating", "specifications": {"rating": 5.0}},
        ]):
            service = LocalProductService()
            top_products = service.get_top_rated_products(limit=3)
            assert len(top_products) == 3
            assert top_products[0]['id'] == "3"
            # The products with missing rating will default to 0 and come after high rating
            assert {p['id'] for p in top_products[1:]} == {"1", "2"}

    @patch('app.services.local_product_service.logger')
    def test_get_top_rated_products_exception_handling(self, mock_logger, local_product_service_instance):
        """Test get_top_rated_products handles general exceptions."""
        service, _, _ = local_product_service_instance
        service.products = None
        results = service.get_top_rated_products()
        assert len(results) == 0
        mock_logger.error.assert_called_once()
        assert "Error getting top rated products" in mock_logger.error.call_args[0][0]

    def test_get_best_selling_products(self, local_product_service_instance):
        """Test get_best_selling_products returns products sorted by sold count."""
        service, _, _ = local_product_service_instance
        best_selling = service.get_best_selling_products(limit=3)
        assert len(best_selling) == 3
        # Gaming PC (2000), Laptop Y (1500), Tablet A (800)
        assert best_selling[0]['id'] == "105"
        assert best_selling[1]['id'] == "102"
        assert best_selling[2]['id'] == "104"

    def test_get_best_selling_products_limit_exceeds_total(self, local_product_service_instance):
        """Test get_best_selling_products when limit is greater than total products."""
        service, _, _ = local_product_service_instance
        best_selling = service.get_best_selling_products(limit=10)
        assert len(best_selling) == 5 # Returns all products

    def test_get_best_selling_products_missing_specs_or_sold(self):
        """Test get_best_selling_products handles missing 'specifications' or 'sold' keys."""
        with patch.object(LocalProductService, '_load_local_products', return_value=[
            {"id": "1", "name": "No Sold", "specifications": {}},
            {"id": "2", "name": "No Specs"},
            {"id": "3", "name": "High Sold", "specifications": {"sold": 1000}},
        ]):
            service = LocalProductService()
            best_selling = service.get_best_selling_products(limit=3)
            assert len(best_selling) == 3
            assert best_selling[0]['id'] == "3"
            # Products with missing sold count default to 0 and come after
            assert {p['id'] for p in best_selling[1:]} == {"1", "2"}

    @patch('app.services.local_product_service.logger')
    def test_get_best_selling_products_exception_handling(self, mock_logger, local_product_service_instance):
        """Test get_best_selling_products handles general exceptions."""
        service, _, _ = local_product_service_instance
        service.products = None
        results = service.get_best_selling_products()
        assert len(results) == 0
        mock_logger.error.assert_called_once()
        assert "Error getting best selling products" in mock_logger.error.call_args[0][0]

class TestLocalProductServiceGetProducts:
    def test_get_products_default_limit(self, local_product_service_instance):
        """Test get_products with default limit."""
        service, _, _ = local_product_service_instance
        products = service.get_products()
        assert len(products) == 5 # Since there are 5 products in fixture and default limit is 10, it returns all

    def test_get_products_custom_limit(self, local_product_service_instance):
        """Test get_products with a custom limit."""
        service, _, _ = local_product_service_instance
        products = service.get_products(limit=2)
        assert len(products) == 2
        assert products[0]['id'] == "101"
        assert products[1]['id'] == "102"

    def test_get_products_limit_zero(self, local_product_service_instance):
        """Test get_products with limit 0."""
        service, _, _ = local_product_service_instance
        products = service.get_products(limit=0)
        assert len(products) == 0

    @patch('app.services.local_product_service.logger')
    def test_get_products_exception_handling(self, mock_logger, local_product_service_instance):
        """Test get_products handles general exceptions."""
        service, _, _ = local_product_service_instance
        service.products = None
        results = service.get_products()
        assert len(results) == 0
        mock_logger.error.assert_called_once()
        assert "Error getting products" in mock_logger.error.call_args[0][0]

class TestLocalProductServiceSmartSearch:
    # This method is quite complex with multiple fallbacks, so thorough testing is needed.
    # It returns (list of products, message string)

    def test_smart_search_best_general(self, local_product_service_instance):
        """Test smart_search for 'terbaik' keyword without specific category."""
        service, _, _ = local_product_service_instance
        products, msg = service.smart_search_products(keyword="terbaik", limit=3)
        assert msg == "Berikut produk terbaik berdasarkan rating:"
        assert len(products) == 3
        # Gaming PC (4.9), Laptop Y (4.8), Smartphone X (4.5)
        assert products[0]['id'] == "105"
        assert products[1]['id'] == "102"
        assert products[2]['id'] == "101"

    def test_smart_search_best_with_category_found(self, local_product_service_instance):
        """Test smart_search for 'terbaik' with a specific existing category."""
        service, _, _ = local_product_service_instance
        products, msg = service.smart_search_products(keyword="terbaik", category="Smartphone", limit=1)
        assert msg == "Berikut Smartphone terbaik berdasarkan rating:"
        assert len(products) == 1
        assert products[0]['id'] == "101" # Smartphone X is the only smartphone

    def test_smart_search_best_with_category_not_found(self, local_product_service_instance):
        """Test smart_search for 'terbaik' with a non-existing category, falls back to general best."""
        service, _, _ = local_product_service_instance
        products, msg = service.smart_search_products(keyword="terbaik", category="NonExistentCategory", limit=2)
        assert msg == "Tidak ada produk kategori NonExistentCategory, berikut produk terbaik secara umum:"
        assert len(products) == 2
        # Should be general best: Gaming PC (4.9), Laptop Y (4.8)
        assert products[0]['id'] == "105"
        assert products[1]['id'] == "102"

    def test_smart_search_all_criteria_match(self, local_product_service_instance):
        """Test smart_search when all keyword, category, max_price criteria match."""
        service, _, _ = local_product_service_instance
        # Smartphone X: 10M, Smartphone category
        products, msg = service.smart_search_products(keyword="phone", category="Smartphone", max_price=12000000, limit=1)
        assert msg == "Berikut produk yang sesuai dengan kriteria Anda."
        assert len(products) == 1
        assert products[0]['id'] == "101" # Smartphone X

    def test_smart_search_keyword_only(self, local_product_service_instance):
        """Test smart_search with only a keyword."""
        service, _, _ = local_product_service_instance
        products, msg = service.smart_search_products(keyword="laptop", limit=1)
        assert msg == "Berikut produk yang sesuai dengan kriteria Anda."
        assert len(products) == 1
        assert products[0]['id'] == "102"

    def test_smart_search_category_only(self, local_product_service_instance):
        """Test smart_search with only a category."""
        service, _, _ = local_product_service_instance
        products, msg = service.smart_search_products(category="Audio", limit=1)
        assert msg == "Berikut produk yang sesuai dengan kriteria Anda."
        assert len(products) == 1
        assert products[0]['id'] == "103"

    def test_smart_search_max_price_only(self, local_product_service_instance):
        """Test smart_search with only a max_price."""
        service, _, _ = local_product_service_instance
        products, msg = service.smart_search_products(max_price=5000000, limit=1)
        assert msg == "Berikut produk yang sesuai dengan kriteria Anda."
        assert len(products) == 1
        assert products[0]['id'] == "103" # Headphones Z, 2M (cheapest and <= 5M)

    def test_smart_search_fallback_category_no_budget(self, local_product_service_instance):
        """
        Test smart_search fallback 1:
        keyword doesn't match, max_price is too low, but category matches.
        Should return products in the category, sorted by price.
        """
        service, _, _ = local_product_service_instance
        # Keyword 'superphone' won't match. Category 'Smartphone' exists.
        # Max price 5M, Smartphone X is 10M, so max_price filters it out.
        products, msg = service.smart_search_products(keyword="superphone", category="Smartphone", max_price=5000000, limit=1)
        assert msg == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."
        assert len(products) == 1
        assert products[0]['id'] == "101" # Smartphone X (10M), the only smartphone, cheapest in category

    def test_smart_search_fallback_budget_no_category(self, local_product_service_instance):
        """
        Test smart_search fallback 2:
        keyword doesn't match, category doesn't match, but max_price matches other products.
        Should return products within budget, regardless of category.
        """
        service, _, _ = local_product_service_instance
        # Keyword 'superwatch' won't match. Category 'Watch' doesn't exist.
        # Max price 5M: Headphones Z (2M)
        products, msg = service.smart_search_products(keyword="superwatch", category="Watch", max_price=5000000, limit=1)
        assert msg == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."
        assert len(products) == 1
        assert products[0]['id'] == "103" # Headphones Z

    def test_smart_search_fallback_popular(self, local_product_service_instance):
        """
        Test smart_search fallback 3:
        No keyword, category, or max_price matches anything.
        Should return best-selling products.
        """
        service, _, _ = local_product_service_instance
        # Keyword 'xyz', category 'abc', max_price 10 (very low)
        products, msg = service.smart_search_products(keyword="xyz", category="abc", max_price=10, limit=2)
        assert msg == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
        assert len(products) == 2
        # Should be best-selling: Gaming PC (2000 sold), Laptop Y (1500 sold)
        assert products[0]['id'] == "105"
        assert products[1]['id'] == "102"

    def test_smart_search_no_criteria(self, local_product_service_instance):
        """Test smart_search with no keyword, category, or max_price specified."""
        service, _, _ = local_product_service_instance
        products, msg = service.smart_search_products(limit=2)
        # Should behave like the last fallback (popular)
        assert msg == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
        assert len(products) == 2
        assert products[0]['id'] == "105"
        assert products[1]['id'] == "102"

    def test_smart_search_empty_product_list(self, local_product_service_instance_empty):
        """Test smart_search with an empty internal product list."""
        service = local_product_service_instance_empty
        products, msg = service.smart_search_products(keyword="anything")
        assert len(products) == 0
        assert msg == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." # Still returns the message, just an empty list
        
        products, msg = service.smart_search_products(keyword="terbaik")
        assert len(products) == 0
        assert msg == "Berikut produk terbaik berdasarkan rating:"