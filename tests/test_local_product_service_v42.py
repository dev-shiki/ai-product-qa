import pytest
from app.services.local_product_service import search_products

from app.services.local_product_service import LocalProductService

def test_search_products_basic():
    """
    Test basic functionality of the search_products method.
    This test verifies keyword search, case insensitivity, application of limits,
    handling of non-existent keywords, and basic price-based filtering.
    It relies on LocalProductService initializing its product list, which
    will likely use the internal fallback products during typical test runs
    if 'data/products.json' is not found in the expected relative path.
    """
    service = LocalProductService()

    # Test 1: Basic keyword search - expect specific products based on the keyword
    results_apple = service.search_products("Apple")
    assert len(results_apple) > 0
    assert any(p.get("name") == "iPhone 15 Pro Max" for p in results_apple), "iPhone should be found by 'Apple' keyword"
    assert any(p.get("name") == "MacBook Pro 14 inch M3" for p in results_apple), "MacBook Pro should be found by 'Apple' keyword"

    # Test 2: Case insensitivity - searching for "samsung" (lowercase)
    results_samsung_lower = service.search_products("samsung")
    assert len(results_samsung_lower) > 0
    assert any(p.get("name") == "Samsung Galaxy S24 Ultra" for p in results_samsung_lower), "Samsung S24 Ultra should be found by 'samsung'"
    assert any(p.get("name") == "Samsung Galaxy Tab S9" for p in results_samsung_lower), "Samsung Tab S9 should be found by 'samsung'"

    # Test 3: Limit functionality - requesting only one product
    results_limited = service.search_products("smartphone", limit=1)
    assert len(results_limited) == 1, "Should return exactly one product when limit is 1"
    # Verify the returned product is relevant (e.g., a smartphone)
    assert "Smartphone" in results_limited[0].get("category", "") or "smartphone" in results_limited[0].get("name", "").lower(), \
        "The single returned product should be a smartphone or related"

    # Test 4: Search for a non-existent keyword - expecting an empty list
    results_non_existent = service.search_products("nonexistentproductxyz_abc_123")
    assert len(results_non_existent) == 0, "Should return an empty list for a non-existent keyword"

    # Test 5: Search with a price-related keyword (e.g., "murah")
    # "murah" maps to a max price of 5,000,000 IDR in _extract_price_from_keyword
    results_cheap_audio = service.search_products("audio murah")
    assert len(results_cheap_audio) > 0, "Should find products for 'audio murah'"
    # The cheapest audio product from fallback is AirPods Pro 2nd Gen (4,500,000 IDR)
    assert any(p.get("name") == "AirPods Pro 2nd Gen" for p in results_cheap_audio), "AirPods Pro should be found for 'audio murah'"
    # Verify that the top result is within the "cheap" range, due to relevance scoring for price
    assert results_cheap_audio[0].get('price', float('inf')) <= 5000000, \
        "The top result for 'audio murah' should be priced <= 5,000,000"

    # Test 6: Empty keyword search - should return a default number of products (or all if fewer)
    # The fallback list has 8 products, default limit for search_products is 10. So it should return all 8.
    results_all = service.search_products("")
    assert len(results_all) == 8, "Empty keyword should return all available products up to the default limit (10)"

    # Test 7: Empty keyword with a specific limit
    results_all_limited = service.search_products("", limit=3)
    assert len(results_all_limited) == 3, "Empty keyword with limit should return specified number of products"
