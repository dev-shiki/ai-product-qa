import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Asumsi LocalProductService sudah diimpor dan tersedia di scope.
    # Misalnya, importnya di awal file test:
    # from app.services.local_product_service import LocalProductService
    service = LocalProductService()

    # Test 1: Cari dengan kata kunci yang ada (case-insensitive)
    keyword_iphone = "iphone"
    results_iphone = service.search_products(keyword_iphone)
    assert len(results_iphone) > 0
    # Pastikan produk-produk Apple (iPhone, AirPods, iPad) muncul karena "iPhone" atau "Apple" adalah bagian dari mereka
    assert any("iPhone 15 Pro Max" == p['name'] for p in results_iphone)
    assert any("AirPods Pro 2nd Gen" == p['name'] for p in results_iphone)
    assert any("iPad Air 5th Gen" == p['name'] for p in results_iphone)

    # Test 2: Cari dengan limit
    results_samsung_limited = service.search_products("samsung", limit=1)
    assert len(results_samsung_limited) == 1
    assert "Samsung" in results_samsung_limited[0]['brand']

    # Test 3: Cari dengan kata kunci yang tidak ada
    results_not_found = service.search_products("produk_yang_tidak_ada_sama_sekali")
    assert len(results_not_found) == 0

    # Test 4: Cari dengan filter harga dari keyword (misal: "laptop 20 juta")
    # ASUS ROG Strix G15 (18M) harusnya masuk, MacBook Pro 14 (35M) tidak
    results_price_laptop = service.search_products("laptop 20 juta")
    assert len(results_price_laptop) > 0
    # Semua produk yang ditemukan harus di bawah atau sama dengan 20 juta
    assert all(p.get('price', 0) <= 20000000 for p in results_price_laptop)
    # Pastikan ASUS ROG Strix G15 ada
    assert any("ASUS ROG Strix G15" == p['name'] for p in results_price_laptop)
    # Pastikan MacBook Pro (yang 35 juta) tidak ada karena melebihi batas harga
    assert not any("MacBook Pro 14 inch M3" == p['name'] for p in results_price_laptop)

    # Test 5: Cari dengan keyword budget (misal: "smartphone murah")
    # Keyword 'murah' memicu batas harga 5 juta
    results_budget_smartphone = service.search_products("smartphone murah")
    assert len(results_budget_smartphone) > 0
    # Pastikan produk-produk yang masuk di bawah 5 juta
    assert all(p.get('price', 0) <= 5000000 for p in results_budget_smartphone)
    # AirPods Pro (4.5M) adalah produk yang cocok dengan kategori 'murah'
    assert any("AirPods Pro 2nd Gen" == p['name'] for p in results_budget_smartphone)
    # Smartphone seperti iPhone (25M) atau Samsung S24 (22M) tidak boleh masuk
    assert not any("iPhone 15 Pro Max" == p['name'] for p in results_budget_smartphone)
    assert not any("Samsung Galaxy S24 Ultra" == p['name'] for p in results_budget_smartphone)

    # Test 6: Pencarian dengan keyword kosong (harus mengembalikan produk dengan limit)
    results_empty_keyword = service.search_products("", limit=3)
    assert len(results_empty_keyword) == 3
    # Pastikan ini adalah produk yang valid (bukan list kosong)
    assert all(isinstance(p, dict) and 'id' in p for p in results_empty_keyword)
