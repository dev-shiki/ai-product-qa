import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    service = LocalProductService()

    # Test case 1: Basic keyword search (case-insensitive)
    results_iphone = service.search_products("iphone")
    assert len(results_iphone) > 0
    assert any(p["id"] == "1" for p in results_iphone)  # iPhone 15 Pro Max should be found
    assert all("iphone" in p["name"].lower() or "apple" in p["brand"].lower() for p in results_iphone)

    results_case_insensitive = service.search_products("IPHONE")
    assert len(results_case_insensitive) == len(results_iphone)
    assert {p['id'] for p in results_case_insensitive} == {p['id'] for p in results_iphone}

    # Test case 2: Search with a limit
    limited_results = service.search_products("samsung", limit=1)
    assert len(limited_results) == 1
    assert "samsung" in limited_results[0]["brand"].lower() or "samsung" in limited_results[0]["name"].lower()

    # Test case 3: Search for a product that doesn't exist
    no_results = service.search_products("xyz_non_existent_product")
    assert len(no_results) == 0

    # Test case 4: Search with price limit extracted from keyword (e.g., "laptop 20 juta")
    # This should find ASUS ROG Strix G15 (18M ID:6) and exclude MacBook Pro (35M ID:3)
    price_search_results = service.search_products("laptop 20 juta")
    assert any(p.get('id') == "6" for p in price_search_results)
    assert not any(p.get('id') == "3" for p in price_search_results)

    # Test case 5: Search with a different price format ("audio rp 5000000")
    # This should find AirPods Pro (4.5M ID:4) and potentially exclude Sony WH-1000XM5 (5.5M ID:7) based on price if strict
    audio_price_search_results = service.search_products("audio rp 5000000")
    assert any(p.get('id') == "4" for p in audio_price_search_results)
    # Based on current search logic, if Sony (ID:7) category 'Audio' matches, it might still be included even if price is above exact 'rp 5000000'
    # We assert it's NOT included if price is strictly limiting and keyword does not override
    assert not any(p.get('id') == "7" and p.get('price', 0) > 5000000 for p in audio_price_search_results)

    # Test case 6: Search for a keyword in specifications
    spec_search_results = service.search_products("A17 Pro")
    assert any(p.get('id') == "1" for p in spec_search_results)  # iPhone 15 Pro Max (ID:1) has A17 Pro in specs
    assert all("a17 pro" in str(p.get('specifications', {})).lower() or "a17 pro" in p.get('name', '').lower() for p in spec_search_results)

    # Test case 7: Empty keyword should return products up to default limit (10)
    all_products_default_limit = service.search_products("")
    assert len(all_products_default_limit) <= 10
    assert len(all_products_default_limit) > 0

    # Test case 8: Empty keyword with explicit limit
    all_products_explicit_limit = service.search_products("", limit=3)
    assert len(all_products_explicit_limit) == 3

    # Test case 9: Search for a brand name and check if relevant products are found and prioritized
    apple_products_search = service.search_products("Apple")
    assert any(p.get('brand') == 'Apple' for p in apple_products_search)
    if apple_products_search:
        # Given relevance score, Apple products should be at the top
        assert apple_products_search[0].get('brand') == 'Apple' or 'apple' in apple_products_search[0].get('name', '').lower()

    # Test case 10: Search for a category
    laptop_results = service.search_products("laptop")
    assert len(laptop_results) > 0
    assert all("laptop" in p["category"].lower() for p in laptop_results)
    assert any(p["id"] == "3" for p in laptop_results) # MacBook Pro
    assert any(p["id"] == "6" for p in laptop_results) # ASUS ROG Strix
