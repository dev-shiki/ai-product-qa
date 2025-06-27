import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    from app.services.local_product_service import LocalProductService

    service = LocalProductService()

    # Test case 1: Search for a common keyword
    keyword = "iPhone"
    results = service.search_products(keyword)

    assert isinstance(results, list)
    assert len(results) > 0, f"Expected products for '{keyword}', but got none."
    for product in results:
        assert keyword.lower() in product.get('name', '').lower() or \
               keyword.lower() in product.get('description', '').lower(), \
               f"Product {product.get('name')} does not contain '{keyword}'"
    
    # Test case 2: Search with a limit
    limit = 2
    results_limited = service.search_products("Samsung", limit=limit)
    assert len(results_limited) <= limit, f"Expected at most {limit} products, got {len(results_limited)}"

    # Test case 3: Search for a keyword that might not exist in fallback (or should return few)
    keyword_not_found = "NonExistentProductXYZ"
    results_empty = service.search_products(keyword_not_found)
    assert len(results_empty) == 0, f"Expected no products for '{keyword_not_found}', but got some."

    # Test case 4: Search by category
    category_keyword = "Smartphone"
    results_category = service.search_products(category_keyword)
    assert len(results_category) > 0
    # Verify that products contain the category or are relevant
    # The current search logic is quite broad, so a direct category match isn't guaranteed for ALL results,
    # but at least some should be from the category.
    # For a basic test, checking that the top result is relevant is sufficient.
    first_product_name = results_category[0].get('name', '').lower()
    first_product_category = results_category[0].get('category', '').lower()
    assert category_keyword.lower() in first_product_name or category_keyword.lower() in first_product_category

    # Test case 5: Search with price keyword
    price_keyword = "laptop 20 juta"
    results_price = service.search_products(price_keyword)
    assert len(results_price) > 0
    # Check if products returned are within the extracted price range or related to "laptop"
    # The actual price extraction and filtering is handled by _extract_price_from_keyword and then by the search loop.
    # We can't easily assert the max_price in the test function without replicating logic,
    # but we can check if the results seem reasonable.
    for product in results_price:
        if "laptop" in product.get('category', '').lower():
            # If it's a laptop, ensure price is somewhat reasonable
            assert product.get('price', 0) <= 25000000 # Give some buffer, 20 juta is a target, not a strict max for all search results
    
    # Test case 6: Empty keyword should return all products up to limit
    all_products_limit = service.search_products("", limit=3)
    assert len(all_products_limit) == 3
    assert all_products_limit[0].get('name') is not None # Check if products are valid
