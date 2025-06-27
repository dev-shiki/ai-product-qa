import pytest
from app.services.local_product_service import search_products

def test_search_products_basic():
    # Asumsi LocalProductService sudah diimpor di luar fungsi ini
    # (misalnya, from app.services.local_product_service import LocalProductService)
    service = LocalProductService()

    # Test 1: Pencarian dengan kata kunci sederhana
    results_iphone = service.search_products(keyword="iPhone")
    assert len(results_iphone) >= 1
    assert any("iPhone 15 Pro Max" in p.get('name', '') for p in results_iphone)

    # Test 2: Pencarian dengan kata kunci yang tidak ada
    results_none = service.search_products(keyword="produk_tidak_ada_xyz")
    assert len(results_none) == 0

    # Test 3: Pencarian dengan batasan limit
    results_limited = service.search_products(keyword="apple", limit=2)
    assert len(results_limited) == 2
    assert all("Apple" in p.get('brand', '') for p in results_limited)

    # Test 4: Pencarian dengan keyword harga (misal: "laptop 20 juta")
    # Logika search_products akan mencari produk <= harga yang diekstrak,
    # dan juga mencari keyword "laptop".
    # ASUS ROG Strix G15 (18jt) harusnya masuk.
    # MacBook Pro 14 inch M3 (35jt) juga harusnya masuk karena "laptop" ada di kategorinya,
    # meskipun harganya melebihi 20 juta (harga ini hanya sebagai filter awal, bukan eksklusi total).
    results_budget_laptop = service.search_products(keyword="laptop 20 juta")
    assert any("ASUS ROG Strix G15" in p.get('name', '') for p in results_budget_laptop)
    assert any("MacBook Pro 14 inch M3" in p.get('name', '') for p in results_budget_laptop)

    # Test 5: Pencarian hanya dengan indikator harga (misal: "murah" atau "5 juta")
    # "murah" akan mengaktifkan max_price = 5,000,000.
    # Hanya produk di bawah atau sama dengan harga ini yang harusnya muncul dari filter harga.
    results_cheap = service.search_products(keyword="murah")
    # AirPods Pro 2nd Gen (4.5jt) seharusnya ada
    assert "AirPods Pro 2nd Gen" in [p.get('name') for p in results_cheap]
    # Produk yang jauh lebih mahal (misal > 5jt) seharusnya tidak muncul jika hanya keyword harga.
    # Berdasarkan logika `search_products`, jika `max_price` diekstrak, produk dengan harga <= `max_price` akan ditambahkan.
    # Kemudian, jika keyword juga cocok di teks, itu juga ditambahkan.
    # Karena keyword hanya 'murah', tidak ada teks 'murah' di produk, maka hanya filter harga yang berlaku.
    assert all(p.get('price', 0) <= 5000000 for p in results_cheap)
<ctrl63>
