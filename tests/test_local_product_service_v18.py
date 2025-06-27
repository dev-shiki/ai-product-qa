import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    service = LocalProductService()

    # Test 1: Pencarian dasar dengan kata kunci yang harus menghasilkan beberapa produk
    results_apple = service.search_products("Apple")
    assert len(results_apple) >= 3  # Mengharapkan setidaknya iPhone, MacBook, AirPods, iPad
    # Memastikan semua produk yang dikembalikan terkait dengan Apple (brand atau nama)
    assert all("apple" in p.get('brand', '').lower() or "apple" in p.get('name', '').lower() for p in results_apple)
    assert any(p.get('name') == "iPhone 15 Pro Max" for p in results_apple)
    assert any(p.get('name') == "MacBook Pro 14 inch M3" for p in results_apple)
    assert any(p.get('name') == "AirPods Pro 2nd Gen" for p in results_apple)

    # Test 2: Pencarian nama produk spesifik
    results_iphone = service.search_products("iPhone 15 Pro Max")
    assert len(results_iphone) == 1
    assert results_iphone[0]['name'] == "iPhone 15 Pro Max"

    # Test 3: Pencarian berdasarkan kategori
    results_laptop = service.search_products("Laptop")
    assert len(results_laptop) >= 1
    # Memastikan semua hasil memang laptop
    assert all("laptop" in p.get('category', '').lower() for p in results_laptop)
    assert any(p.get('name') == "MacBook Pro 14 inch M3" for p in results_laptop)
    assert any(p.get('name') == "ASUS ROG Strix G15" for p in results_laptop)

    # Test 4: Pencarian berdasarkan brand
    results_samsung = service.search_products("Samsung")
    assert len(results_samsung) >= 1
    assert all("samsung" in p.get('brand', '').lower() for p in results_samsung)
    assert any(p.get('name') == "Samsung Galaxy S24 Ultra" for p in results_samsung)
    assert any(p.get('name') == "Samsung Galaxy Tab S9" for p in results_samsung)

    # Test 5: Pencarian kata kunci yang tidak menghasilkan apa-apa
    results_no_match = service.search_products("ProdukTidakAdaXYZ123")
    assert len(results_no_match) == 0

    # Test 6: Menguji parameter limit
    results_limited_apple = service.search_products("Apple", limit=2)
    assert len(results_limited_apple) == 2  # Harus mengembalikan tepat 2 produk jika tersedia
    assert all("apple" in p.get('brand', '').lower() or "apple" in p.get('name', '').lower() for p in results_limited_apple)

    # Test 7: Menguji ekstraksi harga dan preferensi untuk kata kunci "murah"
    # "Apple murah" seharusnya memicu max_price=5,000,000 (dari _extract_price_from_keyword).
    # Dari produk fallback, satu-satunya produk Apple di bawah 5 juta adalah AirPods Pro (4.5M).
    results_apple_budget = service.search_products("Apple murah")
    assert len(results_apple_budget) >= 1
    # AirPods Pro seharusnya ada dan kemungkinan besar berada di peringkat teratas
    assert any(p.get('name') == "AirPods Pro 2nd Gen" for p in results_apple_budget)
    # Verifikasi bahwa AirPods Pro adalah hasil teratas karena kriteria harga
    if results_apple_budget:
        assert results_apple_budget[0].get('name') == "AirPods Pro 2nd Gen"
