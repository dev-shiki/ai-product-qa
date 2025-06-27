import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    service = LocalProductService()

    # Test 1: Basic keyword search (case-insensitive for 'iPhone')
    results_iphone = service.search_products("iPhone")
    assert len(results_iphone) >= 1
    assert any("iPhone 15 Pro Max" == p['name'] for p in results_iphone)

    # Test 2: Case-insensitive search for a brand leading to multiple results
    results_samsung = service.search_products("samsung")
    assert len(results_samsung) >= 2
    assert any("Samsung Galaxy S24 Ultra" == p['name'] for p in results_samsung)
    assert any("Samsung Galaxy Tab S9" == p['name'] for p in results_samsung)

    # Test 3: Search for a category (should return relevant items)
    results_laptop = service.search_products("Laptop")
    assert len(results_laptop) >= 2
    assert any("MacBook Pro 14 inch M3" == p['name'] for p in results_laptop)
    assert any("ASUS ROG Strix G15" == p['name'] for p in results_laptop)

    # Test 4: Search with a specific limit
    results_apple_limited = service.search_products("Apple", limit=2)
    assert len(results_apple_limited) == 2
    for p in results_apple_limited:
        assert p['brand'] == 'Apple'

    # Test 5: Search with a budget keyword ("murah" implies max price ~5M IDR)
    results_murah = service.search_products("murah")
    assert len(results_murah) >= 1
    assert any(p['name'] == "AirPods Pro 2nd Gen" for p in results_murah)
    
    # Test 6: Search for an non-existent keyword
    results_nonexistent = service.search_products("nonexistent_product_xyz")
    assert len(results_nonexistent) == 0

    # Test 7: Empty keyword search (should return all available products up to default limit)
    results_empty_keyword = service.search_products("")
    assert len(results_empty_keyword) == 8 
    assert "iPhone 15 Pro Max" in [p['name'] for p in results_empty_keyword]
    assert "Sony WH-1000XM5" in [p['name'] for p in results_empty_keyword]
