import pytest
import sys
import os
import json
import logging
import re
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

# Adjust path to import the module under test
# Assuming test file is test_services/local_product_service.py
# and source is app/services/local_product_service.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.services.local_product_service import LocalProductService

# --- Fixtures ---

@pytest.fixture
def mock_products_data():
    """Sample raw product data as it would appear in a JSON file."""
    return {
        "products": [
            {
                "id": "prod1",
                "name": "Product Alpha",
                "category": "Electronics",
                "brand": "BrandX",
                "price": 1000000,
                "currency": "IDR",
                "description": "A great product.",
                "rating": 4.5,
                "stock_count": 50,
                "specifications": {"color": "red"}
            },
            {
                "id": "prod2",
                "name": "Product Beta",
                "category": "Books",
                "brand": "BrandY",
                "price": 50000,
                "currency": "IDR",
                "description": "An interesting book.",
                "rating": 3.8,
                "stock_count": 100,
                "reviews_count": 10,
                "specifications": {"pages": 200}
            },
            {
                "id": "prod3",
                "name": "Product Gamma",
                "category": "Electronics",
                "brand": "BrandZ",
                "price": 2000000,
                "currency": "IDR",
                "description": "Another electronic item.",
                "rating": 4.9,
                "stock_count": 20,
                "reviews_count": 5,
                "availability": "out_of_stock",
                "specifications": {"warranty": "1 year"}
            },
            {
                "id": "prod4",
                "name": "Product Delta",
                "category": "Home Goods",
                "brand": "BrandX",
                "price": 150000,
                "currency": "IDR",
                "description": "Useful for home.",
                "rating": 4.0,
                "stock_count": 80,
                "specifications": {"material": "wood"}
            },
            {
                "id": "prod5",
                "name": "Product Epsilon",
                "category": "Electronics",
                "brand": "BrandA",
                "price": 30000000,
                "currency": "IDR",
                "description": "High-end gadget.",
                "rating": 5.0,
                "stock_count": 5,
                "reviews_count": 20,
                "specifications": {"processor": "XYZ"}
            }
        ]
    }

