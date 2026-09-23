"""SEO analizi sekmesi."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
)

from .. import config
from googleapiclient.discovery import build

class SeoTabMixin:
    def init_seo_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Analiz edilecek konuyu girin...")
        self.search_btn   = QPushButton("🔍 Ara ve Analiz Et")
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        self.seo_table = QTableWidget(0, 3)
        self.seo_table.setHorizontalHeaderLabels(["Video Başlığı", "Kanal Adı", "Yayın Tarihi"])
        self.seo_table.horizontalHeader().setStretchLastSection(True)
        layout.addLayout(search_layout)
        layout.addWidget(self.seo_table)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "🔍 SEO")

    # ─────────────────────────────────────────────────────────────── #
    #  SEKME: İŞ AKIŞI (AI)                                           #
    # ─────────────────────────────────────────────────────────────── #
    def run_seo_analysis(self):
        query = self.search_input.text().strip()
        if not query:
            return
        try:
            youtube = build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)
            req  = youtube.search().list(
                part="snippet", q=query, type="video",
                order="relevance", maxResults=20
            )
            resp = req.execute()
            self.seo_table.setRowCount(0)
            for item in resp.get("items", []):
                sn  = item["snippet"]
                row = self.seo_table.rowCount()
                self.seo_table.insertRow(row)
                self.seo_table.setItem(row, 0, QTableWidgetItem(sn["title"]))
                self.seo_table.setItem(row, 1, QTableWidgetItem(sn["channelTitle"]))
                self.seo_table.setItem(row, 2, QTableWidgetItem(sn["publishedAt"][:10]))
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
