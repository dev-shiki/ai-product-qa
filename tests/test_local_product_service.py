from app.services.local_product_service import LocalProductService
import pytest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

@pytest.fixture
def mock_json_data():
    """Mock JSON data for testing"""
    return {
        "products": [
            {
                "id": "P001",
                "name": "iPhone 15 Pro Max",
                "category": "smartphone",
                "brand": "Apple",
                "price": 21999000,
                "currency": "IDR",
                "specifications": {
                    "storage": "256GB, 512GB, 1TB",
                    "camera": "48MP main, 12MP ultrawide, 12MP telephoto",
                    "battery": "4441 mAh",
                    "screen": "6.7 inch Super Retina XDR",
                    "processor": "A17 Pro chip"
                },
                "description": "iPhone 15 Pro Max dengan titanium design, kamera 48MP, dan performa terbaik",
                "availability": "in_stock",
                "stock_count": 25,
                "rating": 4.8,
                "reviews_count": 156
            },
            {
                "id": "P002",
                "name": "Samsung Galaxy S24 Ultra",
                "category": "smartphone",
                "brand": "Samsung",
                "price": 19999000,
                "currency": "IDR",
                "specifications": {
                    "storage": "256GB, 512GB, 1TB",
                    "camera": "200MP main, 12MP ultrawide, 50MP telephoto, 10MP telephoto",
                    "battery": "5000 mAh",
                    "screen": "6.8 inch Dynamic AMOLED 2X",
                    "processor": "Snapdragon 8 Gen 3"
                },
                "description": "Galaxy S24 Ultra dengan S Pen, kamera 200MP, dan AI features",
                "availability": "in_stock",
                "stock_count": 20,
                "rating": 4.8,
                "reviews_count": 134
            },
            {
                "id": "P003",
                "name": "MacBook Pro 14-inch M3",
                "category": "laptop",
                "brand": "Apple",
                "price": 29999000,
                "currency": "IDR",
                "specifications": {
                    "storage": "512GB, 1TB, 2TB",
                    "memory": "8GB, 16GB, 24GB unified memory",
                    "battery": "70Wh",
                    "screen": "14.2 inch Liquid Retina XDR",
                    "processor": "Apple M3 chip"
                },
                "description": "MacBook Pro 14-inch dengan chip M3 untuk produktivitas tinggi",
                "availability": "in_stock",
                "stock_count": 25,
                "rating": 4.8,
                "reviews_count": 156
            }
        ]
    }

@pytest.fixture
def service_with_mock_data(mock_json_data):
    """Create service with mock JSON data"""
    with patch('builtins.open', create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_json_data)
        with patch('pathlib.Path.exists', return_value=True):
            service = LocalProductService()
            return service

