import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # As 'search_products' is a method of LocalProductService, we need to instantiate it.
    # We assume LocalProductService is importable in the test environment.
    service = LocalProductService()

    # Test 1: Basic keyword search (case-insensitive)
    results_iphone = service.search_products("iPhone")
    assert len(results_iphone) > 0
    # Check if results contain products relevant to "iPhone" or "Apple"
    assert any("iphone" in p.get('name', '').lower() or "apple" in p.get('brand', '').lower() for p in results_iphone)

    # Test 2: Search with a specific limit
    results_samsung_one = service.search_products("Samsung", limit=1)
    assert len(results_samsung_one) == 1
    assert "samsung" in results_samsung_one[0].get('brand', '').lower() or "samsung" in results_samsung_one[0].get('name', '').lower()

    # Test 3: Search for a keyword that should yield no results
    results_no_match = service.search_products("nonexistent_product_query_12345")
    assert len(results_no_match) == 0

    # Test 4: Price-based search (e.g., "murah" implies a max price)
    # Based on the source code, "murah" maps to 5,000,000 IDR.
    # Fallback products include "AirPods Pro 2nd Gen" (4,500,000 IDR) and "Sony WH-1000XM5" (5,500,000 IDR).
    # "audio murah" should find AirPods and potentially filter out Sony based on price.
    results_audio_murah = service.search_products("audio murah")
    assert any("airpods" in p.get('name', '').lower() for p in results_audio_murah)
    # Verify that products exceeding the 'murah' threshold (5M) are not present IF they also match 'audio'
    assert not any(p.get('name', '').lower() == "sony wh-1000xm5" for p in results_audio_murah)
    assert all(p.get('price', 0) <= 5000000 for p in results_audio_murah if p.get('category', '').lower() == 'audio')

    # Test 5: Check default limit when results are plentiful
    results_laptops = service.search_products("laptop")
    assert len(results_laptops) > 0
    assert len(results_laptops) <= 10 # Default limit is 10
