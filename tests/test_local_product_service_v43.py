import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Instantiate the service. This will load products from fallback if products.json is not found.
    service = LocalProductService()

    # Test 1: Basic keyword search (e.g., "iPhone")
    results_iphone = service.search_products("iPhone")
    assert len(results_iphone) >= 1
    assert any("iPhone 15 Pro Max" == p["name"] for p in results_iphone)

    # Test 2: Case-insensitivity (e.g., "iphone")
    results_iphone_lower = service.search_products("iphone")
    assert len(results_iphone_lower) >= 1
    assert any("iPhone 15 Pro Max" == p["name"] for p in results_iphone_lower)

    # Test 3: Search with limit for a common brand like "Apple"
    results_apple_limited = service.search_products("Apple", limit=2)
    assert len(results_apple_limited) <= 2
    # Ensure all products returned are related to "Apple" (could be brand or name)
    assert all("apple" in p.get("brand", "").lower() or "apple" in p.get("name", "").lower() for p in results_apple_limited)


    # Test 4: Search for a non-existent product
    results_non_existent = service.search_products("NonExistentGadget")
    assert len(results_non_existent) == 0

    # Test 5: Search with price filter (e.g., "Laptop 20 juta")
    # Expected: ASUS ROG Strix G15 (18M IDR) should be included, MacBook Pro (35M IDR) should not.
    results_laptop_budget = service.search_products("Laptop 20 juta")
    assert any("ASUS ROG Strix G15" == p["name"] for p in results_laptop_budget)
    assert not any("MacBook Pro 14 inch M3" == p["name"] for p in results_laptop_budget)
    
    # Test 6: Search with a budget keyword where a product matches
    # AirPods Pro 2nd Gen is 4.5M IDR. "murah" keyword implies max_price 5M IDR.
    results_airpods_murah = service.search_products("AirPods murah")
    assert any("AirPods Pro 2nd Gen" == p["name"] for p in results_airpods_murah)
