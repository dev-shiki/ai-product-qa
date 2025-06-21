from app.services.local_product_service import LocalProductService
import pytest

def test_local_product_service_init():
    service = LocalProductService()
    assert service is not None

def test_local_product_service_methods():
    service = LocalProductService()
    # Test all public methods with dummy args
    assert hasattr(service, "get_products")
    assert hasattr(service, "get_categories")
    assert hasattr(service, "search_products")
    assert hasattr(service, "get_top_rated_products")
    assert hasattr(service, "get_best_selling_products")

def test_search_products():
    service = LocalProductService()
    result = service.search_products("iPhone", 5)
    
    assert len(result) > 0
    assert any("iPhone" in product["name"] for product in result)

def test_search_products_no_match():
    service = LocalProductService()
    result = service.search_products("nonexistent", 5)
    
    assert len(result) == 0

def test_search_products_empty_keyword():
    service = LocalProductService()
    result = service.search_products("", 5)
    
    assert len(result) > 0

def test_get_product_details():
    service = LocalProductService()
    result = service.get_product_details("1")
    
    assert result is not None
    assert result["name"] == "iPhone 15 Pro Max"

def test_get_product_details_not_found():
    service = LocalProductService()
    result = service.get_product_details("999")
    
    assert result is None

def test_get_categories():
    service = LocalProductService()
    result = service.get_categories()
    
    assert len(result) > 0
    assert "Smartphone" in result
    assert "Laptop" in result

def test_get_brands():
    service = LocalProductService()
    result = service.get_brands()
    
    assert len(result) > 0
    assert "Apple" in result
    assert "Samsung" in result

def test_get_products_by_category():
    service = LocalProductService()
    result = service.get_products_by_category("Smartphone")
    
    assert len(result) > 0
    assert all(product["category"] == "Smartphone" for product in result)

def test_get_products_by_category_not_found():
    service = LocalProductService()
    result = service.get_products_by_category("nonexistent")
    
    assert len(result) == 0

def test_get_products_by_brand():
    service = LocalProductService()
    result = service.get_products_by_brand("Apple")
    
    assert len(result) > 0
    assert all(product["brand"] == "Apple" for product in result)

def test_get_products_by_brand_not_found():
    service = LocalProductService()
    result = service.get_products_by_brand("nonexistent")
    
    assert len(result) == 0

def test_get_top_rated_products():
    service = LocalProductService()
    result = service.get_top_rated_products(3)
    
    assert len(result) > 0
    assert len(result) <= 3

def test_get_best_selling_products():
    service = LocalProductService()
    result = service.get_best_selling_products(3)
    
    assert len(result) > 0
    assert len(result) <= 3

def test_get_products():
    service = LocalProductService()
    result = service.get_products(5)
    
    assert len(result) > 0
    assert len(result) <= 5

def test_get_products_with_large_limit():
    service = LocalProductService()
    result = service.get_products(100)
    
    assert len(result) > 0
    assert len(result) <= 100

def test_search_products_with_relevance():
    service = LocalProductService()
    result = service.search_products("MacBook", 5)
    
    assert len(result) > 0
    # MacBook should be in the results
    assert any("MacBook" in product["name"] for product in result)

def test_search_products_case_insensitive():
    service = LocalProductService()
    result = service.search_products("iphone", 5)
    
    assert len(result) > 0
    assert any("iPhone" in product["name"] for product in result) 