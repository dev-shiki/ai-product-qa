import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Instantiate the service. This will load products using its internal logic.
    service = LocalProductService()

    # Test 1: Search for a common keyword (name/brand)
    results_iphone = service.search_products("iPhone")
    assert len(results_iphone) > 0, "Should find products for 'iPhone'"
    assert any("iPhone" in p["name"] for p in results_iphone), "Results should contain iPhone products"

    # Test 2: Search for a category keyword
    results_smartphone = service.search_products("Smartphone")
    assert len(results_smartphone) > 0, "Should find products for 'Smartphone' category"
    assert any("Smartphone" in p["category"] for p in results_smartphone), "Results should contain Smartphone products"

    # Test 3: Search with a keyword containing a price limit
    results_budget_laptop = service.search_products("laptop 20 juta")
    assert len(results_budget_laptop) > 0, "Should find budget laptops"
    assert all(p.get("price", 0) <= 20000000 for p in results_budget_laptop), "All found products should be within 20 million price limit"
    assert any("laptop" in p["category"].lower() or "laptop" in p["name"].lower() for p in results_budget_laptop), "Results should contain laptops"

    # Test 4: Search with a specific limit
    results_limited = service.search_products("Apple", limit=2)
    assert len(results_limited) == 2, "Should return exactly 2 products when limit is 2"
    assert all("Apple" in p["brand"] for p in results_limited), "Limited results should still be from 'Apple' brand"

    # Test 5: Search for a keyword that should not exist
    results_none = service.search_products("nonExistentProductXYZ123Test")
    assert len(results_none) == 0, "Should return an empty list for a non-existent keyword"
