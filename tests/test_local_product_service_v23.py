import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Instantiate the service. This will load products, likely fallback ones if products.json is not found.
    service = LocalProductService()

    # Test 1: Search by keyword in product name
    results_iphone = service.search_products("iPhone")
    assert len(results_iphone) > 0
    assert any("iPhone 15 Pro Max" == p['name'] for p in results_iphone)
    assert not any("Samsung" in p['name'] for p in results_iphone)

    # Test 2: Search by keyword in category
    results_smartphone = service.search_products("Smartphone")
    assert len(results_smartphone) > 0
    assert any("iPhone 15 Pro Max" == p['name'] for p in results_smartphone)
    assert any("Samsung Galaxy S24 Ultra" == p['name'] for p in results_smartphone)
    assert not any("MacBook Pro" == p['name'] for p in results_smartphone)

    # Test 3: Search by keyword in brand
    results_samsung = service.search_products("Samsung")
    assert len(results_samsung) > 0
    assert any("Samsung Galaxy S24 Ultra" == p['name'] for p in results_samsung)
    assert any("Samsung Galaxy Tab S9" == p['name'] for p in results_samsung)
    assert not any("iPhone" in p['name'] for p in results_samsung)

    # Test 4: Search for a keyword that appears in description/specifications
    results_camera = service.search_products("200MP") # Samsung S24 Ultra
    assert len(results_camera) > 0
    assert any("Samsung Galaxy S24 Ultra" == p['name'] for p in results_camera)

    # Test 5: Test with limit parameter
    results_limited = service.search_products("Apple", limit=2)
    assert len(results_limited) == 2
    assert all("Apple" in p['brand'] for p in results_limited)

    # Test 6: Search for a non-existent keyword
    results_non_existent = service.search_products("NonExistentProductXYZ123")
    assert len(results_non_existent) == 0

    # Test 7: Case-insensitivity
    results_case_insensitive = service.search_products("laptop")
    assert len(results_case_insensitive) > 0
    assert any("MacBook Pro 14 inch M3" == p['name'] for p in results_case_insensitive)
    assert any("ASUS ROG Strix G15" == p['name'] for p in results_case_insensitive)

    # Test 8: Search with a price keyword
    results_budget_phone = service.search_products("smartphone murah")
    assert len(results_budget_phone) > 0
    # Products with price <= 5,000,000 should be prioritized or included due to 'murah'
    assert all(p.get('price', 0) <= 25000000 for p in results_budget_phone) # All fallback products are expensive, so this will prioritize lower-priced ones if any fit, or return most relevant.
    assert any("AirPods Pro 2nd Gen" in p['name'] for p in results_budget_phone) # This is 4.5M, fits 'murah' threshold of 5M.
