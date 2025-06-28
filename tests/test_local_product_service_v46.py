import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    service = LocalProductService()

    # Test 1: Basic search by a common keyword present in product names
    results = service.search_products("iPhone")
    assert len(results) >= 1
    assert any("iPhone 15 Pro Max" == p['name'] for p in results)

    # Test 2: Search by category, expecting multiple relevant products
    results = service.search_products("Smartphone")
    assert len(results) >= 2
    assert any("iPhone 15 Pro Max" == p['name'] for p in results)
    assert any("Samsung Galaxy S24 Ultra" == p['name'] for p in results)

    # Test 3: Search by brand with a specific limit
    results = service.search_products("Apple", limit=2)
    assert len(results) <= 2
    apple_product_names = [p['name'] for p in results]
    assert any("iPhone 15 Pro Max" in name for name in apple_product_names)
    assert any("MacBook Pro 14 inch M3" in name or "AirPods Pro 2nd Gen" in name or "iPad Air 5th Gen" in name for name in apple_product_names)

    # Test 4: Search with a price filter extracted from keyword (e.g., "laptop 20 juta")
    results = service.search_products("laptop 20 juta")
    assert len(results) >= 1
    product_names = [p['name'] for p in results]
    assert "ASUS ROG Strix G15" in product_names # ASUS ROG Strix G15 is 18M, should be included
    assert "MacBook Pro 14 inch M3" not in product_names # MacBook Pro is 35M, should be excluded

    # Test 5: Search for a keyword that does not exist in any product
    results = service.search_products("NonExistentProductXYZ")
    assert len(results) == 0

    # Test 6: Search with an empty keyword, should return products up to the default limit
    results = service.search_products("")
    assert len(results) > 0
    assert len(results) <= 10 # Default limit is 10

    # Test 7: Case-insensitivity check
    results_lower = service.search_products("iphone")
    results_upper = service.search_products("IPHONE")
    assert len(results_lower) == len(results_upper)
    assert any("iPhone 15 Pro Max" == p['name'] for p in results_lower)
<ctrl63>
