import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Instantiate the service. This will load either from products.json or fallback products.
    # For a stable test, we rely on the hardcoded fallback products within the service.
    service = LocalProductService()

    # Test 1: Basic search by a keyword found in product name (case-insensitive)
    results_iphone = service.search_products("iphone")
    assert len(results_iphone) > 0
    # Expecting "iPhone 15 Pro Max" to be among the results
    assert any(p['name'] == "iPhone 15 Pro Max" for p in results_iphone)

    # Test 2: Search by a keyword found in brand (case-insensitive)
    results_samsung = service.search_products("samsung")
    assert len(results_samsung) >= 2  # Expecting Samsung Galaxy S24 Ultra and Samsung Galaxy Tab S9
    assert all("samsung" in p['brand'].lower() for p in results_samsung)

    # Test 3: Test the 'limit' parameter
    results_apple_limited = service.search_products("apple", limit=2)
    assert len(results_apple_limited) <= 2
    # Ensure all returned products are related to Apple (brand or name)
    assert all("apple" in p['brand'].lower() or "apple" in p['name'].lower() for p in results_apple_limited)

    # Test 4: Search for a keyword that should yield no results
    results_no_match = service.search_products("nonexistentproducttype123")
    assert len(results_no_match) == 0

    # Test 5: Search with a price-related keyword ("murah") and category
    # This tests if the relevance scoring for price influences the order.
    # Fallback products relevant to "audio murah": AirPods Pro (4.5M) and Sony WH-1000XM5 (5.5M).
    # AirPods should be prioritized due to lower price and category match.
    results_audio_budget = service.search_products("audio murah")
    assert len(results_audio_budget) >= 2
    assert results_audio_budget[0]['name'] == "AirPods Pro 2nd Gen"
    assert results_audio_budget[1]['name'] == "Sony WH-1000XM5"

    # Test 6: Search with a specific price range in keyword, e.g., "laptop 20 juta"
    # Expecting ASUS ROG Strix G15 (18M) to be found, as it's a laptop within this implicit budget.
    results_laptop_price = service.search_products("laptop 20 juta")
    assert len(results_laptop_price) > 0
    assert any(p['name'] == "ASUS ROG Strix G15" for p in results_laptop_price)
    # Ensure that expensive laptops like MacBook Pro (35M) are not included if the price filter was strict,
    # or that the cheaper one is prioritized due to the price relevance scoring.
    # For this simple test, we just confirm the relevant product under budget is found.
    assert not any(p['name'] == "MacBook Pro 14 inch M3" and p['price'] > 20000000 for p in results_laptop_price)
