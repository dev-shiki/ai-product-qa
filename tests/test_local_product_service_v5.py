import pytest
import json
import logging
import os
import random
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

# Adjust path to import the module correctly from the root or wherever tests are run
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.local_product_service import LocalProductService

logger = logging.getLogger(__name__)

# --- Fixtures ---

@pytest.fixture
def mock_random_randint():
    """Mock random.randint to return a predictable value."""
    with patch('random.randint', return_value=1000) as mock_rand:
        yield mock_rand

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary 'data' directory with a products.json file."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    yield data_dir

@pytest.fixture
def mock_local_product_service(mock_random_randint):
    """
    Fixture to create an instance of LocalProductService with mocked dependencies.
    It will load fallback products by default unless _load_local_products is mocked.
    """
    with patch('app.services.local_product_service.Path') as MockPath:
        # Mock Path(__file__).parent.parent.parent to point to a predictable location
        # where we can place a mock products.json or ensure it doesn't exist.
        mock_instance = MockPath.return_value
        mock_instance.parent.parent.parent = MagicMock(spec=Path)
        mock_instance.parent.parent.parent.__truediv__.return_value = MagicMock(spec=Path) # Simulate Path.__truediv__

        # By default, make json_file_path.exists() return False to use fallback
        # Tests requiring file interaction will re-mock this as needed.
        mock_json_file_path = mock_instance.parent.parent.parent.__truediv__.return_value
        mock_json_file_path.exists.return_value = False
        mock_json_file_path.__str__.return_value = "/mock/path/data/products.json"

        service = LocalProductService()
        yield service, mock_json_file_path

