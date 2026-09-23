"""Tekrar kullanilan ozel Qt widget'lari: DropZone ve RenderDashboard."""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QFileDialog,
    QProgressBar,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent


class DropZone(QFrame):
    """Dosya sürükle-bırak veya tıkla-seç destekli alan."""
    file_dropped = pyqtSignal(str)

    def __init__(self, label_text="Dosyayı buraya sürükleyin veya tıklayın",
                 accept_filter="Medya Dosyaları (*.mp4 *.wav *.mp3 *.mov)",
                 parent=None):
        super().__init__(parent)
        self.accept_filter = accept_filter
        self.setAcceptDrops(True)
        self.setMinimumHeight(72)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_lbl = QLabel("📂")
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setStyleSheet("font-size: 24px; background: transparent; border: none;")

        self.text_lbl = QLabel(label_text)
        self.text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_lbl.setWordWrap(True)
        self.text_lbl.setStyleSheet(
            "color: #8C8C9A; font-size: 13px; background: transparent; border: none;"
        )

        self.path_lbl = QLabel("")
        self.path_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.path_lbl.setWordWrap(True)
        self.path_lbl.setStyleSheet(
            "color: #00D2D3; font-size: 12px; background: transparent; border: none;"
        )

        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.text_lbl)
        layout.addWidget(self.path_lbl)

        self._set_idle_style()

    def _set_idle_style(self):
        self.setStyleSheet("""
            DropZone {
                background-color: #1E1E2E;
                border: 2px dashed #3A3A5C;
                border-radius: 10px;
            }
            DropZone:hover {
                border-color: #00D2D3;
                background-color: #252538;
            }
        """)

    def _set_active_style(self):
        self.setStyleSheet("""
            DropZone {
                background-color: #1A2A2A;
                border: 2px solid #00D2D3;
                border-radius: 10px;
            }
        """)

    def get_path(self):
        return self.path_lbl.text()

    def set_path(self, path):
        self.path_lbl.setText(os.path.basename(path))
        self.path_lbl.setToolTip(path)
        self._set_active_style()

    def mousePressEvent(self, event):
        path, _ = QFileDialog.getOpenFileName(self, "Dosya Seç", "", self.accept_filter)
        if path:
            self.set_path(path)
            self.file_dropped.emit(path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                DropZone {
                    background-color: #1A2A2A;
                    border: 2px solid #00FFB3;
                    border-radius: 10px;
                }
            """)

    def dragLeaveEvent(self, event):
        self._set_idle_style()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self.set_path(path)
            self.file_dropped.emit(path)
        self._set_idle_style()


class RenderDashboard(QWidget):
    """Her render aşaması için durum satırları gösteren panel."""

    STEPS = [
        ("ses_analiz",  "🔊 Ses Analizi"),
        ("ses_temiz",   "✂️  Sessizlik Temizleme"),
        ("transcribe",  "📝 Deşifre (Whisper)"),
        ("broll",       "🎬 B-Roll Seçimi"),
        ("render",      "🎞️  Video Render"),
        ("shorts",      "📱 Shorts Üretimi"),
        ("srt",         "💬 Altyazı"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        title = QLabel("⚙️  Render Durumu")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #00D2D3;")
        layout.addWidget(title)

        self._rows = {}
        for key, label in self.STEPS:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)

            status_lbl = QLabel("⬜")
            status_lbl.setFixedWidth(26)
            status_lbl.setStyleSheet("font-size: 16px;")

            name_lbl = QLabel(label)
            name_lbl.setFixedWidth(200)
            name_lbl.setStyleSheet("color: #8C8C9A;")

            bar = QProgressBar()
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setFixedHeight(10)
            bar.setStyleSheet("""
                QProgressBar { background: #2D2D3F; border-radius: 5px; }
                QProgressBar::chunk { background: #00D2D3; border-radius: 5px; }
            """)

            msg_lbl = QLabel("")
            msg_lbl.setStyleSheet("color: #5A5A72; font-size: 12px;")

            row_layout.addWidget(status_lbl)
            row_layout.addWidget(name_lbl)
            row_layout.addWidget(bar, 1)
            row_layout.addWidget(msg_lbl)

            layout.addWidget(row_widget)
            self._rows[key] = (status_lbl, name_lbl, bar, msg_lbl)

        # CPU/RAM/GPU
        hw_title = QLabel("💻  Donanım İzleyici")
        hw_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #00D2D3; margin-top: 14px;")
        layout.addWidget(hw_title)

        hw_row = QWidget()
        hw_layout = QHBoxLayout(hw_row)
        hw_layout.setContentsMargins(0, 0, 0, 0)

        self.cpu_bar = self._make_hw_bar("CPU", "#4A90E2")
        self.ram_bar = self._make_hw_bar("RAM", "#F5A623")
        self.gpu_bar = self._make_hw_bar("GPU °C", "#E27D60")

        hw_layout.addWidget(self.cpu_bar[0])
        hw_layout.addWidget(self.ram_bar[0])
        hw_layout.addWidget(self.gpu_bar[0])
        layout.addWidget(hw_row)
        layout.addStretch()

    def _make_hw_bar(self, label_text, color):
        container = QWidget()
        vl = QVBoxLayout(container)
        vl.setContentsMargins(4, 4, 4, 4)
        lbl = QLabel(f"{label_text}: —")
        lbl.setStyleSheet("color: #8C8C9A; font-size: 12px;")
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setFixedHeight(12)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{ background: #2D2D3F; border-radius: 6px; }}
            QProgressBar::chunk {{ background: {color}; border-radius: 6px; }}
        """)
        vl.addWidget(lbl)
        vl.addWidget(bar)
        return container, lbl, bar

    # ─── Dışarıdan çağrılan API'lar ────────────────────────────────
    def update_step(self, key: str, pct: int, msg: str = "", done: bool = False, error: bool = False):
        if key not in self._rows:
            return
        status_lbl, name_lbl, bar, msg_lbl = self._rows[key]
        bar.setValue(pct)
        msg_lbl.setText(msg[:60])
        if error:
            status_lbl.setText("🔴")
            name_lbl.setStyleSheet("color: #FF6B6B;")
        elif done or pct >= 100:
            status_lbl.setText("✅")
            name_lbl.setStyleSheet("color: #00FF88;")
        elif pct > 0:
            status_lbl.setText("🔄")
            name_lbl.setStyleSheet("color: #FFFFFF;")

    def reset_step(self, key: str):
        if key not in self._rows:
            return
        status_lbl, name_lbl, bar, msg_lbl = self._rows[key]
        status_lbl.setText("⬜")
        name_lbl.setStyleSheet("color: #8C8C9A;")
        bar.setValue(0)
        msg_lbl.setText("")

    def update_hw(self, cpu: float, ram: float, gpu_temp: float):
        _, cpu_lbl, cpu_bar = self.cpu_bar
        _, ram_lbl, ram_bar = self.ram_bar
        _, gpu_lbl, gpu_bar = self.gpu_bar

        cpu_lbl.setText(f"CPU: {cpu:.0f}%")
        cpu_bar.setValue(int(cpu))

        ram_lbl.setText(f"RAM: {ram:.0f}%")
        ram_bar.setValue(int(ram))

        if gpu_temp > 0:
            gpu_lbl.setText(f"GPU: {gpu_temp:.0f}°C")
            gpu_bar.setValue(min(100, int(gpu_temp)))
        else:
            gpu_lbl.setText("GPU: —")
