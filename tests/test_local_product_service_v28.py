import pytest
from app.services.local_product_service import search_products

import pytest
from app.services.local_product_service import LocalProductService

def test_search_products_basic():
    # Instantiate the service. This will load fallback products if products.json is not found,
    # ensuring a consistent dataset for the test.
    service = LocalProductService()

    # Test 1: Basic keyword search (case-insensitive)
    # Should find products related to 'Apple'
    results_apple = service.search_products("apple")
    assert len(results_apple) > 0
    assert any(p['brand'].lower() == 'apple' for p in results_apple)
    assert any(p['name'] == 'iPhone 15 Pro Max' for p in results_apple)

    # Test 2: Search with a specific limit
    # Should return exactly one Samsung product
    results_limited = service.search_products("Samsung", limit=1)
    assert len(results_limited) == 1
    assert results_limited[0]['brand'] == 'Samsung'

    # Test 3: Search for a keyword that should yield no results
    # Should return an empty list
    results_no_match = service.search_products("nonexistentproductxyz123")
    assert len(results_no_match) == 0

    # Test 4: Search incorporating an explicit price keyword (e.g., "laptop 20 juta")
    # This tests price extraction and how it interacts with keyword matching.
    # 'max_price' will be 20,000,000.
    # Products with price <= 20M are added first.
    # Products with price > 20M are added only if they match the 'laptop' keyword.
    results_laptop_price_limit = service.search_products("laptop 20 juta")
    assert len(results_laptop_price_limit) > 0
    # ASUS ROG Strix G15 (18M) should be present (price <= 20M and matches 'laptop')
    assert any(p['name'] == 'ASUS ROG Strix G15' for p in results_laptop_price_limit)
    # MacBook Pro 14 inch M3 (35M) should be present because it matches 'laptop' keyword, even though its price is > 20M.
    assert any(p['name'] == 'MacBook Pro 14 inch M3' for p in results_laptop_price_limit)
    # AirPods Pro 2nd Gen (4.5M) should be present because its price is <= 20M, even if it's not a 'laptop'.
    assert any(p['name'] == 'AirPods Pro 2nd Gen' for p in results_laptop_price_limit)

    # Test 5: Search using a "budget" keyword (e.g., "murah")
    # 'murah' typically implies a max_price (e.g., 5,000,000).
    # Products with price <= 5M are added. Products with price > 5M are generally excluded unless 'murah' is in their text.
    results_general_cheap = service.search_products("murah")
    assert len(results_general_cheap) > 0
    # AirPods Pro (4.5M) should be included as it's below the implied 'murah' price.
    assert any(p['name'] == 'AirPods Pro 2nd Gen' for p in results_general_cheap)
    # iPhone 15 Pro Max (25M) should NOT be included as its price is far above the 'murah' threshold and 'murah' is not in its description.
    assert not any(p['name'] == 'iPhone 15 Pro Max' for p in results_general_cheap)
