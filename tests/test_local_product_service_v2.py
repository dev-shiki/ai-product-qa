import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    from app.services.local_product_service import LocalProductService

    service = LocalProductService()

    # Test case 1: Search for a common keyword (case-insensitive)
    results_apple = service.search_products(keyword="apple")
    assert len(results_apple) >= 2  # Expecting at least 2 Apple products from fallback
    assert any(p['name'] == 'iPhone 15 Pro Max' for p in results_apple)
    assert any(p['name'] == 'MacBook Pro 14 inch M3' for p in results_apple)

    # Test case 2: Search for a specific product name
    results_iphone = service.search_products(keyword="iPhone 15 Pro Max")
    assert len(results_iphone) >= 1
    assert results_iphone[0]['name'] == 'iPhone 15 Pro Max'

    # Test case 3: Search with limit parameter
    results_limited = service.search_products(keyword="Samsung", limit=1)
    assert len(results_limited) == 1
    assert results_limited[0]['brand'] == 'Samsung' # Ensure it's a Samsung product

    # Test case 4: Search for a non-existent product
    results_none = service.search_products(keyword="NonExistentGadgetXYZ123")
    assert len(results_none) == 0

    # Test case 5: Search with a price keyword
    # "laptop 20 juta" should filter for laptops under 20,000,000 IDR
    # ASUS ROG Strix G15 (18,000,000) should be included, MacBook Pro (35,000,000) should not.
    results_budget_laptop = service.search_products(keyword="laptop 20 juta")
    assert any(p['name'] == 'ASUS ROG Strix G15' for p in results_budget_laptop)
    assert not any(p['name'] == 'MacBook Pro 14 inch M3' for p in results_budget_laptop)
    # Ensure all returned products are indeed within the price range if '20 juta' was the primary filter
    for product in results_budget_laptop:
        if 'laptop' in product.get('category', '').lower():
            assert product.get('price', 0) <= 20000000

    # Test case 6: Empty keyword should return some products (limited by default limit)
    results_all = service.search_products(keyword="")
    assert len(results_all) > 0 # Should return default number of products
    assert len(results_all) <= 10 # Default limit is 10
