import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    service = LocalProductService()

    # Test 1: Basic keyword search (case-insensitive) for a product name
    results_iphone = service.search_products(keyword="iPhone", limit=1)
    assert len(results_iphone) == 1
    assert results_iphone[0]["name"] == "iPhone 15 Pro Max"

    # Test 2: Search for a category (case-insensitive)
    results_laptop = service.search_products(keyword="laptop", limit=5)
    assert len(results_laptop) >= 2 # Should find at least MacBook Pro and ASUS ROG Strix
    assert any("MacBook Pro 14 inch M3" == p["name"] for p in results_laptop)
    assert any("ASUS ROG Strix G15" == p["name"] for p in results_laptop)

    # Test 3: Search for a brand (case-insensitive)
    results_apple = service.search_products(keyword="apple", limit=3)
    assert len(results_apple) >= 3 # Should find iPhone, MacBook, AirPods, iPad (4 in total, so 3 is fine)
    assert any("iPhone 15 Pro Max" == p["name"] for p in results_apple)
    assert any("MacBook Pro 14 inch M3" == p["name"] for p in results_apple)
    assert any("AirPods Pro 2nd Gen" == p["name"] for p in results_apple)

    # Test 4: Search for something that doesn't exist
    results_non_existent = service.search_products(keyword="xyzNonExistentProduct123", limit=5)
    assert len(results_non_existent) == 0

    # Test 5: Test limit functionality
    results_all_products = service.search_products(keyword="a", limit=100) # Search for 'a' to get many products
    # Given the fallback list has 8 products, a limit of 100 should return all 8
    assert len(results_all_products) == 8

    results_limited = service.search_products(keyword="a", limit=3)
    assert len(results_limited) == 3

    # Test 6: Search with price keyword and category
    # "audio 5 juta" -> max_price=5M.
    # AirPods (4.5M, Audio): price <= 5M -> added by price filter.
    # Sony WH-1000XM5 (5.5M, Audio): price > 5M. 'audio' keyword matches category -> added by keyword filter.
    results_audio_budget = service.search_products(keyword="audio 5 juta", limit=5)
    assert len(results_audio_budget) >= 2
    assert any("AirPods Pro 2nd Gen" == p["name"] for p in results_audio_budget)
    assert any("Sony WH-1000XM5" == p["name"] for p in results_audio_budget)

    # Test 7: Empty keyword (should return all products up to limit, default sorting)
    results_empty_keyword = service.search_products(keyword="", limit=3)
    assert len(results_empty_keyword) == 3
    assert all(isinstance(p, dict) for p in results_empty_keyword)
