import pytest
from app.app.utils.config import get_settings

def test_get_settings_basic(monkeypatch):
    # Bersihkan cache lru_cache untuk get_settings()
    # Ini penting agar pemanggilan get_settings() dalam tes ini
    # menghasilkan instance Settings yang baru, meskipun ada pemanggilan
    # `settings = get_settings()` di tingkat modul dalam config.py.
    get_settings.cache_clear()

    # Atur variabel lingkungan yang diperlukan oleh kelas Settings
    # untuk mencegah ValueError saat inisialisasi.
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy-google-api-key")
    monkeypatch.setenv("API_HOST", "test_host_value")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("DEBUG", "False") # Uji konversi boolean

    # Panggil fungsi get_settings() untuk pertama kalinya dalam tes ini
    settings_instance_1 = get_settings()

    # Lakukan afirmasi (assertions) pada instance Settings yang pertama
    assert isinstance(settings_instance_1, Settings)
    assert settings_instance_1.GOOGLE_API_KEY == "dummy-google-api-key"
    assert settings_instance_1.API_HOST == "test_host_value"
    assert settings_instance_1.API_PORT == 9000
    assert settings_instance_1.DEBUG is False

    # Panggil fungsi get_settings() lagi untuk memverifikasi perilaku lru_cache
    settings_instance_2 = get_settings()

    # Afirmasi bahwa panggilan kedua mengembalikan instance yang sama
    # karena adanya caching lru_cache.
    assert settings_instance_1 is settings_instance_2

    # Opsional: Verifikasi status cache (memastikan cache bekerja)
    cache_info = get_settings.cache_info()
    assert cache_info.hits >= 1  # Minimal ada satu hit dari panggilan kedua
    assert cache_info.misses == 1 # Tepat satu miss dari panggilan pertama
