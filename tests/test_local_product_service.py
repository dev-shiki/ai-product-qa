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