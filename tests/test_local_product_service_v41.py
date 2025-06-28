import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    """
    Test basic functionality of search_products method.
    It relies on the LocalProductService's internal product loading (which falls back
    to a hardcoded list if products.json is not found/readable).
    """
    # Create an instance of LocalProductService
    # Assuming LocalProductService is imported and available in this scope.
    service = LocalProductService()

    # Test Case 1: Search for a keyword that should yield specific products (name match)
    results_iphone = service.search_products(keyword="iPhone", limit=5)
    assert len(results_iphone) > 0, "Should find products for 'iPhone'"
    assert any(p['name'] == "iPhone 15 Pro Max" for p in results_iphone), \
        "iPhone 15 Pro Max should be in results for 'iPhone'"
    # Due to relevance score (name match +10), iPhone 15 Pro Max should be first
    assert results_iphone[0]['name'] == "iPhone 15 Pro Max", \
        "iPhone 15 Pro Max should be the first result for 'iPhone'"

    # Test Case 2: Search for a category (case-insensitive)
    results_laptop = service.search_products(keyword="laptop", limit=5)
    assert len(results_laptop) >= 2, "Should find at least two laptops"
    assert any(p['name'] == "MacBook Pro 14 inch M3" for p in results_laptop), \
        "MacBook Pro should be in results for 'laptop'"
    assert any(p['name'] == "ASUS ROG Strix G15" for p in results_laptop), \
        "ASUS ROG Strix G15 should be in results for 'laptop'"

    # Test Case 3: Search with a price constraint (e.g., "laptop 20 juta")
    results_budget_laptop = service.search_products(keyword="laptop 20 juta", limit=5)
    assert len(results_budget_laptop) > 0, "Should find budget laptops"
    # ASUS ROG Strix G15 (18M) should be found, MacBook Pro (35M) should not
    assert any(p['name'] == "ASUS ROG Strix G15" for p in results_budget_laptop), \
        "ASUS ROG Strix G15 should be in results for 'laptop 20 juta'"
    assert not any(p['name'] == "MacBook Pro 14 inch M3" for p in results_budget_laptop), \
        "MacBook Pro should NOT be in results for 'laptop 20 juta' due to price"
    for product in results_budget_laptop:
        assert product.get('price', 0) <= 20000000, \
            f"Product {product.get('name')} price {product.get('price')} exceeds 20 juta"

    # Test Case 4: Search for a brand
    results_samsung = service.search_products(keyword="Samsung", limit=5)
    assert len(results_samsung) >= 2, "Should find at least two Samsung products"
    assert any(p['name'] == "Samsung Galaxy S24 Ultra" for p in results_samsung)
    assert any(p['name'] == "Samsung Galaxy Tab S9" for p in results_samsung)

    # Test Case 5: Search with a non-existent keyword
    results_nonexistent = service.search_products(keyword="xyznonexistentproduct")
    assert len(results_nonexistent) == 0, "Should return an empty list for non-existent keyword"

    # Test Case 6: Verify the limit parameter
    results_limit_one = service.search_products(keyword="Apple", limit=1)
    assert len(results_limit_one) == 1, "Should return exactly one product when limit is 1"
    assert "Apple" in results_limit_one[0]['brand'], "The single result should be an Apple product"
