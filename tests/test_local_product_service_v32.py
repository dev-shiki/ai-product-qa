import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Menginisialisasi service. Ini akan memuat produk dari file JSON
    # atau menggunakan fallback jika file tidak ditemukan.
    # Untuk unit test sederhana ini, kita berasumsi salah satu skenario berhasil.
    service = LocalProductService()

    # Test case 1: Pencarian dengan keyword yang jelas
    results_iphone = service.search_products("iPhone")
    assert len(results_iphone) > 0
    assert any("iPhone 15 Pro Max" == p["name"] for p in results_iphone)

    # Test case 2: Pencarian dengan keyword yang akan mengembalikan beberapa hasil
    results_samsung = service.search_products("Samsung")
    assert len(results_samsung) >= 2 # Harusnya ada S24 Ultra dan Tab S9
    assert any("Samsung Galaxy S24 Ultra" == p["name"] for p in results_samsung)
    assert any("Samsung Galaxy Tab S9" == p["name"] for p in results_samsung)

    # Test case 3: Pencarian dengan limit
    results_limited = service.search_products("Apple", limit=2)
    assert len(results_limited) == 2
    # Memastikan produk yang paling relevan (atau peringkat teratas berdasarkan scoring) ada
    assert "iPhone 15 Pro Max" in [p["name"] for p in results_limited] # iPhone should be high relevance for "Apple"

    # Test case 4: Pencarian dengan keyword harga (misal: "laptop 20 juta")
    results_price_laptop = service.search_products("laptop 20 juta")
    assert any("ASUS ROG Strix G15" == p["name"] for p in results_price_laptop) # ASUS ROG Strix G15 (18M) should be included
    assert not any("MacBook Pro 14 inch M3" == p["name"] for p in results_price_laptop) # MacBook Pro (35M) should be excluded

    # Test case 5: Pencarian dengan keyword "murah"
    results_budget = service.search_products("airpods murah")
    assert any("AirPods Pro 2nd Gen" == p["name"] for p in results_budget)
    # Memastikan produk yang dikembalikan memiliki harga di bawah ambang batas 'murah' (5 juta)
    for product in results_budget:
        assert product.get('price', 0) <= 5000000

    # Test case 6: Pencarian dengan keyword yang tidak ada
    results_no_match = service.search_products("ProdukTidakAdaXYZ")
    assert len(results_no_match) == 0

    # Test case 7: Pencarian dengan keyword kosong (harus mengembalikan semua produk hingga limit)
    results_empty_keyword = service.search_products("", limit=3)
    assert len(results_empty_keyword) == 3
    # Dengan keyword kosong, sorting mungkin berdasarkan urutan asli atau skor default.
    # Cukup pastikan ada 3 produk yang dikembalikan.
