"""Uygulama ayarlari: config.json okuma/yazma ve API anahtarlari.

save_app_settings() bu modul uzerindeki YOUTUBE_API_KEY / GEMINI_API_KEY
degerlerini gunceller; diger sekmeler bu degerlere daima
``config.YOUTUBE_API_KEY`` / ``config.GEMINI_API_KEY`` seklinde erisir ki
anahtar degistiginde tum sekmeler aninda gunceli gorsun (eski tek dosyali
haldeki modul-global davranisiyla ayni).
"""
import os
import json

APP_NAME = "DinamikEdit"

def get_config_path():
    """Kullanıcının AppData klasöründe güvenli bir ayar dosyası yolu oluşturur."""
    if os.name == 'nt': # Windows
        base_path = os.getenv('APPDATA')
    else: # Mac/Linux
        base_path = os.path.expanduser('~')
    
    app_dir = os.path.join(base_path, APP_NAME)
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, 'config.json')

def load_config():
    """Ayarları okur, yoksa boş döndürür."""
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config_data):
    """Ayarları dosyaya kaydeder."""
    with open(get_config_path(), 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4)

# Uygulama başlarken ayarları global olarak yüklüyoruz
APP_CONFIG = load_config()
YOUTUBE_API_KEY = APP_CONFIG.get("YOUTUBE_API_KEY", "")
GEMINI_API_KEY = APP_CONFIG.get("GEMINI_API_KEY", "")

SCOPES = ['https://www.googleapis.com/auth/yt-analytics.readonly']
