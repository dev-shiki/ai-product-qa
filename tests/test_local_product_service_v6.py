import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Menginisialisasi service
    # Asumsi LocalProductService sudah tersedia di scope atau diimpor sebelumnya
    # Karena instruksi "JANGAN menambahkan import statement (sudah disediakan)",
    # kita tidak akan menulis 'from app.services.local_product_service import LocalProductService'
    
    # Untuk tujuan testing, kita akan membuat instance dan langsung menimpa
    # atribut `products` agar tidak bergantung pada pembacaan file `products.json`
    # yang dapat membuat test menjadi rumit dan tidak stabil.
    # Ini adalah cara sederhana untuk mengontrol data yang digunakan fungsi.
    service = LocalProductService()

    # Data produk dummy yang akan digunakan untuk testing
    service.products = [
        {"id": "1", "name": "iPhone 15 Pro Max", "category": "Smartphone", "brand": "Apple", "price": 25000000, "description": "High-end Apple smartphone.", "specifications": {"rating": 4.8, "sold": 1250}},
        {"id": "2", "name": "Samsung Galaxy S24 Ultra", "category": "Smartphone", "brand": "Samsung", "price": 22000000, "description": "Premium Samsung smartphone with S-Pen.", "specifications": {"rating": 4.7, "sold": 980}},
        {"id": "3", "name": "MacBook Pro 14 inch M3", "category": "Laptop", "brand": "Apple", "price": 35000000, "description": "Powerful Apple laptop for professionals.", "specifications": {"rating": 4.9, "sold": 450}},
        {"id": "4", "name": "ASUS ROG Strix G15", "category": "Laptop", "brand": "ASUS", "price": 18000000, "description": "Gaming laptop with RTX 4060.", "specifications": {"rating": 4.4, "sold": 320}},
        {"id": "5", "name": "Sony WH-1000XM5", "category": "Audio", "brand": "Sony", "price": 5500000, "description": "Industry-leading noise cancelling headphones.", "specifications": {"rating": 4.8, "sold": 890}},
        {"id": "6", "name": "Xiaomi Redmi Note 12", "category": "Smartphone", "brand": "Xiaomi", "price": 2500000, "description": "Affordable Android smartphone.", "specifications": {"rating": 4.0, "sold": 5000}},
        {"id": "7", "name": "Headphone Murah", "category": "Audio", "brand": "Generic", "price": 500000, "description": "Budget friendly headphones.", "specifications": {"rating": 3.5, "sold": 700}},
    ]

    # Test Case 1: Pencarian dengan kata kunci sederhana (match di 'name')
    results = service.search_products("iPhone")
    assert len(results) == 1
    assert results[0]["id"] == "1"
    assert results[0]["name"] == "iPhone 15 Pro Max"

    # Test Case 2: Pencarian dengan kata kunci (match di 'description')
    results = service.search_products("gaming")
    assert len(results) == 1
    assert results[0]["id"] == "4"
    assert results[0]["name"] == "ASUS ROG Strix G15"

    # Test Case 3: Pencarian yang case-insensitive
    results = service.search_products("smartphone")
    assert len(results) == 3 # iPhone, Samsung, Xiaomi
    expected_ids = {"1", "2", "6"}
    actual_ids = {p["id"] for p in results}
    assert actual_ids == expected_ids

    # Test Case 4: Pencarian tanpa hasil
    results = service.search_products("Kamera Digital")
    assert len(results) == 0

    # Test Case 5: Menggunakan parameter 'limit'
    results = service.search_products("Smartphone", limit=1)
    assert len(results) == 1
    # Pastikan hasil yang dikembalikan adalah salah satu dari produk smartphone yang ada
    assert results[0]["id"] in {"1", "2", "6"}

    # Test Case 6: Pencarian dengan ekstrak harga (e.g., "smartphone 3 juta")
    # Ini harus menemukan Xiaomi Redmi Note 12 karena harganya <= 3 juta
    results = service.search_products("smartphone 3 juta")
    assert len(results) == 1
    assert results[0]["id"] == "6"
    assert results[0]["name"] == "Xiaomi Redmi Note 12"

    # Test Case 7: Pencarian dengan kata kunci 'budget' (murah)
    # Ini harus menemukan "Headphone Murah" karena harganya <= 5 juta (sesuai definisi 'murah')
    results = service.search_products("headphone murah")
    assert len(results) == 1
    assert results[0]["id"] == "7"
    assert results[0]["name"] == "Headphone Murah"

    # Test Case 8: Pencarian dengan kata kunci brand
    results = service.search_products("Apple")
    assert len(results) == 2
    actual_ids = {p["id"] for p in results}
    assert actual_ids == {"1", "3"} # iPhone and MacBook

    # Test Case 9: Pencarian dengan kata kunci kategori
    results = service.search_products("Audio")
    assert len(results) == 2
    actual_ids = {p["id"] for p in results}
    assert actual_ids == {"5", "7"} # Sony WH-1000XM5 and Headphone Murah
