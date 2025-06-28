import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Asumsi ProductDataService diimpor di level modul tes (tidak di dalam fungsi ini)
    from app.services.product_data_service import ProductDataService

    # Inisialisasi ProductDataService
    service = ProductDataService()

    # Data dummy yang akan dikembalikan oleh mock LocalProductService
    mock_products_data = [
        {"id": "p1", "name": "Laptop XYZ", "category": "Electronics"},
        {"id": "p2", "name": "Smartphone ABC", "category": "Electronics"},
        {"id": "p3", "name": "Tablet Pro", "category": "Electronics"},
        {"id": "p4", "name": "Headphones", "category": "Audio"},
        {"id": "p5", "name": "Smartwatch", "category": "Wearables"},
    ]

    # Mock metode get_products_by_category dari service.local_service
    # Ini memastikan bahwa kita hanya menguji logika di ProductDataService,
    # bukan implementasi dari LocalProductService yang sebenarnya.
    mock_get_products = mocker.patch.object(
        service.local_service,
        'get_products_by_category',
        return_value=[p for p in mock_products_data if p['category'] == "Electronics"]
    )

    # --- Test Case 1: Kategori ditemukan, limit berlaku ---
    category_electronics = "Electronics"
    limit_test = 2
    result = service.get_products_by_category(category_electronics, limit_test)

    # Verifikasi bahwa mock dipanggil dengan argumen yang benar
    mock_get_products.assert_called_once_with(category_electronics)
    # Verifikasi output sesuai dengan ekspektasi (data dipotong berdasarkan limit)
    assert len(result) == limit_test
    assert result == [
        {"id": "p1", "name": "Laptop XYZ", "category": "Electronics"},
        {"id": "p2", "name": "Smartphone ABC", "category": "Electronics"}
    ]

    # --- Test Case 2: Kategori tidak ditemukan (mengembalikan list kosong) ---
    # Reset mock untuk skenario baru
    mock_get_products.reset_mock()
    mock_get_products.return_value = [] # Set mock untuk mengembalikan list kosong

    category_non_existent = "NonExistentCategory"
    result_empty = service.get_products_by_category(category_non_existent)

    # Verifikasi pemanggilan dan output
    mock_get_products.assert_called_once_with(category_non_existent)
    assert result_empty == []

    # --- Test Case 3: Penanganan error (mengembalikan list kosong) ---
    # Reset mock untuk skenario error
    mock_get_products.reset_mock()
    mock_get_products.side_effect = Exception("Mocked error during category retrieval")

    category_error = "CategoryWithError"
    result_error = service.get_products_by_category(category_error)

    # Verifikasi pemanggilan dan output saat terjadi error
    mock_get_products.assert_called_once_with(category_error)
    assert result_error == []
