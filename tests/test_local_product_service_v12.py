import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # As 'search_products' is a method of LocalProductService,
    # we need to instantiate the class. This assumes LocalProductService
    # is available in the test scope (e.g., imported in the test file or conftest.py).
    service = LocalProductService()

    # Test 1: Basic keyword search for "iPhone"
    results_iphone = service.search_products("iPhone")
    assert len(results_iphone) > 0, "Should find products for 'iPhone' keyword"
    # Check if a specific expected iPhone product is found
    assert any("iPhone 15 Pro Max" in p.get('name', '') for p in results_iphone), \
        "iPhone 15 Pro Max should be found in results for 'iPhone'"

    # Test 2: Case insensitivity - searching for "samsung"
    results_samsung_lower = service.search_products("samsung")
    assert len(results_samsung_lower) > 0, "Should find products for 'samsung' (case-insensitive)"
    assert any("Samsung Galaxy S24 Ultra" in p.get('name', '') for p in results_samsung_lower), \
        "Samsung Galaxy S24 Ultra should be found in results for 'samsung'"

    # Test 3: Limit functionality - search for "Apple" with a limit of 2
    results_limited = service.search_products("Apple", limit=2)
    assert len(results_limited) <= 2, "Should return at most 2 products when limit is 2"
    # Ensure that the limited results are indeed Apple-related products
    assert all("Apple" in p.get('brand', '') or "iPhone" in p.get('name', '') or "MacBook" in p.get('name', '') for p in results_limited), \
        "Limited results should still be relevant to 'Apple'"

    # Test 4: No matching products for a non-existent keyword
    results_no_match = service.search_products("XYZNonExistentProduct")
    assert len(results_no_match) == 0, "Should return an empty list for a non-existent keyword"

    # Test 5: Search with price-related keyword ("murah")
    # This checks if _extract_price_from_keyword and price filtering/scoring work.
    # In fallback products, "AirPods Pro 2nd Gen" (4.5M) is the only one under 5M (the 'murah' threshold).
    results_cheap = service.search_products("produk murah")
    assert len(results_cheap) > 0, "Should find products for 'produk murah' keyword"
    assert any(p.get('id') == "4" for p in results_cheap), \
        "AirPods Pro (ID 4, price 4.5M) should be found when searching for 'produk murah'"

    # Test 6: Empty keyword - should return all available products up to the default limit (10)
    # (Assuming fallback products, there are 8, so all 8 should be returned)
    results_empty_keyword = service.search_products("")
    assert len(results_empty_keyword) == 8, "Should return all available products when keyword is empty"
