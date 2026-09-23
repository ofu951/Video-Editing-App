"""Icerik sablonu sekmesi."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox,
)


class TemplateTabMixin:
    def init_workflow_gen_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        row1 = QHBoxLayout()
        self.episode_num_input = QLineEdit()
        self.episode_num_input.setPlaceholderText("Bölüm no (ör: 7)")
        self.topic_input       = QLineEdit()
        self.topic_input.setPlaceholderText("Konu (ör: STM32 DMA Ayarları)")
        row1.addWidget(QLabel("Bölüm:"))
        row1.addWidget(self.episode_num_input)
        row1.addWidget(QLabel("Konu:"))
        row1.addWidget(self.topic_input)
        self.gen_template_btn = QPushButton("📋 Şablonu Oluştur")
        self.output_text_wf = QTextEdit()
        layout.addLayout(row1)
        layout.addWidget(self.gen_template_btn)
        layout.addWidget(self.output_text_wf)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "📋 Şablon")

    # ─────────────────────────────────────────────────────────────── #
    #  SEKME: TREND ANALİZİ                                           #
    # ─────────────────────────────────────────────────────────────── #
    def generate_workflow_template(self):
        ep    = self.episode_num_input.text()
        topic = self.topic_input.text()
        if not ep or not topic:
            QMessageBox.warning(self, "Eksik", "Bölüm no ve konu zorunlu.")
            return
        tmpl = f"""Odadan Çıkmadan Mühendislik - Bölüm {ep}: {topic}

Bu bölümde {topic} üzerine odaklanıyoruz.

⏳ Zaman Çizelgesi:
00:00 - Giriş
02:15 - {topic} Mühendislik Bakış Açısı
08:30 - Arka Planda Çalışan Sistemler
14:45 - Sektörden Örnekler
20:10 - Kapanış

🔗 Bağlantılar: [GitHub] [İletişim]

#robotik #gömülüsistemler #mühendislik #odadançıkmadanmühendislik
"""
        self.output_text_wf.setPlainText(tmpl)
