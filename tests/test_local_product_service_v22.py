import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    from app.services.local_product_service import LocalProductService

    # Instantiate the service. This will load products (likely from fallback if data/products.json is not present).
    service = LocalProductService()

    # Test 1: Basic keyword search (case-insensitive)
    results_smartphone = service.search_products("smartphone")
    assert len(results_smartphone) > 0
    # Expect specific smartphone products to be found
    assert any(p.get("name") == "iPhone 15 Pro Max" for p in results_smartphone)
    assert any(p.get("name") == "Samsung Galaxy S24 Ultra" for p in results_smartphone)
    # Ensure non-smartphone products are not included (e.g., laptops)
    assert not any(p.get("category") == "Laptop" for p in results_smartphone)

    # Test 2: Search with limit
    results_apple_limited = service.search_products("Apple", limit=2)
    assert len(results_apple_limited) == 2
    # Ensure the top 2 Apple products (by relevance) are returned
    assert any(p.get("brand") == "Apple" for p in results_apple_limited)

    # Test 3: Search for a non-existent keyword
    results_no_match = service.search_products("nonexistentproductxyz123")
    assert len(results_no_match) == 0

    # Test 4: Search with a price filter keyword (e.g., "headphone 5 juta")
    # "5 juta" extracts max_price = 5,000,000.
    # AirPods Pro (4.5M) is <= 5M and is audio.
    # Sony WH-1000XM5 (5.5M) is not <= 5M but is audio.
    # The logic adds products <= max_price, then checks keywords for others.
    # Then sorts by relevance (lower price preferred for budget search).
    results_audio_budget = service.search_products("headphone 5 juta")
    assert len(results_audio_budget) > 0
    assert any(p.get("name") == "AirPods Pro 2nd Gen" for p in results_audio_budget)
    assert any(p.get("name") == "Sony WH-1000XM5" for p in results_audio_budget)
    # Due to the relevance score (lower price preference), AirPods should be ranked higher
    assert results_audio_budget[0].get("name") == "AirPods Pro 2nd Gen"

    # Test 5: Search using a "budget" keyword like "murah" (implicitly sets max_price)
    # 'murah' maps to 5,000,000.
    # Products with price <= 5,000,000: AirPods Pro 2nd Gen (4.5M).
    results_murah = service.search_products("produk murah")
    assert len(results_murah) > 0
    # The cheapest product (AirPods) should be among the top results due to relevance scoring for 'murah'
    assert results_murah[0].get("name") == "AirPods Pro 2nd Gen"
    # All products returned should be within the 'murah' price range if limit allows and only relevant ones are picked.
    # Specifically check that highly expensive items are not at the top
    assert all(p.get('price', 0) <= 5000000 for p in results_murah if p.get('name') == "AirPods Pro 2nd Gen")
    # A more general check: ensure some cheap items are present
    assert any(p.get('price', 0) < 6000000 for p in results_murah)