@pytest.fixture
def mock_transformed_products_template(mock_products_data, setup_random_randint_mock):
    """
    Returns a template for transformed product data,
    with 'sold' count set by the mocked random.randint.
    """
    transformed = []
    for p in mock_products_data['products']:
        tp = {
            "id": p.get('id', ''),
            "name": p.get('name', ''),
            "category": p.get('category', ''),
            "brand": p.get('brand', ''),
            "price": p.get('price', 0),
            "currency": p.get('currency', 'IDR'),
            "description": p.get('description', ''),
            "specifications": {
                "rating": p.get('rating', 0),
                "sold": setup_random_randint_mock.return_value, # Uses the fixed mocked value
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
        transformed.append(tp)
    return transformed

@pytest.fixture
def mock_local_product_service(mock_transformed_products_template):
    """Fixture for LocalProductService with mocked products."""
    with patch('app.services.local_product_service.LocalProductService._load_local_products',
               return_value=mock_transformed_products_template):
        service = LocalProductService()
        yield service

@pytest.fixture
def mock_logger():
    """Mock the logger to capture log messages."""
    with patch('app.services.local_product_service.logger') as mock_log:
        yield mock_log

@pytest.fixture(autouse=True)
def setup_random_randint_mock():
    """Always mock random.randint for predictable sold counts."""
    with patch('app.services.local_product_service.random.randint', return_value=500) as mock_rand:
        yield mock_rand

# --- Tests ---

# Test __init__ and _load_local_products
class TestLocalProductServiceInitializationAndLoading:

    @patch('app.services.local_product_service.Path')
    @patch('app.services.local_product_service.json')
    def test_init_and_load_success(self, mock_json, mock_path, mock_products_data, mock_transformed_products_template, mock_logger):
        """Test successful initialization and product loading."""
        mock_file_path = MagicMock()
        mock_file_path.exists.return_value = True
        mock_path.return_value.__truediv__.return_value.__truediv__.return_value = mock_file_path
        
        # Simulate file content with mock_open
        mock_open_func = mock_open(read_data=json.dumps(mock_products_data))
        with patch('builtins.open', mock_open_func):
            mock_json.loads.return_value = mock_products_data

            service = LocalProductService()

            mock_path.assert_called()
            mock_file_path.exists.assert_called_once()
            # It tries 'utf-16-le' first
            mock_open_func.assert_called_with(mock_file_path, 'r', encoding='utf-16-le')
            mock_json.loads.assert_called_once_with(json.dumps(mock_products_data))
            
            assert len(service.products) == len(mock_transformed_products_template)
            # Deep check for one product to ensure transformation is correct
            assert service.products[0] == mock_transformed_products_template[0]
            assert service.products[0]['specifications']['sold'] == 500

            mock_logger.info.assert_any_call(f"Loaded {len(mock_transformed_products_template)} local products from JSON file")
            mock_logger.info.assert_any_call(f"Successfully loaded {len(mock_transformed_products_template)} products from JSON file using utf-16-le encoding")

    @patch('app.services.local_product_service.Path')
    def test_init_file_not_found(self, mock_path, mock_logger):
        """Test initialization when product JSON file is not found."""
        mock_file_path = MagicMock()
        mock_file_path.exists.return_value = False
        mock_path.return_value.__truediv__.return_value.__truediv__.return_value = mock_file_path
        
        service = LocalProductService()

        mock_path.assert_called()
        mock_file_path.exists.assert_called_once()
        mock_logger.error.assert_called_once_with(f"Products JSON file not found at: {mock_file_path}")
        mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error")
        assert len(service.products) == len(service._get_fallback_products())
        assert service.products[0]['id'] == "1" # Check if it's indeed fallback products

    @patch('app.services.local_product_service.Path')
    @patch('app.services.local_product_service.json')
    def test_load_all_encodings_fail_fallback(self, mock_json, mock_path, mock_logger):
        """Test loading where all encoding attempts (and json decoding) fail, leading to fallback."""
        mock_file_path = MagicMock()
        mock_file_path.exists.return_value = True
        mock_path.return_value.__truediv__.return_value.__truediv__.return_value = mock_file_path

        encodings = ['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        
        # Simulate open reading some raw data, but json.loads failing consistently
        mock_open_func = mock_open(read_data='some invalid json data') 
        
        with patch('builtins.open', mock_open_func):
            mock_json.loads.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)

            service = LocalProductService()
            
            # Assertions
            assert mock_open_func.call_count == len(encodings)
            for encoding in encodings:
                mock_open_func.assert_any_call(mock_file_path, 'r', encoding=encoding)
                mock_logger.warning.assert_any_call(f"Failed to load with {encoding} encoding: Expecting value: line 1 column 1 (char 0)")

            mock_logger.error.assert_called_once_with("All encoding attempts failed, using fallback products")
            mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error")
            assert len(service.products) == len(service._get_fallback_products())

    @patch('app.services.local_product_service.Path')
    @patch('app.services.local_product_service.json')
    def test_load_specific_encoding_succeeds_after_failures(self, mock_json, mock_path, mock_products_data, mock_transformed_products_template, mock_logger):
        """Test _load_local_products where a specific encoding succeeds after previous ones fail."""
        mock_file_path = MagicMock()
        mock_file_path.exists.return_value = True
        mock_path.return_value.__truediv__.return_value.__truediv__.return_value = mock_file_path

        # Simulate failures for first two encodings, then success for 'utf-8' (the third in the list)
        mock_open_side_effects = [
            MagicMock(spec=file, __enter__=MagicMock(side_effect=UnicodeDecodeError('utf-16-le', b'', 0, 1, 'reason'))),
            MagicMock(spec=file, __enter__=MagicMock(side_effect=json.JSONDecodeError("Invalid JSON", "", 0))),
            MagicMock(spec=file, __enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=json.dumps(mock_products_data))))), # utf-8 success
        ]
        
        with patch('builtins.open', side_effect=mock_open_side_effects):
            mock_json.loads.return_value = mock_products_data # Will be called for the successful open

            service = LocalProductService()

            # Assertions
            mock_logger.warning.assert_any_call("Failed to load with utf-16-le encoding: reason")
            mock_logger.warning.assert_any_call("Failed to load with utf-16 encoding: Invalid JSON: line 1 column 1 (char 0)") # this assumes utf-16 is the second in the list
            
            # Check for the successful load log
            mock_logger.info.assert_any_call(f"Successfully loaded {len(mock_products_data['products'])} products from JSON file using utf-8 encoding")
            assert len(service.products) == len(mock_products_data['products'])
            assert service.products[0]['id'] == 'prod1' # Check that products were indeed loaded

    @patch('app.services.local_product_service.Path')
    def test_load_general_exception_fallback(self, mock_path, mock_logger):
        """Test _load_local_products handling of general exceptions."""
        mock_file_path = MagicMock()
        mock_file_path.exists.return_value = True
        mock_path.return_value.__truediv__.return_value.__truediv__.return_value = mock_file_path
        
        # Simulate an arbitrary exception during file open
        with patch('builtins.open', side_effect=Exception("Disk full error")):
            service = LocalProductService()

            mock_logger.error.assert_called_once_with("Error loading products from JSON file: Disk full error")
            mock_logger.warning.assert_called_once_with("Using fallback products due to JSON file loading error")
            assert len(service.products) == len(service._get_fallback_products())

    @patch('app.services.local_product_service.Path')
    @patch('app.services.local_product_service.json')
    def test_load_with_bom_content(self, mock_json, mock_path, mock_products_data, mock_logger):
        """Test _load_local_products correctly handles BOM."""
        mock_file_path = MagicMock()
        mock_file_path.exists.return_value = True
        mock_path.return_value.__truediv__.return_value.__truediv__.return_value = mock_file_path
        
        # Simulate content with BOM
        bom_content = '\ufeff' + json.dumps(mock_products_data)
        mock_open_func = mock_open(read_data=bom_content)
        
        with patch('builtins.open', mock_open_func):
            mock_json.loads.return_value = mock_products_data

            service = LocalProductService()
            
            # Ensure json.loads was called with content *without* BOM
            mock_json.loads.assert_called_once_with(json.dumps(mock_products_data))
            mock_logger.info.assert_any_call(f"Successfully loaded {len(mock_products_data['products'])} products from JSON file using utf-16-le encoding")
            assert len(service.products) > 0 # Ensure products were loaded

    @patch('app.services.local_product_service.Path')
    @patch('app.services.local_product_service.json')
    def test_load_empty_json_file(self, mock_json, mock_path, mock_logger):
        """Test _load_local_products with an empty JSON file (valid JSON but empty list)."""
        mock_file_path = MagicMock()
        mock_file_path.exists.return_value = True
        mock_path.return_value.__truediv__.return_value.__truediv__.return_value = mock_file_path
        
        mock_open_func = mock_open(read_data='{"products": []}')
        with patch('builtins.open', mock_open_func):
            mock_json.loads.return_value = {"products": []}

            service = LocalProductService()
            
            assert len(service.products) == 0
            mock_logger.info.assert_any_call("Loaded 0 local products from JSON file")
            mock_logger.info.assert_any_call("Successfully loaded 0 products from JSON file using utf-16-le encoding")

    def test_get_fallback_products(self, mock_logger):
        """Test _get_fallback_products directly."""
        service = LocalProductService() # This will use the mocked _load_local_products
        fallback_products = service._get_fallback_products()
        assert len(fallback_products) > 0
        assert fallback_products[0]['id'] == "1"
        mock_logger.warning.assert_called_with("Using fallback products due to JSON file loading error")

