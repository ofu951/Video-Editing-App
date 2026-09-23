"""Trend analizi sekmesi."""
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox,
)

from .. import config
from googleapiclient.discovery import build
from google import genai

class TrendingTabMixin:
    def init_trending_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        
        self.region_combo = QComboBox()
        self.region_combo.addItems(["Türkiye (TR)", "Global / ABD (US)", "İngiltere (GB)", "Almanya (DE)", "Japonya (JP)"])
        self.region_combo.setStyleSheet("background-color: #2D2D3F; color: white; padding: 5px;")
        
        self.time_combo = QComboBox()
        self.time_combo.addItems(["Anlık (Trend Videolar)", "Son 7 Gün", "Son 30 Gün"])
        self.time_combo.setStyleSheet("background-color: #2D2D3F; color: white; padding: 5px;")

        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Tümü (Filtresiz)", "Bilim ve Teknoloji (28)", "Eğitim (27)", 
            "Oyun (20)", "Nasıl Yapılır ve Stil (26)", "Eğlence (24)", "Film ve Animasyon (1)"
        ])
        self.category_combo.setStyleSheet("background-color: #2D2D3F; color: white; padding: 5px;")

        self.get_trends_btn = QPushButton("Verileri Çek")

        filter_layout.addWidget(QLabel("Bölge:"))
        filter_layout.addWidget(self.region_combo)
        filter_layout.addWidget(QLabel("Zaman:"))
        filter_layout.addWidget(self.time_combo)
        filter_layout.addWidget(QLabel("Kategori:"))
        filter_layout.addWidget(self.category_combo)
        filter_layout.addWidget(self.get_trends_btn)

        self.idea_context_combo = QComboBox()
        self.idea_context_combo.addItems([
            "Teknik Mühendislik (STM32, ROS2, Robotik)",
            "Podcast & Derin Sohbet",
            "Gündelik Hayat & Vlog (Mühendis Yaşamı)",
            "Gündem & Trend İncelemesi",
            "Üretkenlik & Dijital Minimalizm"
        ])
        self.idea_context_combo.setStyleSheet("background-color: #2D2D3F; color: white; padding: 5px;")
        self.generate_idea_btn = QPushButton("💡 AI Video Fikri Üret")
        self.generate_idea_btn.setStyleSheet("background-color: #9b59b6; color: white; font-weight: bold; padding: 5px 15px;")
        
        filter_layout.addWidget(QLabel("Konsept:"))
        filter_layout.addWidget(self.idea_context_combo)
        filter_layout.addWidget(self.generate_idea_btn)

        self.trend_table = QTableWidget(0, 4)
        self.trend_table.setHorizontalHeaderLabels(["Video Başlığı", "Kanal Adı", "İzlenme", "Yayın Tarihi"])
        self.trend_table.horizontalHeader().setStretchLastSection(True)

        self.idea_output = QTextEdit()
        self.idea_output.setReadOnly(True)
        self.idea_output.setPlaceholderText("Yapay zekanın trendlere bakarak üreteceği video fikri burada görünecek...")
        self.idea_output.setStyleSheet("background:#0D0D1A; color:#00FF88; font-family: Consolas, monospace; padding: 10px;")

        layout.addLayout(filter_layout)
        layout.addWidget(self.trend_table)
        layout.addWidget(self.idea_output)  
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Trendler ve Keşif")
        self.get_trends_btn.clicked.connect(self.fetch_trending_videos)
    def fill_trend_table(self, items):
        self.trend_table.setRowCount(0)
        for item in items:
            title = item['snippet']['title']
            channel = item['snippet']['channelTitle']
            date = item['snippet']['publishedAt'][:10]
            views = int(item['statistics'].get('viewCount', 0))

            row = self.trend_table.rowCount()
            self.trend_table.insertRow(row)
            self.trend_table.setItem(row, 0, QTableWidgetItem(title))
            self.trend_table.setItem(row, 1, QTableWidgetItem(channel))
            self.trend_table.setItem(row, 2, QTableWidgetItem(f"{views:,}"))
            self.trend_table.setItem(row, 3, QTableWidgetItem(date))

    def generate_next_video_idea(self):
        row_count = self.trend_table.rowCount()
        if row_count == 0:
            QMessageBox.warning(self, "Veri Yok", "Önce trend verilerini çekin.")
            return
        self.generate_idea_btn.setText("Üretiliyor...")
        QApplication.processEvents()
        limit  = min(row_count, 15)
        trends = [f"- {self.trend_table.item(i,0).text()} | {self.trend_table.item(i,2).text()}" for i in range(limit)]
        secilen_konsept = self.idea_context_combo.currentText()
        try:
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            prompt = f"""
Sen "Odadan Çıkmadan Mühendislik" kanalı için içerik planlayan yaratıcı bir yapımcısın.
Şu an YouTube'da trend olan ve insanların ilgisini çeken videolar şunlar:
{chr(10).join(trends)}

Bugün kanal için "{secilen_konsept}" konseptinde bir içerik üretmek istiyoruz.

Görev: Yukarıdaki trendlerdeki popüler ilgi dinamiklerini (insanların neye tıkladığını, neyi merak ettiğini) analiz et. Bu dinamikleri kullanarak, kanalın "{secilen_konsept}" formatına tam oturan, çarpıcı ve çok izlenebilecek 1 adet video veya podcast fikri üret.

Çıktı Formatı:
🎯 VİDEO/BÖLÜM FİKRİ: (Tıklanmaya doyuracak çarpıcı bir başlık)
🧠 NEDEN BU KONU: (Trendlerle ve seçilen konseptle olan psikolojik/algoritma bağlantısı) veya gündemde yer edinebilecek bir konu tercihi de yapılabilir.
📝 İÇERİK PLANI: (Dikkat çekici 3-4 ana başlık)
"""
            resp = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
            self.idea_output.setPlainText(resp.text)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            self.generate_idea_btn.setText("💡 AI Video Fikri Üret")

    # ═══════════════════════════════════════════════════════════════ #
    #  SIGNAL / SLOT BAĞLANTILARI                                     #
    # ═══════════════════════════════════════════════════════════════ #
    def fetch_trending_videos(self):
        """Seçilen bölge, zaman ve kategoriye göre videoları çeker."""
        # Bölge Kodunu Ayıkla
        region_text = self.region_combo.currentText()
        region_code = region_text[region_text.find("(")+1 : region_text.find(")")]
        
        time_text = self.time_combo.currentText()
        
        # Kategori Kodunu Ayıkla (Örn: "Bilim ve Teknoloji (28)" içinden 28'i alır)
        category_text = self.category_combo.currentText()
        category_id = None
        if "Tümü" not in category_text:
            category_id = category_text[category_text.find("(")+1 : category_text.find(")")]

        self.get_trends_btn.setText("Yükleniyor...")
        self.get_trends_btn.setEnabled(False)
        QApplication.processEvents()

        try:
            youtube = build('youtube', 'v3', developerKey=config.YOUTUBE_API_KEY)
            video_ids = []
            
            # 🔥 SENARYO 1: ANLIK TRENDLER (Asla çökmez, direkt YouTube listesini çeker)
            if "Anlık" in time_text:
                request_params = {
                    'part': 'snippet,statistics',
                    'chart': 'mostPopular',
                    'regionCode': region_code,
                    'maxResults': 20
                }
                if category_id:
                    request_params['videoCategoryId'] = category_id
                    
                request = youtube.videos().list(**request_params)
                response = request.execute()
                self.fill_trend_table(response.get('items', []))

            # 🔥 SENARYO 2: 7 GÜN / 30 GÜN ARAMASI
            else:
                import datetime
                now = datetime.datetime.now(datetime.timezone.utc)
                if "7 Gün" in time_text:
                    start_date = now - datetime.timedelta(days=7)
                else:
                    start_date = now - datetime.timedelta(days=30)
                
                published_after = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')

                search_params = {
                    'part': 'id',
                    'type': 'video',
                    'order': 'viewCount',
                    'regionCode': region_code,
                    'publishedAfter': published_after,
                    'maxResults': 20
                }
                if category_id:
                    search_params['videoCategoryId'] = category_id

                search_request = youtube.search().list(**search_params)
                search_response = search_request.execute()

                for item in search_response.get('items', []):
                    video_ids.append(item['id']['videoId'])

                if video_ids:
                    stats_request = youtube.videos().list(
                        part='snippet,statistics',
                        id=','.join(video_ids)
                    )
                    stats_response = stats_request.execute()
                    self.fill_trend_table(stats_response.get('items', []))
                else:
                    QMessageBox.information(self, "Bilgi", "Bu kriterlere uygun video bulunamadı.")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler çekilemedi:\n{str(e)}")
            
        finally:
            self.get_trends_btn.setText("Verileri Çek")
            self.get_trends_btn.setEnabled(True)
    
