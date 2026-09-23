"""Shorts sekmesi."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar, QComboBox, QSpinBox, QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt

from .. import config
from ..widgets import DropZone
from ..workers import ShortsWorker

class ShortsTabMixin:
    def init_shorts_maker_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab) 

        # ── SOL PANEL (Ayarlar) ──
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)

        # 1. DOSYA SÜRÜKLEME ALANI
        self.shorts_source_drop = DropZone(
            "📹 Shorts yapılacak videoyu sürükleyin",
            "Video Dosyaları (*.mp4 *.mov)"
        )
        self.shorts_source_drop.file_dropped.connect(self._on_shorts_video_loaded)
        left_layout.addWidget(self.shorts_source_drop)

        # 2. ARALIKLAR KUTUSU (Geri Geldi!)
        time_layout = QHBoxLayout()
        time_lbl = QLabel("✂️ Aralıklar:")
        time_lbl.setFixedWidth(80)
        time_lbl.setStyleSheet("font-weight: bold; color: #00D2D3;")
        self.shorts_intervals_input = QLineEdit()
        self.shorts_intervals_input.setPlaceholderText("Örn: 02-05, 12-25 (Max 53sn!)")
        time_layout.addWidget(time_lbl)
        time_layout.addWidget(self.shorts_intervals_input)
        left_layout.addLayout(time_layout)

        # 3. INTRO / OUTRO / GREEN SCREEN VE BOYUT KUTULARI
        gs_frame = QFrame()
        gs_frame.setStyleSheet("background: #1E1E2E; border-radius: 8px; padding: 5px;")
        gs_layout = QGridLayout(gs_frame)
        
        gs_lbl = QLabel("🟩 Ekstra Medya ve Abone Ol Animasyonu")
        gs_lbl.setStyleSheet("font-weight: bold; color: #00FF88;")
        
        # Intro ve Outro
        self.in_intro = QLineEdit(); self.in_intro.setPlaceholderText("Intro Videosu (.mp4)")
        btn_in = QPushButton("📁"); btn_in.clicked.connect(lambda: self.select_file_to_input(self.in_intro))
        
        self.in_outro = QLineEdit(); self.in_outro.setPlaceholderText("Outro Videosu (.mp4)")
        btn_out = QPushButton("📁"); btn_out.clicked.connect(lambda: self.select_file_to_input(self.in_outro))
        
        # GS Dosyası ve Zamanı
        self.in_gs = QLineEdit(); self.in_gs.setPlaceholderText("Green Screen (.mp4)")
        btn_gs = QPushButton("📁"); btn_gs.clicked.connect(lambda: self.select_file_to_input(self.in_gs))
        
        self.in_gs_times = QLineEdit(); self.in_gs_times.setPlaceholderText("GS Saniyeleri (Örn: 10, 30)")
        
        # GS Ölçek ve Konum
        self.shorts_gs_scale_spin = QSpinBox()
        self.shorts_gs_scale_spin.setRange(10, 100); self.shorts_gs_scale_spin.setValue(80)
        self.shorts_gs_scale_spin.setPrefix("Boyut: %")
        
        self.shorts_gs_x_spin = QSpinBox()
        self.shorts_gs_x_spin.setRange(0, 100); self.shorts_gs_x_spin.setValue(50)
        self.shorts_gs_x_spin.setPrefix("X (Sağ-Sol): %")
        
        self.shorts_gs_y_spin = QSpinBox()
        self.shorts_gs_y_spin.setRange(0, 100); self.shorts_gs_y_spin.setValue(85)
        self.shorts_gs_y_spin.setPrefix("Y (Alt-Üst): %")
        
        # Ekrana (Grid'e) Yerleştirme (addWidget kullanımları eksikti, tamamlandı!)
        gs_layout.addWidget(gs_lbl, 0, 0, 1, 4)
        
        gs_layout.addWidget(self.in_intro, 1, 0, 1, 2)
        gs_layout.addWidget(btn_in, 1, 2)
        gs_layout.addWidget(self.in_outro, 1, 3)
        gs_layout.addWidget(btn_out, 1, 4)
        
        gs_layout.addWidget(self.in_gs, 2, 0, 1, 2)
        gs_layout.addWidget(btn_gs, 2, 2)
        gs_layout.addWidget(self.in_gs_times, 2, 3, 1, 2)
        
        gs_layout.addWidget(self.shorts_gs_scale_spin, 3, 0)
        gs_layout.addWidget(self.shorts_gs_x_spin, 3, 1, 1, 2)
        gs_layout.addWidget(self.shorts_gs_y_spin, 3, 3, 1, 2)
        
        left_layout.addWidget(gs_frame) # Tüm kutuyu sol panele ekle

        # 4. ALTYAZI STİLİ
        style_frame = QFrame()
        style_layout = QGridLayout(style_frame)
        style_frame.setStyleSheet("background: #1E1E2E; border-radius: 8px; padding: 5px;")
        
        style_lbl = QLabel("🎨 Altyazı Stili")
        style_lbl.setStyleSheet("font-weight: bold; color: #00D2D3;")
        
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Impact", "Verdana", "Tahoma", "Courier New"])
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 50)
        self.font_size_spin.setValue(16)
        self.font_size_spin.setPrefix("Punto: ")

        self.color_combo = QComboBox()
        self.color_combo.addItems(["Beyaz", "Sarı", "Yeşil", "Kırmızı", "Turkuaz"])
        
        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(10, 300)
        self.margin_spin.setValue(60)
        self.margin_spin.setPrefix("Yükseklik: ")

        style_layout.addWidget(style_lbl, 0, 0, 1, 2)
        style_layout.addWidget(QLabel("Font:"), 1, 0)
        style_layout.addWidget(self.font_combo, 1, 1)
        style_layout.addWidget(QLabel("Renk:"), 2, 0)
        style_layout.addWidget(self.color_combo, 2, 1)
        style_layout.addWidget(self.font_size_spin, 3, 0)
        style_layout.addWidget(self.margin_spin, 3, 1)

        self.char_limit_spin = QSpinBox()
        self.char_limit_spin.setRange(15, 60)
        self.char_limit_spin.setValue(35)
        self.char_limit_spin.setPrefix("Satır Başı Max Karakter: ")
        style_layout.addWidget(self.char_limit_spin, 4, 0, 1, 2)

        left_layout.addWidget(style_frame)

        self.shorts_start_btn = QPushButton("🎬 Kes, Altyazı Ekle ve Üret")
        self.shorts_start_btn.setStyleSheet("background:#00D2D3; color:#1A1A24; font-weight:bold; font-size:14px; padding: 12px;")

        self.shorts_progress = QProgressBar()
        self.shorts_progress.setValue(0)
        self.shorts_progress.setFormat("Bekleniyor...")

        self.shorts_console = QTextEdit()
        self.shorts_console.setReadOnly(True)
        self.shorts_console.setStyleSheet("background:#0D0D1A; color:#00FF88; font-size: 11px;")

        left_layout.addWidget(self.shorts_start_btn)
        left_layout.addWidget(self.shorts_progress)
        left_layout.addWidget(self.shorts_console)

        # ── SAĞ PANEL (Canlı Önizleme) ──
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        preview_lbl = QLabel("📱 Shorts Önizleme")
        preview_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #00D2D3;")
        preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_image_lbl = QLabel("Video yüklendiğinde\nönizleme burada görünecek.")
        self.preview_image_lbl.setFixedSize(270, 480) 
        self.preview_image_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_image_lbl.setStyleSheet("background: #000; border: 2px dashed #3A3A5C; color: #8C8C9A;")

        self.update_preview_btn = QPushButton("🔄 Önizlemeyi Güncelle")
        self.update_preview_btn.setStyleSheet("background:#2D2D3F; color:white;")
        self.update_preview_btn.setEnabled(False) 

        right_layout.addWidget(preview_lbl)
        right_layout.addWidget(self.preview_image_lbl)
        right_layout.addWidget(self.update_preview_btn)

        main_layout.addWidget(left_panel, 2) 
        main_layout.addWidget(right_panel, 1) 

        tab.setLayout(main_layout)
        self.tabs.addTab(tab, "📱 Shorts")

        self.update_preview_btn.clicked.connect(self._refresh_shorts_preview)
        self.font_combo.currentTextChanged.connect(lambda: self.update_preview_btn.click() if self.update_preview_btn.isEnabled() else None)
        self.color_combo.currentTextChanged.connect(lambda: self.update_preview_btn.click() if self.update_preview_btn.isEnabled() else None)
        self.font_size_spin.valueChanged.connect(lambda: self.update_preview_btn.click() if self.update_preview_btn.isEnabled() else None)
        self.margin_spin.valueChanged.connect(lambda: self.update_preview_btn.click() if self.update_preview_btn.isEnabled() else None)
        self.shorts_gs_scale_spin.valueChanged.connect(lambda: self.update_preview_btn.click() if self.update_preview_btn.isEnabled() else None)
        self.shorts_gs_x_spin.valueChanged.connect(lambda: self.update_preview_btn.click() if self.update_preview_btn.isEnabled() else None)
        self.shorts_gs_y_spin.valueChanged.connect(lambda: self.update_preview_btn.click() if self.update_preview_btn.isEnabled() else None)
    def _on_shorts_video_loaded(self, path):
        self.shorts_source_drop.set_path(path)
        self.update_preview_btn.setEnabled(True)
        self.shorts_console.append("[BİLGİ] Video algılandı. Önizleme hazır.")
        self._refresh_shorts_preview() # Video yüklenir yüklenmez ilk önizlemeyi bas
    def _refresh_shorts_preview(self):
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen
        from PyQt6.QtCore import Qt, QRect

        # 270x480 (9:16) formatında koyu gri boş bir tuval oluştur
        pixmap = QPixmap(270, 480)
        pixmap.fill(QColor("#1A1A24")) 

        painter = QPainter(pixmap)
        
        # Font Ayarlarını Al
        font_family = self.font_combo.currentText()
        font_size = self.font_size_spin.value()
        painter.setFont(QFont(font_family, font_size, QFont.Weight.Bold))

        # Renk Ayarlarını Al
        color_map = {"Beyaz": "#FFFFFF", "Sarı": "#FFD700", "Yeşil": "#00FF00", "Kırmızı": "#FF0000", "Turkuaz": "#00D2D3"}
        hex_color = color_map.get(self.color_combo.currentText(), "#FFFFFF")
        painter.setPen(QPen(QColor(hex_color)))

        # Metni sınır değerine göre bölüp ekrana bas
        max_char = self.char_limit_spin.value()
        ornek_metin = "Yapay Zeka İle\nAltyazı Böyle Görünecek"
        margin = self.margin_spin.value()
        
        # Yüksekliği margin'e göre ayarla (Aşağıdan yukarıya)
        rect = QRect(10, 480 - margin - 150, 250, 150)
        painter.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, ornek_metin)
        # 🔥 SHORTS ÖNİZLEMESİNE GREEN SCREEN ÇİZİMİ
        gs_scale = self.shorts_gs_scale_spin.value() / 100.0
        gs_x_pct = self.shorts_gs_x_spin.value() / 100.0
        gs_y_pct = self.shorts_gs_y_spin.value() / 100.0
        
        gs_w = 270 * gs_scale
        gs_h = gs_w * (9/16) # Yatay animasyon varsayımı
        
        pos_x = (270 - gs_w) * gs_x_pct
        pos_y = (480 - gs_h) * gs_y_pct
        
        painter.setBrush(QColor("#00FF88"))
        painter.drawRect(QRect(int(pos_x), int(pos_y), int(gs_w), int(gs_h)))
        painter.setPen(QPen(QColor("#1A1A24")))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        painter.drawText(QRect(int(pos_x), int(pos_y), int(gs_w), int(gs_h)), Qt.AlignmentFlag.AlignCenter, "Abone Ol\nAnimasyonu")
        painter.end()
        self.preview_image_lbl.setPixmap(pixmap)

    # ─────────────────────────────────────────────────────────────── #
    #  SEKME: AI VİDEO ÖZETLEYİCİ                                      #
    # ─────────────────────────────────────────────────────────────── #
    def run_shorts_maker(self):
        kaynak_video = self.shorts_source_drop.path_lbl.toolTip() or self.shorts_source_drop.get_path()
        raw_intervals = self.shorts_intervals_input.text()
        if not kaynak_video:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir video seçin.")
            return
        if not raw_intervals:
            QMessageBox.warning(self, "Uyarı", "Lütfen saniye aralıklarını girin.")
            return
        araliklar = []
        toplam = 0
        try:
            for p in raw_intervals.split(','):
                bas, bit = p.split('-')
                bas, bit = int(bas.strip()), int(bit.strip())
                if bas >= bit:
                    raise ValueError(f"Hatalı: {bas}-{bit}")
                araliklar.append((bas, bit))
                toplam += bit - bas
        except Exception:
            QMessageBox.critical(self, "Format Hatası", "Örnek: 02-05, 75-83, 113-121")
            return
        if toplam > 53: # 59 YERİNE 53 OLDU
            QMessageBox.warning(self, "Süre", f"Toplam {toplam}sn > 53sn sınırı! (Intro/Outro payı)")
            return
            
        gs_saniyeler = []
        if self.in_gs_times.text().strip():
            try:
                gs_saniyeler = [int(x.strip()) for x in self.in_gs_times.text().split(',')]
            except:
                QMessageBox.warning(self, "Hata", "GS saniyelerini doğru girin (Örn: 10, 30)")
                return

        # 🔥 YENİ: Arayüzden seçilen stilleri FFmpeg'in anladığı formata çeviriyoruz
        renk_sozlugu = {
            "Beyaz": "&H00FFFFFF",
            "Sarı": "&H0000FFFF",
            "Yeşil": "&H0000FF00",
            "Kırmızı": "&H000000FF",
            "Turkuaz": "&H00D3D200"
        }
        secilen_renk = renk_sozlugu.get(self.color_combo.currentText(), "&H00FFFFFF")
        secilen_font = self.font_combo.currentText()
        secilen_boyut = self.font_size_spin.value()
        secilen_yukseklik = self.margin_spin.value()

        # 🔥 YENİ: Seçilen renk ve fontları işçiye gönderiyoruz
        self._shorts_worker = ShortsWorker(
            kaynak_video=kaynak_video, araliklar=araliklar, api_key=config.GEMINI_API_KEY,
            intro=self.in_intro.text(), outro=self.in_outro.text(),
            gs_video=self.in_gs.text(), gs_times=gs_saniyeler,
            font_name=secilen_font, font_color=secilen_renk, 
            font_size=secilen_boyut, margin_v=secilen_yukseklik,
            gs_scale=self.shorts_gs_scale_spin.value(),
            gs_x=self.shorts_gs_x_spin.value(),
            gs_y=self.shorts_gs_y_spin.value()
        )

        self.shorts_progress.setValue(0)
        self.shorts_console.clear()
        self.shorts_start_btn.setEnabled(False)
        self.dashboard.update_step("shorts", 5, "Başlatılıyor...")

        self._shorts_worker.progress_signal.connect(self._on_shorts_progress)
        self._shorts_worker.log_signal.connect(self.shorts_console.append)
        self._shorts_worker.finished_signal.connect(self._on_shorts_done)
        self._shorts_worker.error_signal.connect(self._on_shorts_error)
        self._shorts_worker.start()
    def _on_shorts_progress(self, val, text):
        self.shorts_progress.setValue(val)
        self.shorts_progress.setFormat(text)
        self.dashboard.update_step("shorts", val, text)
    def _on_shorts_done(self, path):
        self.shorts_start_btn.setEnabled(True)
        self.shorts_start_btn.setText("🎬 Kes, Altyazı Ekle ve Üret")
        self.shorts_console.append(f"\n✅ Shorts hazır: {path}")
        self.dashboard.update_step("shorts", 100, "Tamamlandı", done=True)
        self._log(f"Shorts tamamlandı → {path}")
        QMessageBox.information(self, "Shorts Tamamlandı", f"Dosya: {path}")
    def _on_shorts_error(self, err):
        self.shorts_start_btn.setEnabled(True)
        self.shorts_start_btn.setText("🎬 Kes, Altyazı Ekle ve Üret")
        self.shorts_progress.setFormat("Hata!")
        self.dashboard.update_step("shorts", 0, err, error=True)
        self._log(f"Shorts hatası: {err}")
        QMessageBox.critical(self, "Shorts Hatası", err)

    # ═══════════════════════════════════════════════════════════════ #
    #  AI ANALİZ (WHISPER + GEMINI)                                   #
    # ═══════════════════════════════════════════════════════════════ #
