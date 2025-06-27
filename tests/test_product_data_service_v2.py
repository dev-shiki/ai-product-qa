import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # 1. Siapkan data mock untuk LocalProductService.get_products_by_category
    mock_products = [
        {'id': 'prod1', 'name': 'Smartphone X', 'category': 'Electronics'},
        {'id': 'prod2', 'name': 'Laptop Pro', 'category': 'Electronics'},
        {'id': 'prod3', 'name': 'Wireless Earbuds', 'category': 'Electronics'},
        {'id': 'prod4', 'name': 'Smartwatch Z', 'category': 'Electronics'},
        {'id': 'prod5', 'name': 'Gaming Console', 'category': 'Electronics'},
    ]

    # 2. Buat instance mock untuk LocalProductService
    mock_local_service_instance = mocker.MagicMock()
    mock_local_service_instance.get_products_by_category.return_value = mock_products

    # 3. Patch definisi kelas LocalProductService
    # Ini memastikan bahwa ketika ProductDataService() diinisialisasi,
    # ia akan menggunakan mock kita untuk atribut 'local_service' nya.
    # Jalur 'app.services.product_data_service.LocalProductService'
    # adalah jalur impor penuh ke kelas yang di-mock.
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service_instance)

    # 4. Inisialisasi ProductDataService
    # Asumsikan ProductDataService tersedia dalam scope ini (misalnya, diimpor oleh test runner).
    service = ProductDataService()

    # 5. Definisikan parameter pengujian
    test_category = "Electronics"
    test_limit = 3

    # 6. Panggil metode yang akan diuji
    result_products = service.get_products_by_category(test_category, test_limit)

    # 7. Assertions (Verifikasi)
    # Verifikasi bahwa metode LocalProductService yang mendasari dipanggil dengan benar
    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category)

    # Verifikasi jumlah produk yang dikembalikan sesuai dengan limit
    assert len(result_products) == test_limit

    # Verifikasi bahwa semua produk yang dikembalikan termasuk dalam kategori yang benar
    assert all(product['category'] == test_category for product in result_products)

    # Verifikasi konten produk yang dikembalikan (misalnya, yang pertama dan terakhir dari limit)
    assert result_products[0] == {'id': 'prod1', 'name': 'Smartphone X', 'category': 'Electronics'}
    assert result_products[2] == {'id': 'prod3', 'name': 'Wireless Earbuds', 'category': 'Electronics'}
