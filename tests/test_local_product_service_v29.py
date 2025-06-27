import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    from app.services.local_product_service import LocalProductService

    # Initialize the service. This will load products (either from file or fallback data).
    service = LocalProductService()

    # Test Case 1: Basic keyword search (case-insensitive)
    results_apple_phone = service.search_products("iPhone")
    assert len(results_apple_phone) > 0, "Should find iPhone products"
    assert any("iPhone 15 Pro Max" == p['name'] for p in results_apple_phone), "Expected 'iPhone 15 Pro Max' in results"

    # Test Case 2: Case-insensitivity (should yield same results as above)
    results_apple_phone_lower = service.search_products("iphone")
    assert len(results_apple_phone_lower) == len(results_apple_phone), "Case-insensitive search should return same number of results"
    assert any("iPhone 15 Pro Max" == p['name'] for p in results_apple_phone_lower), "Expected 'iPhone 15 Pro Max' with lowercase keyword"

    # Test Case 3: Limit parameter
    results_limited_samsung = service.search_products("Samsung", limit=1)
    assert len(results_limited_samsung) == 1, "Should return exactly 1 product due to limit"
    assert "Samsung Galaxy S24 Ultra" == results_limited_samsung[0]['name'], "Expected 'Samsung Galaxy S24 Ultra' as the top result"

    # Test Case 4: Search by category implicitly
    results_laptop_category = service.search_products("Laptop")
    assert any(p.get('category') == 'Laptop' for p in results_laptop_category), "Should find products in 'Laptop' category"
    assert any("MacBook Pro 14 inch M3" == p['name'] for p in results_laptop_category), "Expected 'MacBook Pro' in laptop search"

    # Test Case 5: Search with price extraction (e.g., "produk di bawah 5 juta")
    # '5 juta' is extracted as 5,000,000. AirPods Pro is 4.5M.
    results_under_5m = service.search_products("produk di bawah 5 juta")
    assert len(results_under_5m) > 0, "Should find products under 5 million"
    assert all(p.get('price', 0) <= 5_000_000 for p in results_under_5m), "All returned products should be under or equal to 5 million"
    assert any("AirPods Pro 2nd Gen" in p['name'] for p in results_under_5m), "AirPods Pro should be included (4.5M)"
    assert not any("iPhone 15 Pro Max" in p['name'] for p in results_under_5m), "iPhone 15 Pro Max should NOT be included (25M)"

    # Test Case 6: Search keyword that exists in specifications (e.g., storage capacity)
    results_storage_search = service.search_products("256GB")
    assert len(results_storage_search) > 0, "Should find products with '256GB' in specifications"
    assert any("iPhone 15 Pro Max" == p['name'] for p in results_storage_search), "iPhone 15 Pro Max (256GB) should be found"
    assert any("iPad Air 5th Gen" == p['name'] for p in results_storage_search), "iPad Air 5th Gen (256GB) should be found"

    # Test Case 7: Search for a keyword that does not exist
    results_non_existent = service.search_products("nonexistent_product_xyz")
    assert len(results_non_existent) == 0, "Should return an empty list for non-existent keyword"

    # Test Case 8: Empty keyword (should return default limited products)
    results_empty_keyword = service.search_products("", limit=3)
    assert len(results_empty_keyword) == 3, "Empty keyword should return products up to the specified limit"
    assert all(isinstance(p, dict) for p in results_empty_keyword), "All results should be product dictionaries"
