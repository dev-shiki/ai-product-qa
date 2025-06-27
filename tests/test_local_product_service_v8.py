import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Instantiate the service. This will automatically load products (either from file or use fallback).
    # For testing, it's reliable as the service provides its own fallback products.
    service = LocalProductService()

    # Test Case 1: Basic search for a common keyword (e.g., "iPhone")
    keyword_1 = "iPhone"
    results_1 = service.search_products(keyword_1)
    assert len(results_1) > 0, f"Should find products for keyword '{keyword_1}'"
    # Verify that at least one product name or brand contains the keyword (case-insensitive)
    assert any(keyword_1.lower() in p.get('name', '').lower() or
               keyword_1.lower() in p.get('brand', '').lower()
               for p in results_1), \
        f"Results for '{keyword_1}' should contain relevant products."

    # Test Case 2: Search with a specific limit
    keyword_2 = "Samsung"
    limit_2 = 1
    results_2 = service.search_products(keyword_2, limit=limit_2)
    assert len(results_2) == limit_2, f"Should return exactly {limit_2} product(s) for keyword '{keyword_2}' with limit {limit_2}"
    # Verify the product found is relevant (e.g., contains "Samsung" in name or brand)
    assert keyword_2.lower() in results_2[0].get('brand', '').lower() or \
           keyword_2.lower() in results_2[0].get('name', '').lower(), \
           f"The returned product should be relevant to '{keyword_2}'"

    # Test Case 3: Search for a keyword that does not exist in any fallback product
    keyword_3 = "NonExistentGadgetXYZ123"
    results_3 = service.search_products(keyword_3)
    assert len(results_3) == 0, f"Should find no products for non-existent keyword '{keyword_3}'"

    # Test Case 4: Search keyword by category (e.g., "Laptop")
    keyword_4 = "Laptop"
    results_4 = service.search_products(keyword_4)
    assert len(results_4) > 0, f"Should find products for category '{keyword_4}'"
    # Verify that at least one product is of 'Laptop' category
    assert any(keyword_4.lower() in p.get('category', '').lower() for p in results_4), \
        f"Results for '{keyword_4}' should contain a product with '{keyword_4}' in its category."

    # Test Case 5: Search with a keyword that implies a price range (e.g., "murah")
    # This checks if the _extract_price_from_keyword logic is implicitly used
    keyword_5 = "airpods murah"
    results_5 = service.search_products(keyword_5)
    assert len(results_5) > 0, f"Should find products for '{keyword_5}' that might also consider price."
    # Verify that relevant (and potentially cheaper) products are returned.
    # The fallback data has "AirPods Pro 2nd Gen" which matches "airpods" and has a price (4.5M) that is considered "murah" (<=5M).
    assert any("airpods" in p.get('name', '').lower() for p in results_5), \
        "Results for 'airpods murah' should contain AirPods products."
