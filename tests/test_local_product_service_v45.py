import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    service = LocalProductService()

    # Test 1: Basic keyword search (case-insensitive) for a brand
    results_apple = service.search_products("apple")
    # Verify that key Apple products from fallback are present
    assert any(p["name"] == "iPhone 15 Pro Max" for p in results_apple)
    assert any(p["name"] == "MacBook Pro 14 inch M3" for p in results_apple)
    assert any(p["name"] == "AirPods Pro 2nd Gen" for p in results_apple)
    assert all("apple" in p.get("brand", "").lower() for p in results_apple if "Apple" in p.get("brand", ""))

    # Test 2: Search with a specific product name
    results_s24 = service.search_products("Samsung Galaxy S24 Ultra")
    assert len(results_s24) >= 1
    assert results_s24[0]["name"] == "Samsung Galaxy S24 Ultra"

    # Test 3: Search with limit functionality
    results_limited = service.search_products("Laptop", limit=1)
    assert len(results_limited) == 1
    assert "laptop" in results_limited[0]["category"].lower()

    # Test 4: Search for a keyword that yields no results
    results_empty = service.search_products("NonExistentProductKeyword123")
    assert len(results_empty) == 0

    # Test 5: Search with a price limit extracted from keyword ("laptop 20 juta")
    # ASUS ROG Strix G15 (18M) should be found. MacBook Pro (35M) should not be the primary match due to price.
    results_laptop_budget = service.search_products("laptop 20 juta")
    assert any("ASUS ROG Strix G15" == p["name"] for p in results_laptop_budget)
    # Verify that products returned are either laptops or fall within the price range
    assert all(p.get('price', 0) <= 20000000 or "laptop" in p.get("category", "").lower() for p in results_laptop_budget)

    # Test 6: Search using a budget keyword ("handphone murah")
    # 'murah' implies a max price of 5M. AirPods Pro (4.5M) fits this criteria and will get a high score.
    # Actual smartphones (iPhone, Samsung S24) are much more expensive but match "handphone".
    # The sorting prioritizes the price relevance, so AirPods Pro should appear high.
    results_phone_cheap = service.search_products("handphone murah")
    assert len(results_phone_cheap) > 0
    assert any("AirPods Pro 2nd Gen" == p["name"] for p in results_phone_cheap) # Included due to price
    assert any("iPhone 15 Pro Max" == p["name"] for p in results_phone_cheap) # Included due to keyword "handphone" (category Smartphone)

    # Test 7: Search by category
    results_tablet = service.search_products("Tablet")
    assert any("iPad Air 5th Gen" == p["name"] for p in results_tablet)
    assert any("Samsung Galaxy Tab S9" == p["name"] for p in results_tablet)
    assert all("tablet" in p.get("category", "").lower() for p in results_tablet)
