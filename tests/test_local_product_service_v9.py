import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Import LocalProductService inside the function to adhere to "HANYA return fungsi test saja"
    # and "JANGAN menambahkan import statement" instructions, assuming the necessary
    # module path is available when this test function is run by pytest.
    from app.services.local_product_service import LocalProductService

    # Instantiate the service. This will load products, using fallback if products.json is not found.
    service = LocalProductService()

    # Test 1: Basic search for a common keyword (e.g., "Apple")
    keyword_apple = "Apple"
    results_apple = service.search_products(keyword_apple)
    
    # Assert that results are found
    assert len(results_apple) > 0, f"Expected products for '{keyword_apple}', but got none."
    
    # Assert that results contain relevant products (e.g., name or brand contains the keyword)
    found_relevant = False
    for product in results_apple:
        if keyword_apple.lower() in product.get('name', '').lower() or \
           keyword_apple.lower() in product.get('brand', '').lower():
            found_relevant = True
            break
    assert found_relevant, f"No relevant product found for keyword '{keyword_apple}'."
    
    # Assert that the default limit (10) is respected
    assert len(results_apple) <= 10, "Default search limit (10) was not respected."

    # Test 2: Search with a specific limit (e.g., "Samsung", limit=1)
    keyword_samsung = "Samsung"
    limit_val = 1
    results_limited = service.search_products(keyword_samsung, limit=limit_val)
    
    assert len(results_limited) == limit_val, f"Expected {limit_val} result for '{keyword_samsung}', but got {len(results_limited)}."
    
    # Test 3: Search for a keyword that should yield no results
    keyword_no_match = "NonExistentProductXYZ123ABC"
    results_no_match = service.search_products(keyword_no_match)
    
    assert len(results_no_match) == 0, f"Expected no results for '{keyword_no_match}', but got {len(results_no_match)}."

    # Test 4: Search with a price-related keyword (e.g., "laptop 20 juta")
    keyword_price_laptop = "laptop 20 juta"
    results_price_laptop = service.search_products(keyword_price_laptop)

    assert len(results_price_laptop) > 0, f"Expected products for '{keyword_price_laptop}', but got none."
    # The _extract_price_from_keyword method parses "20 juta" to 20,000,000.
    # The search should return products with price <= max_price.
    for product in results_price_laptop:
        assert product.get('price', 0) <= 20000000, \
            f"Product '{product.get('name')}' (ID: {product.get('id')}) with price {product.get('price')} " \
            f"exceeds the 20 juta (20,000,000) limit."
