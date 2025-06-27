import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    service = LocalProductService()

    # Test 1: Basic keyword search for a common brand
    results_apple = service.search_products("Apple")
    assert len(results_apple) >= 4  # Expecting at least iPhone, MacBook, AirPods, iPad
    apple_product_names = [p['name'] for p in results_apple]
    assert "iPhone 15 Pro Max" in apple_product_names
    assert "MacBook Pro 14 inch M3" in apple_product_names
    assert "AirPods Pro 2nd Gen" in apple_product_names
    assert "iPad Air 5th Gen" in apple_product_names

    # Test 2: Search for a specific product name
    results_s24_ultra = service.search_products("Galaxy S24 Ultra")
    assert len(results_s24_ultra) >= 1
    assert results_s24_ultra[0]['name'] == "Samsung Galaxy S24 Ultra"

    # Test 3: Search with a limit
    results_limited = service.search_products("Samsung", limit=1)
    assert len(results_limited) == 1
    assert results_limited[0]['brand'] == "Samsung"

    # Test 4: Search for a non-existent keyword
    results_none = service.search_products("nonexistentproductxyz")
    assert len(results_none) == 0

    # Test 5: Search with price filtering (e.g., "laptop 20 juta")
    # This should include ASUS ROG Strix G15 (18M) but exclude MacBook Pro (35M)
    results_laptop_budget = service.search_products("laptop 20 juta")
    assert any(p['name'] == "ASUS ROG Strix G15" for p in results_laptop_budget)
    assert not any(p['name'] == "MacBook Pro 14 inch M3" for p in results_laptop_budget)

    # Test 6: Search using a "budget" keyword (e.g., "audio murah" -> max_price 5M)
    # AirPods Pro (4.5M) should be included, Sony WH-1000XM5 (5.5M) should not be filtered by price
    results_audio_cheap = service.search_products("audio murah")
    assert any(p['name'] == "AirPods Pro 2nd Gen" for p in results_audio_cheap)
    assert not any(p['name'] == "Sony WH-1000XM5" and p['price'] > 5000000 for p in results_audio_cheap)