# Test search_products and _extract_price_from_keyword
class TestLocalProductServiceSearch:

    def test_search_products_by_name(self, mock_local_product_service):
        """Test searching products by name keyword (case-insensitive)."""
        results = mock_local_product_service.search_products(keyword="alpha")
        assert len(results) == 1
        assert results[0]['id'] == "prod1"
        results = mock_local_product_service.search_products(keyword="pRODUCT alphA")
        assert len(results) == 1
        assert results[0]['id'] == "prod1"

    def test_search_products_by_description(self, mock_local_product_service):
        """Test searching products by description keyword."""
        results = mock_local_product_service.search_products(keyword="interesting")
        assert len(results) == 1
        assert results[0]['id'] == "prod2"

    def test_search_products_by_category_and_brand(self, mock_local_product_service):
        """Test searching products by category or brand keyword."""
        results = mock_local_product_service.search_products(keyword="electronics")
        assert len(results) == 3 # prod1, prod3, prod5
        assert set([p['id'] for p in results]) == {"prod1", "prod3", "prod5"}

        results = mock_local_product_service.search_products(keyword="brandx")
        assert len(results) == 2 # prod1, prod4
        assert set([p['id'] for p in results]) == {"prod1", "prod4"}

    def test_search_products_limit(self, mock_local_product_service):
        """Test search product limit functionality."""
        results = mock_local_product_service.search_products(keyword="product", limit=2)
        assert len(results) == 2
        
    def test_search_products_no_match(self, mock_local_product_service):
        """Test searching for a keyword that does not match any product."""
        results = mock_local_product_service.search_products(keyword="nonexistent")
        assert len(results) == 0

    def test_search_products_empty_keyword(self, mock_local_product_service):
        """Test searching with an empty keyword (should return limited products)."""
        results = mock_local_product_service.search_products(keyword="")
        assert len(results) == 5 # Returns all products (up to default limit 10)

    def test_extract_price_from_keyword_juta(self, mock_local_product_service):
        """Test price extraction for 'juta' pattern."""
        assert mock_local_product_service._extract_price_from_keyword("laptop 10 juta") == 10000000
        assert mock_local_product_service._extract_price_from_keyword("handphone 20juta") == 20000000

    def test_extract_price_from_keyword_ribu(self, mock_local_product_service):
        """Test price extraction for 'ribu' pattern."""
        assert mock_local_product_service._extract_price_from_keyword("buku 50 ribu") == 50000
        assert mock_local_product_service._extract_price_from_keyword("charger 75ribu") == 75000

    def test_extract_price_from_keyword_rp_prefix(self, mock_local_product_service):
        """Test price extraction for 'Rp' prefix pattern."""
        assert mock_local_product_service._extract_price_from_keyword("mouse rp 100000") == 100000
        assert mock_local_product_service._extract_price_from_keyword("headset RP 150000") == 150000

    def test_extract_price_from_keyword_rp_suffix(self, mock_local_product_service):
        """Test price extraction for 'rp' suffix pattern."""
        assert mock_local_product_service._extract_price_from_keyword("keyboard 200000 rp") == 200000

    def test_extract_price_from_keyword_k_m_shortcuts(self, mock_local_product_service):
        """Test price extraction for 'k' and 'm' shortcuts."""
        assert mock_local_product_service._extract_price_from_keyword("earphone 50k") == 50000
        assert mock_local_product_service._extract_price_from_keyword("mobil 300m") == 300000000

    def test_extract_price_from_keyword_budget_keywords(self, mock_local_product_service):
        """Test price extraction for budget-related keywords."""
        assert mock_local_product_service._extract_price_from_keyword("hp murah") == 5000000
        assert mock_local_product_service._extract_price_from_keyword("laptop budget") == 5000000
        assert mock_local_product_service._extract_price_from_keyword("tablet hemat") == 3000000
        assert mock_local_product_service._extract_price_from_keyword("kulkas terjangkau") == 4000000
        assert mock_local_product_service._extract_price_from_keyword("mesin cuci ekonomis") == 2000000

    def test_extract_price_from_keyword_no_price(self, mock_local_product_service):
        """Test price extraction when no price pattern is found."""
        assert mock_local_product_service._extract_price_from_keyword("any product") is None

    def test_search_products_with_price_filter(self, mock_local_product_service):
        """Test searching products with a price filter extracted from keyword."""
        # Product Alpha: 1jt, Product Beta: 50rb, Product Gamma: 2jt, Product Delta: 150rb, Product Epsilon: 30jt
        # Search for products up to 1 juta (1,000,000)
        results = mock_local_product_service.search_products(keyword="harga 1 juta")
        product_ids = {p['id'] for p in results}
        assert "prod1" in product_ids # 1jt
        assert "prod2" in product_ids # 50rb
        assert "prod4" in product_ids # 150rb
        assert "prod3" not in product_ids # 2jt
        assert "prod5" not in product_ids # 30jt
        assert len(product_ids) == 3

    def test_search_products_price_relevance_sorting(self, mock_local_product_service):
        """Test that budget searches prioritize lower prices."""
        # prod1: 1jt (Electronics), prod2: 50rb (Books), prod3: 2jt (Electronics), prod4: 150rb (Home Goods), prod5: 30jt (Electronics)
        # Keyword "elektronik murah"
        results = mock_local_product_service.search_products(keyword="elektronik murah")
        # Expected: Prod2 and Prod4 get high price score due to low price and general 'murah' keyword.
        # Prod1 gets high score for 'elektronik' + price factor.
        # Prod3 and Prod5 get high score for 'elektronik' but low price factor.
        # Sorting should put lower priced items higher.
        # prod2 (50k), prod4 (150k), prod1 (1M), prod3 (2M), prod5 (30M)
        assert results[0]['id'] == 'prod2' 
        assert results[1]['id'] == 'prod4'
        assert results[2]['id'] == 'prod1'
        assert len(results) == 5

    def test_search_products_error_handling(self, mock_local_product_service, mock_logger):
        """Test error handling in search_products."""
        with patch.object(mock_local_product_service, 'products', side_effect=Exception("Failed access")):
            results = mock_local_product_service.search_products(keyword="test")
            assert results == []
            mock_logger.error.assert_called_once_with("Error searching products: Failed access")

    def test_extract_price_from_keyword_error_handling(self, mock_local_product_service, mock_logger):
        """Test error handling in _extract_price_from_keyword."""
        with patch('re.search', side_effect=Exception("Regex error")):
            result = mock_local_product_service._extract_price_from_keyword("10 juta")
            assert result is None
            mock_logger.error.assert_called_once_with("Error extracting price from keyword: Regex error")


