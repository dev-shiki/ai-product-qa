import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    """
    Test basic functionality of the search_products method within LocalProductService.
    Covers keyword search, case insensitivity, limit, and price extraction.
    """
    # Instantiate the service. If 'products.json' is not found, it will use fallback products,
    # which is ideal for a deterministic unit test without complex mocking.
    service = LocalProductService()

    # Test 1: Basic keyword search (case-insensitive) for "iphone"
    # Should return iPhone 15 Pro Max and AirPods Pro 2nd Gen due to relevance.
    results_iphone = service.search_products(keyword="iphone", limit=5)
    assert len(results_iphone) == 2
    assert any(p["name"] == "iPhone 15 Pro Max" for p in results_iphone)
    assert any(p["name"] == "AirPods Pro 2nd Gen" for p in results_iphone)
    assert not any(p["name"] == "Samsung Galaxy S24 Ultra" for p in results_iphone)

    # Test 2: Search with specific category and brand keyword "Samsung smartphone"
    results_samsung_smartphone = service.search_products(keyword="Samsung smartphone", limit=1)
    assert len(results_samsung_smartphone) == 1
    assert results_samsung_smartphone[0]["name"] == "Samsung Galaxy S24 Ultra"
    assert results_samsung_smartphone[0]["category"] == "Smartphone"
    assert results_samsung_smartphone[0]["brand"] == "Samsung"

    # Test 3: Search with price limit extracted from keyword "laptop 20 juta"
    # Expected: ASUS ROG Strix G15 (18M IDR) should be returned, MacBook Pro (35M IDR) should not.
    results_budget_laptop = service.search_products(keyword="laptop 20 juta", limit=5)
    assert len(results_budget_laptop) == 1
    assert results_budget_laptop[0]["name"] == "ASUS ROG Strix G15"
    assert results_budget_laptop[0]["price"] <= 20000000
    assert not any(p["name"] == "MacBook Pro 14 inch M3" for p in results_budget_laptop)

    # Test 4: Search with a keyword that yields no results
    results_no_match = service.search_products(keyword="nonexistentproductxyz123", limit=10)
    assert len(results_no_match) == 0

    # Test 5: Search with 'murah' keyword (triggers specific max_price of 5M IDR)
    # Expected: AirPods Pro 2nd Gen (4.5M IDR) as it's the only fallback product <= 5M.
    results_murah = service.search_products(keyword="murah", limit=5)
    assert len(results_murah) == 1
    assert results_murah[0]["name"] == "AirPods Pro 2nd Gen"
    assert results_murah[0]["price"] <= 5000000

    # Test 6: Verify limit functionality with an empty keyword (should return top 'limit' products)
    results_all_products_limited = service.search_products(keyword="", limit=3)
    assert len(results_all_products_limited) == 3
    # Ensure returned items are dictionaries representing products
    assert all(isinstance(p, dict) for p in results_all_products_limited)
    # Check for presence of expected first few products based on default relevance/loading order
    assert any(p["name"] == "iPhone 15 Pro Max" for p in results_all_products_limited)
    assert any(p["name"] == "Samsung Galaxy S24 Ultra" for p in results_all_products_limited)
