import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic():
    # Asumsi: unittest.mock.patch dan unittest.mock.MagicMock sudah diimpor di file test ini.
    # Contoh: from unittest.mock import MagicMock, patch
    # Asumsi: AIService sudah diimpor dari app.services.ai_service

    # Mock get_settings untuk menghindari loading konfigurasi sebenarnya dan cek API key
    with patch('app.utils.config.get_settings') as mock_get_settings:
        mock_settings_instance = MagicMock()
        mock_settings_instance.GOOGLE_API_KEY = "dummy-api-key"
        mock_get_settings.return_value = mock_settings_instance

        # Mock ProductDataService karena AIService.__init__ menginisialisasi-nya
        with patch('app.services.product_data_service.ProductDataService') as MockProductDataService:
            mock_product_service_instance = MagicMock()
            MockProductDataService.return_value = mock_product_service_instance

            # Mock google.generativeai.Client dan methodnya
            with patch('google.generativeai.Client') as MockGenaiClient:
                mock_client_instance = MagicMock()
                MockGenaiClient.return_value = mock_client_instance

                # Mock atribut 'models' dan method 'generate_content'
                mock_models_attribute = MagicMock()
                mock_client_instance.models = mock_models_attribute

                # Mock return value dari generate_content (objek dengan atribut .text)
                mock_response_object = MagicMock()
                mock_response_object.text = "Ini adalah respons AI tiruan untuk konteks Anda."
                mock_models_attribute.generate_content.return_value = mock_response_object

                # Inisialisasi AIService (akan menggunakan mock yang sudah dibuat)
                service = AIService()

                # Konteks dummy untuk diuji
                test_context = "Pengguna bertanya tentang fitur produk."

                # Panggil fungsi yang akan diuji
                response = service.generate_response(test_context)

                # Assertions
                # 1. Pastikan respons sesuai dengan nilai tiruan
                assert response == "Ini adalah respons AI tiruan untuk konteks Anda."

                # 2. Pastikan generate_content dipanggil tepat satu kali
                mock_models_attribute.generate_content.assert_called_once()

                # 3. Opsional: Periksa argumen yang diteruskan ke generate_content
                call_args, call_kwargs = mock_models_attribute.generate_content.call_args
                assert call_kwargs["model"] == "gemini-2.0-flash"
                assert test_context in call_kwargs["contents"] # Pastikan konteks ada di prompt
                assert "helpful product assistant" in call_kwargs["contents"] # Pastikan struktur prompt ada

                # 4. Pastikan ProductDataService juga diinisialisasi
                MockProductDataService.assert_called_once()
