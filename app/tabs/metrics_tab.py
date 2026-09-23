"""Metrikler sekmesi (YouTube Analytics)."""
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QMessageBox

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from ..config import SCOPES

class MetricsTabMixin:
    def init_metrics_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.metrics_table = QTableWidget(0, 4)
        self.metrics_table.setHorizontalHeaderLabels(
            ["Tarih", "İzlenme", "İzlenme Süresi (Dk)", "Kazanılan Abone"]
        )
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        self.refresh_metrics_btn = QPushButton("📊 Son 30 Günlük Verileri Çek")
        layout.addWidget(self.metrics_table)
        layout.addWidget(self.refresh_metrics_btn)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "📊 Metrikler")

    # ─────────────────────────────────────────────────────────────── #
    #  SEKME: İÇERİK ŞABLONU                                          #
    # ─────────────────────────────────────────────────────────────── #
    def update_metrics(self):
        QMessageBox.information(
            self, "OAuth Gerekli",
            "Bu özellik için Google Cloud üzerinden OAuth 2.0 Client ID ve credentials.json gereklidir."
        )
    def authenticate_youtube_analytics(self):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as f:
                f.write(creds.to_json())
        return creds
