import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    from app.services.local_product_service import LocalProductService

    service = LocalProductService()

    # Test 1: Basic search with a keyword expecting results
    keyword_apple = "iPhone"
    results_apple = service.search_products(keyword_apple)
    assert isinstance(results_apple, list)
    assert len(results_apple) > 0, f"Expected products for '{keyword_apple}', but got none."
    # Check if at least one product name contains the keyword (case-insensitive)
    assert any(keyword_apple.lower() in p.get('name', '').lower() for p in results_apple)

    # Test 2: Search with a specific limit
    keyword_samsung = "Samsung"
    limit_val = 1
    results_limited = service.search_products(keyword_samsung, limit=limit_val)
    assert isinstance(results_limited, list)
    assert len(results_limited) <= limit_val, f"Expected at most {limit_val} product, got {len(results_limited)}"
    assert len(results_limited) > 0 # Should still find at least one Samsung product

    # Test 3: Search for a keyword that should yield no results
    keyword_no_match = "nonexistentproduct123abc"
    results_empty = service.search_products(keyword_no_match)
    assert isinstance(results_empty, list)
    assert len(results_empty) == 0, "Expected no products for a non-existent keyword."

    # Test 4: Search combining keyword and implicit price (e.g., "audio 5 juta")
    # In fallback products, "AirPods Pro 2nd Gen" (4.5M) and "Sony WH-1000XM5" (5.5M)
    # The search for "audio 5 juta" should prioritize items under 5M.
    keyword_price_search = "audio 5 juta"
    results_price = service.search_products(keyword_price_search)
    assert isinstance(results_price, list)
    assert len(results_price) > 0, "Expected products for price search 'audio 5 juta'."
    # Verify that 'AirPods' is found as it matches both criteria (audio category + price)
    assert any("airpods" in p.get('name', '').lower() and p.get('price', 0) <= 5000000 for p in results_price)

    # Test 5: Search with a budget keyword (e.g., "murah")
    # "murah" implies a max price of 5,000,000 based on _extract_price_from_keyword
    keyword_budget = "tablet murah"
    results_budget = service.search_products(keyword_budget)
    assert isinstance(results_budget, list)
    # Should find products that are cheaper than 5M, even if not directly "tablet".
    # The 'tablet' keyword should filter first, then 'murah' price.
    # Fallback: iPad Air (12M), Galaxy Tab S9 (15M) -> neither is < 5M.
    # So "tablet murah" should return no direct matches for both, but might return other 'cheap' products due to the `search_products` logic.
    # Let's simplify and just test "murah"
    keyword_simple_budget = "murah"
    results_simple_budget = service.search_products(keyword_simple_budget)
    assert len(results_simple_budget) > 0
    # At least one product should have price <= 5,000,000 (e.g., AirPods at 4.5M)
    assert any(p.get('price', 0) <= 5000000 for p in results_simple_budget), "Expected at least one product under 5M for 'murah' keyword."
