"""Ayarlar sekmesi (API anahtarlari)."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox,
)

from .. import config

class SettingsTabMixin:
    def init_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        title = QLabel("⚙️ Uygulama Ayarları ve API Bağlantıları")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00D2D3;")
        
        desc = QLabel(
            "Uygulamanın yapay zeka ve YouTube özelliklerini kullanabilmesi için "
            "kendi API anahtarlarınızı girmelisiniz. Bu bilgiler sadece sizin bilgisayarınızda şifreli olarak saklanır."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #8C8C9A; font-size: 13px; margin-bottom: 10px;")

        # YouTube API Alanı
        yt_layout = QHBoxLayout()
        self.yt_api_input = QLineEdit()
        self.yt_api_input.setPlaceholderText("YouTube Data API v3 Anahtarınızı girin...")
        self.yt_api_input.setText(config.YOUTUBE_API_KEY)
        self.yt_api_input.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit) # Güvenlik için yıldızlı görünüm
        yt_layout.addWidget(QLabel("YouTube API Key:"))
        yt_layout.addWidget(self.yt_api_input, 1)

        # Gemini API Alanı
        gemini_layout = QHBoxLayout()
        self.gemini_api_input = QLineEdit()
        self.gemini_api_input.setPlaceholderText("Google Gemini API Anahtarınızı girin...")
        self.gemini_api_input.setText(config.GEMINI_API_KEY)
        self.gemini_api_input.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        gemini_layout.addWidget(QLabel("Gemini API Key:  "))
        gemini_layout.addWidget(self.gemini_api_input, 1)

        self.save_settings_btn = QPushButton("💾 Ayarları Kaydet")
        self.save_settings_btn.setStyleSheet("background:#7C3AED; color:white; font-weight:bold; font-size:14px; padding:10px;")
        self.save_settings_btn.clicked.connect(self.save_app_settings)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addLayout(yt_layout)
        layout.addLayout(gemini_layout)
        layout.addWidget(self.save_settings_btn)
        layout.addStretch()

        tab.setLayout(layout)
        self.tabs.addTab(tab, "⚙️ Ayarlar")
    def save_app_settings(self):
        """Kullanıcının girdiği ayarları kaydeder ve belleği günceller."""
        yt_key = self.yt_api_input.text().strip()
        gemini_key = self.gemini_api_input.text().strip()
        
        config.YOUTUBE_API_KEY = yt_key
        config.GEMINI_API_KEY = gemini_key
        
        config.APP_CONFIG["YOUTUBE_API_KEY"] = yt_key
        config.APP_CONFIG["GEMINI_API_KEY"] = gemini_key
        
        config.save_config(config.APP_CONFIG)
        QMessageBox.information(self, "Başarılı", "Ayarlar başarıyla kaydedildi!\nYeni anahtarlar hemen aktif oldu.")
    def select_file_to_input(self, line_edit):
        path, _ = QFileDialog.getOpenFileName(self, "Video Seç", "", "Video (*.mp4 *.mov)")
        if path: line_edit.setText(path)
