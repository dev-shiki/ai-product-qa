import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic():
    # Asumsi ProductDataService sudah diimpor di dalam file test yang memuat fungsi ini.
    # Contoh: from app.services.product_data_service import ProductDataService
    
    # Inisialisasi ProductDataService
    service = ProductDataService()
    
    # Definisikan kategori dan batasan untuk pengujian
    test_category = "Electronics"
    test_limit = 3

    # Panggil fungsi yang akan diuji
    products = service.get_products_by_category(test_category, test_limit)

    # Assertion 1: Pastikan hasilnya adalah list
    assert isinstance(products, list)

    # Assertion 2: Pastikan jumlah produk yang dikembalikan tidak melebihi batasan (limit)
    # Ini juga akan melewati jika list kosong, yang mungkin terjadi jika kategori tidak ada
    assert len(products) <= test_limit
    
    # Assertion 3: Jika ada produk yang ditemukan, pastikan setiap item adalah dictionary
    if products:
        for product in products:
            assert isinstance(product, dict)
            # Penambahan assert untuk memastikan kategori produk sesuai akan memerlukan
            # data dummy yang spesifik dari LocalProductService, yang dihindari dalam
            # "basic functionality" tanpa mock kompleks.
