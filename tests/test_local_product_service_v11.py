import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Asumsi LocalProductService sudah diimpor dan tersedia di scope pengujian.
    # Instansiasi service, yang akan memuat produk dari file atau fallback.
    service = LocalProductService()

    # Test 1: Pencarian dasar berdasarkan nama produk (case insensitive)
    results_iphone = service.search_products("iPhone")
    assert len(results_iphone) > 0
    assert any("iPhone 15 Pro Max" in p["name"] for p in results_iphone)

    # Test 2: Pencarian berdasarkan merek
    results_samsung = service.search_products("Samsung")
    assert len(results_samsung) > 0
    assert any("Samsung Galaxy S24 Ultra" in p["name"] for p in results_samsung)

    # Test 3: Pencarian berdasarkan kategori
    results_laptop = service.search_products("Laptop")
    assert len(results_laptop) > 0
    assert any("MacBook Pro 14 inch M3" in p["name"] for p in results_laptop)
    assert any("ASUS ROG Strix G15" in p["name"] for p in results_laptop)

    # Test 4: Pencarian dengan batasan (limit)
    results_limited = service.search_products("Apple", limit=2)
    assert len(results_limited) <= 2
    assert all("Apple" in p["brand"] for p in results_limited)

    # Test 5: Pencarian dengan kata kunci harga (misalnya "laptop 20 juta")
    # Ini harusnya menemukan ASUS ROG Strix G15 (18 juta)
    results_price_laptop = service.search_products("laptop 20 juta")
    assert len(results_price_laptop) > 0
    assert any("ASUS ROG Strix G15" in p["name"] for p in results_price_laptop)
    # Pastikan produk lain dengan harga di atas batas tidak muncul
    assert not any("MacBook Pro 14 inch M3" in p["name"] for p in results_price_laptop if p["price"] > 20000000)

    # Test 6: Pencarian dengan kata kunci 'murah' (menggunakan harga fallback default)
    # Ini harusnya memprioritaskan produk dengan harga lebih rendah yang relevan
    results_cheap_phone = service.search_products("smartphone murah")
    assert len(results_cheap_phone) > 0
    # Jika ada, seharusnya Samsung Galaxy S24 Ultra (22jt) akan lebih prioritas dari iPhone (25jt)
    # berdasarkan logic scoring (10M - price)
    if "Samsung Galaxy S24 Ultra" in results_cheap_phone[0]["name"] or "iPhone 15 Pro Max" in results_cheap_phone[0]["name"]:
        # Specific check: Samsung is cheaper among fallback phones, so it should be prioritized for "murah"
        assert results_cheap_phone[0]["name"] == "Samsung Galaxy S24 Ultra"

    # Test 7: Pencarian yang tidak ditemukan
    results_no_match = service.search_products("ProdukYangTidakAda")
    assert len(results_no_match) == 0

    # Test 8: Pencarian dengan keyword kosong (harusnya mengembalikan semua produk hingga limit)
    # Dalam implementasi ini, keyword kosong akan cocok dengan semua string.
    # Asumsi: fallback_products memiliki 8 produk.
    results_empty_keyword = service.search_products("", limit=10)
    assert len(results_empty_keyword) == 8 # Sesuai jumlah produk fallback

    # Test 9: Pencarian dengan keyword yang terdapat di deskripsi atau spesifikasi
    results_processor = service.search_products("A17 Pro")
    assert len(results_processor) > 0
    assert any("iPhone 15 Pro Max" in p["name"] for p in results_processor)
<ctrl63>