# Test other utility methods
class TestLocalProductServiceUtilities:

    def test_get_product_details_found(self, mock_local_product_service):
        """Test retrieving product details for an existing ID."""
        product = mock_local_product_service.get_product_details("prod1")
        assert product is not None
        assert product['id'] == "prod1"
        assert product['name'] == "Product Alpha"

    def test_get_product_details_not_found(self, mock_local_product_service):
        """Test retrieving product details for a non-existing ID."""
        product = mock_local_product_service.get_product_details("nonexistent_id")
        assert product is None

    def test_get_product_details_error_handling(self, mock_local_product_service, mock_logger):
        """Test error handling in get_product_details."""
        with patch.object(mock_local_product_service, 'products', side_effect=Exception("Access error")):
            result = mock_local_product_service.get_product_details("prod1")
            assert result is None
            mock_logger.error.assert_called_once_with("Error getting product details: Access error")

    def test_get_categories(self, mock_local_product_service):
        """Test retrieving unique and sorted product categories."""
        categories = mock_local_product_service.get_categories()
        assert categories == sorted(['Electronics', 'Books', 'Home Goods']) # Based on mock_products_data

    def test_get_categories_empty_products(self):
        """Test get_categories with no products loaded."""
        with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
            service = LocalProductService()
            categories = service.get_categories()
            assert categories == []

    def test_get_brands(self, mock_local_product_service):
        """Test retrieving unique and sorted product brands."""
        brands = mock_local_product_service.get_brands()
        assert brands == sorted(['BrandX', 'BrandY', 'BrandZ', 'BrandA'])

    def test_get_brands_empty_products(self):
        """Test get_brands with no products loaded."""
        with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
            service = LocalProductService()
            brands = service.get_brands()
            assert brands == []

    def test_get_products_by_category_found(self, mock_local_product_service):
        """Test retrieving products by category (case-insensitive)."""
        products = mock_local_product_service.get_products_by_category("electronics")
        assert len(products) == 3
        assert set([p['id'] for p in products]) == {"prod1", "prod3", "prod5"}
        
        products = mock_local_product_service.get_products_by_category("ELECTRONICS")
        assert len(products) == 3
        assert set([p['id'] for p in products]) == {"prod1", "prod3", "prod5"}

    def test_get_products_by_category_not_found(self, mock_local_product_service):
        """Test retrieving products for a non-existing category."""
        products = mock_local_product_service.get_products_by_category("Sport")
        assert len(products) == 0

    def test_get_products_by_category_error_handling(self, mock_local_product_service, mock_logger):
        """Test error handling in get_products_by_category."""
        with patch.object(mock_local_product_service, 'products', side_effect=Exception("List error")):
            results = mock_local_product_service.get_products_by_category("Electronics")
            assert results == []
            mock_logger.error.assert_called_once_with("Error getting products by category: List error")

    def test_get_products_by_brand_found(self, mock_local_product_service):
        """Test retrieving products by brand (case-insensitive)."""
        products = mock_local_product_service.get_products_by_brand("brandx")
        assert len(products) == 2
        assert set([p['id'] for p in products]) == {"prod1", "prod4"}

        products = mock_local_product_service.get_products_by_brand("BRANDX")
        assert len(products) == 2
        assert set([p['id'] for p in products]) == {"prod1", "prod4"}

    def test_get_products_by_brand_not_found(self, mock_local_product_service):
        """Test retrieving products for a non-existing brand."""
        products = mock_local_product_service.get_products_by_brand("Dell")
        assert len(products) == 0

    def test_get_products_by_brand_error_handling(self, mock_local_product_service, mock_logger):
        """Test error handling in get_products_by_brand."""
        with patch.object(mock_local_product_service, 'products', side_effect=Exception("List error")):
            results = mock_local_product_service.get_products_by_brand("BrandX")
            assert results == []
            mock_logger.error.assert_called_once_with("Error getting products by brand: List error")

    def test_get_top_rated_products(self, mock_local_product_service):
        """Test retrieving top-rated products with limit."""
        # prod5: 5.0, prod3: 4.9, prod1: 4.5, prod4: 4.0, prod2: 3.8
        top_products = mock_local_product_service.get_top_rated_products(limit=3)
        assert len(top_products) == 3
        assert [p['id'] for p in top_products] == ["prod5", "prod3", "prod1"]

    def test_get_top_rated_products_less_than_limit(self, mock_local_product_service):
        """Test retrieving top-rated products when fewer products than limit exist."""
        # Simulate only 2 products available
        mock_local_product_service.products = mock_local_product_service.products[:2]
        top_products = mock_local_product_service.get_top_rated_products(limit=5)
        assert len(top_products) == 2
        assert [p['id'] for p in top_products] == ["prod1", "prod2"] # 4.5 then 3.8

    def test_get_top_rated_products_empty(self):
        """Test get_top_rated_products with no products."""
        with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
            service = LocalProductService()
            top_products = service.get_top_rated_products()
            assert top_products == []

    def test_get_top_rated_products_error_handling(self, mock_local_product_service, mock_logger):
        """Test error handling in get_top_rated_products."""
        with patch.object(mock_local_product_service, 'products', side_effect=Exception("Sort error")):
            results = mock_local_product_service.get_top_rated_products()
            assert results == []
            mock_logger.error.assert_called_once_with("Error getting top rated products: Sort error")

    def test_get_best_selling_products(self, mock_local_product_service):
        """Test retrieving best-selling products with limit."""
        # All products initially have 'sold' count mocked to 500 by setup_random_randint_mock
        # We need to manually set different sold counts for testing sorting.
        mock_local_product_service.products[0]['specifications']['sold'] = 1000 # prod1
        mock_local_product_service.products[1]['specifications']['sold'] = 200 # prod2
        mock_local_product_service.products[2]['specifications']['sold'] = 1500 # prod3
        mock_local_product_service.products[3]['specifications']['sold'] = 500 # prod4
        mock_local_product_service.products[4]['specifications']['sold'] = 2000 # prod5

        best_sellers = mock_local_product_service.get_best_selling_products(limit=3)
        assert len(best_sellers) == 3
        assert [p['id'] for p in best_sellers] == ["prod5", "prod3", "prod1"]

    def test_get_best_selling_products_less_than_limit(self, mock_local_product_service):
        """Test retrieving best-selling products when fewer products than limit exist."""
        mock_local_product_service.products = mock_local_product_service.products[:2]
        mock_local_product_service.products[0]['specifications']['sold'] = 1000
        mock_local_product_service.products[1]['specifications']['sold'] = 200
        best_sellers = mock_local_product_service.get_best_selling_products(limit=5)
        assert len(best_sellers) == 2
        assert [p['id'] for p in best_sellers] == ["prod1", "prod2"]

    def test_get_best_selling_products_empty(self):
        """Test get_best_selling_products with no products."""
        with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
            service = LocalProductService()
            best_sellers = service.get_best_selling_products()
            assert best_sellers == []

    def test_get_best_selling_products_error_handling(self, mock_local_product_service, mock_logger):
        """Test error handling in get_best_selling_products."""
        with patch.object(mock_local_product_service, 'products', side_effect=Exception("Sort error")):
            results = mock_local_product_service.get_best_selling_products()
            assert results == []
            mock_logger.error.assert_called_once_with("Error getting best selling products: Sort error")

    def test_get_products(self, mock_local_product_service):
        """Test retrieving all products with default limit."""
        all_products = mock_local_product_service.get_products()
        assert len(all_products) == 5 # Default limit 10, but only 5 products in fixture
        assert all_products[0]['id'] == "prod1"

    def test_get_products_with_custom_limit(self, mock_local_product_service):
        """Test retrieving products with a custom limit."""
        products_limited = mock_local_product_service.get_products(limit=2)
        assert len(products_limited) == 2
        assert [p['id'] for p in products_limited] == ["prod1", "prod2"]

    def test_get_products_empty(self):
        """Test get_products with no products."""
        with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
            service = LocalProductService()
            products = service.get_products()
            assert products == []

    def test_get_products_error_handling(self, mock_local_product_service, mock_logger):
        """Test error handling in get_products."""
        with patch.object(mock_local_product_service, 'products', side_effect=Exception("List error")):
            results = mock_local_product_service.get_products()
            assert results == []
            mock_logger.error.assert_called_once_with("Error getting products: List error")


