import pytest
import logging
import json
import random
from unittest.mock import mock_open, patch, MagicMock
from pathlib import Path

# Adjust import path based on the file's location
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.services.local_product_service import LocalProductService

# Configure logging for tests
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@pytest.fixture
def mock_products_data():
    """Fixture for standard valid product data JSON content."""
    return {
        "products": [
            {
                "id": "test-1",
                "name": "Test Product A",
                "category": "Electronics",
                "brand": "BrandX",
                "price": 1000000,
                "currency": "IDR",
                "description": "Description for product A.",
                "specifications": {
                    "rating": 4.5,
                    "stock_count": 50,
                    "color": "Black"
                },
                "availability": "in_stock",
                "reviews_count": 10
            },
            {
                "id": "test-2",
                "name": "Test Product B",
                "category": "Home Goods",
                "brand": "BrandY",
                "price": 500000,
                "currency": "IDR",
                "description": "Description for product B.",
                "specifications": {
                    "rating": 3.8,
                    "stock_count": 20,
                    "material": "Wood"
                },
                "availability": "out_of_stock",
                "reviews_count": 5
            },
            {
                "id": "test-3",
                "name": "Another Product",
                "category": "Electronics",
                "brand": "BrandZ",
                "price": 1500000,
                "currency": "IDR",
                "description": "High-end electronic device.",
                "specifications": {
                    "rating": 4.9,
                    "stock_count": 10
                },
                "availability": "pre_order",
                "reviews_count": 25
            },
            {
                "id": "test-4",
                "name": "Laptop Murah",
                "category": "Computers",
                "brand": "BudgetTech",
                "price": 3000000,
                "currency": "IDR",
                "description": "An affordable laptop.",
                "specifications": {
                    "rating": 4.2,
                    "stock_count": 30
                },
                "availability": "in_stock",
                "reviews_count": 8
            }
        ]
    }

@pytest.fixture
def mock_transformed_products(mocker):
    """Fixture for mock products that would result from successful loading and transformation."""
    # Mock random.randint to ensure predictable 'sold' values
    mocker.patch('random.randint', return_value=1000)
    
    return [
        {
            "id": "test-1",
            "name": "Test Product A",
            "category": "Electronics",
            "brand": "BrandX",
            "price": 1000000,
            "currency": "IDR",
            "description": "Description for product A.",
            "specifications": {
                "rating": 4.5,
                "sold": 1000, # Mocked
                "stock": 50, # Transformed from stock_count
                "condition": "Baru",
                "shop_location": "Indonesia",
                "shop_name": "BrandX Store", # Transformed from brand
                "color": "Black"
            },
            "availability": "in_stock",
            "reviews_count": 10,
            "images": ["https://example.com/test-1.jpg"], # Generated
            "url": "https://shopee.co.id/test-1" # Generated
        },
        {
            "id": "test-2",
            "name": "Test Product B",
            "category": "Home Goods",
            "brand": "BrandY",
            "price": 500000,
            "currency": "IDR",
            "description": "Description for product B.",
            "specifications": {
                "rating": 3.8,
                "sold": 1000, # Mocked
                "stock": 20, # Transformed from stock_count
                "condition": "Baru",
                "shop_location": "Indonesia",
                "shop_name": "BrandY Store", # Transformed from brand
                "material": "Wood"
            },
            "availability": "out_of_stock",
            "reviews_count": 5,
            "images": ["https://example.com/test-2.jpg"], # Generated
            "url": "https://shopee.co.id/test-2" # Generated
        },
        {
            "id": "test-3",
            "name": "Another Product",
            "category": "Electronics",
            "brand": "BrandZ",
            "price": 1500000,
            "currency": "IDR",
            "description": "High-end electronic device.",
            "specifications": {
                "rating": 4.9,
                "sold": 1000, # Mocked
                "stock": 10, # Transformed from stock_count
                "condition": "Baru",
                "shop_location": "Indonesia",
                "shop_name": "BrandZ Store" # Transformed from brand
            },
            "availability": "pre_order",
            "reviews_count": 25,
            "images": ["https://example.com/test-3.jpg"], # Generated
            "url": "https://shopee.co.id/test-3" # Generated
        },
        {
            "id": "test-4",
            "name": "Laptop Murah",
            "category": "Computers",
            "brand": "BudgetTech",
            "price": 3000000,
            "currency": "IDR",
            "description": "An affordable laptop.",
            "specifications": {
                "rating": 4.2,
                "sold": 1000, # Mocked
                "stock": 30, # Transformed from stock_count
                "condition": "Baru",
                "shop_location": "Indonesia",
                "shop_name": "BudgetTech Store" # Transformed from brand
            },
            "availability": "in_stock",
            "reviews_count": 8,
            "images": ["https://example.com/test-4.jpg"], # Generated
            "url": "https://shopee.co.id/test-4" # Generated
        }
    ]


@pytest.fixture
def mock_path_exists(mocker):
    """Mocks Path.exists() to return True by default for tests."""
    mock_exists = mocker.patch('pathlib.Path.exists', return_value=True)
    return mock_exists

@pytest.fixture
def mock_open_success(mocker, mock_products_data):
    """Mocks builtins.open to simulate successful file read."""
    mocker.patch('random.randint', return_value=1000) # Ensure consistent 'sold' values
    return mocker.patch('builtins.open', mock_open(read_data=json.dumps(mock_products_data)))

