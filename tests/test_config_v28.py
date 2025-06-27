import pytest
from app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Untuk menguji get_settings, kita perlu memastikan kelas Settings dapat diinisialisasi.
    # Kelas Settings membutuhkan GOOGLE_API_KEY diset, jadi kita atur sementara menggunakan monkeypatch.
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy_google_api_key_for_test")

    # Panggil fungsi yang akan diuji untuk pertama kali
    settings_instance_1 = get_settings()

    # Pastikan sebuah instance dikembalikan dan memiliki atribut yang diharapkan
    assert settings_instance_1 is not None
    assert settings_instance_1.GOOGLE_API_KEY == "dummy_google_api_key_for_test"
    assert settings_instance_1.API_HOST == "localhost" # Nilai default

    # Uji perilaku lru_cache: panggilan berikutnya harus mengembalikan instance yang sama
    settings_instance_2 = get_settings()
    assert settings_instance_1 is settings_instance_2