def test_local_product_service_init():
    """Test LocalProductService initialization"""
    with patch('builtins.open', create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = '{"products": []}'
        with patch('pathlib.Path.exists', return_value=True):
            service = LocalProductService()
            assert service is not None
            assert hasattr(service, 'products')

def test_local_product_service_init_with_fallback():
    """Test LocalProductService initialization with fallback data"""
    with patch('pathlib.Path.exists', return_value=False):
        service = LocalProductService()
        assert service is not None
        assert len(service.products) > 0

def test_search_products(service_with_mock_data):
    """Test product search functionality"""
    result = service_with_mock_data.search_products("iPhone", 5)
    
    assert len(result) > 0
    assert any("iPhone" in product["name"] for product in result)

def test_search_products_no_match(service_with_mock_data):
    """Test product search with no matches"""
    result = service_with_mock_data.search_products("nonexistent", 5)
    
    assert len(result) == 0

def test_search_products_empty_keyword(service_with_mock_data):
    """Test product search with empty keyword"""
    result = service_with_mock_data.search_products("", 5)
    
    assert len(result) > 0

def test_get_product_details(service_with_mock_data):
    """Test getting product details by ID"""
    result = service_with_mock_data.get_product_details("P001")
    
    assert result is not None
    assert result["name"] == "iPhone 15 Pro Max"

def test_get_product_details_not_found(service_with_mock_data):
    """Test getting product details for non-existent ID"""
    result = service_with_mock_data.get_product_details("999")
    
    assert result is None

def test_get_categories(service_with_mock_data):
    """Test getting product categories"""
    result = service_with_mock_data.get_categories()
    
    assert len(result) > 0
    assert "smartphone" in result
    assert "laptop" in result

def test_get_brands(service_with_mock_data):
    """Test getting product brands"""
    result = service_with_mock_data.get_brands()
    
    assert len(result) > 0
    assert "Apple" in result
    assert "Samsung" in result

def test_get_products_by_category(service_with_mock_data):
    """Test getting products by category"""
    result = service_with_mock_data.get_products_by_category("smartphone")
    
    assert len(result) > 0
    assert all(product["category"] == "smartphone" for product in result)

def test_get_products_by_category_not_found(service_with_mock_data):
    """Test getting products by non-existent category"""
    result = service_with_mock_data.get_products_by_category("nonexistent")
    
    assert len(result) == 0

def test_get_products_by_brand(service_with_mock_data):
    """Test getting products by brand"""
    result = service_with_mock_data.get_products_by_brand("Apple")
    
    assert len(result) > 0
    assert all(product["brand"] == "Apple" for product in result)

def test_get_products_by_brand_not_found(service_with_mock_data):
    """Test getting products by non-existent brand"""
    result = service_with_mock_data.get_products_by_brand("nonexistent")
    
    assert len(result) == 0

def test_get_top_rated_products(service_with_mock_data):
    """Test getting top rated products"""
    result = service_with_mock_data.get_top_rated_products(3)
    
    assert len(result) > 0
    assert len(result) <= 3
    # Check if products are sorted by rating (descending)
    ratings = [product.get("specifications", {}).get("rating", 0) for product in result]
    assert ratings == sorted(ratings, reverse=True)

def test_get_best_selling_products(service_with_mock_data):
    """Test getting best selling products"""
    result = service_with_mock_data.get_best_selling_products(3)
    
    assert len(result) > 0
    assert len(result) <= 3

def test_get_products(service_with_mock_data):
    """Test getting all products with limit"""
    result = service_with_mock_data.get_products(5)
    
    assert len(result) > 0
    assert len(result) <= 5

def test_get_products_with_large_limit(service_with_mock_data):
    """Test getting products with large limit"""
    result = service_with_mock_data.get_products(100)
    
    assert len(result) > 0
    assert len(result) <= 100

def test_search_products_with_relevance(service_with_mock_data):
    """Test product search with relevance scoring"""
    result = service_with_mock_data.search_products("MacBook", 5)
    
    assert len(result) > 0
    # MacBook should be in the results
    assert any("MacBook" in product["name"] for product in result)

def test_search_products_case_insensitive(service_with_mock_data):
    """Test product search is case insensitive"""
    result = service_with_mock_data.search_products("iphone", 5)
    
    assert len(result) > 0
    assert any("iPhone" in product["name"] for product in result)

def test_search_products_in_description(service_with_mock_data):
    """Test product search in description"""
    result = service_with_mock_data.search_products("titanium", 5)
    
    assert len(result) > 0
    assert any("titanium" in product["description"].lower() for product in result)

def test_search_products_in_specifications(service_with_mock_data):
    """Test product search in specifications"""
    result = service_with_mock_data.search_products("A17", 5)
    
    assert len(result) > 0
    assert any("A17" in str(product.get("specifications", {})) for product in result)

def test_smart_search_products_best_request():
    """Test smart_search_products with 'terbaik' keyword"""
    service = LocalProductService()
    
    # Test "terbaik" without category
    products, message = service.smart_search_products(keyword="produk terbaik", limit=3)
    assert len(products) > 0
    assert "terbaik" in message.lower()
    assert "rating" in message.lower()
    
    # Test "terbaik" with category
    products, message = service.smart_search_products(keyword="laptop terbaik", category="laptop", limit=3)
    assert len(products) > 0
    assert "laptop" in message.lower()
    assert "terbaik" in message.lower()

def test_smart_search_products_best_request_no_category():
    """Test smart_search_products with 'terbaik' but category not found"""
    service = LocalProductService()
    
    products, message = service.smart_search_products(keyword="nonexistent terbaik", category="nonexistent", limit=3)
    assert len(products) > 0
    assert "nonexistent" in message.lower()
    assert "umum" in message.lower()

def test_smart_search_products_exact_match():
    """Test smart_search_products with exact criteria match"""
    service = LocalProductService()
    
    products, message = service.smart_search_products(keyword="iPhone", category="smartphone", limit=3)
    assert len(products) > 0
    assert "sesuai dengan kriteria" in message

def test_smart_search_products_category_fallback():
    """Test smart_search_products category fallback"""
    service = LocalProductService()
    
    products, message = service.smart_search_products(keyword="laptop mahal", category="laptop", max_price=1000000, limit=3)
    assert len(products) > 0
    assert "termurah" in message.lower()

def test_smart_search_products_budget_fallback():
    """Test smart_search_products budget fallback"""
    service = LocalProductService()
    
    # Test dengan kategori yang ada tapi budget terlalu rendah
    products, message = service.smart_search_products(keyword="smartphone murah", category="smartphone", max_price=1000000, limit=3)
    assert len(products) > 0
    assert "termurah" in message.lower()  # Fallback ke kategori termurah
    
    # Test dengan kategori tidak ada tapi ada produk di bawah budget
    products, message = service.smart_search_products(keyword="produk murah", category="nonexistent", max_price=5000000, limit=3)
    assert len(products) > 0
    assert "sesuai budget" in message.lower()  # Fallback ke produk sesuai budget

def test_smart_search_products_popular_fallback():
    """Test smart_search_products popular fallback"""
    service = LocalProductService()
    
    products, message = service.smart_search_products(keyword="produk tidak ada", category="nonexistent", max_price=100, limit=3)
    assert len(products) > 0
    assert "terpopuler" in message.lower()

def test_extract_price_from_keyword():
    """Test _extract_price_from_keyword method"""
    service = LocalProductService()
    
    # Test "5 juta"
    max_price = service._extract_price_from_keyword("laptop 5 juta")
    assert max_price == 5000000
    
    # Test "budget"
    max_price = service._extract_price_from_keyword("laptop budget")
    assert max_price == 5000000
    
    # Test "murah"
    max_price = service._extract_price_from_keyword("laptop murah")
    assert max_price == 5000000
    
    # Test "hemat"
    max_price = service._extract_price_from_keyword("laptop hemat")
    assert max_price == 3000000
    
    # Test no price
    max_price = service._extract_price_from_keyword("laptop biasa")
    assert max_price is None

def test_search_products_with_price_extraction():
    """Test search_products with price extraction"""
    service = LocalProductService()
    
    # Test with budget keyword
    products = service.search_products("laptop budget 3 juta", limit=5)
    assert len(products) > 0
    
    # Test with "murah" keyword
    products = service.search_products("smartphone murah", limit=5)
    assert len(products) > 0 