@pytest.fixture
def mock_open_file_not_found(mocker):
    """Mocks builtins.open to simulate FileNotFoundError."""
    mocker.patch('pathlib.Path.exists', return_value=False)
    return mocker.patch('builtins.open', side_effect=FileNotFoundError)

@pytest.fixture
def mock_open_json_decode_error(mocker):
    """Mocks builtins.open to simulate JSONDecodeError."""
    # Simulate content that causes JSONDecodeError for all encodings
    mock_files = [
        mock_open(read_data='{"products": [invalid json]').return_value,
        mock_open(read_data='{"products": [invalid json]').return_value,
        mock_open(read_data='{"products": [invalid json]').return_value,
        mock_open(read_data='{"products": [invalid json]').return_value,
        mock_open(read_data='{"products": [invalid json]').return_value,
        mock_open(read_data='{"products": [invalid json]').return_value,
    ]
    
    def mock_open_side_effect(*args, **kwargs):
        # Return a mock file object that will raise JSONDecodeError when read and json.loads is called
        m = MagicMock()
        m.read.side_effect = json.JSONDecodeError("Expecting value", "", 0)
        return m

    # Patch open to provide a mock file object that, when read, returns malformed JSON
    mocker.patch('builtins.open', side_effect=mock_open_side_effect)
    # Patch json.loads to ensure it fails on any content
    mocker.patch('json.loads', side_effect=json.JSONDecodeError("Expecting value", "", 0))
    return mocker.patch('pathlib.Path.exists', return_value=True) # File exists, but content is bad


@pytest.fixture
def mock_open_unicode_decode_error(mocker):
    """Mocks builtins.open to simulate UnicodeDecodeError."""
    # Simulate content that causes UnicodeDecodeError for all encodings
    def mock_read_side_effect(*args, **kwargs):
        encoding = kwargs.get('encoding')
        if encoding in ['utf-8', 'utf-8-sig']:
            raise UnicodeDecodeError('utf-8', b'\xfe', 0, 1, 'invalid start byte')
        elif encoding in ['utf-16', 'utf-16-le']:
            raise UnicodeDecodeError('utf-16', b'\xfe', 0, 1, 'invalid start byte')
        else: # for latin-1, cp1252, just return something that won't decode as JSON
            return b'\x00\x00\x00\x00'.decode('latin-1') # Raw bytes that are valid for latin-1 but not json
    
    mock_file_obj = mock_open().return_value
    mock_file_obj.read.side_effect = mock_read_side_effect
    
    mocker.patch('builtins.open', return_value=mock_file_obj)
    mocker.patch('json.loads', side_effect=json.JSONDecodeError("Expecting value", "", 0))
    return mocker.patch('pathlib.Path.exists', return_value=True) # File exists, but content is bad


@pytest.fixture
def mock_local_product_service(mocker, mock_transformed_products):
    """
    Fixture to create a LocalProductService instance with pre-loaded products,
    bypassing the actual file loading for most tests.
    """
    mocker.patch.object(LocalProductService, '_load_local_products', return_value=mock_transformed_products)
    service = LocalProductService()
    return service

