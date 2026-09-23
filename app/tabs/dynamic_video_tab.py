"""Dinamik Video (Podcast/Vlog) sekmesi."""
import os
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar, QSpinBox, QDoubleSpinBox, QCheckBox, QFrame, QButtonGroup, QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt

from .. import config
from ..widgets import DropZone
from ..workers import (
    DynamicRenderWorker, VlogWorker, CleanAudioWorker,
)
from podcast_flow import PodcastFlow

class DynamicVideoTabMixin:
    def init_dynamic_video_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        
        # ── SOL PANEL (Ayarlar) ──
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)

        # Mod seçimi
        mode_layout = QHBoxLayout()
        self.mode_podcast_rb = QPushButton("🎙️ Podcast Modu\n(Temiz Ses + B-Roll)")
        self.mode_podcast_rb.setCheckable(True)
        self.mode_podcast_rb.setChecked(True)
        self.mode_video_rb   = QPushButton("🎬 Vlog Modu\n(Sessizlikleri Kes)")
        self.mode_video_rb.setCheckable(True)
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.mode_podcast_rb)
        self.mode_group.addButton(self.mode_video_rb)
        box_style = """
            QPushButton { background:#2D2D3F; color:#8C8C9A; border:2px solid #323242; border-radius:10px; padding:15px; font-weight:bold; font-size:14px; }
            QPushButton:checked { background:#00D2D3; color:#1A1A24; border:2px solid #00D2D3; }
            QPushButton:hover:!checked { background:#323242; color:#FFF; border:2px solid #5A5A72; }
        """
        self.mode_podcast_rb.setStyleSheet(box_style)
        self.mode_video_rb.setStyleSheet(box_style)
        mode_layout.addWidget(self.mode_podcast_rb)
        mode_layout.addWidget(self.mode_video_rb)

        ai_layout = QHBoxLayout()
        ai_label = QLabel("AI Görsel Sayısı (0 = Kapalı):")
        ai_label.setStyleSheet("color: #00D2D3; font-weight: bold;")
        self.ai_image_count = QSpinBox()
        self.ai_image_count.setRange(0, 5); self.ai_image_count.setValue(2)
        ai_layout.addWidget(ai_label); ai_layout.addWidget(self.ai_image_count); ai_layout.addStretch()

        self.dyn_source_drop = DropZone("🎵 Kaynak ses/video sürükleyin", "Medya (*.mp4 *.wav *.mp3 *.mov)")
        self.dyn_source_drop.file_dropped.connect(self._on_dyn_source_dropped)

        broll_row = QHBoxLayout()
        self.dyn_folder_input = QLineEdit(); self.dyn_folder_input.setPlaceholderText("B-Roll Klasörü (Podcast modunda zorunlu)")
        self.dyn_folder_input.setReadOnly(True)
        self.dyn_folder_btn   = QPushButton("📁 Klasör Seç")
        broll_row.addWidget(self.dyn_folder_input, 1); broll_row.addWidget(self.dyn_folder_btn)

        smart_row = QHBoxLayout()
        self.smart_broll_chk = QCheckBox("🤖 Akıllı B-Roll Seçimi")
        self.smart_broll_chk.setStyleSheet("color: #00D2D3; font-weight: bold;")
        smart_row.addWidget(self.smart_broll_chk); smart_row.addStretch()

        # 🔥 YENİ: GELİŞMİŞ GREEN SCREEN AYARLARI
        gs_frame = QFrame()
        gs_frame.setStyleSheet("background: #1E1E2E; border-radius: 8px; padding: 5px;")
        gs_layout = QGridLayout(gs_frame)
        gs_lbl = QLabel("🟩 Abone Ol (Green Screen) Ayarları")
        gs_lbl.setStyleSheet("font-weight: bold; color: #00FF88;")
        
        self.dyn_gs_input = QLineEdit(); self.dyn_gs_input.setPlaceholderText("Animasyon (.mp4)")
        btn_dyn_gs = QPushButton("📁"); btn_dyn_gs.clicked.connect(lambda: self.select_file_to_input(self.dyn_gs_input))
        
        self.dyn_gs_interval = QSpinBox()
        self.dyn_gs_interval.setRange(0, 3600)  # Maksimum 1 saate kadar saniye girilebilir
        self.dyn_gs_interval.setValue(75)       # Varsayılan 75 saniye oldu
        self.dyn_gs_interval.setPrefix("Her ")
        self.dyn_gs_interval.setSuffix(" Saniye (0=Kapalı)") # Dk yerine Saniye yazdık
        
