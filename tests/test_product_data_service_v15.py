import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic():
    # Asumsi ProductDataService sudah diimpor dan tersedia di scope ini.
    # Dalam skenario pytest nyata, Anda akan memiliki:
    # from app.services.product_data_service import ProductDataService

    # Buat mock sederhana untuk LocalProductService
    # Ini diperlukan karena ProductDataService menginisialisasi LocalProductService
    # secara internal, dan kita tidak diizinkan menggunakan mock yang "rumit"
    # atau fixture seperti monkeypatch.
    class MockLocalProductService:
        def get_products_by_category(self, category: str):
            if category == "Electronics":
                # Mengembalikan daftar yang lebih panjang dari batas default (10)
                # untuk menguji logika pemotongan [:limit] di ProductDataService.
                return [
                    {"id": f"e{i}", "name": f"Electronic Item {i}", "category": "Electronics"}
                    for i in range(20)
                ]
            elif category == "Books":
                return [
                    {"id": "b1", "name": "The Great Novel", "category": "Books"},
                    {"id": "b2", "name": "Python for Dummies", "category": "Books"},
                ]
            return [] # Untuk kategori lain, kembalikan kosong

    # Inisialisasi ProductDataService
    service = ProductDataService()

    # Ganti instance local_service dengan mock kita
    service.local_service = MockLocalProductService()

    # Test Case 1: Mendapatkan produk dengan batas (limit) yang spesifik
    category_name = "Electronics"
    test_limit = 5
    products = service.get_products_by_category(category_name, test_limit)

    # Assertions
    assert isinstance(products, list)
    assert len(products) == test_limit
    assert all(p['category'] == category_name for p in products)
    assert products[0]['name'] == "Electronic Item 0" # Pastikan data dari mock yang digunakan

    # Test Case 2: Mendapatkan produk tanpa batas (menggunakan default limit 10)
    products_default_limit = service.get_products_by_category(category_name)
    assert isinstance(products_default_limit, list)
    assert len(products_default_limit) == 10 # Default limit
    assert all(p['category'] == category_name for p in products_default_limit)

    # Test Case 3: Kategori yang tidak ada
    products_non_existent = service.get_products_by_category("NonExistentCategory", 5)
    assert isinstance(products_non_existent, list)
    assert len(products_non_existent) == 0

    # Test Case 4: Kategori dengan jumlah item kurang dari limit
    products_books = service.get_products_by_category("Books", 5)
    assert isinstance(products_books, list)
    assert len(products_books) == 2 # Hanya ada 2 buku di mock data
    assert all(p['category'] == "Books" for p in products_books)

    # Test Case 5: Menangani Exception dari local_service
    class ErrorMockLocalProductService:
        def get_products_by_category(self, category: str):
            raise ValueError("Simulated error from LocalProductService")

    service.local_service = ErrorMockLocalProductService()
    products_on_error = service.get_products_by_category("AnyCategory", 5)
    assert isinstance(products_on_error, list)
    assert len(products_on_error) == 0 # Harus mengembalikan list kosong saat terjadi error
