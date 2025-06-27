import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    service = LocalProductService()

    # Test case 1: Search by product name
    results_iphone = service.search_products("iPhone")
    assert len(results_iphone) >= 1
    assert any(p['name'] == "iPhone 15 Pro Max" for p in results_iphone)

    # Test case 2: Search by category
    results_smartphone = service.search_products("Smartphone")
    assert len(results_smartphone) >= 2
    assert any(p['name'] == "iPhone 15 Pro Max" for p in results_smartphone)
    assert any(p['name'] == "Samsung Galaxy S24 Ultra" for p in results_smartphone)

    # Test case 3: Search by brand
    results_apple = service.search_products("Apple")
    assert len(results_apple) >= 4
    assert any(p['brand'] == "Apple" for p in results_apple)

    # Test case 4: Search with price limit and keyword ("laptop 20 juta" -> max 20M)
    # ASUS ROG Strix G15 (18M) should be found. MacBook Pro (35M) should not be found by price.
    results_laptop_budget = service.search_products("laptop 20 juta")
    assert any(p['name'] == "ASUS ROG Strix G15" for p in results_laptop_budget)
    assert not any(p['name'] == "MacBook Pro 14 inch M3" for p in results_laptop_budget) 

    # Test case 5: Search for non-existent product
    results_non_existent = service.search_products("NonExistentProductXYZ")
    assert len(results_non_existent) == 0

    # Test case 6: Check limit parameter
    results_limited = service.search_products("Smartphone", limit=1)
    assert len(results_limited) == 1

    # Test case 7: Search with a budget keyword ("audio murah" -> max 5M)
    # AirPods Pro (4.5M) should be found. Sony WH-1000XM5 (5.5M) should NOT be found due to price filter.
    results_budget_audio = service.search_products("audio murah")
    assert any(p['name'] == "AirPods Pro 2nd Gen" for p in results_budget_audio)
    assert not any(p['name'] == "Sony WH-1000XM5" for p in results_budget_audio)
    for p in results_budget_audio:
        if p.get('category', '').lower() == 'audio':
            assert p.get('price', 0) <= 5000000