# Test smart_search_products
class TestSmartSearchProducts:
    
    # Fixture for products with different ratings and sold counts for smart_search tests
    @pytest.fixture
    def smart_search_products(self):
        return [
            # High rating, high price, high sold
            {"id": "s1", "name": "Smart Phone X", "category": "Electronics", "brand": "TechCo", "price": 10000000,
             "description": "Top-tier smartphone.", "specifications": {"rating": 4.9, "sold": 2000}},
            # Medium rating, medium price, medium sold
            {"id": "s2", "name": "Basic Laptop Z", "category": "Laptops", "brand": "CompCorp", "price": 7000000,
             "description": "Everyday laptop.", "specifications": {"rating": 4.2, "sold": 800}},
            # Low rating, low price, low sold
            {"id": "s3", "name": "Cheap Earbuds", "category": "Audio", "brand": "SoundInc", "price": 500000,
             "description": "Affordable audio.", "specifications": {"rating": 3.5, "sold": 300}},
            # High rating, low price (good value), medium sold
            {"id": "s4", "name": "Value Tablet", "category": "Tablets", "brand": "PadPro", "price": 2500000,
             "description": "Great budget tablet.", "specifications": {"rating": 4.7, "sold": 1200}},
            # Specific product for exact matches
            {"id": "s5", "name": "Gaming PC Elite", "category": "Computers", "brand": "GameMakers", "price": 25000000,
             "description": "High performance gaming.", "specifications": {"rating": 4.8, "sold": 1500}},
            # Another electronics product for category testing
            {"id": "s6", "name": "Smartwatch Pro", "category": "Electronics", "brand": "WatchCo", "price": 3000000,
             "description": "Feature-rich smartwatch.", "specifications": {"rating": 4.6, "sold": 900}},
            # Product with 'Terbaik' in name for edge case testing
            {"id": "s7", "name": "TV Terbaik 2024", "category": "Electronics", "brand": "ViewMaster", "price": 15000000,
             "description": "Best TV of the year.", "specifications": {"rating": 4.9, "sold": 1800}},
        ]

    @pytest.fixture
    def mock_smart_search_service(self, smart_search_products):
        with patch('app.services.local_product_service.LocalProductService._load_local_products',
                   return_value=smart_search_products):
            service = LocalProductService()
            yield service

    def test_smart_search_best_request_no_category(self, mock_smart_search_service):
        """Test smart_search with 'terbaik' keyword, no specific category."""
        # Should return top 5 by rating, general message
        # s1 (4.9), s7 (4.9), s5 (4.8), s4 (4.7), s6 (4.6), s2 (4.2), s3 (3.5)
        # Top 5: s1, s7 (tie), s5, s4, s6
        products, message = mock_smart_search_service.smart_search_products(keyword="produk terbaik", limit=5)
        assert message == "Berikut produk terbaik berdasarkan rating:"
        assert len(products) == 5
        assert {p['id'] for p in products} == {"s1", "s7", "s5", "s4", "s6"}
        assert products[0]['id'] == 's1' # s1 and s7 have same rating, s1 comes first in original list
        assert products[1]['id'] == 's7'

    def test_smart_search_best_request_with_category_found(self, mock_smart_search_service):
        """Test smart_search with 'terbaik' keyword and specific category where products exist."""
        # Electronics: s1 (4.9), s6 (4.6), s7 (4.9)
        # Should be s1/s7 (tied), then s6
        products, message = mock_smart_search_service.smart_search_products(keyword="terbaik", category="Electronics", limit=5)
        assert message == "Berikut Electronics terbaik berdasarkan rating:"
        assert len(products) == 3
        assert {p['id'] for p in products} == {"s1", "s6", "s7"}
        assert products[0]['id'] == 's1' # s1 and s7 have same rating, s1 comes first in original list
        assert products[1]['id'] == 's7'

    def test_smart_search_best_request_with_category_not_found_fallback_general(self, mock_smart_search_service):
        """Test smart_search with 'terbaik' keyword and specific category not found, falls back to general best."""
        products, message = mock_smart_search_service.smart_search_products(keyword="terbaik", category="Furniture", limit=5)
        assert message == "Tidak ada produk kategori Furniture, berikut produk terbaik secara umum:"
        assert len(products) == 5
        # Should be general top 5 by rating: s1, s7, s5, s4, s6
        assert {p['id'] for p in products} == {"s1", "s7", "s5", "s4", "s6"}

    def test_smart_search_all_criteria_met(self, mock_smart_search_service):
        """Test smart_search with keyword, category, and max_price all matching."""
        # s1: 10M, Elec, Smart Phone X
        # s6: 3M, Elec, Smartwatch Pro
        products, message = mock_smart_search_service.smart_search_products(
            keyword="smart", category="Electronics", max_price=5000000, limit=5
        )
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."
        assert len(products) == 1
        assert products[0]['id'] == "s6" # Smartwatch Pro is < 5M and in Electronics and has "Smart"

    def test_smart_search_fallback_category_only(self, mock_smart_search_service):
        """Test smart_search: exact criteria no match, fallback to category only (sorted by price)."""
        # Keyword "nonexistent" ensures exact match fails.
        # Category "Electronics": s1 (10M), s6 (3M), s7 (15M)
        # Should return all electronics, sorted by price.
        products, message = mock_smart_search_service.smart_search_products(
            keyword="nonexistent", category="Electronics", max_price=1000000, limit=5
        )
        assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."
        assert len(products) == 3
        assert [p['id'] for p in products] == ["s6", "s1", "s7"] # Sorted by price: 3M, 10M, 15M

    def test_smart_search_fallback_max_price_only(self, mock_smart_search_service):
        """Test smart_search: exact/category no match, fallback to max_price only."""
        # Keyword "nonexistent" and category "NonExistentCat" ensures prior fallbacks fail.
        # Max price 3M: s3 (500k), s4 (2.5M), s6 (3M)
        products, message = mock_smart_search_service.smart_search_products(
            keyword="nonexistent", category="NonExistentCat", max_price=3000000, limit=5
        )
        assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."
        assert len(products) == 3
        # Order is not specified by price here, it's just filtered. Should be original order of filtered products
        assert {p['id'] for p in products} == {"s3", "s4", "s6"}
        
    def test_smart_search_fallback_popular_products(self, mock_smart_search_service):
        """Test smart_search: all previous fallbacks fail, fall back to best-selling."""
        # Keyword "nonexistent", category "NonExistentCat", max_price 100 ensures everything fails.
        # Sorted by sold: s1 (2000), s7 (1800), s5 (1500), s4 (1200), s6 (900), s2 (800), s3 (300)
        products, message = mock_smart_search_service.smart_search_products(
            keyword="nonexistent", category="NonExistentCat", max_price=100, limit=5
        )
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
        assert len(products) == 5
        assert [p['id'] for p in products] == ["s1", "s7", "s5", "s4", "s6"]

    def test_smart_search_empty_input_defaults_to_popular(self, mock_smart_search_service):
        """Test smart_search with no input, should return popular products as final fallback."""
        products, message = mock_smart_search_service.smart_search_products(limit=5)
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
        # Sorted by sold: s1 (2000), s7 (1800), s5 (1500), s4 (1200), s6 (900)
        assert [p['id'] for p in products] == ["s1", "s7", "s5", "s4", "s6"]

    def test_smart_search_keyword_only_match(self, mock_smart_search_service):
        """Test smart_search with keyword only, matching products."""
        products, message = mock_smart_search_service.smart_search_products(keyword="laptop", limit=5)
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."
        assert len(products) == 1
        assert products[0]['id'] == "s2"

    def test_smart_search_keyword_and_category_match(self, mock_smart_search_service):
        """Test smart_search with keyword and category, matching products."""
        products, message = mock_smart_search_service.smart_search_products(keyword="smart", category="Electronics", limit=5)
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."
        assert len(products) == 2
        # s1: "Smart Phone X", category Electronics
        # s6: "Smartwatch Pro", category Electronics
        # Order is based on how they appear in the original products list when all criteria match
        assert {p['id'] for p in products} == {"s1", "s6"}

    def test_smart_search_max_price_only_match(self, mock_smart_search_service):
        """Test smart_search with max_price only, matching products."""
        products, message = mock_smart_search_service.smart_search_products(max_price=2000000, limit=5)
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."
        assert len(products) == 2
        # s3: 500k, s4: 2.5M
        assert {p['id'] for p in products} == {"s3", "s4"}

    def test_smart_search_limit_application(self, mock_smart_search_service):
        """Test that the limit parameter is respected in smart_search."""
        products, message = mock_smart_search_service.smart_search_products(keyword="product", limit=1)
        assert len(products) == 1
        assert products[0]['id'] == 's1' # "Smart Phone X" - "product" is in description "Top-tier smartphone."
        
        products, message = mock_smart_search_service.smart_search_products(category="Electronics", limit=1)
        assert len(products) == 1
        assert products[0]['id'] == 's1' # This is from the "best request" path or the generic search, should be 's1' (highest rated electronics)

    def test_smart_search_empty_products_list(self):
        """Test smart_search when the service has no products loaded."""
        with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
            service = LocalProductService()
            products, message = service.smart_search_products(keyword="test")
            assert products == []
            assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." # Still returns this message, but with empty list