import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Asumsi: LocalProductService akan menginisialisasi produk, baik dari file JSON
    # atau menggunakan produk fallback jika file tidak ditemukan,
    # sehingga service.products akan berisi data produk yang dapat dicari.
    service = LocalProductService()

    # Test Case 1: Pencarian dengan kata kunci umum ("Apple")
    # Diharapkan menemukan beberapa produk terkait "Apple".
    results_apple = service.search_products("Apple")
    assert len(results_apple) > 0, "Seharusnya menemukan produk untuk kata kunci 'Apple'"
    assert any("apple" in p.get('brand', '').lower() or "apple" in p.get('name', '').lower() for p in results_apple), \
        "Setidaknya satu produk yang ditemukan harus relevan dengan 'Apple'"

    # Test Case 2: Pencarian dengan kata kunci kategori ("Smartphone")
    # Diharapkan menemukan produk yang dikategorikan sebagai 'Smartphone'.
    results_smartphone = service.search_products("Smartphone")
    assert len(results_smartphone) > 0, "Seharusnya menemukan produk untuk kategori 'Smartphone'"
    assert any("smartphone" in p.get('category', '').lower() for p in results_smartphone), \
        "Setidaknya satu produk yang ditemukan harus relevan dengan kategori 'Smartphone'"

    # Test Case 3: Menguji parameter 'limit'
    # Pencarian dengan kata kunci umum ("product") yang mencocokkan banyak produk,
    # dan memastikan jumlah hasil tidak melebihi batas yang ditentukan.
    results_limited = service.search_products("product", limit=2)
    assert len(results_limited) <= 2, "Jumlah hasil seharusnya tidak melebihi batas yang ditentukan (limit=2)"

    # Test Case 4: Pencarian dengan kata kunci yang tidak ada/tidak cocok
    # Diharapkan mengembalikan daftar kosong.
    results_no_match = service.search_products("NonExistentProductXYZ123")
    assert len(results_no_match) == 0, "Seharusnya tidak ada hasil untuk kata kunci yang tidak cocok"

    # Test Case 5: Pencarian dengan kata kunci yang mengandung informasi harga
    # Ini menguji apakah fungsi dapat memproses kata kunci tersebut tanpa error
    # dan mengembalikan hasil yang relevan.
    results_with_price_keyword = service.search_products("laptop 15 juta")
    assert len(results_with_price_keyword) > 0, "Seharusnya menemukan produk ketika kata kunci termasuk harga"
    assert any("laptop" in p.get('category', '').lower() or "laptop" in p.get('name', '').lower() for p in results_with_price_keyword), \
        "Setidaknya satu produk yang ditemukan harus relevan dengan 'laptop'"