class TestLocalProductServiceInitialization:

    def test_init_success(self, mock_path_exists, mock_open_success, mock_transformed_products, caplog):
        """Test successful initialization and product loading."""
        caplog.set_level(logging.INFO)
        service = LocalProductService()
        
        assert service.products == mock_transformed_products
        mock_open_success.assert_called_once()
        mock_path_exists.assert_called_once()
        
        assert f"Loaded {len(mock_transformed_products)} local products from JSON file" in caplog.text
        assert f"Successfully loaded {len(mock_transformed_products)} products from JSON file using utf-16-le encoding" in caplog.text # First successful encoding used
    
    def test_init_file_not_found(self, mock_open_file_not_found, caplog):
        """Test initialization when products.json is not found."""
        caplog.set_level(logging.ERROR)
        service = LocalProductService()
        
        assert service.products == service._get_fallback_products()
        assert "Products JSON file not found at:" in caplog.text
        assert "Using fallback products due to JSON file loading error" in caplog.text
    
    def test_init_json_decode_error(self, mock_open_json_decode_error, caplog):
        """Test initialization when JSON is malformed."""
        caplog.set_level(logging.WARNING)
        service = LocalProductService()
        
        assert service.products == service._get_fallback_products()
        assert "Failed to load with utf-16-le encoding: Expecting value" in caplog.text # First attempt logs warning
        assert "All encoding attempts failed, using fallback products" in caplog.text # All attempts fail, then error
        assert "Using fallback products due to JSON file loading error" in caplog.text
    
    def test_init_unicode_decode_error(self, mock_open_unicode_decode_error, caplog):
        """Test initialization when file has unicode decode errors."""
        caplog.set_level(logging.WARNING)
        service = LocalProductService()
        
        assert service.products == service._get_fallback_products()
        assert "Failed to load with utf-16-le encoding: invalid start byte" in caplog.text
        assert "Failed to load with utf-16 encoding: invalid start byte" in caplog.text
        assert "Failed to load with utf-8 encoding: invalid start byte" in caplog.text
        assert "All encoding attempts failed, using fallback products" in caplog.text
        assert "Using fallback products due to JSON file loading error" in caplog.text

    def test_init_general_exception_in_load_local_products(self, mocker, caplog):
        """Test initialization when an unexpected exception occurs during loading."""
        caplog.set_level(logging.ERROR)
        mocker.patch('pathlib.Path.exists', side_effect=Exception("Disk error"))
        
        service = LocalProductService()
        
        assert service.products == service._get_fallback_products()
        assert "Error loading products from JSON file: Disk error" in caplog.text
        assert "Using fallback products due to JSON file loading error" in caplog.text

    def test_load_local_products_with_bom(self, mocker, caplog):
        """Test _load_local_products handles BOM correctly."""
        caplog.set_level(logging.INFO)
        
        bom_content = '\ufeff' + json.dumps({"products": [{"id": "bom-test", "name": "BOM Product"}]})
        
        mock_open_func = mock_open(read_data=bom_content)
        mocker.patch('builtins.open', mock_open_func)
        mocker.patch('pathlib.Path.exists', return_value=True)
        mocker.patch('random.randint', return_value=1000)
        
        service = LocalProductService()
        products = service._load_local_products()
        
        assert len(products) == 1
        assert products[0]['id'] == 'bom-test'
        assert "Successfully loaded 1 products from JSON file using utf-16-le encoding" in caplog.text # utf-16-le is first in list

    def test_load_local_products_missing_products_key(self, mocker, caplog):
        """Test _load_local_products handles JSON without 'products' key."""
        caplog.set_level(logging.INFO)
        mock_data = {"other_key": [{"id": "no-prod-key", "name": "No Products Key"}]}
        
        mock_open_func = mock_open(read_data=json.dumps(mock_data))
        mocker.patch('builtins.open', mock_open_func)
        mocker.patch('pathlib.Path.exists', return_value=True)
        mocker.patch('random.randint', return_value=1000)

        service = LocalProductService()
        products = service._load_local_products()
        
        assert products == [] # Should return empty list if 'products' key is missing
        assert "Successfully loaded 0 products from JSON file using utf-16-le encoding" in caplog.text

    def test_load_local_products_empty_products_list(self, mocker, caplog):
        """Test _load_local_products handles empty 'products' list."""
        caplog.set_level(logging.INFO)
        mock_data = {"products": []}
        
        mock_open_func = mock_open(read_data=json.dumps(mock_data))
        mocker.patch('builtins.open', mock_open_func)
        mocker.patch('pathlib.Path.exists', return_value=True)
        mocker.patch('random.randint', return_value=1000)

        service = LocalProductService()
        products = service._load_local_products()
        
        assert products == []
        assert "Successfully loaded 0 products from JSON file using utf-16-le encoding" in caplog.text

    def test_load_local_products_product_transformation_defaults(self, mocker, caplog):
        """Test product transformation logic, especially default values."""
        caplog.set_level(logging.INFO)
        
        # Product with minimum required fields to test defaults
        minimal_product_data = {
            "products": [
                {
                    "id": "min-prod",
                    "name": "Minimal Product"
                    # All other fields are missing
                }
            ]
        }
        
        mock_open_func = mock_open(read_data=json.dumps(minimal_product_data))
        mocker.patch('builtins.open', mock_open_func)
        mocker.patch('pathlib.Path.exists', return_value=True)
        mocker.patch('random.randint', return_value=500) # Mock random sold count
        
        service = LocalProductService()
        products = service._load_local_products()
        
        assert len(products) == 1
        product = products[0]
        
        assert product['id'] == 'min-prod'
        assert product['name'] == 'Minimal Product'
        assert product['category'] == ''
        assert product['brand'] == ''
        assert product['price'] == 0
        assert product['currency'] == 'IDR'
        assert product['description'] == ''
        assert product['availability'] == 'in_stock'
        assert product['reviews_count'] == 0
        assert product['images'] == ["https://example.com/min-prod.jpg"]
        assert product['url'] == "https://shopee.co.id/min-prod"
        
        assert product['specifications']['rating'] == 0
        assert product['specifications']['sold'] == 500
        assert product['specifications']['stock'] == 0
        assert product['specifications']['condition'] == 'Baru'
        assert product['specifications']['shop_location'] == 'Indonesia'
        assert product['specifications']['shop_name'] == 'Unknown Store' # No brand, so 'Unknown Store'

class TestLocalProductServiceFallback:

    def test_get_fallback_products(self, caplog):
        """Test _get_fallback_products returns expected data and logs warning."""
        caplog.set_level(logging.WARNING)
        service = LocalProductService()
        # Mock _load_local_products to prevent actual file ops during __init__
        # and test _get_fallback_products in isolation
        service.products = [] 
        
        fallback_products = service._get_fallback_products()
        
        assert len(fallback_products) > 0 # Check if it returns products
        assert "iPhone 15 Pro Max" in [p['name'] for p in fallback_products]
        assert "Using fallback products due to JSON file loading error" in caplog.text

