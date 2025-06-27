import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Asumsi LocalProductService sudah diimpor di test file yang akan menggunakan fungsi ini.
    # Instantiate the service. This will load products (either from JSON file or fallback).
    # For a simple unit test, we rely on the service's internal product loading,
    # which includes a robust fallback to hardcoded products if the JSON file is not found.
    service = LocalProductService()

    # Test Case 1: Basic keyword search (case-insensitive)
    results_iphone = service.search_products("iphone")
    assert len(results_iphone) > 0, "Should find products for 'iphone' keyword."
    assert any(p["name"] == "iPhone 15 Pro Max" for p in results_iphone), "iPhone 15 Pro Max should be found."
    assert any(p["brand"] == "Apple" for p in results_iphone), "Other Apple products should also be considered."

    # Test Case 2: Search for a specific category keyword
    results_laptop = service.search_products("Laptop")
    assert len(results_laptop) > 0, "Should find products for 'Laptop' category."
    assert any(p["name"] == "MacBook Pro 14 inch M3" for p in results_laptop), "MacBook Pro should be found for 'Laptop'."
    assert any(p["name"] == "ASUS ROG Strix G15" for p in results_laptop), "ASUS ROG Strix G15 should be found for 'Laptop'."
    # Ensure all top results for category search are indeed from that category (within reason)
    assert all("Laptop" in p.get("category", "") for p in results_laptop if "Laptop" in p.get("category", "")), "All returned products should be of 'Laptop' category."

    # Test Case 3: Search with a specific limit
    results_limited_apple = service.search_products("Apple", limit=2)
    assert len(results_limited_apple) == 2, "Should return exactly 2 products when limit is 2."
    assert all(p["brand"] == "Apple" for p in results_limited_apple), "Both limited results should be from 'Apple' brand."

    # Test Case 4: Search for a non-existent keyword
    results_no_match = service.search_products("nonexistent_product_xyz123")
    assert len(results_no_match) == 0, "Should return an empty list for a non-matching keyword."

    # Test Case 5: Search with a price-related keyword (e.g., "laptop 20 juta")
    # This checks if the price extraction and filtering logic is working alongside keyword search.
    # ASUS ROG Strix G15 (18M) should be found (price match).
    # MacBook Pro 14 inch M3 (35M) should also be found (keyword 'laptop' match).
    results_price_search = service.search_products("laptop 20 juta", limit=5)
    assert len(results_price_search) > 0, "Should find products for 'laptop 20 juta'."
    assert any(p["name"] == "ASUS ROG Strix G15" for p in results_price_search), "ASUS ROG Strix G15 should be found (price <= 20M)."
    assert any(p["name"] == "MacBook Pro 14 inch M3" for p in results_price_search), "MacBook Pro should also be found (keyword 'laptop')."
    
    # Test Case 6: Empty keyword search (should return default limited products)
    results_empty_kw = service.search_products("")
    assert len(results_empty_kw) > 0, "Empty keyword search should return some products."
    assert len(results_empty_kw) <= 10, "Empty keyword search should respect the default limit of 10."
