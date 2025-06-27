import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Mengimport LocalProductService secara lokal di dalam fungsi test
    # Ini untuk mematuhi aturan "JANGAN menambahkan import statement" di bagian atas file
    # namun tetap memungkinkan fungsi test untuk berjalan dengan benar.
    # Pada praktiknya, 'from app.services.local_product_service import LocalProductService'
    # akan diletakkan di bagian atas file test jika ini adalah file test mandiri.
    from app.services.local_product_service import LocalProductService

    # Inisiasi service. Ini akan memuat produk (dari file JSON atau fallback)
    service = LocalProductService()

    # Test 1: Cari dengan keyword umum (case-insensitive)
    keyword_1 = "iphone"
    results_1 = service.search_products(keyword_1)

    assert isinstance(results_1, list)
    assert len(results_1) > 0, f"Seharusnya menemukan produk untuk keyword '{keyword_1}'"
    # Pastikan produk spesifik ditemukan
    assert any(p.get('name') == "iPhone 15 Pro Max" for p in results_1), \
        f"'iPhone 15 Pro Max' tidak ditemukan untuk keyword '{keyword_1}'"
    assert len(results_1) <= 10, "Jumlah hasil seharusnya tidak melebihi limit default (10)"

    # Test 2: Cari dengan keyword yang diharapkan mengembalikan beberapa hasil
    keyword_2 = "Apple"
    results_2 = service.search_products(keyword_2)

    assert isinstance(results_2, list)
    assert len(results_2) >= 3, f"Seharusnya menemukan setidaknya 3 produk untuk keyword '{keyword_2}'"
    # Pastikan beberapa produk Apple yang berbeda ditemukan
    assert any(p.get('name') == "MacBook Pro 14 inch M3" for p in results_2)
    assert any(p.get('name') == "AirPods Pro 2nd Gen" for p in results_2)
    assert len(results_2) <= 10, "Jumlah hasil seharusnya tidak melebihi limit default (10)"

    # Test 3: Cari dengan limit spesifik
    keyword_3 = "Laptop"
    limit_3 = 1
    results_3 = service.search_products(keyword_3, limit=limit_3)

    assert isinstance(results_3, list)
    assert len(results_3) == limit_3, f"Jumlah hasil seharusnya sama dengan limit yang ditentukan ({limit_3})"
    # Pastikan produk yang dikembalikan adalah laptop
    assert any(p.get('category') == "Laptop" for p in results_3), "Produk yang dikembalikan seharusnya berkategori 'Laptop'"

    # Test 4: Cari dengan keyword yang tidak ada
    keyword_4 = "produknonsenseabcd"
    results_4 = service.search_products(keyword_4)

    assert isinstance(results_4, list)
    assert len(results_4) == 0, f"Seharusnya mengembalikan list kosong untuk keyword yang tidak ada '{keyword_4}'"

    # Test 5: Cari dengan keyword yang menyertakan batasan harga (misal: "laptop 20 juta")
    # Dengan produk fallback: ASUS ROG Strix G15 (18 jt), MacBook Pro 14 inch M3 (35 jt)
    # Keyword "laptop 20 juta" seharusnya menemukan ASUS ROG tapi tidak MacBook Pro
    keyword_5 = "laptop 20 juta"
    results_5 = service.search_products(keyword_5)

    assert isinstance(results_5, list)
    assert any(p.get('name') == "ASUS ROG Strix G15" for p in results_5), \
        f"ASUS ROG Strix G15 seharusnya ditemukan dalam pencarian '{keyword_5}'"
    assert not any(p.get('name') == "MacBook Pro 14 inch M3" for p in results_5), \
        f"MacBook Pro 14 inch M3 seharusnya TIDAK ditemukan dalam pencarian '{keyword_5}' karena melebihi harga"
