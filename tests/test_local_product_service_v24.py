import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Menginisiasi LocalProductService. Ini akan memuat produk dari JSON atau menggunakan fallback.
    service = LocalProductService()

    # Test Case 1: Pencarian dengan kata kunci yang seharusnya menemukan hasil
    keyword_found = "iphone"
    results_found = service.search_products(keyword_found)
    assert len(results_found) > 0, f"Expected products for '{keyword_found}', but got none."
    # Memastikan produk spesifik ada di hasil (pencarian tidak case-sensitive)
    assert any("iPhone 15 Pro Max" == p["name"] for p in results_found), "iPhone 15 Pro Max not found in results for 'iphone'."

    # Test Case 2: Pencarian dengan kata kunci dan batasan jumlah hasil (limit)
    keyword_limited = "samsung"
    limit_value = 1
    results_limited = service.search_products(keyword_limited, limit=limit_value)
    assert len(results_limited) == limit_value, f"Expected {limit_value} product(s) for '{keyword_limited}', but got {len(results_limited)}."
    assert any("Samsung" in p["brand"] for p in results_limited), "Limited search did not return a Samsung product."

    # Test Case 3: Pencarian dengan kata kunci yang tidak ada, diharapkan tidak ada hasil
    keyword_not_found = "NonExistentGadget999"
    results_not_found = service.search_products(keyword_not_found)
    assert len(results_not_found) == 0, f"Expected no products for '{keyword_not_found}', but got {len(results_not_found)}."

    # Test Case 4: Pencarian dengan kata kunci kosong, diharapkan mengembalikan semua produk (hingga batas default)
    # Berdasarkan kode fallback, ada 8 produk. Batas default search_products adalah 10.
    results_all = service.search_products("")
    assert len(results_all) == 8, f"Expected 8 products for empty keyword, but got {len(results_all)}."
