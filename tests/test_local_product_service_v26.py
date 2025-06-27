import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    service = LocalProductService()

    # Test 1: Basic keyword search (case-insensitive)
    results_iphone = service.search_products("iPhone")
    assert len(results_iphone) > 0
    assert any(p['id'] == '1' for p in results_iphone) # iPhone 15 Pro Max
    assert all("iphone" in p['name'].lower() or "apple" in p['brand'].lower() for p in results_iphone)

    # Test 2: Search by category
    results_laptop = service.search_products("Laptop")
    assert len(results_laptop) > 0
    assert any(p['id'] == '3' for p in results_laptop) # MacBook Pro 14 inch M3
    assert any(p['id'] == '6' for p in results_laptop) # ASUS ROG Strix G15
    assert all("laptop" in p['category'].lower() for p in results_laptop)

    # Test 3: Search with limit
    results_limited = service.search_products("Apple", limit=2)
    assert len(results_limited) <= 2
    assert all("apple" in p['brand'].lower() or "apple" in p['name'].lower() for p in results_limited)

    # Test 4: Search for non-existent product
    results_non_existent = service.search_products("xyz_non_existent_product_123")
    assert len(results_non_existent) == 0

    # Test 5: Search with price hint in keyword (e.g., "laptop 20 juta")
    # ASUS ROG Strix G15 (18M) should match via price or text.
    # MacBook Pro (35M) should match via text ("laptop").
    results_price_keyword = service.search_products("laptop 20 juta")
    assert any(p['id'] == '6' for p in results_price_keyword)
    assert any(p['id'] == '3' for p in results_price_keyword)

    # Test 6: Search with a budget keyword (e.g., "murah")
    # "murah" maps to 5,000,000 max price. AirPods Pro (4.5M) should be found.
    results_budget = service.search_products("audio murah")
    assert any(p['id'] == '4' for p in results_budget) # AirPods Pro 2nd Gen
    assert any(p['id'] == '7' for p in results_budget) # Sony WH-1000XM5 (might be included due to text match and relevance score)

    # Test 7: Empty keyword (should return all products up to limit)
    results_all = service.search_products("", limit=3)
    assert len(results_all) == 3
    assert all(isinstance(p, dict) for p in results_all) # Ensure results are products
