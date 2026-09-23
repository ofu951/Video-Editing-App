"""Dashboard sekmesi (render durumu + genel log + donanim izleyici baslatma)."""
import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QScrollArea
from PyQt6.QtCore import Qt

from ..widgets import RenderDashboard
from ..workers import SystemMonitorWorker

class DashboardTabMixin:
    def init_dashboard_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)

        # Sol: render dashboard
        self.dashboard = RenderDashboard()
        scroll = QScrollArea()
        scroll.setWidget(self.dashboard)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Sağ: global log
        right = QWidget()
        right_layout = QVBoxLayout(right)
        log_title = QLabel("📋 Genel Log")
        log_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #00D2D3;")
        self.global_log = QTextEdit()
        self.global_log.setReadOnly(True)
        self.global_log.setStyleSheet(
            "background: #0D0D1A; color: #00FF88; font-family: 'Consolas', monospace; font-size: 12px;"
        )
        right_layout.addWidget(log_title)
        right_layout.addWidget(self.global_log)

        layout.addWidget(scroll, 1)
        layout.addWidget(right, 1)
        self.tabs.addTab(tab, "⚙️ Dashboard")
    def _log(self, msg: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.global_log.append(f"[{ts}] {msg}")
    def _start_system_monitor(self):
        try:
            import psutil
            self._sys_monitor = SystemMonitorWorker()
            self._sys_monitor.stats_signal.connect(self.dashboard.update_hw)
            self._sys_monitor.start()
        except ImportError:
            self._log("psutil yüklü değil — donanım izleyici kapalı. (pip install psutil)")

    # ─────────────────────────────────────────────────────────────── #
    #  SEKME: DİNAMİK VİDEO (YATAY / VLOG)                            #
    # ─────────────────────────────────────────────────────────────── #
