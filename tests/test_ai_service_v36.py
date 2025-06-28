import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic():
    # Menggunakan unittest.mock untuk mengisolasi AIService dari dependensi eksternal.
    # Diasumsikan 'mock' sudah diimpor (e.g., import unittest.mock as mock) di file test.
    
    # Mock genai.Client dan metode generate_content-nya
    with mock.patch('app.services.ai_service.genai.Client') as MockGenaiClient:
        # Konfigurasi objek mock yang akan dikembalikan oleh generate_content
        mock_response_object = mock.Mock()
        mock_response_object.text = "Ini adalah respons AI tiruan dari generate_response."
        
        # Konfigurasi instance mock client dan rantai panggilannya: client.models.generate_content
        mock_client_instance = MockGenaiClient.return_value
        mock_client_instance.models.generate_content.return_value = mock_response_object

        # Mock app.utils.config.get_settings karena AIService constructor memanggilnya
        with mock.patch('app.services.ai_service.get_settings') as mock_get_settings:
            mock_settings = mock.Mock()
            mock_settings.GOOGLE_API_KEY = "dummy_api_key_for_test"
            mock_get_settings.return_value = mock_settings

            # Mock app.services.product_data_service.ProductDataService
            # AIService constructor juga menginisialisasi ProductDataService
            with mock.patch('app.services.ai_service.ProductDataService'):
                # Inisialisasi AIService (akan menggunakan mock yang telah kita buat)
                service = AIService()

                # Konteks uji coba yang akan diberikan ke generate_response
                test_context = "Pengguna bertanya tentang rekomendasi laptop untuk gaming dengan budget 15 juta."
                
                # Respons yang diharapkan dari AI berdasarkan mock yang telah disiapkan
                expected_ai_response = "Ini adalah respons AI tiruan dari generate_response."

                # Panggil fungsi yang akan diuji
                actual_response = service.generate_response(test_context)

                # Assert (memastikan) bahwa respons yang diterima sesuai dengan yang diharapkan
                assert actual_response == expected_ai_response

                # Assert (memastikan) bahwa metode generate_content dari klien AI telah dipanggil satu kali
                mock_client_instance.models.generate_content.assert_called_once()

                # Dapatkan argumen yang digunakan saat memanggil generate_content
                call_args, call_kwargs = mock_client_instance.models.generate_content.call_args
                
                # Assert (memastikan) model yang digunakan sudah benar
                assert call_kwargs['model'] == "gemini-2.0-flash"
                
                # Assert (memastikan) bahwa prompt yang dihasilkan mengandung konteks yang diberikan
                generated_prompt = call_kwargs['contents']
                assert "You are a helpful product assistant." in generated_prompt
                assert test_context in generated_prompt
                assert "Please provide a clear and concise answer that helps the user understand the products and make an informed decision." in generated_prompt
