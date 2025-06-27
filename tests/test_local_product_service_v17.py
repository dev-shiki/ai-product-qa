import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    """
    Test basic functionality of search_products method of LocalProductService.
    Assumes LocalProductService class is accessible in the test environment's scope.
    """
    service = LocalProductService()

    # Test 1: Basic keyword search (case-insensitive, finds 'iPhone 15 Pro Max')
    results_iphone = service.search_products("iphone")
    assert len(results_iphone) >= 1
    assert any(p['name'] == "iPhone 15 Pro Max" for p in results_iphone)

    # Test 2: Search by brand (case-insensitive, finds 'Samsung Galaxy S24 Ultra', 'Samsung Galaxy Tab S9')
    results_samsung = service.search_products("samsung")
    assert len(results_samsung) >= 2 # Should find at least two Samsung products
    assert any(p['name'] == "Samsung Galaxy S24 Ultra" for p in results_samsung)
    assert any(p['name'] == "Samsung Galaxy Tab S9" for p in results_samsung)

    # Test 3: Search with limit parameter
    results_apple_limit_2 = service.search_products("Apple", limit=2)
    assert len(results_apple_limit_2) == 2
    # All results should be from 'Apple' brand
    assert all('Apple' in p.get('brand', '') for p in results_apple_limit_2)

    # Test 4: Search for non-existent product
    results_no_match = service.search_products("nonexistent_product_xyz")
    assert len(results_no_match) == 0

    # Test 5: Search with price extraction from keyword ("laptop 20 juta")
    # This should find "ASUS ROG Strix G15" (18M) but not "MacBook Pro 14 inch M3" (35M)
    results_laptop_budget = service.search_products("laptop 20 juta")
    assert len(results_laptop_budget) >= 1
    assert any(p['name'] == "ASUS ROG Strix G15" for p in results_laptop_budget)
    assert not any(p['name'] == "MacBook Pro 14 inch M3" for p in results_laptop_budget)
    assert all(p['price'] <= 20000000 for p in results_laptop_budget if p.get('category', '').lower() == 'laptop')

    # Test 6: Search by a keyword found in description or specifications
    results_a17_chip = service.search_products("A17 Pro chip")
    assert len(results_a17_chip) >= 1
    assert any(p['name'] == "iPhone 15 Pro Max" for p in results_a17_chip)
