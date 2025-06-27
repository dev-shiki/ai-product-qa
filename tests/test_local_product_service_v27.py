import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    from app.services.local_product_service import LocalProductService

    service = LocalProductService()

    # Test 1: Basic keyword search (case-insensitive)
    results_iphone = service.search_products("iphone")
    assert len(results_iphone) > 0
    assert any("iPhone 15 Pro Max" in p['name'] for p in results_iphone)
    assert any("Apple" in p['brand'] for p in results_iphone)

    # Test 2: Search with a different keyword and limit
    results_samsung_limit_1 = service.search_products("samsung", limit=1)
    assert len(results_samsung_limit_1) == 1
    assert "Samsung" in results_samsung_limit_1[0]['brand']

    # Test 3: Search for a non-existent keyword
    results_no_match = service.search_products("NonExistentProductKeyword")
    assert len(results_no_match) == 0

    # Test 4: Search for a category keyword
    results_laptops = service.search_products("Laptop")
    assert len(results_laptops) == 2
    assert any("MacBook Pro 14 inch M3" in p['name'] for p in results_laptops)
    assert any("ASUS ROG Strix G15" in p['name'] for p in results_laptops)

    # Test 5: Search with a budget keyword, checking sorting
    # "laptop budget" -> 'budget' sets max_price = 5,000,000.
    # Both laptops (35M, 18M) exceed this, but still match 'laptop'.
    # The relevance score for budget keywords should prioritize lower prices *among the matched items*.
    # ASUS ROG (18M) is cheaper than MacBook Pro (35M), so it should be listed first.
    results_laptop_budget = service.search_products("laptop budget")
    assert len(results_laptop_budget) == 2
    assert results_laptop_budget[0]['name'] == "ASUS ROG Strix G15"
    assert results_laptop_budget[1]['name'] == "MacBook Pro 14 inch M3"

    # Test 6: Verify structure of returned products
    if results_iphone:
        product = results_iphone[0]
        assert 'id' in product
        assert 'name' in product
        assert 'price' in product
        assert 'category' in product
        assert 'brand' in product
        assert 'specifications' in product
        assert 'rating' in product['specifications']
        assert 'sold' in product['specifications']