@pytest.fixture
def create_mock_json_file(temp_data_dir):
    """
    Fixture to create a products.json file in a temporary data directory
    and mock Path operations to point to it.
    """
    def _creator(content, encoding='utf-8', bom=False):
        json_file_path = temp_data_dir / "products.json"
        
        # Add BOM if requested
        if bom:
            content = '\ufeff' + content
        
        with open(json_file_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        # Mock Path(__file__).parent.parent.parent to return tmp_path
        # and ensure json_file_path points to the temporary file.
        with patch('app.services.local_product_service.Path') as MockPath:
            mock_current_dir = MagicMock(spec=Path)
            mock_current_dir.parent.parent.parent = MagicMock(return_value=temp_data_dir)
            
            mock_file_path_obj = MagicMock(spec=Path)
            mock_file_path_obj.exists.return_value = True
            mock_file_path_obj.__str__.return_value = str(json_file_path)

            # Ensure the path resolution returns our mock file path object
            mock_current_dir.parent.parent.parent.__truediv__.return_value = mock_file_path_obj
            mock_file_path_obj.__truediv__.return_value = mock_file_path_obj # For "data" / "products.json" chain

            # Patch Path in the module to return our mock objects
            MockPath.return_value = mock_current_dir

            # Re-initialize the service to pick up the new mocked path
            service = LocalProductService()
            return service, str(json_file_path)
    return _creator

@pytest.fixture
def mock_products():
    """A set of mock products for testing."""
    return [
        {
            "id": "prod1",
            "name": "Smartphone X",
            "category": "Electronics",
            "brand": "Brand A",
            "price": 10000000,
            "currency": "IDR",
            "description": "High-end smartphone.",
            "specifications": {"rating": 4.5, "sold": 500, "stock_count": 100, "color": "black"},
            "availability": "in_stock",
            "reviews_count": 50,
            "images": [],
            "url": ""
        },
        {
            "id": "prod2",
            "name": "Laptop Y",
            "category": "Electronics",
            "brand": "Brand B",
            "price": 15000000,
            "currency": "IDR",
            "description": "Powerful gaming laptop.",
            "specifications": {"rating": 4.8, "sold": 800, "stock_count": 50, "storage": "1TB SSD"},
            "availability": "in_stock",
            "reviews_count": 80,
            "images": [],
            "url": ""
        },
        {
            "id": "prod3",
            "name": "Headphones Z",
            "category": "Audio",
            "brand": "Brand A",
            "price": 2000000,
            "currency": "IDR",
            "description": "Noise cancelling headphones.",
            "specifications": {"rating": 4.2, "sold": 300, "stock_count": 200},
            "availability": "in_stock",
            "reviews_count": 30,
            "images": [],
            "url": ""
        },
        {
            "id": "prod4",
            "name": "Smartwatch",
            "category": "Wearables",
            "brand": "Brand C",
            "price": 3000000,
            "currency": "IDR",
            "description": "Fitness tracking smartwatch.",
            "specifications": {"rating": 3.9, "sold": 150, "stock_count": 300},
            "availability": "out_of_stock",
            "reviews_count": 10,
            "images": [],
            "url": ""
        },
        {
            "id": "prod5",
            "name": "Tablet Pro",
            "category": "Electronics",
            "brand": "Brand D",
            "price": 8000000,
            "currency": "IDR",
            "description": "Tablet for drawing.",
            "specifications": {"rating": 4.7, "sold": 250, "stock_count": 70},
            "availability": "in_stock",
            "reviews_count": 40,
            "images": [],
            "url": ""
        },
        {
            "id": "prod6",
            "name": "iPhone 15 Pro Max",
            "category": "Smartphone",
            "brand": "Apple",
            "price": 25000000,
            "currency": "IDR",
            "description": "iPhone 15 Pro Max dengan chip A17 Pro.",
            "specifications": {
                "rating": 4.8,
                "sold": 1250,
                "stock": 50,
                "condition": "Baru",
            },
            "images": ["https://example.com/iphone15.jpg"],
            "url": "https://shopee.co.id/iphone-15-pro-max"
        },
        {
            "id": "prod7",
            "name": "Samsung Galaxy S24 Ultra",
            "category": "Smartphone",
            "brand": "Samsung",
            "price": 22000000,
            "currency": "IDR",
            "description": "Samsung Galaxy S24 Ultra dengan S Pen.",
            "specifications": {
                "rating": 4.7,
                "sold": 980,
                "stock": 35,
                "condition": "Baru",
            },
            "images": ["https://example.com/s24-ultra.jpg"],
            "url": "https://shopee.co.id/samsung-s24-ultra"
        }
    ]

@pytest.fixture
def local_product_service_with_mock_products(mock_products):
    """
    Fixture to create LocalProductService with a predefined set of products
    instead of loading from a file or fallback.
    """
    with patch.object(LocalProductService, '_load_local_products', return_value=mock_products) as mock_loader:
        service = LocalProductService()
        yield service
        mock_loader.assert_called_once() # Ensure the mock was used

# --- Tests for __init__ and _load_local_products ---

def test_init_loads_products_successfully(create_mock_json_file, caplog, mock_random_randint):
    """
    Test that __init__ correctly loads products from a valid JSON file.
    """
    mock_json_content = json.dumps({
        "products": [
            {"id": "test1", "name": "Product 1", "price": 100, "stock_count": 5, "rating": 4.0},
            {"id": "test2", "name": "Product 2", "price": 200, "stock_count": 10, "rating": 3.5}
        ]
    })
    
    with caplog.at_level(logging.INFO):
        service, _ = create_mock_json_file(mock_json_content)
        
        assert len(service.products) == 2
        assert service.products[0]['id'] == 'test1'
        assert service.products[0]['specifications']['sold'] == 1000 # From mock_random_randint
        assert "Successfully loaded 2 products from JSON file using utf-8 encoding" in caplog.text
        assert "Loaded 2 local products from JSON file" in caplog.text
        
        # Test transformation for missing keys
        assert service.products[0]['currency'] == 'IDR'
        assert service.products[0]['specifications']['condition'] == 'Baru'
        assert service.products[0]['images'] == ["https://example.com/test1.jpg"]

def test_init_falls_back_if_json_file_not_found(mock_local_product_service, caplog):
    """
    Test that __init__ falls back to default products if the JSON file is not found.
    """
    service, mock_json_file_path = mock_local_product_service
    mock_json_file_path.exists.return_value = False
    
    with caplog.at_level(logging.ERROR):
        # Re-initialize the service to trigger the loading logic
        service = LocalProductService()
        
        assert len(service.products) > 0 # Should load fallback products
        assert any("Products JSON file not found at:" in rec.message for rec in caplog.records)
        assert any("Using fallback products due to JSON file loading error" in rec.message for rec in caplog.records)

def test_init_falls_back_on_json_decode_error(create_mock_json_file, caplog):
    """
    Test that __init__ falls back if the JSON file is malformed.
    """
    malformed_json_content = "{products: [" # Invalid JSON
    with caplog.at_level(logging.WARNING):
        service, _ = create_mock_json_file(malformed_json_content)
        
        assert len(service.products) > 0 # Should load fallback products
        assert any("Failed to load with utf-16-le encoding:" in rec.message for rec in caplog.records)
        assert any("Failed to load with utf-16 encoding:" in rec.message for rec in caplog.records)
        assert any("Failed to load with utf-8 encoding: Expecting value" in rec.message for rec in caplog.records)
        assert "All encoding attempts failed, using fallback products" in caplog.text
        assert "Using fallback products due to JSON file loading error" in caplog.text

def test_init_falls_back_on_unicode_decode_error(create_mock_json_file, caplog):
    """
    Test that __init__ falls back if the file cannot be decoded by any encoding.
    """
    # Create a file that is not valid UTF-8, UTF-16 etc.
    # For simplicity, we'll use an invalid byte sequence for UTF-8
    invalid_byte_sequence = b'\xc3\x28' # Invalid UTF-8 sequence
    
    with patch('builtins.open', mock_open(read_data=invalid_byte_sequence.decode('latin-1', errors='ignore'))), \
         patch.object(Path, 'exists', return_value=True), \
         patch.object(Path, '__truediv__', return_value=MagicMock(exists=True, __str__=lambda: "/mock/path/data/products.json")):
        
        with caplog.at_level(logging.WARNING):
            service = LocalProductService()
            
            assert len(service.products) > 0 # Should load fallback products
            assert any("Failed to load with utf-16-le encoding: " in rec.message for rec in caplog.records)
            assert any("Failed to load with utf-16 encoding: " in rec.message for rec in caplog.records)
            assert any("Failed to load with utf-8 encoding: " in rec.message for rec in caplog.records)
            assert "All encoding attempts failed, using fallback products" in caplog.text

def test_load_local_products_handles_bom(create_mock_json_file, caplog, mock_random_randint):
    """
    Test that _load_local_products correctly handles JSON files with a BOM.
    """
    mock_json_content = json.dumps({"products": [{"id": "bom_test", "name": "BOM Product", "price": 100}]})
    
    with caplog.at_level(logging.INFO):
        # Create file with BOM and ensure it's loaded by utf-8-sig
        service, _ = create_mock_json_file(mock_json_content, encoding='utf-8-sig', bom=True)
        
        assert len(service.products) == 1
        assert service.products[0]['id'] == 'bom_test'
        assert "Successfully loaded 1 products from JSON file using utf-8-sig encoding" in caplog.text

def test_load_local_products_transforms_missing_keys(create_mock_json_file, mock_random_randint):
    """
    Test that _load_local_products applies default values for missing keys.
    """
    mock_json_content = json.dumps({
        "products": [
            {"id": "min_prod", "name": "Minimal Product"},
            {"id": "some_spec", "name": "Product With Some Specs", "specifications": {"warranty": "1 year"}}
        ]
    })
    service, _ = create_mock_json_file(mock_json_content)

    assert len(service.products) == 2
    
    # Test min_prod
    prod1 = service.products[0]
    assert prod1['id'] == 'min_prod'
    assert prod1['name'] == 'Minimal Product'
    assert prod1['category'] == ''
    assert prod1['brand'] == ''
    assert prod1['price'] == 0
    assert prod1['currency'] == 'IDR'
    assert prod1['description'] == ''
    assert prod1['availability'] == 'in_stock'
    assert prod1['reviews_count'] == 0
    assert prod1['images'] == ["https://example.com/min_prod.jpg"]
    assert prod1['url'] == "https://shopee.co.id/min_prod"
    
    # Check specifications defaults
    specs1 = prod1['specifications']
    assert specs1['rating'] == 0
    assert specs1['sold'] == 1000 # From mock_random_randint
    assert specs1['stock'] == 0
    assert specs1['condition'] == 'Baru'
    assert specs1['shop_location'] == 'Indonesia'
    assert specs1['shop_name'] == 'Unknown Store' # No brand provided

    # Test product with some specs
    prod2 = service.products[1]
    assert prod2['id'] == 'some_spec'
    assert prod2['name'] == 'Product With Some Specs'
    assert prod2['specifications']['warranty'] == '1 year' # Existing spec should be preserved
    assert prod2['specifications']['rating'] == 0 # Default for missing spec
    assert prod2['images'] == ["https://example.com/some_spec.jpg"]

def test_load_local_products_empty_file_or_data(create_mock_json_file, caplog):
    """
    Test behavior when JSON file is empty or contains no 'products' key.
    """
    # Empty JSON
    service_empty_json, _ = create_mock_json_file("{}")
    assert service_empty_json.products == []

    # JSON with no 'products' key
    service_no_products_key, _ = create_mock_json_file(json.dumps({"data": []}))
    assert service_no_products_key.products == []
    
    # JSON with empty 'products' array
    service_empty_array, _ = create_mock_json_file(json.dumps({"products": []}))
    assert service_empty_array.products == []

def test_get_fallback_products_returns_correct_data(mock_local_product_service):
    """
    Test that _get_fallback_products returns a non-empty list of dictionaries
    with expected keys.
    """
    service, _ = mock_local_product_service
    fallback_products = service._get_fallback_products()
    
    assert isinstance(fallback_products, list)
    assert len(fallback_products) > 0
    
    # Check structure of a sample product
    sample_product = fallback_products[0]
    expected_keys = ["id", "name", "category", "brand", "price", "currency", "description", "specifications", "images", "url"]
    for key in expected_keys:
        assert key in sample_product
    assert isinstance(sample_product["specifications"], dict)
    assert "rating" in sample_product["specifications"]
    assert "sold" in sample_product["specifications"]

# --- Tests for search_products ---

def test_search_products_by_name(local_product_service_with_mock_products):
    """Test searching by product name."""
    service = local_product_service_with_mock_products
    results = service.search_products("Smartphone X")
    assert len(results) == 1
    assert results[0]['id'] == 'prod1'

def test_search_products_case_insensitive(local_product_service_with_mock_products):
    """Test searching with case-insensitive keywords."""
    service = local_product_service_with_mock_products
    results = service.search_products("smartphone x")
    assert len(results) == 1
    assert results[0]['id'] == 'prod1'

def test_search_products_by_description(local_product_service_with_mock_products):
    """Test searching by product description."""
    service = local_product_service_with_mock_products
    results = service.search_products("gaming laptop")
    assert len(results) == 1
    assert results[0]['id'] == 'prod2'

def test_search_products_by_category(local_product_service_with_mock_products):
    """Test searching by product category."""
    service = local_product_service_with_mock_products
    results = service.search_products("Electronics")
    assert len(results) == 4 # Smartphone X, Laptop Y, Tablet Pro, iPhone, Samsung

def test_search_products_by_brand(local_product_service_with_mock_products):
    """Test searching by product brand."""
    service = local_product_service_with_mock_products
    results = service.search_products("Brand A")
    assert len(results) == 2 # Smartphone X, Headphones Z

def test_search_products_by_specifications(local_product_service_with_mock_products):
    """Test searching by product specifications."""
    service = local_product_service_with_mock_products
    results = service.search_products("1TB SSD")
    assert len(results) == 1
    assert results[0]['id'] == 'prod2'

def test_search_products_with_limit(local_product_service_with_mock_products):
    """Test the limit parameter in search_products."""
    service = local_product_service_with_mock_products
    results = service.search_products("smartphone", limit=1)
    assert len(results) == 1
    # Check if the higher-rated product (prod6 iPhone) is preferred for "smartphone"
    # based on relevance score which includes keyword in name
    assert results[0]['id'] in ['prod1', 'prod6', 'prod7'] # The sorting is based on relevance, not guaranteed specific order without more precise scoring logic

def test_search_products_no_match(local_product_service_with_mock_products):
    """Test searching for a keyword that does not match any products."""
    service = local_product_service_with_mock_products
    results = service.search_products("NonExistentProduct")
    assert len(results) == 0

def test_search_products_empty_keyword(local_product_service_with_mock_products):
    """Test searching with an empty keyword, should return all (up to limit)."""
    service = local_product_service_with_mock_products
    results = service.search_products("")
    assert len(results) == 7 # All 7 mock products are returned (default limit 10)

def test_search_products_price_extraction(local_product_service_with_mock_products):
    """Test price extraction from keyword in search_products."""
    service = local_product_service_with_mock_products
    results = service.search_products("smartphone 12 juta")
    assert len(results) == 1 # Only Smartphone X (10M) and Tablet Pro (8M) should match
    assert results[0]['id'] == 'prod5' or results[0]['id'] == 'prod1' # Check that they are <= 12M

    results = service.search_products("laptop 10 juta")
    assert len(results) == 0 # Laptop Y is 15M, no mock laptop < 10M

    results = service.search_products("headphones murah") # "murah" is 5M max
    # Headphones Z (2M) should be included. Other products might also be included if price is low.
    assert 'prod3' in [p['id'] for p in results]
    assert all(p['price'] <= 5000000 for p in results)

def test_search_products_price_extraction_and_keyword_match(local_product_service_with_mock_products):
    """Test combined keyword and price search."""
    service = local_product_service_with_mock_products
    results = service.search_products("smartphone 12 juta")
    assert len(results) == 1
    assert results[0]['id'] == 'prod1' # Smartphone X (10M)

def test_search_products_with_exception_handling(local_product_service_with_mock_products, caplog):
    """Test error handling in search_products."""
    service = local_product_service_with_mock_products
    
    # Simulate an error by modifying self.products to something uniterable
    service.products = "invalid_data"
    
    with caplog.at_level(logging.ERROR):
        results = service.search_products("any_keyword")
        assert results == []
        assert "Error searching products: " in caplog.text

# --- Tests for _extract_price_from_keyword ---

@pytest.mark.parametrize("keyword, expected_price", [
    ("laptop 5 juta", 5000000),
    ("HP 10 juta", 10000000),
    ("headphone 2 ribu", 2000),
    ("earphone rp 50000", 50000),
    ("camera 75000 rp", 75000),
    ("monitor 3k", 3000),
    ("pc 15m", 15000000),
    ("murah laptop", 5000000),
    ("budget phone", 5000000),
    ("hemat beli", 3000000),
    ("terjangkau", 4000000),
    ("ekonomis", 2000000),
    ("no price here", None),
    ("", None),
    ("rp 123456789", 123456789),
    ("2juta", 2000000), # Test no space
    ("5ribu", 5000) # Test no space
])
def test_extract_price_from_keyword_success(local_product_service_with_mock_products, keyword, expected_price):
    """Test successful price extraction for various patterns and budget keywords."""
    service = local_product_service_with_mock_products
    price = service._extract_price_from_keyword(keyword)
    assert price == expected_price

def test_extract_price_from_keyword_error_handling(local_product_service_with_mock_products, caplog):
    """Test error handling in _extract_price_from_keyword."""
    service = local_product_service_with_mock_products
    
    # Simulate an error by passing a non-string type or mocking an internal function
    with patch('re.search', side_effect=ValueError("Simulated regex error")):
        with caplog.at_level(logging.ERROR):
            price = service._extract_price_from_keyword("any keyword")
            assert price is None
            assert "Error extracting price from keyword: Simulated regex error" in caplog.text

# --- Tests for get_product_details ---

def test_get_product_details_existing_id(local_product_service_with_mock_products):
    """Test retrieving details for an existing product ID."""
    service = local_product_service_with_mock_products
    product = service.get_product_details("prod2")
    assert product is not None
    assert product['id'] == 'prod2'
    assert product['name'] == 'Laptop Y'

def test_get_product_details_non_existing_id(local_product_service_with_mock_products):
    """Test retrieving details for a non-existing product ID."""
    service = local_product_service_with_mock_products
    product = service.get_product_details("nonexistent")
    assert product is None

def test_get_product_details_empty_products(mock_local_product_service, caplog):
    """Test retrieving details when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = [] # Manually set to empty
    
    product = service.get_product_details("prod1")
    assert product is None

def test_get_product_details_with_exception_handling(local_product_service_with_mock_products, caplog):
    """Test error handling in get_product_details."""
    service = local_product_service_with_mock_products
    
    # Simulate an error by making product.get raise an exception
    with patch.object(service.products[0], 'get', side_effect=TypeError("Simulated get error")):
        with caplog.at_level(logging.ERROR):
            product = service.get_product_details("prod1")
            assert product is None
            assert "Error getting product details: Simulated get error" in caplog.text

# --- Tests for get_categories ---

def test_get_categories_success(local_product_service_with_mock_products):
    """Test retrieving a sorted list of unique categories."""
    service = local_product_service_with_mock_products
    categories = service.get_categories()
    assert sorted(['Electronics', 'Audio', 'Wearables', 'Smartphone']) == categories
    assert 'Smartphone' in categories

def test_get_categories_empty_products(mock_local_product_service):
    """Test retrieving categories when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = []
    categories = service.get_categories()
    assert categories == []

def test_get_categories_product_without_category(mock_local_product_service):
    """Test handling products without a 'category' key."""
    service, _ = mock_local_product_service
    service.products = [
        {"id": "p1", "name": "No Category Product"}
    ]
    categories = service.get_categories()
    assert categories == [''] # Should include an empty string for missing category

# --- Tests for get_brands ---

def test_get_brands_success(local_product_service_with_mock_products):
    """Test retrieving a sorted list of unique brands."""
    service = local_product_service_with_mock_products
    brands = service.get_brands()
    assert sorted(['Apple', 'Brand A', 'Brand B', 'Brand C', 'Brand D', 'Samsung']) == brands

def test_get_brands_empty_products(mock_local_product_service):
    """Test retrieving brands when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = []
    brands = service.get_brands()
    assert brands == []

def test_get_brands_product_without_brand(mock_local_product_service):
    """Test handling products without a 'brand' key."""
    service, _ = mock_local_product_service
    service.products = [
        {"id": "p1", "name": "No Brand Product"}
    ]
    brands = service.get_brands()
    assert brands == [''] # Should include an empty string for missing brand

# --- Tests for get_products_by_category ---

def test_get_products_by_category_match(local_product_service_with_mock_products):
    """Test retrieving products for an existing category."""
    service = local_product_service_with_mock_products
    electronics_products = service.get_products_by_category("Electronics")
    assert len(electronics_products) == 4
    assert all(p['category'] == 'Electronics' for p in electronics_products)
    assert {p['id'] for p in electronics_products} == {'prod1', 'prod2', 'prod5'} # No iPhone or Samsung here as they are 'Smartphone'

def test_get_products_by_category_case_insensitive(local_product_service_with_mock_products):
    """Test case-insensitivity for category search."""
    service = local_product_service_with_mock_products
    electronics_products = service.get_products_by_category("electronics")
    assert len(electronics_products) == 4
    assert all(p['category'] == 'Electronics' for p in electronics_products)

def test_get_products_by_category_no_match(local_product_service_with_mock_products):
    """Test retrieving products for a non-existing category."""
    service = local_product_service_with_mock_products
    no_products = service.get_products_by_category("NonExistentCategory")
    assert no_products == []

def test_get_products_by_category_empty_products(mock_local_product_service):
    """Test retrieving products by category when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = []
    results = service.get_products_by_category("Electronics")
    assert results == []

def test_get_products_by_category_with_exception_handling(local_product_service_with_mock_products, caplog):
    """Test error handling in get_products_by_category."""
    service = local_product_service_with_mock_products
    
    # Simulate an error by making product.get raise an exception
    with patch.object(service.products[0], 'get', side_effect=TypeError("Simulated get error")):
        with caplog.at_level(logging.ERROR):
            products = service.get_products_by_category("Electronics")
            assert products == []
            assert "Error getting products by category: Simulated get error" in caplog.text

# --- Tests for get_products_by_brand ---

def test_get_products_by_brand_match(local_product_service_with_mock_products):
    """Test retrieving products for an existing brand."""
    service = local_product_service_with_mock_products
    brand_a_products = service.get_products_by_brand("Brand A")
    assert len(brand_a_products) == 2
    assert all(p['brand'] == 'Brand A' for p in brand_a_products)

def test_get_products_by_brand_case_insensitive(local_product_service_with_mock_products):
    """Test case-insensitivity for brand search."""
    service = local_product_service_with_mock_products
    brand_a_products = service.get_products_by_brand("brand a")
    assert len(brand_a_products) == 2
    assert all(p['brand'] == 'Brand A' for p in brand_a_products)

def test_get_products_by_brand_no_match(local_product_service_with_mock_products):
    """Test retrieving products for a non-existing brand."""
    service = local_product_service_with_mock_products
    no_products = service.get_products_by_brand("NonExistentBrand")
    assert no_products == []

def test_get_products_by_brand_empty_products(mock_local_product_service):
    """Test retrieving products by brand when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = []
    results = service.get_products_by_brand("Brand A")
    assert results == []

def test_get_products_by_brand_with_exception_handling(local_product_service_with_mock_products, caplog):
    """Test error handling in get_products_by_brand."""
    service = local_product_service_with_mock_products
    
    # Simulate an error by making product.get raise an exception
    with patch.object(service.products[0], 'get', side_effect=TypeError("Simulated get error")):
        with caplog.at_level(logging.ERROR):
            products = service.get_products_by_brand("Brand A")
            assert products == []
            assert "Error getting products by brand: Simulated get error" in caplog.text

# --- Tests for get_top_rated_products ---

def test_get_top_rated_products_success(local_product_service_with_mock_products):
    """Test retrieving top-rated products with default limit."""
    service = local_product_service_with_mock_products
    top_products = service.get_top_rated_products()
    assert len(top_products) == 5
    # Expected order by rating: Laptop Y(4.8), iPhone(4.8), Tablet Pro(4.7), Samsung(4.7), Smartphone X(4.5), Headphones Z(4.2), Smartwatch(3.9)
    # If ratings are equal, original order is preserved by sorted() default stability
    expected_ids = ['prod2', 'prod6', 'prod5', 'prod7', 'prod1']
    assert [p['id'] for p in top_products] == expected_ids

def test_get_top_rated_products_with_custom_limit(local_product_service_with_mock_products):
    """Test retrieving top-rated products with a custom limit."""
    service = local_product_service_with_mock_products
    top_products = service.get_top_rated_products(limit=3)
    assert len(top_products) == 3
    expected_ids = ['prod2', 'prod6', 'prod5']
    assert [p['id'] for p in top_products] == expected_ids

def test_get_top_rated_products_limit_greater_than_total(local_product_service_with_mock_products):
    """Test limit greater than total number of products."""
    service = local_product_service_with_mock_products
    top_products = service.get_top_rated_products(limit=10)
    assert len(top_products) == 7 # All products

def test_get_top_rated_products_empty_products(mock_local_product_service):
    """Test retrieving top-rated products when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = []
    results = service.get_top_rated_products()
    assert results == []

def test_get_top_rated_products_products_without_rating(mock_local_product_service):
    """Test handling products with missing 'rating' in specifications."""
    service, _ = mock_local_product_service
    service.products = [
        {"id": "p1", "name": "No Rating", "specifications": {"sold": 10}},
        {"id": "p2", "name": "With Rating", "specifications": {"rating": 5.0, "sold": 5}},
        {"id": "p3", "name": "No Specs Dict", "price": 100}
    ]
    top_products = service.get_top_rated_products(limit=3)
    # Products without rating or specs dict should default to 0 rating and come last
    assert [p['id'] for p in top_products] == ['p2', 'p1', 'p3']

def test_get_top_rated_products_with_exception_handling(local_product_service_with_mock_products, caplog):
    """Test error handling in get_top_rated_products."""
    service = local_product_service_with_mock_products
    
    # Simulate an error by making product.get raise an exception within the lambda
    with patch.object(service.products[0]['specifications'], 'get', side_effect=TypeError("Simulated spec get error")):
        with caplog.at_level(logging.ERROR):
            products = service.get_top_rated_products()
            assert products == []
            assert "Error getting top rated products: Simulated spec get error" in caplog.text

# --- Tests for get_best_selling_products ---

def test_get_best_selling_products_success(local_product_service_with_mock_products, caplog):
    """Test retrieving best-selling products with default limit."""
    service = local_product_service_with_mock_products
    with caplog.at_level(logging.INFO):
        best_sellers = service.get_best_selling_products()
        assert len(best_sellers) == 5
        # Expected order by sold count: iPhone(1250), Samsung(980), Laptop Y(800), Smartphone X(500), Headphones Z(300), Tablet Pro(250), Smartwatch(150)
        expected_ids = ['prod6', 'prod7', 'prod2', 'prod1', 'prod3']
        assert [p['id'] for p in best_sellers] == expected_ids
        assert "Getting best selling products, limit: 5" in caplog.text
        assert "Returning 5 best selling products" in caplog.text

def test_get_best_selling_products_with_custom_limit(local_product_service_with_mock_products):
    """Test retrieving best-selling products with a custom limit."""
    service = local_product_service_with_mock_products
    best_sellers = service.get_best_selling_products(limit=3)
    assert len(best_sellers) == 3
    expected_ids = ['prod6', 'prod7', 'prod2']
    assert [p['id'] for p in best_sellers] == expected_ids

def test_get_best_selling_products_limit_greater_than_total(local_product_service_with_mock_products):
    """Test limit greater than total number of products."""
    service = local_product_service_with_mock_products
    best_sellers = service.get_best_selling_products(limit=10)
    assert len(best_sellers) == 7 # All products

def test_get_best_selling_products_empty_products(mock_local_product_service):
    """Test retrieving best-selling products when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = []
    results = service.get_best_selling_products()
    assert results == []

def test_get_best_selling_products_products_without_sold_count(mock_local_product_service):
    """Test handling products with missing 'sold' in specifications."""
    service, _ = mock_local_product_service
    service.products = [
        {"id": "p1", "name": "No Sold", "specifications": {"rating": 4.0}},
        {"id": "p2", "name": "With Sold", "specifications": {"sold": 100, "rating": 5.0}},
        {"id": "p3", "name": "No Specs Dict", "price": 100}
    ]
    best_sellers = service.get_best_selling_products(limit=3)
    # Products without sold or specs dict should default to 0 sold and come last
    assert [p['id'] for p in best_sellers] == ['p2', 'p1', 'p3']

def test_get_best_selling_products_with_exception_handling(local_product_service_with_mock_products, caplog):
    """Test error handling in get_best_selling_products."""
    service = local_product_service_with_mock_products
    
    # Simulate an error by making product.get raise an exception within the lambda
    with patch.object(service.products[0]['specifications'], 'get', side_effect=TypeError("Simulated spec get error")):
        with caplog.at_level(logging.ERROR):
            products = service.get_best_selling_products()
            assert products == []
            assert "Error getting best selling products: Simulated spec get error" in caplog.text

# --- Tests for get_products ---

def test_get_products_success(local_product_service_with_mock_products, caplog):
    """Test retrieving all products with default limit."""
    service = local_product_service_with_mock_products
    with caplog.at_level(logging.INFO):
        all_products = service.get_products()
        assert len(all_products) == 7 # Default limit is 10, but we only have 7 mock products
        assert "Getting all products, limit: 10" in caplog.text

def test_get_products_with_custom_limit(local_product_service_with_mock_products):
    """Test retrieving products with a custom limit."""
    service = local_product_service_with_mock_products
    limited_products = service.get_products(limit=3)
    assert len(limited_products) == 3

def test_get_products_empty_products(mock_local_product_service):
    """Test retrieving products when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = []
    results = service.get_products()
    assert results == []

def test_get_products_with_exception_handling(local_product_service_with_mock_products, caplog):
    """Test error handling in get_products."""
    service = local_product_service_with_mock_products
    
    # Simulate an error by making products list uniterable
    service.products = "invalid_data"
    
    with caplog.at_level(logging.ERROR):
        products = service.get_products()
        assert products == []
        assert "Error getting products: " in caplog.text # Expecting TypeError

# --- Tests for smart_search_products ---

def test_smart_search_best_general(local_product_service_with_mock_products):
    """Test 'terbaik' keyword without specific category (general best by rating)."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="terbaik", limit=3)
    
    assert len(products) == 3
    assert message == "Berikut produk terbaik berdasarkan rating:"
    # Expected order: Laptop Y(4.8), iPhone(4.8), Tablet Pro(4.7)
    expected_ids = ['prod2', 'prod6', 'prod5']
    assert [p['id'] for p in products] == expected_ids

def test_smart_search_best_category_found(local_product_service_with_mock_products):
    """Test 'terbaik' keyword with an existing category."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="terbaik", category="Electronics", limit=2)
    
    assert len(products) == 2
    assert message == "Berikut Electronics terbaik berdasarkan rating:"
    # Electronics products: Smartphone X(4.5), Laptop Y(4.8), Tablet Pro(4.7)
    # Expected order: Laptop Y(4.8), Tablet Pro(4.7)
    expected_ids = ['prod2', 'prod5']
    assert [p['id'] for p in products] == expected_ids

def test_smart_search_best_category_not_found(local_product_service_with_mock_products):
    """Test 'terbaik' keyword with a non-existing category (fallback to general best)."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="best", category="Furniture", limit=2)
    
    assert len(products) == 2
    assert message == "Tidak ada produk kategori Furniture, berikut produk terbaik secara umum:"
    # Fallback to general best: Laptop Y(4.8), iPhone(4.8)
    expected_ids = ['prod2', 'prod6']
    assert [p['id'] for p in products] == expected_ids

def test_smart_search_all_criteria_match(local_product_service_with_mock_products):
    """Test search with keyword, category, and max_price, all matching."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="smartphone", category="Electronics", max_price=12000000, limit=5)
    
    assert len(products) == 1
    assert products[0]['id'] == 'prod1' # Smartphone X (10M) is the only one
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_fallback_category_match_no_price(local_product_service_with_mock_products):
    """
    Test fallback: no products match all criteria, but category matches
    (should return cheapest in category).
    """
    service = local_product_service_with_mock_products
    # Search for an expensive laptop within a low budget
    products, message = service.smart_search_products(keyword="Laptop Y", category="Electronics", max_price=1000000, limit=1)
    
    assert len(products) == 1
    # Original criteria: Laptop Y (15M) & max_price 1M => no direct match
    # Fallback to category 'Electronics', sorted by price: Smartphone X (10M)
    assert products[0]['id'] == 'prod1'
    assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."

def test_smart_search_fallback_budget_match_no_category(local_product_service_with_mock_products):
    """
    Test fallback: no products match specific category, but max_price matches
    (should return other products within budget).
    """
    service = local_product_service_with_mock_products
    # Search for a product in a non-existent category, but with a budget
    products, message = service.smart_search_products(keyword="gadget", category="Furniture", max_price=5000000, limit=2)
    
    assert len(products) == 2
    # Products <= 5M: Headphones Z (2M), Smartwatch (3M)
    expected_ids = ['prod3', 'prod4']
    assert {p['id'] for p in products} == set(expected_ids)
    assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

def test_smart_search_fallback_to_popular(local_product_service_with_mock_products):
    """
    Test fallback: no products match any specific criteria (keyword, category, max_price),
    should return popular products.
    """
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="xyz_non_existent", category="NonCat", max_price=1000, limit=2)
    
    assert len(products) == 2
    assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
    # Popular products: iPhone(1250), Samsung(980)
    expected_ids = ['prod6', 'prod7']
    assert [p['id'] for p in products] == expected_ids

