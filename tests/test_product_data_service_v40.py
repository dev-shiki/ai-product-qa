import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    from app.services.product_data_service import ProductDataService
    
    # Mock data yang akan dikembalikan oleh LocalProductService
    mock_products_from_local = [
        {"id": "prod1", "name": "Product A", "category": "Electronics"},
        {"id": "prod2", "name": "Product B", "category": "Electronics"},
        {"id": "prod3", "name": "Product C", "category": "Electronics"},
        {"id": "prod4", "name": "Product D", "category": "Electronics"},
        {"id": "prod5", "name": "Product E", "category": "Electronics"},
    ]

    # Buat mock untuk instance LocalProductService
    mock_local_service_instance = mocker.Mock()
    # Atur nilai kembalian untuk metode get_products_by_category dari mock
    mock_local_service_instance.get_products_by_category.return_value = mock_products_from_local
    
    # Patch kelas LocalProductService agar setiap kali ProductDataService dibuat,
    # ia menggunakan instance mock kita sebagai self.local_service
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service_instance)

    # Inisialisasi ProductDataService, yang kini akan menggunakan mock LocalProductService
    service = ProductDataService()

    # Parameter untuk pengujian
    test_category = "Electronics"
    test_limit = 3

    # Panggil fungsi yang akan diuji
    result_products = service.get_products_by_category(test_category, test_limit)

    # Assertions
    # Memastikan hasilnya adalah list
    assert isinstance(result_products, list)
    
    # Memastikan jumlah produk yang dikembalikan sesuai limit
    assert len(result_products) == test_limit
    
    # Memastikan metode mock dipanggil dengan argumen yang benar
    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category)
    
    # Memastikan produk yang dikembalikan sesuai dengan mock data dan sudah dipotong
    assert result_products[0]["id"] == "prod1"
    assert result_products[1]["id"] == "prod2"
    assert result_products[2]["id"] == "prod3"
    
    # Test case: Ketika jumlah produk di LocalProductService lebih sedikit dari limit
    mock_products_less = [
        {"id": "book1", "name": "Book X", "category": "Books"},
        {"id": "book2", "name": "Book Y", "category": "Books"},
    ]
    mock_local_service_instance.get_products_by_category.return_value = mock_products_less
    
    test_category_less = "Books"
    test_limit_less = 5 # Meminta 5, tapi hanya ada 2 di mock
    
    result_products_less = service.get_products_by_category(test_category_less, test_limit_less)
    
    assert isinstance(result_products_less, list)
    assert len(result_products_less) == len(mock_products_less) # Seharusnya 2
    mock_local_service_instance.get_products_by_category.assert_called_with(test_category_less)

    # Test case: Penanganan error
    mock_local_service_instance.get_products_by_category.side_effect = Exception("Simulated error during fetch")
    result_on_error = service.get_products_by_category("NonExistent", 10)
    assert result_on_error == [] # Seharusnya mengembalikan list kosong saat error
    mock_local_service_instance.get_products_by_category.assert_called_with("NonExistent")