class TestLocalProductServiceSearch:

    def test_search_products_by_keyword_name(self, mock_local_product_service):
        """Test searching products by name keyword."""
        service = mock_local_product_service
        results = service.search_products("Test Product A")
        assert len(results) == 1
        assert results[0]['id'] == 'test-1'
    
    def test_search_products_by_keyword_description(self, mock_local_product_service):
        """Test searching products by description keyword."""
        service = mock_local_product_service
        results = service.search_products("Description for product B")
        assert len(results) == 1
        assert results[0]['id'] == 'test-2'

    def test_search_products_by_keyword_category(self, mock_local_product_service):
        """Test searching products by category keyword."""
        service = mock_local_product_service
        results = service.search_products("Home Goods")
        assert len(results) == 1
        assert results[0]['id'] == 'test-2'

    def test_search_products_by_keyword_brand(self, mock_local_product_service):
        """Test searching products by brand keyword."""
        service = mock_local_product_service
        results = service.search_products("BrandZ")
        assert len(results) == 1
        assert results[0]['id'] == 'test-3'

    def test_search_products_case_insensitivity(self, mock_local_product_service):
        """Test search is case-insensitive."""
        service = mock_local_product_service
        results = service.search_products("test product a")
        assert len(results) == 1
        assert results[0]['id'] == 'test-1'

    def test_search_products_no_match(self, mock_local_product_service):
        """Test searching with a keyword that yields no matches."""
        service = mock_local_product_service
        results = service.search_products("NonExistentProduct")
        assert len(results) == 0

    def test_search_products_limit(self, mock_local_product_service):
        """Test search results are limited correctly."""
        service = mock_local_product_service
        results = service.search_products("Product", limit=2) # "Product" matches 3 items
        assert len(results) == 2
        # Order is based on relevance score, so check if top 2 are returned
        assert results[0]['id'] in ['test-1', 'test-3'] # Both have "Product" in name and higher rating
        assert results[1]['id'] in ['test-1', 'test-3'] # Order between these two might vary slightly based on other factors

    def test_search_products_empty_keyword(self, mock_local_product_service):
        """Test searching with an empty keyword returns all products up to limit."""
        service = mock_local_product_service
        results = service.search_products("", limit=2)
        assert len(results) == 2
        assert set(p['id'] for p in results).issubset(set(p['id'] for p in service.products))

    def test_search_products_with_price_keyword(self, mock_local_product_service):
        """Test search products using a keyword that includes a max price."""
        service = mock_local_product_service
        # test-2 is 500k, test-1 is 1M, test-3 is 1.5M, test-4 is 3M
        results = service.search_products("Product A 1 juta") # Should match Test Product A, but also test-2 due to price
        
        # The price filter will include products below or equal to 1 juta.
        # Relevance score will then sort them.
        # test-1 (1M) matches 'Product A', '1 juta' price criteria.
        # test-2 (500k) matches 'Product' and '1 juta' price criteria.
        # test-3 (1.5M) matches 'Product' but not '1 juta' price criteria.
        
        assert len(results) == 2
        assert results[0]['id'] == 'test-1' # Exact match for name
        assert results[1]['id'] == 'test-2' # Matches price criteria and 'Product'
        assert results[0]['price'] <= 1000000
        assert results[1]['price'] <= 1000000

    def test_search_products_with_budget_keyword(self, mock_local_product_service):
        """Test search products using a budget keyword like 'murah'."""
        service = mock_local_product_service
        # Fallback products have iPhone (25M), Samsung (22M), MacBook (35M), etc.
        # Mocked products: Test Product A (1M), Test Product B (0.5M), Test Product C (1.5M), Laptop Murah (3M)
        
        # When keyword is 'laptop murah', it should find Laptop Murah (3M).
        # The budget keyword 'murah' (5M) also applies, so it should score lower prices higher.
        results = service.search_products("laptop murah")
        assert len(results) >= 1
        assert results[0]['id'] == 'test-4' # Exact match for "Laptop Murah"

        results = service.search_products("product murah")
        # should return test-2 (500k) first, then test-1 (1M)
        assert len(results) == 2
        assert results[0]['id'] == 'test-2' # 500k, higher score due to price
        assert results[1]['id'] == 'test-1' # 1M

    def test_search_products_error_handling(self, mock_local_product_service, mocker, caplog):
        """Test error handling in search_products."""
        caplog.set_level(logging.ERROR)
        mocker.patch.object(mock_local_product_service, '_extract_price_from_keyword', side_effect=Exception("Price extraction failed"))
        
        results = mock_local_product_service.search_products("any keyword")
        assert results == []
        assert "Error searching products: Price extraction failed" in caplog.text

class TestLocalProductServiceExtractPrice:

    @pytest.mark.parametrize("keyword, expected_price", [
        ("iphone 1 juta", 1000000),
        ("tv 200 ribu", 200000),
        ("Rp 50000", 50000),
        ("50000 Rp", 50000),
        ("mouse 100k", 100000),
        ("laptop 1m", 1000000),
        ("hp murah", 5000000),
        ("keyboard budget", 5000000),
        ("speaker hemat", 3000000),
        ("monitor terjangkau", 4000000),
        ("earphone ekonomis", 2000000),
        ("not a price", None),
        ("1juta", 1000000), # Test without space
        ("100ribu", 100000), # Test without space
        ("Rp12345", 12345), # Test without space
        ("12345Rp", 12345), # Test without space
    ])
    def test_extract_price_from_keyword_success(self, mock_local_product_service, keyword, expected_price):
        """Test successful price extraction from various keyword patterns."""
        service = mock_local_product_service
        price = service._extract_price_from_keyword(keyword)
        assert price == expected_price
    
    def test_extract_price_from_keyword_error_handling(self, mock_local_product_service, mocker, caplog):
        """Test error handling in _extract_price_from_keyword."""
        caplog.set_level(logging.ERROR)
        # Simulate a regex error or type conversion error for a specific pattern
        mocker.patch('re.search', side_effect=Exception("Regex error"))
        
        price = mock_local_product_service._extract_price_from_keyword("1 juta")
        assert price is None
        assert "Error extracting price from keyword: Regex error" in caplog.text