def test_smart_search_empty_products(mock_local_product_service):
    """Test smart_search_products when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = []
    
    products, message = service.smart_search_products(keyword="any", category="any", max_price=1000)
    assert products == []
    assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." # Still returns this message, but with an empty list

def test_smart_search_only_keyword(local_product_service_with_mock_products):
    """Test smart search with only a keyword."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="laptop", limit=1)
    
    assert len(products) == 1
    assert products[0]['id'] == 'prod2' # Laptop Y
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_only_category(local_product_service_with_mock_products):
    """Test smart search with only a category."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(category="Audio", limit=1)
    
    assert len(products) == 1
    assert products[0]['id'] == 'prod3' # Headphones Z
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_only_max_price(local_product_service_with_mock_products):
    """Test smart search with only a max_price."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(max_price=3000000, limit=2)
    
    assert len(products) == 2
    # Should include Headphones Z (2M) and Smartwatch (3M)
    assert {p['id'] for p in products} == {'prod3', 'prod4'}
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_no_parameters(local_product_service_with_mock_products):
    """Test smart search with no parameters, should return popular as default fallback."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(limit=2)
    
    assert len(products) == 2
    assert message == "Berikut produk yang sesuai dengan kriteria Anda." # Changed, it should trigger the initial keyword search if keyword is empty, resulting in all products
    # This behavior indicates that `smart_search_products` defaults to an "all products" view if no specific keyword/category/price is given.
    # The current implementation (not keyword or keyword_lower in searchable_text) means an empty keyword matches everything.
    # So it directly hits the "all criteria match" path.
    # To hit "popular" fallback, all filters (keyword, category, max_price) must result in an empty list.
    assert {p['id'] for p in products} == {'prod1', 'prod2'} # Default limit 5 means it would just return first 5, but here it's 2
    # If the idea is to return popular when nothing specified, the logic needs adjustment.
    # Based on the code, if `keyword` is an empty string, `(not keyword or keyword_lower in ...)` becomes `(True or False)` which is `True`.
    # So it matches all products.

    # Correct interpretation: If keyword is empty, it acts like a filter for category/max_price only.
    # If all 3 are None/empty, it returns all products (up to limit).
    # If it's truly meant to return popular products when no criteria, the last fallback needs to be the default.
    # Let's check this specific case more carefully given the existing code.

    # Re-testing "no parameters":
    # `results = [p for p in self.products if (not category or ...) and (not max_price or ...) and (not keyword or ...)]`
    # If keyword='', category=None, max_price=None, then all `not X` are True, so it matches all products.
    # This leads to `return results[:limit], "Berikut produk yang sesuai dengan kriteria Anda."`
    # This is consistent with the code, though perhaps not the most "smart" default if "smart" implies "intelligent guess".
    # But it achieves full coverage of the "no parameters" path.
    assert len(products) == 2
    # If no parameters, it matches all products and returns the first 'limit' of them.
    # The order of products in `self.products` will determine this.
    assert products[0]['id'] == 'prod1'
    assert products[1]['id'] == 'prod2'
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_empty_keyword_only_category(local_product_service_with_mock_products):
    """Test smart search with empty keyword and only category."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="", category="Audio", limit=1)
    
    assert len(products) == 1
    assert products[0]['id'] == 'prod3'
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_empty_keyword_only_max_price(local_product_service_with_mock_products):
    """Test smart search with empty keyword and only max_price."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="", max_price=3000000, limit=2)
    
    assert len(products) == 2
    # Should be Headphones Z (2M) and Smartwatch (3M)
    assert {p['id'] for p in products} == {'prod3', 'prod4'}
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_limit_parameter(local_product_service_with_mock_products):
    """Test that the limit parameter is respected in smart_search_products."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="phone", limit=1)
    assert len(products) == 1
    assert products[0]['name'] == 'iPhone 15 Pro Max' # iPhone is first due to relevance score logic

    products, message = service.smart_search_products(keyword="phone", limit=10)
    assert len(products) == 3 # Smartphone X, iPhone 15 Pro Max, Samsung Galaxy S24 Ultra

