import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # 1. Siapkan data tiruan (mock data) yang akan dikembalikan oleh layanan lokal.
    mock_products_from_local_service = [
        {"id": "P1", "name": "Smartphone Pro", "category": "Electronics"},
        {"id": "P2", "name": "Laptop Ultra", "category": "Electronics"},
        {"id": "P3", "name": "Wireless Headphones", "category": "Electronics"},
        {"id": "P4", "name": "Smart TV 4K", "category": "Electronics"},
    ]

    # 2. Gunakan 'mocker' untuk mengganti metode internal yang dipanggil oleh fungsi target.
    #    ProductDataService.get_products_by_category memanggil self.local_service.get_products_by_category.
    #    Kita perlu meniru (patch) metode 'get_products_by_category' dari kelas LocalProductService.
    mock_local_service_method = mocker.patch(
        'app.services.local_product_service.LocalProductService.get_products_by_category',
        return_value=mock_products_from_local_service
    )

    # 3. Inisialisasi instance dari kelas ProductDataService yang akan diuji.
    service = ProductDataService()

    # 4. Tentukan parameter input untuk fungsi yang akan diuji.
    test_category = "Electronics"
    test_limit = 2

    # 5. Panggil fungsi yang akan diuji.
    result_products = service.get_products_by_category(test_category, test_limit)

    # 6. Lakukan asersi untuk memverifikasi hasil:
    #    a. Pastikan metode internal LocalProductService dipanggil dengan argumen yang benar.
    mock_local_service_method.assert_called_once_with(test_category)

    #    b. Pastikan panjang daftar produk yang dikembalikan sesuai dengan 'limit'.
    assert len(result_products) == test_limit

    #    c. Pastikan isi daftar produk yang dikembalikan sesuai dengan data tiruan dan batasan 'limit'.
    assert result_products == mock_products_from_local_service[:test_limit]
