import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Asumsikan ProductDataService tersedia dari import global di test file
    # Mock instance LocalProductService yang dibuat oleh ProductDataService
    # Kita akan mem-patch method get_products_by_category pada instance local_service yang ada.
    
    # 1. Inisialisasi ProductDataService untuk membuat instance local_service
    # Ini akan membuat ProductDataService memiliki instance self.local_service = LocalProductService()
    from app.services.product_data_service import ProductDataService
    service = ProductDataService()

    # 2. Mock method get_products_by_category dari instance self.local_service
    mock_local_service_get_by_category = mocker.patch.object(
        service.local_service,
        'get_products_by_category'
    )

    # 3. Definisikan nilai kembalian mock. Pastikan ada lebih banyak produk dari limit untuk menguji slicing.
    mock_products_from_service = [
        {"id": "p001", "name": "Laptop XPS", "category": "Electronics"},
        {"id": "p002", "name": "Smartphone A", "category": "Electronics"},
        {"id": "p003", "name": "Headphones ANC", "category": "Electronics"},
        {"id": "p004", "name": "Smartwatch V2", "category": "Electronics"},
        {"id": "p005", "name": "Monitor Ultrawide", "category": "Electronics"},
    ]
    mock_local_service_get_by_category.return_value = mock_products_from_service

    # 4. Definisikan parameter untuk fungsi yang akan diuji
    test_category = "Electronics"
    test_limit = 3

    # 5. Panggil fungsi yang sedang diuji
    result = service.get_products_by_category(test_category, test_limit)

    # 6. Lakukan assertion
    # Pastikan method di local_service dipanggil dengan argumen yang benar
    mock_local_service_get_by_category.assert_called_once_with(test_category)

    # Pastikan jumlah produk yang dikembalikan sesuai dengan limit
    assert len(result) == test_limit

    # Pastikan konten produk yang dikembalikan benar (hasil slicing dari mock data)
    expected_result = mock_products_from_service[:test_limit]
    assert result == expected_result