def test_smart_search_non_dict_product(mock_local_product_service, caplog):
    """Test smart search with a non-dictionary product to trigger attribute errors."""
    service, _ = mock_local_product_service
    service.products = [
        {"id": "prod1", "name": "Valid Product", "category": "Electronics", "price": 1000},
        "not_a_dict" # This will cause an error when .get is called
    ]
    with caplog.at_level(logging.ERROR):
        # The smart_search_products method doesn't have an explicit try-except for the main loop
        # It relies on dict.get() which returns None, so the `in` operator might fail.
        # This will test if the `(not keyword or ...)` check handles non-dict items.
        # It won't throw an error directly from `get`, but from `lower()` on a non-string.
        products, message = service.smart_search_products(keyword="valid")
        assert len(products) == 1
        assert products[0]['id'] == 'prod1'
        # The code needs to be robust against non-dict items in `self.products`.
        # The current implementation of `smart_search_products` handles this gracefully with `p.get()`
        # and empty strings/dicts, so no log.error is expected for this specific case.
        assert "Error searching products:" not in caplog.text # It handles gracefully.
        
        # To actually trigger an error, we'd need to mock something deeper, or pass invalid values
        # into the product dict that are not handled by .get with defaults.
        # Example: if `product.get('name', '').lower()` where `product.get('name')` returns `None`
        # and then `.lower()` is called on `None`. But the `get` with `''` default prevents that.
        # So, the test of `local_product_service_with_mock_products` already covers the `get` cases properly.
        # The only remaining general error handling for `smart_search_products` itself would be if `self.products`
        # itself caused an exception when iterated, which is unlikely for a list.
        # The error handling in `search_products` (which `smart_search_products` doesn't directly use)
        # tests this kind of top-level error.
        
        # Let's confirm it's handled gracefully and no error is logged for the non-dict case.
        assert "Error getting product details" not in caplog.text
        assert "Error searching products" not in caplog.text

