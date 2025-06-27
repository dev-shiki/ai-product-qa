import pytest
from app.services.local_product_service import search_products

import pytest
from app.services.local_product_service import LocalProductService # Assume this import is handled by the calling context

def test_search_products_basic():
    service = LocalProductService() # This will load fallback products if products.json is not found

    # Test 1: Search for a common keyword "iPhone"
    results_iphone = service.search_products("iPhone")
    assert len(results_iphone) >= 1
    assert any("iPhone 15 Pro Max" == p['name'] for p in results_iphone)
    assert not any("Samsung Galaxy S24 Ultra" == p['name'] for p in results_iphone) # Should not contain Samsung

    # Test 2: Search for a brand "Samsung"
    results_samsung = service.search_products("Samsung")
    assert len(results_samsung) >= 2 # S24 Ultra and Tab S9
    assert any("Samsung Galaxy S24 Ultra" == p['name'] for p in results_samsung)
    assert any("Samsung Galaxy Tab S9" == p['name'] for p in results_samsung)

    # Test 3: Search for a category "Laptop"
    results_laptop = service.search_products("Laptop")
    assert len(results_laptop) >= 2 # MacBook Pro and ASUS ROG
    assert any("MacBook Pro 14 inch M3" == p['name'] for p in results_laptop)
    assert any("ASUS ROG Strix G15" == p['name'] for p in results_laptop)

    # Test 4: Search with a limit
    results_limited = service.search_products("Apple", limit=2)
    assert len(results_limited) <= 2
    # Check if they are likely Apple products
    assert all("Apple" in p['brand'] for p in results_limited)

    # Test 5: Search for a non-existent keyword
    results_nonexistent = service.search_products("XYZNonExistentProduct")
    assert len(results_nonexistent) == 0

    # Test 6: Search with price keyword "Smartphone 10 juta" (should find items <= 10M)
    # Based on fallback products, only AirPods Pro (4.5M) and Sony WH-1000XM5 (5.5M) are within 10M range and are not smartphones.
    # The current logic will find products by price OR by keyword.
    # Let's search for "hp 15 juta" (HP is a common term for smartphone in Indonesia, but not in data)
    # The price extraction from keyword takes precedence for price filtering, then the general search.
    results_budget_phone = service.search_products("hp 15 juta")
    # Expected: The price limit of 15M should apply.
    # Products under 15M: iPhone 15 Pro Max (25M), Samsung S24 Ultra (22M)
    # MacBook (35M), AirPods (4.5M), iPad Air (12M), ASUS ROG (18M), Sony (5.5M), Samsung Tab S9 (15M)
    # Products <= 15M: AirPods, iPad Air, Sony, Samsung Tab S9.
    # The 'hp' keyword might not match anything, so the filter primarily works on price.
    assert any(p['price'] <= 15000000 for p in results_budget_phone)
    assert any("iPad Air 5th Gen" == p['name'] for p in results_budget_phone)
    assert any("Samsung Galaxy Tab S9" == p['name'] for p in results_budget_phone)
    assert any("AirPods Pro 2nd Gen" == p['name'] for p in results_budget_phone)
    assert any("Sony WH-1000XM5" == p['name'] for p in results_budget_phone)
    # Check that expensive items are excluded
    assert not any("iPhone 15 Pro Max" == p['name'] for p in results_budget_phone)
    assert not any("MacBook Pro 14 inch M3" == p['name'] for p in results_budget_phone)

    # Test 7: Search with a general budget keyword "tablet murah"
    results_budget_tablet = service.search_products("tablet murah")
    # "murah" maps to 5,000,000.
    # Tablets are: iPad Air (12M), Samsung Galaxy Tab S9 (15M)
    # Neither are <= 5M. The keyword "tablet" should match, but "murah" will set a price limit.
    # If no products match the price, it might still return products matching "tablet" if the price filter is a soft one or other keywords dominate.
    # Re-reading logic: "if max_price and product_price <= max_price: filtered_products.append(product); continue"
    # This means if it hits price, it's added. Otherwise, it checks text.
    # So for "tablet murah", it will first check for products <= 5M. None of the tablets match this.
    # Then it will check for 'tablet' in text. Both iPad Air and Galaxy Tab S9 will be found.
    # The relevance score will prefer lower prices for "murah" keyword.
    assert any("iPad Air 5th Gen" == p['name'] for p in results_budget_tablet)
    assert any("Samsung Galaxy Tab S9" == p['name'] for p in results_budget_tablet)
    # Ensure the cheaper tablet is prioritized (iPad Air 12M vs Samsung Tab S9 15M)
    # This relies on the sorting logic based on price for budget searches.
    assert results_budget_tablet[0]['name'] == "iPad Air 5th Gen" # iPad Air is 12M, Samsung Tab S9 is 15M

    # Test 8: Search with empty keyword (should return limited number of all products)
    results_all = service.search_products("")
    assert len(results_all) == 8 # Default limit is 10, and we have 8 fallback products
    assert len(results_all) <= 10 # Should not exceed default limit

    # Test 9: Case insensitivity
    results_case_insensitive = service.search_products("apple")
    assert len(results_case_insensitive) >= 3 # iPhone, MacBook, AirPods, iPad
    assert any("iPhone 15 Pro Max" == p['name'] for p in results_case_insensitive)
    assert any("MacBook Pro 14 inch M3" == p['name'] for p in results_case_insensitive)
