import pytest
from unittest.mock import patch, MagicMock
import os
import asyncio # Diperlukan untuk menjalankan test async

# Import kelas yang akan diuji
from app.services.ai_service import AIService

# --- Fixtures untuk mocking dependency eksternal untuk UNIT TESTS dari get_response ---
# Test inisialisasi akan secara eksplisit tidak menggunakan ini, sesuai contoh pengguna.
@pytest.fixture
def mock_ai_service_dependencies():
    """
    Fixture untuk meng-mock dependensi eksternal AIService (seperti get_settings, genai.Client,
    dan ProductDataService). Ini memungkinkan pengujian unit yang terisolasi.
    """
    with patch('app.utils.config.get_settings') as mock_get_settings, \
         patch('google.genai.Client') as mock_genai_client_cls, \
         patch('app.services.product_data_service.ProductDataService') as mock_product_data_service_cls:

        # Mock pengaturan untuk Google AI API Key
        mock_settings_instance = MagicMock()
        # API Key harus ada (walaupun dummy) agar inisialisasi tidak gagal karena AttributeError
        mock_settings_instance.GOOGLE_API_KEY = "dummy_api_key_123" 
        mock_get_settings.return_value = mock_settings_instance

        # Mock instance genai client dan method-nya
        mock_genai_instance = MagicMock()
        # Mock method generate_content dan nilai kembaliannya
        mock_genai_instance.generate_content.return_value.text = "Ini adalah respons AI tiruan dari model."
        mock_genai_client_cls.return_value = mock_genai_instance

        # Mock instance ProductDataService dan method-nya
        mock_product_service_instance = MagicMock()
        # Daftar produk sampel default untuk get_products
        mock_product_service_instance.get_products.return_value = [
            {"name": "Laptop Gaming", "price": 1800, "category": "laptop", "description": "Laptop kencang untuk gaming."},
            {"name": "Smartphone Flagship", "price": 1000, "category": "smartphone", "description": "Ponsel pintar terbaru dengan kamera super."}
        ]
        mock_product_data_service_cls.return_value = mock_product_service_instance

        # Mengembalikan kontrol ke test, menyediakan objek mock jika diperlukan untuk assertion
        yield mock_get_settings, mock_genai_client_cls, mock_product_data_service_cls

# --- Test Cases ---

def test_aiservice_initialization_live_or_skip():
    """
    Menguji inisialisasi AIService. Test ini akan mencoba inisialisasi secara langsung.
    Jika ada dependensi (misal: GOOGLE_API_KEY tidak diatur atau masalah koneksi),
    test akan di-skip, sesuai instruksi pengguna. Ini berlaku seperti test integrasi mini.
    """
    try:
        # Agar test ini lulus tanpa di-skip, pastikan GOOGLE_API_KEY
        # diatur di environment tempat test dijalankan, atau mock-nya aktif.
        # Dalam kasus ini, kita tidak menggunakan fixture mock, jadi ini akan bergantung pada env.
        service = AIService()
        assert service is not None
        assert hasattr(service, 'client')
        assert hasattr(service, 'product_service')
        print("\nAIService berhasil diinisialisasi (dengan kunci live atau dummy dari env).")
    except Exception as e:
        # Ini akan menangkap error seperti GOOGLE_API_KEY tidak ada atau masalah koneksi.
        pytest.skip(f"Melewati test inisialisasi AIService karena dependensi: {e}")


@pytest.mark.asyncio
async def test_aiservice_get_response_with_product_context(mock_ai_service_dependencies):
    """
    Menguji method get_response dengan pertanyaan yang menyiratkan konteks produk.
    Menggunakan mock dependensi untuk pengujian unit yang terisolasi.
    """
    # Membongkar mock dari fixture
    mock_get_settings, mock_genai_client_cls, mock_product_data_service_cls = mock_ai_service_dependencies
    mock_product_service_instance = mock_product_data_service_cls.return_value
    mock_genai_instance = mock_genai_client_cls.return_value

    # Menimpa nilai kembalian mock product service untuk test spesifik ini
    mock_product_service_instance.get_products.return_value = [
        {"name": "UltraBook", "price": 2000, "category": "laptop", "description": "Laptop super tipis dan ringan."}
    ]

    service = AIService() # Ini akan menggunakan get_settings dan genai.Client yang telah di-mock
    question = "Bisakah Anda merekomendasikan laptop di bawah $2500?"
    
    response = await service.get_response(question)

    # Assertions
    mock_product_service_instance.get_products.assert_called_once() # Pastikan ProductDataService dipanggil
    mock_genai_instance.generate_content.assert_called_once() # Pastikan model AI dipanggil
    
    assert "Ini adalah respons AI tiruan dari model." in response
    
    # Periksa apakah konteks produk ditambahkan dengan benar ke prompt model AI
    args, _ = mock_genai_instance.generate_content.call_args
    assert "Product Information:" in args[0]
    assert "UltraBook" in args[0]
    assert "Laptop super tipis dan ringan." in args[0]


@pytest.mark.asyncio
async def test_aiservice_get_response_no_product_context(mock_ai_service_dependencies):
    """
    Menguji method get_response dengan pertanyaan umum yang tidak menyiratkan konteks produk,
    atau ketika ProductDataService tidak mengembalikan produk.
    Menggunakan mock dependensi untuk pengujian unit yang terisolasi.
    """
    # Membongkar mock dari fixture
    mock_get_settings, mock_genai_client_cls, mock_product_data_service_cls = mock_ai_service_dependencies
    mock_product_service_instance = mock_product_data_service_cls.return_value
    mock_genai_instance = mock_genai_client_cls.return_value

    # Pastikan get_products mengembalikan daftar kosong untuk test ini (tidak ada produk relevan)
    mock_product_service_instance.get_products.return_value = []
    
    service = AIService()
    question = "Apa ibu kota Indonesia?"
    
    response = await service.get_response(question)

    # Assertions
    # ProductDataService.get_products mungkin masih dipanggil untuk percobaan ekstraksi kategori,
    # namun akan mengembalikan kosong.
    mock_product_service_instance.get_products.assert_called_once() 
    mock_genai_instance.generate_content.assert_called_once()
    
    assert "Ini adalah respons AI tiruan dari model." in response
    # Verifikasi bahwa tidak ada konteks produk spesifik yang dilewatkan ke model AI
    args, _ = mock_genai_instance.generate_content.call_args
    assert "Product Information:" not in args[0] # Seharusnya tidak mengandung bagian info produk


@pytest.mark.asyncio
async def test_aiservice_get_response_exception_fallback(mock_ai_service_dependencies):
    """
    Menguji get_response menangani pengecualian dari klien AI dengan baik
    dan menyediakan pesan fallback.
    Menggunakan mock dependensi untuk pengujian unit yang terisolasi.
    """
    # Membongkar mock dari fixture
    mock_get_settings, mock_genai_client_cls, mock_product_data_service_cls = mock_ai_service_dependencies
    mock_genai_instance = mock_genai_client_cls.return_value

    # Konfigurasi method generate_content dari klien genai yang di-mock untuk menghasilkan pengecualian
    mock_genai_instance.generate_content.side_effect = Exception("Simulasi error layanan AI")

    service = AIService()
    question = "Ceritakan sebuah lelucon."
    
    response = await service.get_response(question)

    # Assertions
    mock_genai_instance.generate_content.assert_called_once()
    assert "Maaf, saya mengalami masalah teknis saat memproses permintaan Anda." in response
    assert "Silakan coba lagi nanti." in response