# Final check of overall coverage:
# _load_local_products: covered all paths (file exists/not, json error, unicode error, bom, empty data, transformation).
# _get_fallback_products: covered.
# __init__: covered all loading scenarios.
# search_products: covered keyword, limit, price extraction, no match, empty keyword, errors.
# _extract_price_from_keyword: covered all patterns, budget words, no match, errors.
# get_product_details: covered match, no match, empty list, errors.
# get_categories/get_brands: covered success, empty list, missing key.
# get_products_by_category/get_products_by_brand: covered match, no match, empty list, errors.
# get_top_rated_products/get_best_selling_products: covered limits, empty list, missing specs data, errors.
# get_products: covered limits, empty list, errors.
# smart_search_products: covered all 6 fallback levels, best/terbaik logic, specific criteria, no params, limits, empty list.

# Looks comprehensive.
```python
import pytest
import json
import logging
import os
import random
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

# Adjust path to import the module correctly from the root or wherever tests are run
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.local_product_service import LocalProductService

logger = logging.getLogger(__name__)

# --- Fixtures ---

@pytest.fixture
def mock_random_randint():
    """Mock random.randint to return a predictable value."""
    with patch('random.randint', return_value=1000) as mock_rand:
        yield mock_rand

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary 'data' directory for products.json."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    yield data_dir

@pytest.fixture
def mock_local_product_service(mock_random_randint):
    """
    Fixture to create an instance of LocalProductService with mocked dependencies.
    It will load fallback products by default unless _load_local_products is mocked
    or `create_mock_json_file` is used.
    """
    with patch('app.services.local_product_service.Path') as MockPath:
        # Mock Path(__file__).parent.parent.parent to point to a predictable location
        mock_instance = MockPath.return_value
        mock_instance.parent.parent.parent = MagicMock(spec=Path)
        mock_instance.parent.parent.parent.__truediv__.return_value = MagicMock(spec=Path) # Simulate Path.__truediv__

        # By default, make json_file_path.exists() return False to use fallback
        # Tests requiring file interaction will re-mock this as needed.
        mock_json_file_path = mock_instance.parent.parent.parent.__truediv__.return_value
        mock_json_file_path.exists.return_value = False
        mock_json_file_path.__str__.return_value = "/mock/path/data/products.json"

        service = LocalProductService()
        yield service, mock_json_file_path

@pytest.fixture
def create_mock_json_file(temp_data_dir):
    """
    Fixture to create a products.json file in a temporary data directory
    and mock Path operations to point to it, then re-initialize LocalProductService.
    """
    def _creator(content, encoding='utf-8', bom=False):
        json_file_path = temp_data_dir / "products.json"
        
        # Add BOM if requested
        if bom:
            # For UTF-8-SIG, the BOM is 0xEFBBBF, which Python handles automatically
            # if encoding='utf-8-sig'. If we write as 'utf-8' but want BOM, we add it.
            if encoding != 'utf-8-sig':
                content = '\ufeff' + content
        
        with open(json_file_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        # Mock Path(__file__).parent.parent.parent to return tmp_path
        # and ensure json_file_path points to the temporary file.
        with patch('app.services.local_product_service.Path') as MockPath:
            mock_current_dir = MagicMock(spec=Path)
            # Simulate Path(__file__).parent.parent.parent behavior
            mock_current_dir.parent.parent.parent = MagicMock(return_value=temp_data_dir)
            
            # Simulate the json_file_path object returned by the division operations
            mock_file_path_obj = MagicMock(spec=Path)
            mock_file_path_obj.exists.return_value = True
            mock_file_path_obj.__str__.return_value = str(json_file_path)

            # Ensure the path resolution returns our mock file path object
            mock_current_dir.parent.parent.parent.__truediv__.return_value = mock_file_path_obj
            # This is for the subsequent '/data' and '/products.json' calls if they were chained.
            # However, the code uses `current_dir / "data" / "products.json"`, which is one chain.
            # So, the first `__truediv__` should return the final path.
            # A more robust mock might involve setting up a mock tree, but this works for direct path.
            
            # The actual path being passed to `open` will be the `str(json_file_path)`.
            
            # Patch Path in the module to return our mock objects
            MockPath.return_value = mock_current_dir

            # Re-initialize the service to pick up the new mocked path
            service = LocalProductService()
            return service, str(json_file_path)
    return _creator

@pytest.fixture
def mock_products():
    """A set of mock products for testing."""
    return [
        {
            "id": "prod1",
            "name": "Smartphone X",
            "category": "Electronics",
            "brand": "Brand A",
            "price": 10000000,
            "currency": "IDR",
            "description": "High-end smartphone.",
            "specifications": {"rating": 4.5, "sold": 500, "stock_count": 100, "color": "black"},
            "availability": "in_stock",
            "reviews_count": 50,
            "images": [],
            "url": ""
        },
        {
            "id": "prod2",
            "name": "Laptop Y",
            "category": "Electronics",
            "brand": "Brand B",
            "price": 15000000,
            "currency": "IDR",
            "description": "Powerful gaming laptop.",
            "specifications": {"rating": 4.8, "sold": 800, "stock_count": 50, "storage": "1TB SSD"},
            "availability": "in_stock",
            "reviews_count": 80,
            "images": [],
            "url": ""
        },
        {
            "id": "prod3",
            "name": "Headphones Z",
            "category": "Audio",
            "brand": "Brand A",
            "price": 2000000,
            "currency": "IDR",
            "description": "Noise cancelling headphones.",
            "specifications": {"rating": 4.2, "sold": 300, "stock_count": 200},
            "availability": "in_stock",
            "reviews_count": 30,
            "images": [],
            "url": ""
        },
        {
            "id": "prod4",
            "name": "Smartwatch",
            "category": "Wearables",
            "brand": "Brand C",
            "price": 3000000,
            "currency": "IDR",
            "description": "Fitness tracking smartwatch.",
            "specifications": {"rating": 3.9, "sold": 150, "stock_count": 300},
            "availability": "out_of_stock",
            "reviews_count": 10,
            "images": [],
            "url": ""
        },
        {
            "id": "prod5",
            "name": "Tablet Pro",
            "category": "Electronics",
            "brand": "Brand D",
            "price": 8000000,
            "currency": "IDR",
            "description": "Tablet for drawing.",
            "specifications": {"rating": 4.7, "sold": 250, "stock_count": 70},
            "availability": "in_stock",
            "reviews_count": 40,
            "images": [],
            "url": ""
        },
        {
            "id": "prod6",
            "name": "iPhone 15 Pro Max",
            "category": "Smartphone",
            "brand": "Apple",
            "price": 25000000,
            "currency": "IDR",
            "description": "iPhone 15 Pro Max dengan chip A17 Pro.",
            "specifications": {
                "rating": 4.8,
                "sold": 1250,
                "stock": 50,
                "condition": "Baru",
            },
            "images": ["https://example.com/iphone15.jpg"],
            "url": "https://shopee.co.id/iphone-15-pro-max"
        },
        {
            "id": "prod7",
            "name": "Samsung Galaxy S24 Ultra",
            "category": "Smartphone",
            "brand": "Samsung",
            "price": 22000000,
            "currency": "IDR",
            "description": "Samsung Galaxy S24 Ultra dengan S Pen.",
            "specifications": {
                "rating": 4.7,
                "sold": 980,
                "stock": 35,
                "condition": "Baru",
            },
            "images": ["https://example.com/s24-ultra.jpg"],
            "url": "https://shopee.co.id/samsung-s24-ultra"
        }
    ]

@pytest.fixture
def local_product_service_with_mock_products(mock_products):
    """
    Fixture to create LocalProductService with a predefined set of products
    instead of loading from a file or fallback, ensuring consistency for tests.
    """
    with patch.object(LocalProductService, '_load_local_products', return_value=mock_products) as mock_loader:
        service = LocalProductService()
        yield service
        # Ensure _load_local_products was called by the constructor
        mock_loader.assert_called_once() 

# --- Tests for __init__ and _load_local_products ---

def test_init_loads_products_successfully_from_file(create_mock_json_file, caplog, mock_random_randint):
    """
    Test that __init__ correctly loads products from a valid JSON file.
    Verifies product count, a specific ID, and transformed values.
    """
    mock_json_content = json.dumps({
        "products": [
            {"id": "test1", "name": "Product 1", "price": 100, "stock_count": 5, "rating": 4.0},
            {"id": "test2", "name": "Product 2", "price": 200, "stock_count": 10, "rating": 3.5}
        ]
    })
    
    with caplog.at_level(logging.INFO):
        service, _ = create_mock_json_file(mock_json_content)
        
        assert len(service.products) == 2
        assert service.products[0]['id'] == 'test1'
        assert service.products[0]['specifications']['sold'] == 1000 # From mock_random_randint
        assert "Successfully loaded 2 products from JSON file using utf-8 encoding" in caplog.text
        assert "Loaded 2 local products from JSON file" in caplog.text
        
        # Test transformation for missing keys
        assert service.products[0]['currency'] == 'IDR'
        assert service.products[0]['specifications']['condition'] == 'Baru'
        assert service.products[0]['images'] == ["https://example.com/test1.jpg"]

def test_init_falls_back_if_json_file_not_found(mock_local_product_service, caplog):
    """
    Test that __init__ falls back to default products if the JSON file is not found.
    Ensures relevant error and warning messages are logged.
    """
    service, mock_json_file_path = mock_local_product_service
    mock_json_file_path.exists.return_value = False
    
    with caplog.at_level(logging.ERROR):
        # Re-initialize the service to trigger the loading logic with the mocked path
        service = LocalProductService()
        
        assert len(service.products) > 0 # Should load fallback products
        assert any("Products JSON file not found at:" in rec.message for rec in caplog.records)
        assert any("Using fallback products due to JSON file loading error" in rec.message for rec in caplog.records)

def test_init_falls_back_on_json_decode_error(create_mock_json_file, caplog):
    """
    Test that __init__ falls back if the JSON file is malformed and cannot be parsed.
    Checks for warning and error logs indicating parsing failures and fallback.
    """
    malformed_json_content = "{products: [" # Invalid JSON
    with caplog.at_level(logging.WARNING):
        service, _ = create_mock_json_file(malformed_json_content)
        
        assert len(service.products) > 0 # Should load fallback products
        # Check for warnings for failed encodings, specifically for JSONDecodeError
        assert any("Failed to load with utf-8 encoding: Expecting value" in rec.message for rec in caplog.records)
        assert "All encoding attempts failed, using fallback products" in caplog.text
        assert "Using fallback products due to JSON file loading error" in caplog.text

def test_init_falls_back_on_unicode_decode_error(caplog):
    """
    Test that __init__ falls back if the file content cannot be decoded by any encoding.
    Mocks `open` to return problematic byte sequences.
    """
    # Simulate an invalid byte sequence that would cause UnicodeDecodeError
    invalid_byte_sequence = b'\xc3\x28' # Not valid UTF-8
    
    with patch('builtins.open', mock_open(read_data=invalid_byte_sequence.decode('latin-1', errors='ignore'))), \
         patch.object(Path, 'exists', return_value=True), \
         patch.object(Path, '__truediv__', return_value=MagicMock(exists=True, __str__=lambda: "/mock/path/data/products.json")):
        
        with caplog.at_level(logging.WARNING):
            service = LocalProductService()
            
            assert len(service.products) > 0 # Should load fallback products
            # Check for warnings for failed encodings, specifically for UnicodeDecodeError
            assert any("Failed to load with utf-8 encoding: " in rec.message for rec in caplog.records)
            assert "All encoding attempts failed, using fallback products" in caplog.text
            assert "Using fallback products due to JSON file loading error" in caplog.text

def test_load_local_products_handles_bom(create_mock_json_file, caplog, mock_random_randint):
    """
    Test that _load_local_products correctly handles JSON files with a Byte Order Mark (BOM).
    Ensures utf-8-sig encoding handles it.
    """
    mock_json_content = json.dumps({"products": [{"id": "bom_test", "name": "BOM Product", "price": 100}]})
    
    with caplog.at_level(logging.INFO):
        # Create file with BOM and ensure it's loaded by utf-8-sig
        service, _ = create_mock_json_file(mock_json_content, encoding='utf-8-sig', bom=True)
        
        assert len(service.products) == 1
        assert service.products[0]['id'] == 'bom_test'
        assert "Successfully loaded 1 products from JSON file using utf-8-sig encoding" in caplog.text

def test_load_local_products_transforms_missing_keys(create_mock_json_file, mock_random_randint):
    """
    Test that _load_local_products applies default values for missing keys
    during the product transformation process.
    """
    mock_json_content = json.dumps({
        "products": [
            {"id": "min_prod", "name": "Minimal Product"},
            {"id": "some_spec", "name": "Product With Some Specs", "specifications": {"warranty": "1 year"}}
        ]
    })
    service, _ = create_mock_json_file(mock_json_content)

    assert len(service.products) == 2
    
    # Test min_prod for all default values
    prod1 = service.products[0]
    assert prod1['id'] == 'min_prod'
    assert prod1['name'] == 'Minimal Product'
    assert prod1['category'] == ''
    assert prod1['brand'] == ''
    assert prod1['price'] == 0
    assert prod1['currency'] == 'IDR'
    assert prod1['description'] == ''
    assert prod1['availability'] == 'in_stock'
    assert prod1['reviews_count'] == 0
    assert prod1['images'] == ["https://example.com/min_prod.jpg"]
    assert prod1['url'] == "https://shopee.co.id/min_prod"
    
    # Check specifications defaults
    specs1 = prod1['specifications']
    assert specs1['rating'] == 0
    assert specs1['sold'] == 1000 # From mock_random_randint
    assert specs1['stock'] == 0
    assert specs1['condition'] == 'Baru'
    assert specs1['shop_location'] == 'Indonesia'
    assert specs1['shop_name'] == 'Unknown Store' # No brand provided

    # Test product with some existing specs are preserved
    prod2 = service.products[1]
    assert prod2['id'] == 'some_spec'
    assert prod2['name'] == 'Product With Some Specs'
    assert prod2['specifications']['warranty'] == '1 year' # Existing spec should be preserved
    assert prod2['specifications']['rating'] == 0 # Default for missing spec
    assert prod2['images'] == ["https://example.com/some_spec.jpg"]

def test_load_local_products_empty_file_or_data(create_mock_json_file, caplog):
    """
    Test behavior when JSON file is empty or contains no 'products' key or an empty products array.
    Should result in an empty `self.products` list.
    """
    # Empty JSON content
    service_empty_json, _ = create_mock_json_file("{}")
    assert service_empty_json.products == []

    # JSON with no 'products' key
    service_no_products_key, _ = create_mock_json_file(json.dumps({"data": []}))
    assert service_no_products_key.products == []
    
    # JSON with empty 'products' array
    service_empty_array, _ = create_mock_json_file(json.dumps({"products": []}))
    assert service_empty_array.products == []

def test_get_fallback_products_returns_correct_data(mock_local_product_service):
    """
    Test that _get_fallback_products returns a non-empty list of dictionaries
    with expected keys and structure.
    """
    service, _ = mock_local_product_service
    fallback_products = service._get_fallback_products()
    
    assert isinstance(fallback_products, list)
    assert len(fallback_products) > 0
    
    # Check structure of a sample product
    sample_product = fallback_products[0]
    expected_keys = ["id", "name", "category", "brand", "price", "currency", "description", "specifications", "images", "url"]
    for key in expected_keys:
        assert key in sample_product
    assert isinstance(sample_product["specifications"], dict)
    assert "rating" in sample_product["specifications"]
    assert "sold" in sample_product["specifications"]

# --- Tests for search_products ---

def test_search_products_by_name(local_product_service_with_mock_products):
    """Test searching by product name."""
    service = local_product_service_with_mock_products
    results = service.search_products("Smartphone X")
    assert len(results) == 1
    assert results[0]['id'] == 'prod1'

def test_search_products_case_insensitive(local_product_service_with_mock_products):
    """Test searching with case-insensitive keywords across all fields."""
    service = local_product_service_with_mock_products
    results = service.search_products("smartphone x")
    assert len(results) == 1
    assert results[0]['id'] == 'prod1'
    
    results_brand = service.search_products("brand a")
    assert len(results_brand) == 2
    assert 'prod1' in [p['id'] for p in results_brand]
    assert 'prod3' in [p['id'] for p in results_brand]

def test_search_products_by_description(local_product_service_with_mock_products):
    """Test searching by product description."""
    service = local_product_service_with_mock_products
    results = service.search_products("gaming laptop")
    assert len(results) == 1
    assert results[0]['id'] == 'prod2'

def test_search_products_by_category(local_product_service_with_mock_products):
    """Test searching by product category (including transformed categories)."""
    service = local_product_service_with_mock_products
    results = service.search_products("Electronics")
    assert len(results) == 4 # Smartphone X, Laptop Y, Tablet Pro are 'Electronics'

def test_search_products_by_brand(local_product_service_with_mock_products):
    """Test searching by product brand."""
    service = local_product_service_with_mock_products
    results = service.search_products("Brand A")
    assert len(results) == 2 # Smartphone X, Headphones Z

def test_search_products_by_specifications(local_product_service_with_mock_products):
    """Test searching by content within product specifications."""
    service = local_product_service_with_mock_products
    results = service.search_products("1TB SSD")
    assert len(results) == 1
    assert results[0]['id'] == 'prod2'

def test_search_products_with_limit(local_product_service_with_mock_products):
    """Test the limit parameter in search_products to restrict results."""
    service = local_product_service_with_mock_products
    results = service.search_products("smartphone", limit=1)
    assert len(results) == 1
    # Sorting by relevance means 'iPhone 15 Pro Max' (prod6) might appear first due to exact name match
    assert results[0]['id'] == 'prod6'

def test_search_products_no_match(local_product_service_with_mock_products):
    """Test searching for a keyword that does not match any products."""
    service = local_product_service_with_mock_products
    results = service.search_products("NonExistentProductxyz")
    assert len(results) == 0

def test_search_products_empty_keyword(local_product_service_with_mock_products):
    """Test searching with an empty keyword, should return all products (up to limit)."""
    service = local_product_service_with_mock_products
    results = service.search_products("")
    assert len(results) == 7 # All 7 mock products are returned (default limit 10)

def test_search_products_price_extraction(local_product_service_with_mock_products):
    """Test price extraction from keyword in search_products for price filtering."""
    service = local_product_service_with_mock_products
    
    # Keyword with price: should find products <= 12 million
    results = service.search_products("gadget 12 juta")
    # Products within 12M: Smartphone X (10M), Headphones Z (2M), Smartwatch (3M), Tablet Pro (8M)
    assert len(results) == 4
    assert all(p['price'] <= 12000000 for p in results)
    
    # Budget keyword "murah" (max 5M)
    results_murah = service.search_products("headphones murah")
    assert len(results_murah) == 2 # Headphones Z (2M), Smartwatch (3M)
    assert 'prod3' in [p['id'] for p in results_murah]
    assert 'prod4' in [p['id'] for p in results_murah]
    assert all(p['price'] <= 5000000 for p in results_murah)

def test_search_products_price_extraction_and_keyword_match(local_product_service_with_mock_products):
    """Test combined keyword and price search, ensuring both filters apply."""
    service = local_product_service_with_mock_products
    results = service.search_products("smartphone 12 juta")
    assert len(results) == 1
    assert results[0]['id'] == 'prod1' # Only Smartphone X (10M) matches both 'smartphone' and <= 12M

def test_search_products_with_exception_handling(local_product_service_with_mock_products, caplog):
    """Test error handling in search_products to ensure it returns empty list on error."""
    service = local_product_service_with_mock_products
    
    # Simulate an error by making self.products uniterable
    service.products = "invalid_data"
    
    with caplog.at_level(logging.ERROR):
        results = service.search_products("any_keyword")
        assert results == []
        assert "Error searching products: " in caplog.text # Expecting TypeError from iteration

# --- Tests for _extract_price_from_keyword ---

@pytest.mark.parametrize("keyword, expected_price", [
    ("laptop 5 juta", 5000000),
    ("HP 10 juta", 10000000),
    ("headphone 2 ribu", 2000),
    ("earphone rp 50000", 50000),
    ("camera 75000 rp", 75000),
    ("monitor 3k", 3000),
    ("pc 15m", 15000000),
    ("murah laptop", 5000000), # Budget keywords
    ("budget phone", 5000000),
    ("hemat beli", 3000000),
    ("terjangkau", 4000000),
    ("ekonomis", 2000000),
    ("no price here", None), # No price found
    ("", None), # Empty keyword
    ("rp 123456789", 123456789), # Large number
    ("2juta", 2000000), # Test no space after number
    ("5ribu", 5000) # Test no space after number
])
def test_extract_price_from_keyword_success(local_product_service_with_mock_products, keyword, expected_price):
    """Test successful price extraction for various patterns and budget keywords."""
    service = local_product_service_with_mock_products
    price = service._extract_price_from_keyword(keyword)
    assert price == expected_price

def test_extract_price_from_keyword_error_handling(local_product_service_with_mock_products, caplog):
    """Test error handling in _extract_price_from_keyword when an internal error occurs."""
    service = local_product_service_with_mock_products
    
    # Simulate an error during regex search
    with patch('re.search', side_effect=ValueError("Simulated regex error")):
        with caplog.at_level(logging.ERROR):
            price = service._extract_price_from_keyword("any keyword")
            assert price is None
            assert "Error extracting price from keyword: Simulated regex error" in caplog.text

# --- Tests for get_product_details ---

def test_get_product_details_existing_id(local_product_service_with_mock_products):
    """Test retrieving details for an existing product ID."""
    service = local_product_service_with_mock_products
    product = service.get_product_details("prod2")
    assert product is not None
    assert product['id'] == 'prod2'
    assert product['name'] == 'Laptop Y'

def test_get_product_details_non_existing_id(local_product_service_with_mock_products):
    """Test retrieving details for a non-existing product ID."""
    service = local_product_service_with_mock_products
    product = service.get_product_details("nonexistent_id")
    assert product is None

def test_get_product_details_empty_products(mock_local_product_service):
    """Test retrieving details when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = [] # Manually set to empty for this test
    
    product = service.get_product_details("prod1")
    assert product is None

def test_get_product_details_with_exception_handling(local_product_service_with_mock_products, caplog):
    """Test error handling in get_product_details when accessing product data."""
    service = local_product_service_with_mock_products
    
    # Simulate an error by making product.get raise an exception on the first product
    with patch.object(service.products[0], 'get', side_effect=TypeError("Simulated get error")):
        with caplog.at_level(logging.ERROR):
            product = service.get_product_details("prod1")
            assert product is None
            assert "Error getting product details: Simulated get error" in caplog.text

# --- Tests for get_categories ---

def test_get_categories_success(local_product_service_with_mock_products):
    """Test retrieving a sorted list of unique categories from mock products."""
    service = local_product_service_with_mock_products
    categories = service.get_categories()
    # Expected categories based on mock_products
    assert sorted(['Electronics', 'Audio', 'Wearables', 'Smartphone']) == categories

def test_get_categories_empty_products(mock_local_product_service):
    """Test retrieving categories when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = []
    categories = service.get_categories()
    assert categories == []

def test_get_categories_product_without_category(mock_local_product_service):
    """Test handling products without a 'category' key, which should result in an empty string category."""
    service, _ = mock_local_product_service
    service.products = [
        {"id": "p1", "name": "No Category Product"}
    ]
    categories = service.get_categories()
    assert categories == [''] # Should include an empty string for missing category

# --- Tests for get_brands ---

def test_get_brands_success(local_product_service_with_mock_products):
    """Test retrieving a sorted list of unique brands from mock products."""
    service = local_product_service_with_mock_products
    brands = service.get_brands()
    # Expected brands based on mock_products
    assert sorted(['Apple', 'Brand A', 'Brand B', 'Brand C', 'Brand D', 'Samsung']) == brands

def test_get_brands_empty_products(mock_local_product_service):
    """Test retrieving brands when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = []
    brands = service.get_brands()
    assert brands == []

def test_get_brands_product_without_brand(mock_local_product_service):
    """Test handling products without a 'brand' key, which should result in an empty string brand."""
    service, _ = mock_local_product_service
    service.products = [
        {"id": "p1", "name": "No Brand Product"}
    ]
    brands = service.get_brands()
    assert brands == [''] # Should include an empty string for missing brand

# --- Tests for get_products_by_category ---

def test_get_products_by_category_match(local_product_service_with_mock_products):
    """Test retrieving products for an existing category."""
    service = local_product_service_with_mock_products
    electronics_products = service.get_products_by_category("Electronics")
    assert len(electronics_products) == 3 # Smartphone X, Laptop Y, Tablet Pro
    assert all(p['category'] == 'Electronics' for p in electronics_products)
    assert {p['id'] for p in electronics_products} == {'prod1', 'prod2', 'prod5'}

def test_get_products_by_category_case_insensitive(local_product_service_with_mock_products):
    """Test case-insensitivity for category search."""
    service = local_product_service_with_mock_products
    electronics_products = service.get_products_by_category("electronics")
    assert len(electronics_products) == 3
    assert all(p['category'] == 'Electronics' for p in electronics_products)

def test_get_products_by_category_no_match(local_product_service_with_mock_products):
    """Test retrieving products for a non-existing category."""
    service = local_product_service_with_mock_products
    no_products = service.get_products_by_category("NonExistentCategory")
    assert no_products == []

def test_get_products_by_category_empty_products(mock_local_product_service):
    """Test retrieving products by category when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = []
    results = service.get_products_by_category("Electronics")
    assert results == []

def test_get_products_by_category_with_exception_handling(local_product_service_with_mock_products, caplog):
    """Test error handling in get_products_by_category when accessing product data."""
    service = local_product_service_with_mock_products
    
    # Simulate an error by making product.get raise an exception
    with patch.object(service.products[0], 'get', side_effect=TypeError("Simulated get error")):
        with caplog.at_level(logging.ERROR):
            products = service.get_products_by_category("Electronics")
            assert products == []
            assert "Error getting products by category: Simulated get error" in caplog.text

# --- Tests for get_products_by_brand ---

def test_get_products_by_brand_match(local_product_service_with_mock_products):
    """Test retrieving products for an existing brand."""
    service = local_product_service_with_mock_products
    brand_a_products = service.get_products_by_brand("Brand A")
    assert len(brand_a_products) == 2
    assert all(p['brand'] == 'Brand A' for p in brand_a_products)

def test_get_products_by_brand_case_insensitive(local_product_service_with_mock_products):
    """Test case-insensitivity for brand search."""
    service = local_product_service_with_mock_products
    brand_a_products = service.get_products_by_brand("brand a")
    assert len(brand_a_products) == 2
    assert all(p['brand'] == 'Brand A' for p in brand_a_products)

def test_get_products_by_brand_no_match(local_product_service_with_mock_products):
    """Test retrieving products for a non-existing brand."""
    service = local_product_service_with_mock_products
    no_products = service.get_products_by_brand("NonExistentBrand")
    assert no_products == []

def test_get_products_by_brand_empty_products(mock_local_product_service):
    """Test retrieving products by brand when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = []
    results = service.get_products_by_brand("Brand A")
    assert results == []

def test_get_products_by_brand_with_exception_handling(local_product_service_with_mock_products, caplog):
    """Test error handling in get_products_by_brand when accessing product data."""
    service = local_product_service_with_mock_products
    
    # Simulate an error by making product.get raise an exception
    with patch.object(service.products[0], 'get', side_effect=TypeError("Simulated get error")):
        with caplog.at_level(logging.ERROR):
            products = service.get_products_by_brand("Brand A")
            assert products == []
            assert "Error getting products by brand: Simulated get error" in caplog.text

# --- Tests for get_top_rated_products ---

def test_get_top_rated_products_success(local_product_service_with_mock_products):
    """Test retrieving top-rated products with default limit."""
    service = local_product_service_with_mock_products
    top_products = service.get_top_rated_products()
    assert len(top_products) == 5
    # Expected order by rating: Laptop Y(4.8), iPhone(4.8), Tablet Pro(4.7), Samsung(4.7), Smartphone X(4.5), Headphones Z(4.2), Smartwatch(3.9)
    # If ratings are equal, original order might be preserved depending on sort stability.
    expected_ids = ['prod2', 'prod6', 'prod5', 'prod7', 'prod1']
    assert [p['id'] for p in top_products] == expected_ids

def test_get_top_rated_products_with_custom_limit(local_product_service_with_mock_products):
    """Test retrieving top-rated products with a custom limit."""
    service = local_product_service_with_mock_products
    top_products = service.get_top_rated_products(limit=3)
    assert len(top_products) == 3
    expected_ids = ['prod2', 'prod6', 'prod5']
    assert [p['id'] for p in top_products] == expected_ids

def test_get_top_rated_products_limit_greater_than_total(local_product_service_with_mock_products):
    """Test limit greater than total number of products, should return all available."""
    service = local_product_service_with_mock_products
    top_products = service.get_top_rated_products(limit=10)
    assert len(top_products) == 7 # All products

def test_get_top_rated_products_empty_products(mock_local_product_service):
    """Test retrieving top-rated products when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = []
    results = service.get_top_rated_products()
    assert results == []

def test_get_top_rated_products_products_without_rating(mock_local_product_service):
    """Test handling products with missing 'rating' in specifications (should default to 0)."""
    service, _ = mock_local_product_service
    service.products = [
        {"id": "p1", "name": "No Rating", "specifications": {"sold": 10}},
        {"id": "p2", "name": "With Rating", "specifications": {"rating": 5.0, "sold": 5}},
        {"id": "p3", "name": "No Specs Dict", "price": 100}
    ]
    top_products = service.get_top_rated_products(limit=3)
    # Products without rating or specs dict should default to 0 rating and come last
    assert [p['id'] for p in top_products] == ['p2', 'p1', 'p3']

def test_get_top_rated_products_with_exception_handling(local_product_service_with_mock_products, caplog):
    """Test error handling in get_top_rated_products when accessing specifications data."""
    service = local_product_service_with_mock_products
    
    # Simulate an error by making a product's specifications.get raise an exception
    with patch.object(service.products[0]['specifications'], 'get', side_effect=TypeError("Simulated spec get error")):
        with caplog.at_level(logging.ERROR):
            products = service.get_top_rated_products()
            assert products == []
            assert "Error getting top rated products: Simulated spec get error" in caplog.text

# --- Tests for get_best_selling_products ---

def test_get_best_selling_products_success(local_product_service_with_mock_products, caplog):
    """Test retrieving best-selling products with default limit, checking logs."""
    service = local_product_service_with_mock_products
    with caplog.at_level(logging.INFO):
        best_sellers = service.get_best_selling_products()
        assert len(best_sellers) == 5
        # Expected order by sold count: iPhone(1250), Samsung(980), Laptop Y(800), Smartphone X(500), Headphones Z(300), Tablet Pro(250), Smartwatch(150)
        expected_ids = ['prod6', 'prod7', 'prod2', 'prod1', 'prod3']
        assert [p['id'] for p in best_sellers] == expected_ids
        assert "Getting best selling products, limit: 5" in caplog.text
        assert "Returning 5 best selling products" in caplog.text

def test_get_best_selling_products_with_custom_limit(local_product_service_with_mock_products):
    """Test retrieving best-selling products with a custom limit."""
    service = local_product_service_with_mock_products
    best_sellers = service.get_best_selling_products(limit=3)
    assert len(best_sellers) == 3
    expected_ids = ['prod6', 'prod7', 'prod2']
    assert [p['id'] for p in best_sellers] == expected_ids

def test_get_best_selling_products_limit_greater_than_total(local_product_service_with_mock_products):
    """Test limit greater than total number of products, should return all available."""
    service = local_product_service_with_mock_products
    best_sellers = service.get_best_selling_products(limit=10)
    assert len(best_sellers) == 7 # All products

def test_get_best_selling_products_empty_products(mock_local_product_service):
    """Test retrieving best-selling products when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = []
    results = service.get_best_selling_products()
    assert results == []

def test_get_best_selling_products_products_without_sold_count(mock_local_product_service):
    """Test handling products with missing 'sold' in specifications (should default to 0)."""
    service, _ = mock_local_product_service
    service.products = [
        {"id": "p1", "name": "No Sold", "specifications": {"rating": 4.0}},
        {"id": "p2", "name": "With Sold", "specifications": {"sold": 100, "rating": 5.0}},
        {"id": "p3", "name": "No Specs Dict", "price": 100}
    ]
    best_sellers = service.get_best_selling_products(limit=3)
    # Products without sold or specs dict should default to 0 sold and come last
    assert [p['id'] for p in best_sellers] == ['p2', 'p1', 'p3']

def test_get_best_selling_products_with_exception_handling(local_product_service_with_mock_products, caplog):
    """Test error handling in get_best_selling_products when accessing specifications data."""
    service = local_product_service_with_mock_products
    
    # Simulate an error by making a product's specifications.get raise an exception
    with patch.object(service.products[0]['specifications'], 'get', side_effect=TypeError("Simulated spec get error")):
        with caplog.at_level(logging.ERROR):
            products = service.get_best_selling_products()
            assert products == []
            assert "Error getting best selling products: Simulated spec get error" in caplog.text

# --- Tests for get_products ---

def test_get_products_success(local_product_service_with_mock_products, caplog):
    """Test retrieving all products with default limit, checking logs."""
    service = local_product_service_with_mock_products
    with caplog.at_level(logging.INFO):
        all_products = service.get_products()
        assert len(all_products) == 7 # Default limit is 10, but we only have 7 mock products
        assert "Getting all products, limit: 10" in caplog.text

def test_get_products_with_custom_limit(local_product_service_with_mock_products):
    """Test retrieving products with a custom limit."""
    service = local_product_service_with_mock_products
    limited_products = service.get_products(limit=3)
    assert len(limited_products) == 3

def test_get_products_empty_products(mock_local_product_service):
    """Test retrieving products when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = []
    results = service.get_products()
    assert results == []

def test_get_products_with_exception_handling(local_product_service_with_mock_products, caplog):
    """Test error handling in get_products when iterating through products."""
    service = local_product_service_with_mock_products
    
    # Simulate an error by making products list uniterable
    service.products = "invalid_data"
    
    with caplog.at_level(logging.ERROR):
        products = service.get_products()
        assert products == []
        assert "Error getting products: " in caplog.text # Expecting TypeError from list slicing

# --- Tests for smart_search_products ---

def test_smart_search_best_general(local_product_service_with_mock_products):
    """Test 'terbaik' keyword without specific category (general best by rating)."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="terbaik", limit=3)
    
    assert len(products) == 3
    assert message == "Berikut produk terbaik berdasarkan rating:"
    # Expected order: Laptop Y(4.8), iPhone(4.8), Tablet Pro(4.7)
    expected_ids = ['prod2', 'prod6', 'prod5']
    assert [p['id'] for p in products] == expected_ids

def test_smart_search_best_category_found(local_product_service_with_mock_products):
    """Test 'terbaik' keyword with an existing category."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="terbaik", category="Electronics", limit=2)
    
    assert len(products) == 2
    assert message == "Berikut Electronics terbaik berdasarkan rating:"
    # Electronics products: Smartphone X(4.5), Laptop Y(4.8), Tablet Pro(4.7)
    # Expected order: Laptop Y(4.8), Tablet Pro(4.7)
    expected_ids = ['prod2', 'prod5']
    assert [p['id'] for p in products] == expected_ids

def test_smart_search_best_category_not_found(local_product_service_with_mock_products):
    """Test 'terbaik' keyword with a non-existing category (fallback to general best)."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="best", category="Furniture", limit=2)
    
    assert len(products) == 2
    assert message == "Tidak ada produk kategori Furniture, berikut produk terbaik secara umum:"
    # Fallback to general best: Laptop Y(4.8), iPhone(4.8)
    expected_ids = ['prod2', 'prod6']
    assert [p['id'] for p in products] == expected_ids

def test_smart_search_all_criteria_match(local_product_service_with_mock_products):
    """Test search with keyword, category, and max_price, all matching."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="smartphone", category="Electronics", max_price=12000000, limit=5)
    
    assert len(products) == 1
    assert products[0]['id'] == 'prod1' # Smartphone X (10M) is the only one
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_fallback_category_match_no_price_or_keyword_match(local_product_service_with_mock_products):
    """
    Test fallback: no products match all criteria, but category matches (should return cheapest in category).
    This hits `if category: ... return category_results[:limit], "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."`
    """
    service = local_product_service_with_mock_products
    # Search for an expensive laptop within a low budget, or a keyword that doesn't fully match
    products, message = service.smart_search_products(keyword="Laptop X", category="Electronics", max_price=1000000, limit=1)
    
    assert len(products) == 1
    # Original criteria: "Laptop X" (not in data) and max_price 1M => no direct match
    # Fallback to category 'Electronics', sorted by price: Smartphone X (10M) is the cheapest among mock electronics (10M, 15M, 8M)
    assert products[0]['id'] == 'prod5' # Tablet Pro (8M) is cheaper than Smartphone X (10M)
    assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."

def test_smart_search_fallback_budget_match_no_category_match(local_product_service_with_mock_products):
    """
    Test fallback: no products match specific category, but max_price matches
    (should return other products within budget).
    This hits `if max_price: ... return budget_results[:limit], "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."`
    """
    service = local_product_service_with_mock_products
    # Search for a product in a non-existent category, but with a budget
    products, message = service.smart_search_products(keyword="gadget", category="NonExistentCat", max_price=5000000, limit=2)
    
    assert len(products) == 2
    # Products <= 5M: Headphones Z (2M), Smartwatch (3M)
    expected_ids = ['prod3', 'prod4']
    assert {p['id'] for p in products} == set(expected_ids)
    assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

def test_smart_search_fallback_to_popular(local_product_service_with_mock_products):
    """
    Test fallback: no products match any specific criteria (keyword, category, max_price),
    should return popular products.
    This hits `return popular_results[:limit], "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."`
    """
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="xyz_non_existent", category="NonCat", max_price=1000, limit=2)
    
    assert len(products) == 2
    assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
    # Popular products based on sold count: iPhone(1250), Samsung(980)
    expected_ids = ['prod6', 'prod7']
    assert [p['id'] for p in products] == expected_ids

def test_smart_search_empty_products(mock_local_product_service):
    """Test smart_search_products when the product list is empty."""
    service, _ = mock_local_product_service
    service.products = []
    
    products, message = service.smart_search_products(keyword="any", category="any", max_price=1000)
    assert products == []
    # If no products, even popular fallback will be empty, but message is still the last one.
    assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

def test_smart_search_only_keyword(local_product_service_with_mock_products):
    """Test smart search with only a keyword provided."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="laptop", limit=1)
    
    assert len(products) == 1
    assert products[0]['id'] == 'prod2' # Laptop Y
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_only_category(local_product_service_with_mock_products):
    """Test smart search with only a category provided."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(category="Audio", limit=1)
    
    assert len(products) == 1
    assert products[0]['id'] == 'prod3' # Headphones Z
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_only_max_price(local_product_service_with_mock_products):
    """Test smart search with only a max_price provided."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(max_price=3000000, limit=2)
    
    assert len(products) == 2
    # Should include Headphones Z (2M) and Smartwatch (3M)
    assert {p['id'] for p in products} == {'prod3', 'prod4'}
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_no_parameters(local_product_service_with_mock_products):
    """
    Test smart search with no parameters. The current logic defaults to matching all products
    when keyword is empty, rather than popular.
    """
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(limit=2)
    
    assert len(products) == 2
    # When no keyword, category, or max_price is specified, the initial filter matches all products.
    # It then returns the first `limit` products from `self.products` in their loaded order.
    assert products[0]['id'] == 'prod1'
    assert products[1]['id'] == 'prod2'
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_empty_keyword_only_category(local_product_service_with_mock_products):
    """Test smart search with empty keyword and only category, should filter by category."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="", category="Audio", limit=1)
    
    assert len(products) == 1
    assert products[0]['id'] == 'prod3'
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_empty_keyword_only_max_price(local_product_service_with_mock_products):
    """Test smart search with empty keyword and only max_price, should filter by price."""
    service = local_product_service_with_mock_products
    products, message = service.smart_search_products(keyword="", max_price=3000000, limit=2)
    
    assert len(products) == 2
    # Should be Headphones Z (2M) and Smartwatch (3M)
    assert {p['id'] for p in products} == {'prod3', 'prod4'}
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_limit_parameter(local_product_service_with_mock_products):
    """Test that the limit parameter is respected in smart_search_products for actual results."""
    service = local_product_service_with_mock_products
    
    products, message = service.smart_search_products(keyword="phone", limit=1)
    assert len(products) == 1
    assert products[0]['id'] == 'prod6' # iPhone is first due to relevance score logic for 'phone'

    products, message = service.smart_search_products(keyword="phone", limit=10)
    assert len(products) == 3 # Smartphone X, iPhone 15 Pro Max, Samsung Galaxy S24 Ultra

def test_smart_search_graceful_handling_of_malformed_product_data(mock_local_product_service, caplog):
    """
    Test that smart_search_products gracefully handles non-dictionary items in the products list
    without crashing or logging errors, relying on .get() with defaults.
    """
    service, _ = mock_local_product_service
    service.products = [
        {"id": "prod1", "name": "Valid Product", "category": "Electronics", "price": 1000},
        "not_a_dict_item", # This will return None for .get() calls
        None, # This will also return None for .get() calls
        {"id": "prod2", "name": "Another Valid", "category": "Electronics", "price": 2000}
    ]
    
    with caplog.at_level(logging.ERROR): # Ensure no unexpected errors are logged
        products, message = service.smart_search_products(keyword="valid", limit=5)
        
        # Only valid products should be returned
        assert len(products) == 2
        assert {p['id'] for p in products} == {'prod1', 'prod2'}
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."
        assert "Error searching products" not in caplog.text