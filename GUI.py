"""Uygulama giris noktasi.

Tum arayuz kodu okunabilirlik icin app/ paketine bolunmustur:
  app/config.py         -> ayarlar / API anahtarlari
  app/style.py           -> QSS stylesheet
  app/widgets.py          -> DropZone, RenderDashboard
  app/workers.py          -> arka plan QThread isci siniflari
  app/tabs/*.py           -> her sekme icin ayri mixin sinifi
  app/main_window.py      -> tum sekmeleri birlestiren YouTubeManagerApp
"""
import os
import sys
import datetime
import traceback

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from app.config import get_config_path
from app.style import STYLESHEET
from app.main_window import YouTubeManagerApp


def global_exception_handler(exc_type, exc_value, exc_traceback):
    import os
    import sys
    import traceback
    
    # 1. Hatayı metne çevir
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # 2. HİÇBİR KLASÖR ARAMADAN DİREKT MASAÜSTÜNE YAZIYORUZ
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "KOCAMAN_CRASH_LOG.txt")
    
    try:
        with open(desktop_path, "w", encoding="utf-8") as f:
            f.write(error_msg)
    except:
        pass # Masaüstüne bile yazamazsa sal gitsin, terminale basacağız
        
    # 3. Terminale (PowerShell) eşek gibi büyük yaz
    print("\n" + "!"*50)
    print("!!! KRİTİK ÇÖKME HATASI !!!")
    print(error_msg)
    print("!"*50 + "\n")
    
    # 4. Ekrana Pop-up Çıkar
    try:
        from PyQt6.QtWidgets import QMessageBox
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Vay Arkadaş Yine Çöktü!")
        msg_box.setStyleSheet("background-color: #1E1E2E; color: white;")
        msg_box.setText("Hata dosyası MASAÜSTÜNE 'KOCAMAN_CRASH_LOG.txt' olarak oluşturuldu!\n\nLütfen o dosyaya veya terminal (PowerShell) ekranına bak.")
        msg_box.setInformativeText(f"Hata Özeti:\n{exc_value}")
        msg_box.exec()
    except:
        pass
        
    sys.exit(1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    sys.excepthook = global_exception_handler
    default_font = QFont("Segoe UI", 10)
    if default_font.pointSize() <= 0:
        default_font.setPixelSize(14)
    app.setFont(default_font)
    
    app.setStyleSheet(STYLESHEET)
    window = YouTubeManagerApp()
    window.show()
    sys.exit(app.exec())