class TestLocalProductServiceProductDetails:

    def test_get_product_details_found(self, mock_local_product_service):
        """Test getting product details for an existing ID."""
        service = mock_local_product_service
        product = service.get_product_details("test-1")
        assert product is not None
        assert product['id'] == 'test-1'
        assert product['name'] == 'Test Product A'

    def test_get_product_details_not_found(self, mock_local_product_service):
        """Test getting product details for a non-existent ID."""
        service = mock_local_product_service
        product = service.get_product_details("non-existent-id")
        assert product is None

    def test_get_product_details_error_handling(self, mock_local_product_service, mocker, caplog):
        """Test error handling in get_product_details."""
        caplog.set_level(logging.ERROR)
        # Simulate an error within the loop
        mocker.patch.object(mock_local_product_service.products, '__iter__', side_effect=Exception("Iteration error"))
        
        product = mock_local_product_service.get_product_details("test-1")
        assert product is None
        assert "Error getting product details: Iteration error" in caplog.text

class TestLocalProductServiceCategoriesAndBrands:

    def test_get_categories(self, mock_local_product_service):
        """Test getting unique sorted product categories."""
        service = mock_local_product_service
        categories = service.get_categories()
        assert sorted(['Electronics', 'Home Goods', 'Computers']) == sorted(categories)
        assert len(categories) == 3

    def test_get_categories_no_products(self, mocker):
        """Test getting categories when there are no products."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        categories = service.get_categories()
        assert categories == []

    def test_get_categories_missing_category_field(self, mocker):
        """Test getting categories when some products lack 'category' field."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[
            {"id": "1", "name": "Prod 1", "category": "A"},
            {"id": "2", "name": "Prod 2"}, # Missing category
            {"id": "3", "name": "Prod 3", "category": "B"}
        ])
        service = LocalProductService()
        categories = service.get_categories()
        assert sorted(['', 'A', 'B']) == sorted(categories) # Empty string for missing category

    def test_get_brands(self, mock_local_product_service):
        """Test getting unique sorted product brands."""
        service = mock_local_product_service
        brands = service.get_brands()
        assert sorted(['BrandX', 'BrandY', 'BrandZ', 'BudgetTech']) == sorted(brands)
        assert len(brands) == 4

    def test_get_brands_no_products(self, mocker):
        """Test getting brands when there are no products."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        brands = service.get_brands()
        assert brands == []

    def test_get_brands_missing_brand_field(self, mocker):
        """Test getting brands when some products lack 'brand' field."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[
            {"id": "1", "name": "Prod 1", "brand": "A"},
            {"id": "2", "name": "Prod 2"}, # Missing brand
            {"id": "3", "name": "Prod 3", "brand": "B"}
        ])
        service = LocalProductService()
        brands = service.get_brands()
        assert sorted(['', 'A', 'B']) == sorted(brands) # Empty string for missing brand

class TestLocalProductServiceFiltering:

    def test_get_products_by_category(self, mock_local_product_service):
        """Test getting products filtered by category."""
        service = mock_local_product_service
        electronics_products = service.get_products_by_category("Electronics")
        assert len(electronics_products) == 2
        assert {p['id'] for p in electronics_products} == {'test-1', 'test-3'}

    def test_get_products_by_category_case_insensitivity(self, mock_local_product_service):
        """Test category filtering is case-insensitive."""
        service = mock_local_product_service
        electronics_products = service.get_products_by_category("electronics")
        assert len(electronics_products) == 2
        assert {p['id'] for p in electronics_products} == {'test-1', 'test-3'}

    def test_get_products_by_category_no_match(self, mock_local_product_service):
        """Test getting products for a non-existent category."""
        service = mock_local_product_service
        results = service.get_products_by_category("NonExistentCategory")
        assert results == []

    def test_get_products_by_category_error_handling(self, mock_local_product_service, mocker, caplog):
        """Test error handling in get_products_by_category."""
        caplog.set_level(logging.ERROR)
        mocker.patch.object(mock_local_product_service.products, '__iter__', side_effect=Exception("Iteration error"))
        
        results = mock_local_product_service.get_products_by_category("Electronics")
        assert results == []
        assert "Error getting products by category: Iteration error" in caplog.text

    def test_get_products_by_brand(self, mock_local_product_service):
        """Test getting products filtered by brand."""
        service = mock_local_product_service
        brandx_products = service.get_products_by_brand("BrandX")
        assert len(brandx_products) == 1
        assert brandx_products[0]['id'] == 'test-1'

    def test_get_products_by_brand_case_insensitivity(self, mock_local_product_service):
        """Test brand filtering is case-insensitive."""
        service = mock_local_product_service
        brandx_products = service.get_products_by_brand("brandx")
        assert len(brandx_products) == 1
        assert brandx_products[0]['id'] == 'test-1'

    def test_get_products_by_brand_no_match(self, mock_local_product_service):
        """Test getting products for a non-existent brand."""
        service = mock_local_product_service
        results = service.get_products_by_brand("NonExistentBrand")
        assert results == []

    def test_get_products_by_brand_error_handling(self, mock_local_product_service, mocker, caplog):
        """Test error handling in get_products_by_brand."""
        caplog.set_level(logging.ERROR)
        mocker.patch.object(mock_local_product_service.products, '__iter__', side_effect=Exception("Iteration error"))
        
        results = mock_local_product_service.get_products_by_brand("BrandX")
        assert results == []
        assert "Error getting products by brand: Iteration error" in caplog.text

