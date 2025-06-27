import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic():
    # Asumsi ProductDataService dan MagicMock sudah diimpor di scope file test.
    # Contoh:
    # from unittest.mock import MagicMock
    # from app.services.product_data_service import ProductDataService

    # Data dummy yang akan dikembalikan oleh mock LocalProductService
    mock_all_electronics_products = [
        {"id": "e1", "name": "Laptop", "category": "Electronics"},
        {"id": "e2", "name": "Smartphone", "category": "Electronics"},
        {"id": "e3", "name": "Tablet", "category": "Electronics"},
        {"id": "e4", "name": "Smart TV", "category": "Electronics"},
        {"id": "e5", "name": "Headphones", "category": "Electronics"},
    ]

    # Arrange: Setup ProductDataService dengan mock LocalProductService
    # Buat instance ProductDataService
    product_service = ProductDataService()
    
    # Buat objek MagicMock untuk menggantikan self.local_service
    mock_local_service = MagicMock()
    
    # Konfigurasi metode get_products_by_category pada mock untuk mengembalikan data dummy kita
    mock_local_service.get_products_by_category.return_value = mock_all_electronics_products
    
    # Ganti objek local_service yang asli dengan mock kita
    product_service.local_service = mock_local_service

    # Parameter untuk pengujian
    test_category = "Electronics"
    test_limit = 3
    
    # Act: Panggil fungsi yang akan diuji
    result = product_service.get_products_by_category(test_category, test_limit)

    # Assert 1: Pastikan metode get_products_by_category dari mock dipanggil dengan argumen yang benar
    mock_local_service.get_products_by_category.assert_called_once_with(test_category)
    
    # Assert 2: Pastikan hasil yang dikembalikan sesuai dengan ekspektasi (sudah terpotong sesuai limit)
    expected_result = mock_all_electronics_products[:test_limit]
    assert result == expected_result
    
    # Assert 3: Pastikan jumlah item yang dikembalikan sesuai dengan limit
    assert len(result) == test_limit
