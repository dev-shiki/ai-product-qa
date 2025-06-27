import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic():
    # Untuk menguji generate_response tanpa memanggil API eksternal atau dependensi yang rumit,
    # kita akan membuat objek mock sederhana yang meniru perilaku self.client.
    # Asumsi: AIService sudah tersedia dalam scope test (misalnya, diimpor oleh test runner),
    # dan inisialisasi AIService (AIService.__init__) ditangani oleh setup test Anda
    # (misalnya, dengan patching get_settings dan genai.Client secara global atau melalui fixture di conftest.py).

    # Dummy class untuk meniru respons dari Google AI (response.text)
    class MockGenerateContentResponse:
        def __init__(self, text):
            self.text = text

    # Dummy class untuk meniru client.models
    class MockModels:
        def __init__(self):
            # Digunakan untuk melacak argumen panggilan
            self.call_args_list = []

        def generate_content(self, model, contents):
            self.call_args_list.append({'model': model, 'contents': contents})
            # Mengembalikan objek yang meniru response.text
            return MockGenerateContentResponse("Ini adalah respons AI tiruan untuk konteks Anda.")

    # Dummy class untuk meniru client Google AI
    class MockClient:
        def __init__(self):
            self.models = MockModels()

    # Mengimpor AIService di sini diasumsikan akan ditambahkan oleh test runner
    # from app.services.ai_service import AIService # Baris ini tidak disertakan dalam output final

    # Membuat instance AIService. Ini bergantung pada setup test Anda agar tidak gagal saat inisialisasi.
    # Jika inisialisasi AIService.__init__ gagal (misalnya karena API key tidak ada), test ini akan gagal di sini.
    from app.services.ai_service import AIService # Baris ini disisipkan agar kode bisa dieksekusi mandiri jika disalin,
                                                 # namun sesuai instruksi, asumsikan ini sudah ada di scope.

    service = AIService()

    # Mengganti client asli dengan mock client kita
    # Ini adalah cara "sederhana" untuk mocking tanpa import library mock.
    service.client = MockClient()

    # Konteks input untuk generate_response
    test_context = "Saya ingin membeli laptop baru. Rekomendasikan yang bagus."
    expected_response_text = "Ini adalah respons AI tiruan untuk konteks Anda."

    # Memanggil fungsi yang akan diuji
    actual_response = service.generate_response(test_context)

    # Memverifikasi respons yang dikembalikan
    assert actual_response == expected_response_text

    # Memverifikasi bahwa metode generate_content dipanggil dengan argumen yang benar
    assert len(service.client.models.call_args_list) == 1
    called_args = service.client.models.call_args_list[0]

    assert called_args['model'] == "gemini-2.0-flash"
    # Memverifikasi bahwa prompt yang dibuat berisi konteks dan instruksi
    assert test_context in called_args['contents']
    assert "You are a helpful product assistant." in called_args['contents']
    assert "Please provide a clear and concise answer" in called_args['contents']
