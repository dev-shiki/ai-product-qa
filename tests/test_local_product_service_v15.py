import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    service = LocalProductService()

    # Test 1: Basic search for a common product name (e.g., "iPhone")
    keyword_iphone = "iPhone"
    results_iphone = service.search_products(keyword_iphone, limit=5)

    # Assert that results are returned
    assert len(results_iphone) > 0, f"Expected products for '{keyword_iphone}', but got none."

    # Assert that a highly relevant product (iPhone 15 Pro Max) is in the results
    # due to its direct name match and higher relevance score.
    iphone_15_pro_max_found = False
    for product in results_iphone:
        if "iphone 15 pro max" in product.get('name', '').lower():
            iphone_15_pro_max_found = True
            break
    assert iphone_15_pro_max_found, "Expected 'iPhone 15 Pro Max' in search results for 'iPhone'."
    
    # Assert that the number of results does not exceed the limit
    assert len(results_iphone) <= 5, "Expected results count to be less than or equal to limit (5)."

    # Test 2: Search for a keyword that should yield no results
    keyword_no_match = "xyznonexistentproductabc"
    results_no_match = service.search_products(keyword_no_match)
    assert len(results_no_match) == 0, f"Expected no products for '{keyword_no_match}', but got some."

    # Test 3: Search with a specific limit (e.g., limit=1)
    keyword_samsung = "Samsung"
    results_limited = service.search_products(keyword_samsung, limit=1)
    assert len(results_limited) == 1, "Expected exactly 1 product when limit is set to 1."
    assert "samsung" in results_limited[0].get('name', '').lower(), "Expected a Samsung product in limited results."

    # Test 4: Search incorporating price extraction (e.g., "laptop 20 juta")
    # Based on fallback products:
    # - MacBook Pro 14 inch M3 (35,000,000 IDR)
    # - ASUS ROG Strix G15 (18,000,000 IDR)
    # A search for "laptop 20 juta" should include the ASUS ROG Strix G15 but exclude the MacBook Pro.
    keyword_laptop_price = "laptop 20 juta"
    results_laptop_price = service.search_products(keyword_laptop_price, limit=5)

    assert len(results_laptop_price) > 0, "Expected products for 'laptop 20 juta', but got none."
    
    asus_rog_strix_found = False
    macbook_pro_found = False
    for product in results_laptop_price:
        if "asus rog strix g15" in product.get('name', '').lower():
            asus_rog_strix_found = True
        if "macbook pro" in product.get('name', '').lower():
            macbook_pro_found = True
            
    assert asus_rog_strix_found, "Expected 'ASUS ROG Strix G15' for 'laptop 20 juta' search."
    assert not macbook_pro_found, "Did not expect 'MacBook Pro' for 'laptop 20 juta' search due to price limit."
