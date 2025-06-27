import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    service = LocalProductService()

    # Test 1: Basic keyword search for a product name
    results_iphone = service.search_products("iPhone")
    assert len(results_iphone) >= 1
    assert any("iPhone 15 Pro Max" == p.get("name") for p in results_iphone)

    # Test 2: Keyword search for a category
    results_smartphone = service.search_products("Smartphone")
    assert len(results_smartphone) >= 2
    assert any("Smartphone" == p.get("category") for p in results_smartphone)

    # Test 3: Keyword search with limit parameter
    results_limited_apple = service.search_products("Apple", limit=2)
    assert len(results_limited_apple) <= 2
    assert all("Apple" == p.get("brand") for p in results_limited_apple)

    # Test 4: Keyword search with price extraction (e.g., "laptop 20 juta")
    results_budget_laptop = service.search_products("laptop 20 juta")
    assert any("ASUS ROG Strix G15" == p.get("name") for p in results_budget_laptop)
    # Verify products are within the price range (20,000,000 IDR) and are laptops
    for p in results_budget_laptop:
        if "laptop" in p.get("category", "").lower():
            assert p.get("price", 0) <= 20000000

    # Test 5: Search with a budget keyword ("murah")
    results_cheap_phone = service.search_products("hp murah")
    # Expecting products under 5,000,000 IDR based on _extract_price_from_keyword logic for 'murah'
    assert any(p.get("price", 0) <= 5000000 for p in results_cheap_phone)
    assert any("AirPods Pro 2nd Gen" == p.get("name") for p in results_cheap_phone)

    # Test 6: Search with a non-existent keyword
    results_no_match = service.search_products("xyz_nonexistent_product")
    assert len(results_no_match) == 0

    # Test 7: Search with an empty keyword (should return default limit of products)
    results_empty_keyword = service.search_products("")
    assert len(results_empty_keyword) > 0
    assert len(results_empty_keyword) <= 10 # Default limit is 10
