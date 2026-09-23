"""AI Ozet Video sekmesi."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QProgressBar, QSpinBox, QMessageBox,
)

from .. import config
from ..widgets import DropZone
from ..workers import SummaryVideoWorker

class SummaryTabMixin:
    def init_summary_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        self.summary_drop = DropZone(
            "📹 Özetlenecek uzun videoyu sürükleyin (.mp4, .mov)",
            "Video Dosyaları (*.mp4 *.mov)"
        )
        self.summary_drop.file_dropped.connect(lambda p: self.summary_drop.set_path(p))

        # 🔥 ARALIKLARI GÖR VE DÜZENLE
        aralık_label = QLabel("📊 Özet Aralıkları (saniye cinsinden, format: 0-45, 60-120, 180-240)")
        aralık_label.setStyleSheet("color: #00D2D3; font-weight: bold;")
        
        self.summary_ranges_input = QTextEdit()
        self.summary_ranges_input.setPlaceholderText(
            "AI Analiz'dan aralıkları kopyala ve yapıştır.\n"
            "Format 1 (Saniye): 0-90, 150-210, 240-300\n"
            "Format 2 (MM:SS): 00:00-01:30, 02:30-03:30\n"
            "İkisi de desteklenir - karıştırıp yazabilirsin: 0-90, 02:30-03:30"
        )
        self.summary_ranges_input.setStyleSheet("background:#0D0D1A; color:#00FF88; font-size: 12px; font-family: Consolas;")
        self.summary_ranges_input.setMaximumHeight(100)

        # Süre Seçimi (bilgi amaçlı)
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("⏱️ Hedef Özet Süresi (Dakika):"))
        self.summary_time_spin = QSpinBox()
        self.summary_time_spin.setRange(1, 60)
        self.summary_time_spin.setValue(5)
        self.summary_time_spin.setStyleSheet("font-size: 14px; padding: 5px;")
        time_layout.addWidget(self.summary_time_spin)
        time_layout.addStretch()

        self.start_summary_btn = QPushButton("🚀 Aralıklardan Özet Oluştur")
        self.start_summary_btn.setStyleSheet("background:#F5A623; color:#1A1A24; font-weight:bold; font-size:14px; padding: 12px;")
        self.start_summary_btn.clicked.connect(self.run_summary_maker)

        self.summary_progress = QProgressBar()
        self.summary_progress.setValue(0)
        
        self.summary_console = QTextEdit()
        self.summary_console.setReadOnly(True)
        self.summary_console.setStyleSheet("background:#0D0D1A; color:#00FF88; font-size: 12px; font-family: Consolas;")

        layout.addWidget(self.summary_drop)
        layout.addWidget(aralık_label)
        layout.addWidget(self.summary_ranges_input)
        layout.addLayout(time_layout)
        layout.addWidget(self.start_summary_btn)
        layout.addWidget(self.summary_progress)
        layout.addWidget(self.summary_console)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "✂️ AI Özet Video")
    def _parse_time_to_seconds(self, time_str):
        """MM:SS veya saniye formatını saniyeye çevirir. Örn: '01:30' -> 90, '90' -> 90"""
        time_str = time_str.strip()
        if ':' in time_str:
            try:
                parts = time_str.split(':')
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes * 60 + seconds
            except:
                return None
        else:
            try:
                return int(time_str)
            except:
                return None
    
    def run_summary_maker(self):
        video_path = self.summary_drop.path_lbl.toolTip() or self.summary_drop.get_path()
        if not video_path:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir video seçin.")
            return

        # 🔥 ARALIKLARI PARSE ET — MM:SS veya saniye cinsinden
        ranges_text = self.summary_ranges_input.toPlainText().strip()
        if not ranges_text:
            QMessageBox.warning(self, "Uyarı", "Lütfen özet aralıklarını girin.\nFormat: 0-45, 60-120 veya 00:00-01:30, 02:30-03:30")
            return
        
        try:
            ranges = []
            for part in ranges_text.split(","):
                part = part.strip()
                if "-" in part:
                    start_str, end_str = part.split("-", 1)
                    start = self._parse_time_to_seconds(start_str)
                    end = self._parse_time_to_seconds(end_str)
                    
                    if start is None or end is None:
                        raise ValueError(f"'{part}' parse edilemedi")
                    
                    ranges.append((start, end))
            
            if not ranges:
                raise ValueError("Geçerli aralık bulunamadı")
            
            self.summary_console.clear()
            self.summary_console.append(f"✓ {len(ranges)} aralık okundu: {ranges}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Aralıkları parse edemedi: {e}\n\nFormat: 0-45, 60-120 VEYA 00:00-01:30, 02:30-03:30")
            return

        self.start_summary_btn.setEnabled(False)
        self.summary_progress.setValue(0)

        # YENİ: SummaryVideoWorker'ı aralıklar ile çağır (AI değil!)
        self._summary_worker = SummaryVideoWorker(
            video_path=video_path,
            target_minutes=self.summary_time_spin.value(),
            api_key=config.GEMINI_API_KEY,
            ranges=ranges  # 🔥 ARALIKLARI GEÇIR
        )
        self._summary_worker.progress_signal.connect(lambda val, txt: self.summary_progress.setValue(val) or self.summary_progress.setFormat(txt))
        self._summary_worker.log_signal.connect(self.summary_console.append)
        
        def on_done(path):
            self.start_summary_btn.setEnabled(True)
            self.summary_console.append(f"\n✅ İŞLEM TAMAMLANDI! Video şuraya kaydedildi: {path}")
            QMessageBox.information(self, "Başarılı", f"Özet videonuz hazır:\n{path}")
            
        def on_error(err):
            self.start_summary_btn.setEnabled(True)
            self.summary_console.append(f"\n❌ HATA: {err}")
            QMessageBox.critical(self, "Hata", err)
        
        self._summary_worker.finished_signal.connect(on_done)
        self._summary_worker.error_signal.connect(on_error)
        self._summary_worker.start()
    
    # ─────────────────────────────────────────────────────────────── #
    #  SEKME: SEO ANALİZİ                                              #
    # ─────────────────────────────────────────────────────────────── #