class TestLocalProductServiceSorting:

    def test_get_top_rated_products(self, mock_local_product_service):
        """Test getting top-rated products with default limit."""
        service = mock_local_product_service
        # Products ratings: test-1 (4.5), test-2 (3.8), test-3 (4.9), test-4 (4.2)
        top_products = service.get_top_rated_products()
        assert len(top_products) == 4 # All products, as default limit is 5 and we have 4
        assert top_products[0]['id'] == 'test-3' # Rating 4.9
        assert top_products[1]['id'] == 'test-1' # Rating 4.5

    def test_get_top_rated_products_with_limit(self, mock_local_product_service):
        """Test getting top-rated products with a specific limit."""
        service = mock_local_product_service
        top_products = service.get_top_rated_products(limit=2)
        assert len(top_products) == 2
        assert top_products[0]['id'] == 'test-3'
        assert top_products[1]['id'] == 'test-1'
    
    def test_get_top_rated_products_missing_rating(self, mocker):
        """Test get_top_rated_products handles products missing rating."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[
            {"id": "A", "name": "Prod A", "specifications": {"rating": 3.0}},
            {"id": "B", "name": "Prod B", "specifications": {}}, # Missing rating
            {"id": "C", "name": "Prod C"}, # Missing specifications
            {"id": "D", "name": "Prod D", "specifications": {"rating": 5.0}}
        ])
        service = LocalProductService()
        top_products = service.get_top_rated_products()
        assert len(top_products) == 4
        assert top_products[0]['id'] == 'D'
        assert top_products[1]['id'] == 'A'
        # Products B and C should come last, as their rating defaults to 0
        assert {top_products[2]['id'], top_products[3]['id']} == {'B', 'C'}

    def test_get_top_rated_products_empty(self, mocker):
        """Test get_top_rated_products with no products."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        top_products = service.get_top_rated_products()
        assert top_products == []

    def test_get_top_rated_products_error_handling(self, mock_local_product_service, mocker, caplog):
        """Test error handling in get_top_rated_products."""
        caplog.set_level(logging.ERROR)
        mocker.patch.object(mock_local_product_service, 'products', side_effect=Exception("Products access error"))
        
        results = mock_local_product_service.get_top_rated_products()
        assert results == []
        assert "Error getting top rated products: Products access error" in caplog.text

    def test_get_best_selling_products(self, mock_local_product_service, mocker):
        """Test getting best-selling products."""
        # Mock 'sold' counts for predictable sorting
        mocker.patch('random.randint', side_effect=[1200, 800, 1500, 100]) # test-1, test-2, test-3, test-4
        
        # Reload service to use new mock for sold counts
        service = LocalProductService() 
        service.products = [
            {"id": "test-1", "name": "Prod A", "specifications": {"sold": 1200}},
            {"id": "test-2", "name": "Prod B", "specifications": {"sold": 800}},
            {"id": "test-3", "name": "Prod C", "specifications": {"sold": 1500}},
            {"id": "test-4", "name": "Prod D", "specifications": {"sold": 100}},
        ]

        best_selling = service.get_best_selling_products()
        assert len(best_selling) == 4
        assert best_selling[0]['id'] == 'test-3' # 1500 sold
        assert best_selling[1]['id'] == 'test-1' # 1200 sold

    def test_get_best_selling_products_with_limit(self, mock_local_product_service, mocker):
        """Test getting best-selling products with a specific limit."""
        mocker.patch('random.randint', side_effect=[1200, 800, 1500, 100])
        service = LocalProductService() 
        service.products = [
            {"id": "test-1", "name": "Prod A", "specifications": {"sold": 1200}},
            {"id": "test-2", "name": "Prod B", "specifications": {"sold": 800}},
            {"id": "test-3", "name": "Prod C", "specifications": {"sold": 1500}},
            {"id": "test-4", "name": "Prod D", "specifications": {"sold": 100}},
        ]
        
        best_selling = service.get_best_selling_products(limit=2)
        assert len(best_selling) == 2
        assert best_selling[0]['id'] == 'test-3'
        assert best_selling[1]['id'] == 'test-1'

    def test_get_best_selling_products_missing_sold(self, mocker):
        """Test get_best_selling_products handles products missing sold count."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[
            {"id": "A", "name": "Prod A", "specifications": {"sold": 100}},
            {"id": "B", "name": "Prod B", "specifications": {}}, # Missing sold
            {"id": "C", "name": "Prod C"}, # Missing specifications
            {"id": "D", "name": "Prod D", "specifications": {"sold": 500}}
        ])
        service = LocalProductService()
        best_selling = service.get_best_selling_products()
        assert len(best_selling) == 4
        assert best_selling[0]['id'] == 'D'
        assert best_selling[1]['id'] == 'A'
        # Products B and C should come last, as their sold count defaults to 0
        assert {best_selling[2]['id'], best_selling[3]['id']} == {'B', 'C'}

    def test_get_best_selling_products_empty(self, mocker):
        """Test get_best_selling_products with no products."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        best_selling = service.get_best_selling_products()
        assert best_selling == []

    def test_get_best_selling_products_error_handling(self, mock_local_product_service, mocker, caplog):
        """Test error handling in get_best_selling_products."""
        caplog.set_level(logging.ERROR)
        mocker.patch.object(mock_local_product_service, 'products', side_effect=Exception("Products access error"))
        
        results = mock_local_product_service.get_best_selling_products()
        assert results == []
        assert "Error getting best selling products: Products access error" in caplog.text

    def test_get_products(self, mock_local_product_service):
        """Test getting all products with default limit."""
        service = mock_local_product_service
        all_products = service.get_products()
        assert len(all_products) == 4
        assert all(p in service.products for p in all_products)

    def test_get_products_with_limit(self, mock_local_product_service):
        """Test getting all products with a specific limit."""
        service = mock_local_product_service
        limited_products = service.get_products(limit=2)
        assert len(limited_products) == 2
        assert limited_products[0] == service.products[0]
        assert limited_products[1] == service.products[1]

    def test_get_products_empty(self, mocker):
        """Test get_products with no products."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        all_products = service.get_products()
        assert all_products == []
    
    def test_get_products_error_handling(self, mock_local_product_service, mocker, caplog):
        """Test error handling in get_products."""
        caplog.set_level(logging.ERROR)
        mocker.patch.object(mock_local_product_service, 'products', side_effect=Exception("Products access error"))
        
        results = mock_local_product_service.get_products()
        assert results == []
        assert "Error getting products: Products access error" in caplog.text


class TestLocalProductServiceSmartSearch:

    @pytest.fixture(autouse=True)
    def setup_smart_search_products(self, mocker, mock_local_product_service):
        """Setup mock products for smart search tests with varied ratings and sold counts."""
        mocker.patch('random.randint', return_value=1000) # Reset random.randint mock
        # Custom products for smart search to test sorting logic more clearly
        mock_products = [
            {
                "id": "s1", "name": "Best Smartphone", "category": "Smartphone", "brand": "TechCo",
                "price": 10000000, "specifications": {"rating": 4.9, "sold": 2000},
            },
            {
                "id": "s2", "name": "Budget Smartphone", "category": "Smartphone", "brand": "CheapCo",
                "price": 3000000, "specifications": {"rating": 4.2, "sold": 500},
            },
            {
                "id": "l1", "name": "Premium Laptop", "category": "Laptop", "brand": "ProBook",
                "price": 25000000, "specifications": {"rating": 4.8, "sold": 1500},
            },
            {
                "id": "l2", "name": "Cheap Laptop", "category": "Laptop", "brand": "StudentPC",
                "price": 7000000, "specifications": {"rating": 3.5, "sold": 300},
            },
            {
                "id": "t1", "name": "Top Tablet", "category": "Tablet", "brand": "PadPro",
                "price": 12000000, "specifications": {"rating": 4.7, "sold": 1000},
            },
             {
                "id": "t2", "name": "Entry Tablet", "category": "Tablet", "brand": "TabGo",
                "price": 4000000, "specifications": {"rating": 4.0, "sold": 600},
            },
        ]
        mock_local_product_service.products = mock_products
        return mock_local_product_service

    def test_smart_search_best_no_category(self, setup_smart_search_products):
        """Test smart search for "best" products without a specific category."""
        service = setup_smart_search_products
        results, message = service.smart_search_products(keyword="produk terbaik", limit=2)
        assert message == "Berikut produk terbaik berdasarkan rating:"
        assert len(results) == 2
        # s1 (4.9), l1 (4.8), t1 (4.7)
        assert results[0]['id'] == 's1'
        assert results[1]['id'] == 'l1'

    def test_smart_search_best_with_category_found(self, setup_smart_search_products):
        """Test smart search for "best" products within a specific category (found)."""
        service = setup_smart_search_products
        results, message = service.smart_search_products(keyword="smartphone terbaik", category="Smartphone", limit=2)
        assert message == "Berikut Smartphone terbaik berdasarkan rating:"
        assert len(results) == 2
        # s1 (4.9), s2 (4.2)
        assert results[0]['id'] == 's1'
        assert results[1]['id'] == 's2'

    def test_smart_search_best_with_category_not_found_fallback(self, setup_smart_search_products):
        """Test smart search for "best" products in non-existent category, falling back to general best."""
        service = setup_smart_search_products
        results, message = service.smart_search_products(keyword="sepatu terbaik", category="Shoes", limit=2)
        assert message == "Tidak ada produk kategori Shoes, berikut produk terbaik secara umum:"
        assert len(results) == 2
        assert results[0]['id'] == 's1'
        assert results[1]['id'] == 'l1'

    def test_smart_search_all_criteria_met(self, setup_smart_search_products):
        """Test smart search when keyword, category, and max_price all match."""
        service = setup_smart_search_products
        results, message = service.smart_search_products(keyword="smartphone", category="Smartphone", max_price=5000000, limit=1)
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."
        assert len(results) == 1
        assert results[0]['id'] == 's2' # Budget Smartphone (3M)

    def test_smart_search_fallback_to_category_only(self, setup_smart_search_products):
        """Test smart search fallback to category-only when keyword/price don't match."""
        service = setup_smart_search_products
        results, message = service.smart_search_products(keyword="gaming", category="Laptop", max_price=5000000, limit=1)
        # Keyword "gaming" doesn't match, max_price 5M excludes l1 (25M) and l2 (7M).
        # Fallback to category "Laptop" without price filter.
        assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."
        assert len(results) == 1
        assert results[0]['id'] == 'l2' # Cheap Laptop (7M) is cheapest in Laptop category

    def test_smart_search_fallback_to_budget_only(self, setup_smart_search_products):
        """Test smart search fallback to budget-only when category/keyword don't match."""
        service = setup_smart_search_products
        results, message = service.smart_search_products(keyword="nonexistent", category="NonCat", max_price=5000000, limit=1)
        # Keyword and category don't match. Fallback to products within 5M budget.
        assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."
        assert len(results) == 1
        assert results[0]['id'] == 's2' # Budget Smartphone (3M) is cheapest within 5M (from s2, t2)

    def test_smart_search_fallback_to_popular(self, setup_smart_search_products):
        """Test smart search fallback to popular products when no criteria match."""
        service = setup_smart_search_products
        results, message = service.smart_search_products(keyword="ultra rare", category="Collectibles", max_price=100, limit=2)
        # No matches at all. Fallback to best selling.
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
        assert len(results) == 2
        # s1 (2000 sold), l1 (1500 sold)
        assert results[0]['id'] == 's1'
        assert results[1]['id'] == 'l1'
    
    def test_smart_search_empty_input(self, setup_smart_search_products):
        """Test smart search with empty keyword, category, and max_price."""
        service = setup_smart_search_products
        results, message = service.smart_search_products(keyword="", category=None, max_price=None, limit=2)
        # Should fallback to popular products as no specific criteria given
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
        assert len(results) == 2
        assert results[0]['id'] == 's1'
        assert results[1]['id'] == 'l1'

    def test_smart_search_only_keyword(self, setup_smart_search_products):
        """Test smart search with only a keyword (no category/price filters)."""
        service = setup_smart_search_products
        results, message = service.smart_search_products(keyword="laptop", limit=2)
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."
        assert len(results) == 2
        # Should return 'l1' and 'l2'
        assert {p['id'] for p in results} == {'l1', 'l2'}
    
    def test_smart_search_only_category(self, setup_smart_search_products):
        """Test smart search with only a category (no keyword/price filters)."""
        service = setup_smart_search_products
        results, message = service.smart_search_products(category="Tablet", limit=2)
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."
        assert len(results) == 2
        # Should return 't1' and 't2'
        assert {p['id'] for p in results} == {'t1', 't2'}

    def test_smart_search_only_max_price(self, setup_smart_search_products):
        """Test smart search with only max_price (no keyword/category filters)."""
        service = setup_smart_search_products
        results, message = service.smart_search_products(max_price=8000000, limit=2)
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."
        assert len(results) == 2
        # s2 (3M), l2 (7M), t2 (4M)
        # Should return the cheapest ones that match the price
        assert {p['id'] for p in results} == {'s2', 't2'} # sorted by price if no keyword score

    def test_smart_search_limit_less_than_available(self, setup_smart_search_products):
        """Test smart search where limit is less than available matching products."""
        service = setup_smart_search_products
        results, message = service.smart_search_products(keyword="smartphone", limit=1)
        assert len(results) == 1
        assert results[0]['id'] == 's1' # Best Smartphone
    
    def test_smart_search_limit_more_than_available(self, setup_smart_search_products):
        """Test smart search where limit is more than available matching products."""
        service = setup_smart_search_products
        results, message = service.smart_search_products(keyword="smartphone", limit=10)
        assert len(results) == 2
        assert results[0]['id'] == 's1'
        assert results[1]['id'] == 's2'

    def test_smart_search_with_product_missing_fields(self, mocker):
        """Test smart_search_products handles products with missing fields gracefully."""
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[
            {"id": "p1", "name": "Product Alpha", "category": "CategoryA"},
            {"id": "p2", "name": "Product Beta", "specifications": {"rating": 4.0}},
            {"id": "p3", "price": 1000000, "brand": "BrandC"},
            {"id": "p4", "name": "Test Product", "category": "TestCategory", "price": 500000, "specifications": {"rating": 4.5, "sold": 100}}
        ])
        service = LocalProductService()

        # Test best search with missing ratings
        results_best, msg_best = service.smart_search_products(keyword="terbaik", limit=1)
        assert results_best[0]['id'] == 'p4' # p4 has a rating, p2 has one but lower, others default to 0
        
        # Test category search with missing category
        results_cat, msg_cat = service.smart_search_products(category="CategoryA")
        assert len(results_cat) == 1
        assert results_cat[0]['id'] == 'p1'

        # Test price search with missing price
        results_price, msg_price = service.smart_search_products(max_price=700000)
        assert len(results_price) == 1
        assert results_price[0]['id'] == 'p4'

        # Test general search
        results_general, msg_general = service.smart_search_products(keyword="product")
        assert len(results_general) == 2
        assert {p['id'] for p in results_general} == {'p1', 'p4'}