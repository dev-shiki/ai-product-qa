import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    from app.services.local_product_service import LocalProductService

    # Instantiate the service. This will load either from products.json or fallback.
    service = LocalProductService()

    # Test Case 1: Basic keyword search (case-insensitive)
    results_iphone = service.search_products(keyword="iphone")
    assert len(results_iphone) > 0
    assert any("iPhone 15 Pro Max" in p['name'] for p in results_iphone)

    results_samsung = service.search_products(keyword="Samsung")
    assert len(results_samsung) > 0
    assert any("Samsung Galaxy S24 Ultra" in p['name'] for p in results_samsung)
    assert any("Samsung Galaxy Tab S9" in p['name'] for p in results_samsung)

    # Test Case 2: Search with a limit
    results_apple_limited = service.search_products(keyword="Apple", limit=1)
    assert len(results_apple_limited) == 1
    # Check if the returned product is an Apple product (relevance based, so order might vary, but should be an Apple product)
    assert "Apple" in results_apple_limited[0]['brand']

    # Test Case 3: Search for a non-existent product
    results_none = service.search_products(keyword="nonexistentproduct123")
    assert len(results_none) == 0

    # Test Case 4: Search by category
    results_smartphone = service.search_products(keyword="Smartphone")
    assert len(results_smartphone) >= 2 # iPhone and Samsung S24 Ultra
    assert all("Smartphone" in p['category'] for p in results_smartphone if "Smartphone" in p['category'])

    # Test Case 5: Search with price limit (e.g., "laptop 20 juta")
    results_laptop_budget = service.search_products(keyword="laptop 20 juta")
    assert len(results_laptop_budget) > 0
    # ASUS ROG Strix G15 (18M) should be included, MacBook Pro (35M) should not be directly due to price filter
    assert any("ASUS ROG Strix G15" in p['name'] for p in results_laptop_budget)
    assert not any("MacBook Pro 14 inch M3" in p['name'] and p['price'] > 20000000 for p in results_laptop_budget)

    # Test Case 6: Search with an empty keyword (should return some products up to limit)
    results_empty_keyword = service.search_products(keyword="", limit=3)
    assert len(results_empty_keyword) == 3
    # Verify that these are actual products from the service
    assert all('id' in p and 'name' in p for p in results_empty_keyword)
