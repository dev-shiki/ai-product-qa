import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    from app.services.local_product_service import LocalProductService

    # Instantiate the service
    service = LocalProductService()

    # Test 1: Search for a common keyword, expecting multiple results
    keyword_apple = "iPhone"
    results_apple = service.search_products(keyword_apple)
    assert isinstance(results_apple, list)
    assert len(results_apple) > 0
    # Verify that the primary iPhone product is found
    assert any("iPhone 15 Pro Max" in p.get('name', '') for p in results_apple)
    # Due to relevance scoring, iPhone should be high up
    assert results_apple[0]['name'] == "iPhone 15 Pro Max"

    # Test 2: Search for another keyword with different products
    keyword_samsung = "Samsung"
    results_samsung = service.search_products(keyword_samsung)
    assert isinstance(results_samsung, list)
    assert len(results_samsung) >= 2 # Expecting Galaxy S24 Ultra and Galaxy Tab S9
    assert any("Samsung Galaxy S24 Ultra" in p.get('name', '') for p in results_samsung)
    assert any("Samsung Galaxy Tab S9" in p.get('name', '') for p in results_samsung)

    # Test 3: Search with a limit
    keyword_limited = "Apple"
    results_limited = service.search_products(keyword_limited, limit=2)
    assert isinstance(results_limited, list)
    assert len(results_limited) <= 2
    # Verify top Apple products are found within the limit
    apple_names = [p.get('name', '') for p in results_limited]
    assert "iPhone 15 Pro Max" in apple_names
    # The second product could be MacBook Pro or AirPods Pro based on scoring
    assert "MacBook Pro 14 inch M3" in apple_names or "AirPods Pro 2nd Gen" in apple_names


    # Test 4: Search for a non-existent keyword
    keyword_non_existent = "nonexistentproductxyz"
    results_empty = service.search_products(keyword_non_existent)
    assert isinstance(results_empty, list)
    assert len(results_empty) == 0

    # Test 5: Search with a price limit extracted from keyword (e.g., "laptop 20 juta")
    keyword_price = "laptop 20 juta"
    results_price = service.search_products(keyword_price)
    assert isinstance(results_price, list)
    assert len(results_price) > 0
    # Verify that returned laptops are within the specified price (20,000,000 IDR)
    for product in results_price:
        if "laptop" in product.get('category', '').lower():
            assert product.get('price', 0) <= 20000000

    # Test 6: Search with a "budget" related keyword (e.g., "tablet murah")
    keyword_budget = "tablet murah"
    results_budget = service.search_products(keyword_budget)
    assert isinstance(results_budget, list)
    assert len(results_budget) > 0
    # Both iPad Air (12M) and Galaxy Tab S9 (15M) are higher than 'murah' default (5M),
    # but they match "tablet" keyword and should be returned, with iPad Air potentially first due to lower price.
    assert any("iPad Air 5th Gen" in p.get('name', '') for p in results_budget)
    assert any("Samsung Galaxy Tab S9" in p.get('name', '') for p in results_budget)
    # Given the relevance score favoring lower prices for 'murah', iPad Air (12M) should be before Tab S9 (15M)
    assert results_budget[0]['name'] == "iPad Air 5th Gen"

    # Test 7: Search with an empty keyword (should return all products up to limit)
    keyword_empty = ""
    results_all = service.search_products(keyword_empty)
    assert isinstance(results_all, list)
    assert len(results_all) == 8 # All 8 fallback products should be returned by default limit of 10
    
    # Test 8: Search by category
    keyword_category = "Smartphone"
    results_category = service.search_products(keyword_category)
    assert len(results_category) == 2
    assert any("iPhone 15 Pro Max" in p['name'] for p in results_category)
    assert any("Samsung Galaxy S24 Ultra" in p['name'] for p in results_category)
