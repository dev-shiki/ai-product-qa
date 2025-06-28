import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic():
    # Inisialisasi AIService. Perlu dicatat bahwa ini akan mencoba menginisialisasi
    # Google AI Client dan membutuhkan GOOGLE_API_KEY yang valid di environment
    # tempat tes dijalankan, serta koneksi internet.
    # Ini menjadikannya lebih seperti tes integrasi daripada unit tes murni
    # karena tidak menggunakan mocking untuk mengisolasi fungsi dari dependensi eksternal.
    # Asumsi: AIService class sudah di-import di file test (misal: from app.services.ai_service import AIService).
    ai_service = AIService()

    # Siapkan konteks sederhana untuk AI.
    test_context = "Berikan ringkasan singkat tentang manfaat kesehatan dari olahraga teratur."

    # Panggil fungsi generate_response.
    response = ai_service.generate_response(test_context)

    # Lakukan asersi dasar:
    # 1. Pastikan respons adalah string.
    # 2. Pastikan respons tidak kosong.
    # (Tidak dapat menguji konten spesifik karena output AI non-deterministik,
    #  tetapi dapat memverifikasi bahwa respons berhasil dihasilkan.)
    assert isinstance(response, str)
    assert len(response) > 0
