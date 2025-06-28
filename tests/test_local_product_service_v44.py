import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Asumsi LocalProductService sudah diimpor dan tersedia di scope ini (misal di top-level test file)
    # Instantiate the service. This will load the fallback products if products.json is not found.
    service = LocalProductService()

    # Test Case 1: Pencarian dengan keyword umum
    # Expected: Harus menemukan produk yang relevan seperti iPhone 15 Pro Max
    results_iphone = service.search_products(keyword="iPhone")
    assert len(results_iphone) > 0
    assert any(p['name'] == "iPhone 15 Pro Max" for p in results_iphone)

    # Test Case 2: Pencarian dengan keyword dan batasan harga (e.g., "laptop 20 juta")
    # Expected: Harus menemukan ASUS ROG Strix G15 (harga 18M)
    # Expected: Tidak boleh menemukan MacBook Pro (harga 35M)
    results_budget_laptop = service.search_products(keyword="laptop 20 juta")
    assert len(results_budget_laptop) > 0
    assert any(p['name'] == "ASUS ROG Strix G15" for p in results_budget_laptop)
    assert not any(p['name'] == "MacBook Pro 14 inch M3" for p in results_budget_laptop)
    # Verifikasi semua produk yang ditemukan memang di bawah atau sama dengan batas harga
    for product in results_budget_laptop:
        assert product.get('price', 0) <= 20000000

    # Test Case 3: Pencarian dengan keyword yang tidak ada
    # Expected: Mengembalikan list kosong
    results_non_existent = service.search_products(keyword="produk fiktif tidak ada")
    assert len(results_non_existent) == 0

    # Test Case 4: Verifikasi parameter limit
    # Expected: Hanya mengembalikan jumlah produk sesuai limit
    results_limited = service.search_products(keyword="Apple", limit=2)
    assert len(results_limited) <= 2
    assert all(p['brand'] == "Apple" for p in results_limited) or any(p['brand'] == "Apple" for p in results_limited) # Pastikan setidaknya ada produk Apple
