"""AI Analiz (Whisper + Gemini) sekmesi."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QProgressBar, QCheckBox, QFrame, QMessageBox,
)

from .. import config
from ..widgets import DropZone
from ..workers import AiWorker

class AiAnalysisTabMixin:
    def init_workflow_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        self.workflow_drop = DropZone(
            "🎵 Analiz edilecek ses/video dosyasını sürükleyin",
            "Medya (*.mp4 *.wav *.mp3 *.mov)"
        )
        self.workflow_drop.file_dropped.connect(lambda p: None)

        opt_row = QHBoxLayout()
        self.chromadb_chk = QCheckBox("💾 ChromaDB'ye kaydet (Bellek Araması için)")
        self.chromadb_chk.setChecked(True)
        self.chromadb_chk.setStyleSheet("color: #00D2D3;")
        
        # 🔥 YENİ: Altyazı Dilleri Kutusu
        lang_group = QFrame()
        lang_group.setStyleSheet("background: #1E1E2E; border-radius: 8px; padding: 10px;")
        lang_layout = QHBoxLayout(lang_group)
        lang_layout.addWidget(QLabel("<b>🌍 YouTube SRT Çıktıları:</b> TR (Varsayılan) + "))
        
        self.lang_en_chk = QCheckBox("İngilizce")
        self.lang_ru_chk = QCheckBox("Rusça")
        self.lang_de_chk = QCheckBox("Almanca")
        self.lang_es_chk = QCheckBox("İspanyolca")
        
        # Rusça ve İngilizceyi varsayılan olarak seçili yapalım
        self.lang_en_chk.setChecked(True)
        self.lang_ru_chk.setChecked(True)
        
        lang_layout.addWidget(self.lang_en_chk)
        lang_layout.addWidget(self.lang_ru_chk)
        lang_layout.addWidget(self.lang_de_chk)
        lang_layout.addWidget(self.lang_es_chk)
        
        opt_row.addWidget(self.chromadb_chk)
        opt_row.addStretch()

        # 🔥 DİKKAT: Silinen Buton Tanımlamasını Buraya Geri Getirdik
        self.analyze_btn = QPushButton("🤖 AI Analizini Başlat (Whisper + Gemini)")
        self.analyze_btn.setStyleSheet("background:#7C3AED; color:white; font-weight:bold; font-size:14px; padding:12px;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Bekleniyor...")

        self.output_text = QTextEdit()
        self.output_text.setPlaceholderText(
            "Başlık, açıklama, zaman çizelgesi ve Shorts aralıkları burada görünecek..."
        )

        # ── Ekrana Çizme Sırası ──
        layout.addWidget(self.workflow_drop)
        layout.addLayout(opt_row)
        layout.addWidget(lang_group)      # Dil kutusu
        layout.addWidget(self.analyze_btn) # Eksik olan analiz butonu
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.output_text)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "🤖 AI Analiz")

    # ─────────────────────────────────────────────────────────────── #
    #  SEKME: BELLEK ARAMASI (ChromaDB)                               #
    # ─────────────────────────────────────────────────────────────── #
    def run_ai_pipeline(self):
        file_path = self.workflow_drop.path_lbl.toolTip() or self.workflow_drop.get_path()
        if not file_path:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir dosya seçin.")
            return
        self.analyze_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Başlıyor...")
        self.dashboard.update_step("transcribe", 5, "Whisper başlatılıyor...")

        selected_langs = {}
        if self.lang_en_chk.isChecked(): selected_langs["EN"] = "İngilizce"
        if self.lang_ru_chk.isChecked(): selected_langs["RU"] = "Rusça"
        if self.lang_de_chk.isChecked(): selected_langs["DE"] = "Almanca"
        if self.lang_es_chk.isChecked(): selected_langs["ES"] = "İspanyolca"
        self._ai_worker = AiWorker(
            file_path=file_path,
            gemini_api_key=config.GEMINI_API_KEY,
            save_to_chromadb=self.chromadb_chk.isChecked(),
            target_langs=selected_langs
        )
        self._ai_worker.progress_signal.connect(self._on_ai_progress)
        self._ai_worker.result_signal.connect(self._on_ai_result)
        self._ai_worker.error_signal.connect(self._on_ai_error)
        self._ai_worker.segments_signal.connect(self._on_ai_segments)
        self._ai_worker.start()
    def _on_ai_progress(self, val, text):
        self.progress_bar.setValue(val)
        self.progress_bar.setFormat(text)
        self.dashboard.update_step("transcribe", val, text)
        self._log(f"AI: {val}% — {text}")
    def _on_ai_result(self, text):
        self.output_text.setPlainText(text)
        self.analyze_btn.setEnabled(True)
        self.dashboard.update_step("transcribe", 100, "Tamamlandı", done=True)
        self._log("AI analizi tamamlandı.")
    def _on_ai_error(self, err):
        self.analyze_btn.setEnabled(True)
        self.dashboard.update_step("transcribe", 0, err, error=True)
        self._log(f"AI hatası: {err}")
        QMessageBox.critical(self, "AI Hatası", err)
    def _on_ai_segments(self, segments):
        """Whisper segmentlerini kaydeder (Akıllı B-Roll için)."""
        self._transcript_segments = segments
        self._log(f"📝 {len(segments)} adet transcript segment kaydedildi (Akıllı B-Roll için)")
        if segments:
            self.dyn_console.append(f"[BİLGİ] Segmentler kaydedildi: {len(segments)} adet")
        else:
            self.dyn_console.append("[UYARI] Boş segment listesi kaydedildi!")

    # ═══════════════════════════════════════════════════════════════ #
    #  BELLEK ARAMASI (ChromaDB)                                      #
    # ═══════════════════════════════════════════════════════════════ #
