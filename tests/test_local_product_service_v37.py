import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Asumsikan LocalProductService sudah diimpor dan tersedia di scope ini
    # from app.services.local_product_service import LocalProductService

    service = LocalProductService()

    # Mengganti daftar produk internal dengan data dummy untuk pengujian yang terisolasi
    # Ini menghindari ketergantungan pada file system (products.json)
    service.products = [
        {
            "id": "1", "name": "Laptop Gaming Pro", "category": "Laptop", "brand": "TechBrand",
            "price": 15000000, "currency": "IDR", "description": "Powerful gaming laptop.",
            "specifications": {"rating": 4.5, "sold": 500, "stock": 20}
        },
        {
            "id": "2", "name": "Smartphone Ultra", "category": "Smartphone", "brand": "MobileCorp",
            "price": 12000000, "currency": "IDR", "description": "High-end smartphone with great camera.",
            "specifications": {"rating": 4.8, "sold": 1200, "stock": 50}
        },
        {
            "id": "3", "name": "Wireless Earbuds", "category": "Audio", "brand": "SoundGen",
            "price": 1500000, "currency": "IDR", "description": "Noise-cancelling earbuds.",
            "specifications": {"rating": 4.2, "sold": 800, "stock": 100}
        },
        {
            "id": "4", "name": "Smartwatch X", "category": "Wearable", "brand": "WatchTech",
            "price": 3000000, "currency": "IDR", "description": "Advanced smartwatch with health tracking.",
            "specifications": {"rating": 4.0, "sold": 300, "stock": 30}
        },
        {
            "id": "5", "name": "Basic Laptop", "category": "Laptop", "brand": "EcoComp",
            "price": 4000000, "currency": "IDR", "description": "Affordable laptop for daily use.",
            "specifications": {"rating": 3.8, "sold": 1500, "stock": 80}
        },
        {
            "id": "6", "name": "iPhone 13", "category": "Smartphone", "brand": "Apple",
            "price": 10000000, "currency": "IDR", "description": "Apple iPhone 13.",
            "specifications": {"rating": 4.7, "sold": 2000, "stock": 60}
        }
    ]

    # Test Case 1: Pencarian keyword dasar (case-insensitive)
    results = service.search_products("laptop")
    assert len(results) == 2
    assert any(p["name"] == "Laptop Gaming Pro" for p in results)
    assert any(p["name"] == "Basic Laptop" for p in results)

    # Test Case 2: Pencarian dengan keyword berbeda
    results = service.search_products("smartphone")
    assert len(results) == 2
    assert any(p["name"] == "Smartphone Ultra" for p in results)
    assert any(p["name"] == "iPhone 13" for p in results)

    # Test Case 3: Pencarian berdasarkan brand
    results = service.search_products("apple")
    assert len(results) == 1
    assert results[0]["name"] == "iPhone 13"

    # Test Case 4: Pencarian produk yang tidak ada
    results = service.search_products("chair")
    assert len(results) == 0

    # Test Case 5: Fungsionalitas limit
    results = service.search_products("laptop", limit=1)
    assert len(results) == 1
    assert results[0]["name"] in ["Laptop Gaming Pro", "Basic Laptop"] # Urutan bisa bervariasi karena skor relevansi sama

    # Test Case 6: Pencarian dengan filter harga eksplisit (misal "laptop 5 juta")
    # Logika search_products akan memasukkan produk di bawah harga YANG DIKUTIP ATAU
    # produk yang cocok dengan keyword teks.
    # Produk <= 5 juta: Wireless Earbuds (1.5Juta), Smartwatch X (3Juta), Basic Laptop (4Juta)
    # Produk yang mengandung "laptop": Laptop Gaming Pro (15Juta), Basic Laptop (4Juta)
    # Hasil unik yang diharapkan: Laptop Gaming Pro, Wireless Earbuds, Smartwatch X, Basic Laptop
    results = service.search_products("laptop 5 juta")
    assert len(results) == 4
    expected_names_price_search = {"Laptop Gaming Pro", "Wireless Earbuds", "Smartwatch X", "Basic Laptop"}
    found_names_price_search = {p["name"] for p in results}
    assert found_names_price_search == expected_names_price_search
    # Verifikasi urutan berdasarkan skor relevansi (Basic Laptop, Wireless Earbuds, Smartwatch X, Laptop Gaming Pro)
    assert results[0]["name"] == "Basic Laptop"
    assert results[1]["name"] == "Wireless Earbuds"
    assert results[2]["name"] == "Smartwatch X"
    assert results[3]["name"] == "Laptop Gaming Pro"

    # Test Case 7: Pencarian dengan kata kunci budget (misal "earbuds murah")
    # "murah" mengindikasikan harga maksimal 5.000.000.
    # Produk <= 5 juta: Wireless Earbuds (1.5Juta), Smartwatch X (3Juta), Basic Laptop (4Juta)
    # Produk yang mengandung "earbuds": Wireless Earbuds (1.5Juta)
    # Hasil unik yang diharapkan: Wireless Earbuds, Smartwatch X, Basic Laptop
    results = service.search_products("earbuds murah")
    assert len(results) == 3
    expected_names_budget_search = {"Wireless Earbuds", "Smartwatch X", "Basic Laptop"}
    found_names_budget_search = {p["name"] for p in results}
    assert found_names_budget_search == expected_names_budget_search
    # Verifikasi urutan berdasarkan skor relevansi (Wireless Earbuds, Smartwatch X, Basic Laptop)
    assert results[0]["name"] == "Wireless Earbuds"
    assert results[1]["name"] == "Smartwatch X"
    assert results[2]["name"] == "Basic Laptop"