# 🔥 YENİ: KANCA (HOOK) VE GEÇİŞ EFEKTİ AYARLARI
        hook_frame = QFrame()
        hook_frame.setStyleSheet("background: #1E1E2E; border-radius: 8px; padding: 5px;")
        hook_layout = QGridLayout(hook_frame)
        hook_lbl = QLabel("🪝 Kanca (Hook) ve Geçiş Ayarları")
        hook_lbl.setStyleSheet("font-weight: bold; color: #F5A623;")
        
        self.dyn_hook_input = QLineEdit()
        self.dyn_hook_input.setPlaceholderText("Kanca Aralığı (Örn: 34-45) - Boşsa Kanca Yok")
        
        self.dyn_transition_audio = QLineEdit()
        self.dyn_transition_audio.setPlaceholderText("Geçiş Sesi (Örn: whoosh.mp3)")
        btn_trans_audio = QPushButton("📁")
        btn_trans_audio.clicked.connect(lambda: self.select_file_to_input(self.dyn_transition_audio))
        
        hook_layout.addWidget(hook_lbl, 0, 0, 1, 3)
        hook_layout.addWidget(QLabel("Zaman (sn):"), 1, 0)
        hook_layout.addWidget(self.dyn_hook_input, 1, 1, 1, 2)
        hook_layout.addWidget(QLabel("Efekt:"), 2, 0)
        hook_layout.addWidget(self.dyn_transition_audio, 2, 1)
        hook_layout.addWidget(btn_trans_audio, 2, 2)
        
        left_layout.addWidget(hook_frame)

        self.gs_scale_spin = QSpinBox(); self.gs_scale_spin.setRange(10, 100); self.gs_scale_spin.setValue(25)
        self.gs_scale_spin.setPrefix("Boyut: %")
        self.gs_x_spin = QSpinBox(); self.gs_x_spin.setRange(0, 100); self.gs_x_spin.setValue(95)
        self.gs_x_spin.setPrefix("Sağ/Sol (X): %")
        self.gs_y_spin = QSpinBox(); self.gs_y_spin.setRange(0, 100); self.gs_y_spin.setValue(95)
        self.gs_y_spin.setPrefix("Alt/Üst (Y): %")

        gs_layout.addWidget(gs_lbl, 0, 0, 1, 4)
        gs_layout.addWidget(self.dyn_gs_input, 1, 0, 1, 2); gs_layout.addWidget(btn_dyn_gs, 1, 2)
        gs_layout.addWidget(self.dyn_gs_interval, 1, 3)
        gs_layout.addWidget(self.gs_scale_spin, 2, 0); gs_layout.addWidget(self.gs_x_spin, 2, 1)
        gs_layout.addWidget(self.gs_y_spin, 2, 2, 1, 2)

        config_layout = QHBoxLayout()
        self.dyn_threshold_spin = QDoubleSpinBox(); self.dyn_threshold_spin.setRange(-80.0, -10.0); self.dyn_threshold_spin.setValue(-55.0)
        self.dyn_silence_len_spin = QSpinBox(); self.dyn_silence_len_spin.setRange(100, 2000); self.dyn_silence_len_spin.setValue(500)
        self.dyn_keep_silence_spin = QSpinBox(); self.dyn_keep_silence_spin.setRange(0, 500); self.dyn_keep_silence_spin.setValue(200)
        config_layout.addWidget(self.dyn_threshold_spin); config_layout.addWidget(self.dyn_silence_len_spin); config_layout.addWidget(self.dyn_keep_silence_spin)

        btn_layout = QHBoxLayout()
        self.dyn_analyze_btn = QPushButton("🔊 Ses Analizi"); self.dyn_analyze_btn.setStyleSheet("background:#4A90E2; color:white; font-weight:bold;")
        self.dyn_clean_btn   = QPushButton("✂️ Sesi Temizle"); self.dyn_clean_btn.setStyleSheet("background:#F5A623; color:white; font-weight:bold;")
        self.dyn_start_btn   = QPushButton("🚀 Render Başlat"); self.dyn_start_btn.setStyleSheet("background:#E27D60; color:white; font-weight:bold;")
        btn_layout.addWidget(self.dyn_analyze_btn); btn_layout.addWidget(self.dyn_clean_btn); btn_layout.addWidget(self.dyn_start_btn)

        self.dyn_progress = QProgressBar(); self.dyn_progress.setValue(0); self.dyn_progress.setFormat("Bekleniyor...")
        self.dyn_console = QTextEdit(); self.dyn_console.setReadOnly(True); self.dyn_console.setStyleSheet("background:#0D0D1A; color:#00FF88; font-size: 11px;")

        left_layout.addLayout(mode_layout); left_layout.addLayout(ai_layout)
        left_layout.addWidget(self.dyn_source_drop); left_layout.addLayout(broll_row); left_layout.addLayout(smart_row)
        left_layout.addWidget(gs_frame) # YENİ GS KUTUSU
        left_layout.addLayout(config_layout); left_layout.addLayout(btn_layout)
        left_layout.addWidget(self.dyn_progress); left_layout.addWidget(self.dyn_console)

        # ── SAĞ PANEL (Canlı Önizleme - 16:9 Yatay) ──
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        preview_lbl = QLabel("🖥️ Animasyon Önizleme (16:9)")
        preview_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #00D2D3;")
        preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dyn_preview_lbl = QLabel("Ayarları değiştirdiğinizde\nanimasyon konumu burada görünecek.")
        self.dyn_preview_lbl.setFixedSize(480, 270) # 16:9 Yatay Format
        self.dyn_preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dyn_preview_lbl.setStyleSheet("background: #000; border: 2px dashed #3A3A5C; color: #8C8C9A;")

        self.update_dyn_preview_btn = QPushButton("🔄 Önizlemeyi Güncelle")
        self.update_dyn_preview_btn.setStyleSheet("background:#2D2D3F; color:white;")

        right_layout.addWidget(preview_lbl)
        right_layout.addWidget(self.dyn_preview_lbl)
        right_layout.addWidget(self.update_dyn_preview_btn)

        main_layout.addWidget(left_panel, 6) 
        main_layout.addWidget(right_panel, 4) 
        tab.setLayout(main_layout)
        self.tabs.addTab(tab, "🎬 Dinamik Video")

        # Buton tetiklemeleri
        self.update_dyn_preview_btn.clicked.connect(self._refresh_dyn_preview)
        self.gs_scale_spin.valueChanged.connect(self.update_dyn_preview_btn.click)
        self.gs_x_spin.valueChanged.connect(self.update_dyn_preview_btn.click)
        self.gs_y_spin.valueChanged.connect(self.update_dyn_preview_btn.click)
    def _refresh_dyn_preview(self):
        """Green Screen animasyonunun ekranda nerede duracağını çizer."""
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen
        from PyQt6.QtCore import Qt, QRect

        pixmap = QPixmap(480, 270)
        pixmap.fill(QColor("#1A1A24")) 
        painter = QPainter(pixmap)
        
        # Kullanıcı Ayarları
        scale = self.gs_scale_spin.value() / 100.0
        x_pct = self.gs_x_spin.value() / 100.0
        y_pct = self.gs_y_spin.value() / 100.0

        # Animasyonun sahte boyutunu hesapla (Örn: Orijinal video yatay dikdörtgen varsayımı)
        gs_w = 480 * scale
        gs_h = gs_w * (9/16)

        # Pozisyonu hesapla (Ekran Genişliği - Obje Genişliği) * Yüzde
        pos_x = (480 - gs_w) * x_pct
        pos_y = (270 - gs_h) * y_pct

        # Yeşil kutuyu çiz
        painter.setBrush(QColor("#00FF88"))
        painter.drawRect(QRect(int(pos_x), int(pos_y), int(gs_w), int(gs_h)))
        
        # İçine yazı yaz
        painter.setPen(QPen(QColor("#1A1A24")))
        painter.drawText(QRect(int(pos_x), int(pos_y), int(gs_w), int(gs_h)), Qt.AlignmentFlag.AlignCenter, "Abone Ol\nAnimasyonu")

        painter.end()
        self.dyn_preview_lbl.setPixmap(pixmap)
    # ─────────────────────────────────────────────────────────────── #
    #  SEKME: SHORTS VE ALTYAZI ÖNİZLEME                               #
    # ─────────────────────────────────────────────────────────────── #
    def select_dyn_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "B-Roll Klasörü Seç")
        if folder:
            self.dyn_folder_input.setText(folder)
    def make_output_folder(self, source_path):
        base = os.path.splitext(os.path.basename(source_path))[0]
        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out  = os.path.join(os.path.dirname(os.path.abspath(source_path)) or '.', f"{base}_output_{ts}")
        os.makedirs(out, exist_ok=True)
        return out

    # ═══════════════════════════════════════════════════════════════ #
    #  DİNAMİK VİDEO İŞLEMLERİ                                       #
    # ═══════════════════════════════════════════════════════════════ #
    def _on_dyn_source_dropped(self, path):
        """Dosya sürükle-bırak ile seçildiğinde çağrılır."""
        self.dyn_source_drop.set_path(path)
        self.dyn_console.append(f"[✓] Kaynak dosya algılandı: {os.path.basename(path)}")
    def analyze_dynamic_audio(self):
        ses_dosyasi = self.dyn_source_drop.get_path()
        if not ses_dosyasi:
            QMessageBox.warning(self, "Uyarı", "Lütfen kaynak ses dosyasını seçin.")
            return
        # Tam yolu al (DropZone sadece basename gösterir)
        full_path = self.dyn_source_drop.path_lbl.toolTip() or ses_dosyasi
        self.dashboard.update_step("ses_analiz", 10, "Başlıyor...")
        try:
            flow = PodcastFlow(source_audio_path=full_path, b_roll_folder=self.dyn_folder_input.text() or '.')
            analysis = flow.analyze_audio()
            msg = (f"Süre: {analysis['duration_seconds']}s | "
                   f"Ort: {analysis['average_dbfs']} dBFS | "
                   f"Önerilen Eşik: {analysis['recommended_silence_thresh']} dB")
            self.dyn_console.append(f"[SES ANALİZİ] {msg}")
            self.dyn_threshold_spin.setValue(analysis['recommended_silence_thresh'])
            self.dashboard.update_step("ses_analiz", 100, "Tamamlandı", done=True)
            self._log(f"Ses analizi tamamlandı: {msg}")
        except Exception as e:
            self.dashboard.update_step("ses_analiz", 0, str(e), error=True)
            QMessageBox.critical(self, "Hata", f"Ses analizi başarısız: {e}")
    def create_clean_audio(self):
        full_path = self.dyn_source_drop.path_lbl.toolTip() or self.dyn_source_drop.get_path()
        if not full_path:
            QMessageBox.warning(self, "Uyarı", "Lütfen kaynak ses dosyasını seçin.")
            return

        self.dyn_console.append("[1/2] Temizlenmiş ses oluşturuluyor (arka planda)...")
        self.dashboard.update_step("ses_temiz", 5, "Başlatılıyor...")

        threshold    = self.dyn_threshold_spin.value()
        silence_len  = self.dyn_silence_len_spin.value()
        keep_silence = self.dyn_keep_silence_spin.value()
        base  = os.path.splitext(os.path.basename(full_path))[0]
        yeni  = f"{base}_temizlenmis.wav"

        self.dyn_clean_btn.setEnabled(False)

        self._clean_audio_worker = CleanAudioWorker(
            source_audio_path=full_path,
            b_roll_folder=self.dyn_folder_input.text() or '.',
            min_silence_ms=silence_len,
            silence_thresh=threshold,
            keep_silence_ms=keep_silence,
            output_filename=yeni
        )
        self._clean_audio_worker.progress_signal.connect(self._on_clean_audio_progress)
        self._clean_audio_worker.finished_signal.connect(self._on_clean_audio_finished)
        self._clean_audio_worker.error_signal.connect(self._on_clean_audio_error)
        self._clean_audio_worker.start()
    def run_dynamic_video_maker(self):
        full_path = self.dyn_source_drop.path_lbl.toolTip() or self.dyn_source_drop.get_path()
        if not full_path:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir kaynak dosyası seçin.")
            return

        # 🔥 MONTAJ KANCA (HOOK) SÜRELERİNİ AYRIŞTIRMA 🔥
        hook_ranges = []
        raw_hook = self.dyn_hook_input.text().strip()
        if raw_hook:
            try:
                for part in raw_hook.split(','):
                    h_s, h_e = part.split('-')
                    start = int(h_s.strip())
                    end = int(h_e.strip())
                    if end <= start: raise ValueError
                    hook_ranges.append((start, end))
            except:
                QMessageBox.warning(self, "Hata", "Kanca formatı hatalı! Doğru format: 15-20, 85-90, 150-155")
                return

        trans_audio = self.dyn_transition_audio.text().strip()

        if self.mode_video_rb.isChecked():
            if not full_path.lower().endswith(('.mp4', '.mov')):
                QMessageBox.warning(self, "Uyarı", "Video edit modu için .mp4 veya .mov seçin.")
                return
        
            base = os.path.splitext(os.path.basename(full_path))[0]
            out = os.path.join(os.path.dirname(full_path), f"{base}_otomatik_edit.mp4")
        
            self.dyn_console.append("🎬 Vlog Modu başlatılıyor (arka planda)...")
            self.dyn_start_btn.setEnabled(False)
            self.dyn_progress.setValue(0)
        
            self._vlog_worker = VlogWorker(
                video_path=full_path,
                output_path=out,
                min_silence_ms=self.dyn_silence_len_spin.value(),
                silence_thresh=self.dyn_threshold_spin.value(),
                gs_video=self.dyn_gs_input.text(),          
                gs_interval=self.dyn_gs_interval.value(),   
                gs_scale=self.gs_scale_spin.value(), 
                gs_x=self.gs_x_spin.value(),         
                gs_y=self.gs_y_spin.value(),
                hook_ranges=hook_ranges,          # 🔥 İŞÇİYE GİRDİ
                transition_audio=trans_audio      # 🔥 İŞÇİYE GİRDİ
            )
            self._vlog_worker.progress_signal.connect(self._on_vlog_progress)
            self._vlog_worker.finished_signal.connect(self._on_vlog_finished)
            self._vlog_worker.error_signal.connect(self._on_vlog_error)
            self._vlog_worker.start()
        
        else:
            video_klasoru = self.dyn_folder_input.text()
            if not video_klasoru:
                QMessageBox.warning(self, "Uyarı", "B-Roll klasörünü seçin.")
                return
        
            base = os.path.splitext(os.path.basename(full_path))[0]
            out = os.path.join(os.path.dirname(full_path), f"{base}_dinamik.mp4")
            use_smart = self.smart_broll_chk.isChecked()
            
            try:
                ai_count = self.ai_image_count.value()
            except AttributeError:
                ai_count = 0
        
            if ai_count > 0 and not config.GEMINI_API_KEY:
                QMessageBox.warning(
                    self, "⚠️ API Key Eksik",
                    f"AI Görsel için Gemini API Key gereklidir!\n\nLütfen Ayarlar'dan ekleyin."
                )
                return
        
            has_transcript = hasattr(self, '_transcript_segments') and bool(self._transcript_segments)
            
            if (use_smart or ai_count > 0) and not has_transcript:
                reply = QMessageBox.question(
                    self, "🤖 Akıllı B-Roll & AI Görsel",
                    "Henüz transcript verisi yok! Devam ederseniz rastgele B-Roll seçilecek. İptal etmek için HAYIR'a basın.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
                use_smart = False
                ai_count = 0
                self.smart_broll_chk.setChecked(False)
                if hasattr(self, 'ai_image_count'):
                    self.ai_image_count.setValue(0)
                self.dyn_console.append("[BİLGİ] Segment olmadığı için rastgele B-Roll moduna geçildi, AI Görsel kapatıldı.")
        
            segs_for_ai = self._transcript_segments if (use_smart or ai_count > 0) else []
            self.dyn_start_btn.setEnabled(False)
            self.dyn_progress.setValue(0)

            self._render_worker = DynamicRenderWorker(
                clean_audio_path=full_path,
                b_roll_folder=video_klasoru,
                output_path=out,
                use_smart_broll=use_smart,
                gemini_api_key=config.GEMINI_API_KEY,
                transcript_segments=segs_for_ai,
                ai_image_count=ai_count,
                gs_video=self.dyn_gs_input.text(),          
                gs_interval=self.dyn_gs_interval.value(), 
                gs_scale=self.gs_scale_spin.value(), 
                gs_x=self.gs_x_spin.value(),         
                gs_y=self.gs_y_spin.value(),
                hook_ranges=hook_ranges,          # 🔥 İŞÇİYE GİRDİ
                transition_audio=trans_audio      # 🔥 İŞÇİYE GİRDİ
            )
            self._render_worker.progress_signal.connect(self._on_render_progress)
            self._render_worker.finished_signal.connect(self._on_render_done)
            self._render_worker.error_signal.connect(self._on_render_error)
            self._render_worker.start()
            
    def _on_render_progress(self, val, text):
        self.dyn_progress.setValue(val)
        self.dyn_progress.setFormat(text)
        self.dyn_console.append(f"[{val}%] {text}")
        if val < 70:
            self.dashboard.update_step("broll", val * 2, text)
        else:
            self.dashboard.update_step("render", val, text)
        self._log(f"Render: {val}% — {text}")
    def _on_render_done(self, path):
        self.dyn_console.append(f"\n✅ Render tamamlandı: {path}")
        self.dyn_start_btn.setEnabled(True)
        self.dashboard.update_step("render", 100, "Tamamlandı", done=True)
        self._log(f"Render tamamlandı → {path}")
        QMessageBox.information(self, "Render Tamamlandı", f"Video hazır:\n{path}")
    def _on_render_error(self, err):
        self.dyn_console.append(f"\n[HATA] {err}")
        self.dyn_start_btn.setEnabled(True)
        self.dashboard.update_step("render", 0, err, error=True)
        self._log(f"Render hatası: {err}")
        QMessageBox.critical(self, "Render Hatası", err)

    # ═══════════════════════════════════════════════════════════════ #
    #  SHORTS İŞLEMİ                                                  #
    # ═══════════════════════════════════════════════════════════════ #
    def _on_vlog_progress(self, val, text):
        """Vlog işleminin ilerlemesini güncelle."""
        self.dyn_progress.setValue(val)
        self.dyn_progress.setFormat(text)
        self.dyn_console.append(f"[{val}%] {text}")
        self.dashboard.update_step("render", val, text)
        self._log(f"Vlog: {val}% — {text}")
    def _on_vlog_finished(self, path):
        """Vlog işlemi tamamlandı."""
        self.dyn_console.append(f"\n✅ Vlog edit tamamlandı: {path}")
        self.dyn_start_btn.setEnabled(True)
        self.dashboard.update_step("render", 100, "Tamamlandı", done=True)
        self._log(f"Vlog edit tamamlandı → {path}")
        QMessageBox.information(self, "Vlog Tamamlandı", f"Video hazır:\n{path}")
    def _on_vlog_error(self, err):
        """Vlog işleminde hata oluştu."""
        self.dyn_console.append(f"\n❌ HATA: {err}")
        self.dyn_start_btn.setEnabled(True)
        self.dashboard.update_step("render", 0, err, error=True)
        self._log(f"Vlog hatası: {err}")
        QMessageBox.critical(self, "Vlog Hatası", err)
    def _on_clean_audio_progress(self, val, text):
        self.dyn_console.append(f"[{val}%] {text}")
        self.dashboard.update_step("ses_temiz", val, text)
    def _on_clean_audio_finished(self, clean_path, duration):
        self.dyn_source_drop.set_path(clean_path)
        self.dyn_source_drop.path_lbl.setToolTip(clean_path)
        self.dyn_console.append(f"[2/2] Temizlenmiş ses: {clean_path} ({duration}s)")
        self.dashboard.update_step("ses_temiz", 100, f"{duration}s", done=True)
        self._log(f"Ses temizlendi → {clean_path}")
        self.dyn_clean_btn.setEnabled(True)
    def _on_clean_audio_error(self, err):
        self.dyn_console.append(f"[HATA] Ses temizleme başarısız: {err}")
        self.dashboard.update_step("ses_temiz", 0, err, error=True)
        self._log(f"Ses temizleme hatası: {err}")
        self.dyn_clean_btn.setEnabled(True)
        try:
            from audio_processing import AudioProcessingError
            if "Temizlenecek anlamlı konuşma bulunamadı" in err:
                QMessageBox.critical(self, "Temizleme Hatası", f"{err}\n\nLütfen eşik değerlerini düşürüp tekrar deneyin.")
            else:
                QMessageBox.critical(self, "Hata", f"Temizleme başarısız: {err}\nDetaylar konsolda.")
        except Exception:
            QMessageBox.critical(self, "Hata", f"Temizleme başarısız: {err}\nDetaylar konsolda.")
