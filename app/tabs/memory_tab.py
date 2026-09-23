"""Bellek arama (ChromaDB) sekmesi."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
)

from ..workers import ChromaSearchWorker

class MemoryTabMixin:
    def init_memory_search_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        title = QLabel("🧠 Geçmiş İçerik Araması")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00D2D3;")

        desc = QLabel(
            "Whisper ile deşifre ettiğin tüm video içerikleri ChromaDB vektör veritabanında saklanır.\n"
            "Buradan doğal dil ile arama yapabilirsin — örn: 'STM32 DMA ayarları', 'ROS2 Navigation', 'ROV tasarımı'"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #8C8C9A; font-size: 13px;")

        search_row = QHBoxLayout()
        self.memory_search_input = QLineEdit()
        self.memory_search_input.setPlaceholderText("Geçmiş içeriklerinde ara... (Türkçe veya İngilizce)")
        self.memory_search_input.setStyleSheet("font-size: 14px; padding: 10px;")
        self.memory_search_btn = QPushButton("🔍 Ara")
        self.memory_search_btn.setStyleSheet("background:#7C3AED; color:white; font-weight:bold;")
        search_row.addWidget(self.memory_search_input, 1)
        search_row.addWidget(self.memory_search_btn)

        self.memory_result_text = QTextEdit()
        self.memory_result_text.setReadOnly(True)
        self.memory_result_text.setPlaceholderText(
            "Sonuçlar burada görünecek.\n\n"
            "NOT: İlk kullanımdan önce en az bir videoyu AI Analiz sekmesinden analiz etmelisin."
        )
        self.memory_result_text.setStyleSheet(
            "background:#0D0D1A; color:#E0E0E0; font-size: 13px; padding: 10px;"
        )

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addLayout(search_row)
        layout.addWidget(self.memory_result_text)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "🧠 Bellek")

    # ─────────────────────────────────────────────────────────────── #
    #  SEKME: METRİKLER                                                #
    # ─────────────────────────────────────────────────────────────── #
    def run_memory_search(self):
        query = self.memory_search_input.text().strip()
        if not query:
            return
        self.memory_search_btn.setEnabled(False)
        self.memory_result_text.setPlaceholderText("Aranıyor...")
        self._chroma_worker = ChromaSearchWorker(query)
        self._chroma_worker.result_signal.connect(self._on_memory_result)
        self._chroma_worker.error_signal.connect(self._on_memory_error)
        self._chroma_worker.start()
    def _on_memory_result(self, text):
        self.memory_result_text.setPlainText(text)
        self.memory_search_btn.setEnabled(True)
    def _on_memory_error(self, err):
        self.memory_result_text.setPlainText(f"[HATA] {err}")
        self.memory_search_btn.setEnabled(True)

    # ═══════════════════════════════════════════════════════════════ #
    #  SEO, METRİK, TREND, ŞABLON (öncekiyle aynı)                   #
    # ═══════════════════════════════════════════════════════════════ #
