import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    from app.services.local_product_service import LocalProductService

    service = LocalProductService()

    # Test 1: Basic keyword search and verify presence of an expected product
    results_iphone = service.search_products(keyword="iPhone")
    assert len(results_iphone) >= 1
    assert any(p['name'] == "iPhone 15 Pro Max" for p in results_iphone)
    # Check if the most relevant product (exact name match) is at the top
    assert results_iphone[0]['name'] == "iPhone 15 Pro Max"

    # Test 2: Case-insensitivity
    results_samsung_lower = service.search_products(keyword="samsung")
    assert len(results_samsung_lower) >= 2
    assert any(p['brand'] == "Samsung" for p in results_samsung_lower)
    assert any(p['name'] == "Samsung Galaxy S24 Ultra" for p in results_samsung_lower)

    # Test 3: Search with limit parameter
    results_limited_apple = service.search_products(keyword="Apple", limit=2)
    assert len(results_limited_apple) == 2
    assert all(p['brand'] == "Apple" for p in results_limited_apple)

    # Test 4: Search for a non-existent keyword
    results_nonexistent = service.search_products(keyword="NonExistentProductXYZ123")
    assert len(results_nonexistent) == 0

    # Test 5: Search combining keyword and price (e.g., "laptop 20 juta")
    # This tests the _extract_price_from_keyword and its interaction.
    # It should return laptops (e.g., ASUS ROG, MacBook Pro) and/or products under 20M.
    results_price_and_keyword = service.search_products(keyword="laptop 20 juta")
    assert len(results_price_and_keyword) >= 2
    assert any(p['name'] == "ASUS ROG Strix G15" for p in results_price_and_keyword) # Price 18M, Laptop keyword
    assert any(p['name'] == "MacBook Pro 14 inch M3" for p in results_price_and_keyword) # Price 35M (matches 'laptop', not price)
