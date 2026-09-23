"""Ana uygulama penceresi: tum sekme mixin'lerini bir araya getirir."""
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget

from .tabs.settings_tab import SettingsTabMixin
from .tabs.dashboard_tab import DashboardTabMixin
from .tabs.dynamic_video_tab import DynamicVideoTabMixin
from .tabs.shorts_tab import ShortsTabMixin
from .tabs.summary_tab import SummaryTabMixin
from .tabs.seo_tab import SeoTabMixin
from .tabs.ai_analysis_tab import AiAnalysisTabMixin
from .tabs.memory_tab import MemoryTabMixin
from .tabs.metrics_tab import MetricsTabMixin
from .tabs.template_tab import TemplateTabMixin
from .tabs.trending_tab import TrendingTabMixin


# ═══════════════════════════════════════════════════════════════════ #
#  ANA UYGULAMA PENCERESİ                                             #
# ═══════════════════════════════════════════════════════════════════ #
class YouTubeManagerApp(
    QMainWindow,
    SettingsTabMixin,
    DashboardTabMixin,
    DynamicVideoTabMixin,
    ShortsTabMixin,
    SummaryTabMixin,
    SeoTabMixin,
    AiAnalysisTabMixin,
    MemoryTabMixin,
    MetricsTabMixin,
    TemplateTabMixin,
    TrendingTabMixin,
):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎬 İçerik & Veri Yönetim Paneli")
        self.setGeometry(80, 80, 1100, 720)
        self.setMinimumSize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # State
        self.dyn_output_dir        = None
        self.dyn_clean_audio_path  = None
        self._transcript_segments  = []   # Whisper segmentleri (AI B-Roll için)
        self._sys_monitor          = None

        # Sekme başlatma
        self.init_dashboard_tab()       # [0] Dashboard
        self.init_dynamic_video_tab()   # [1] Dinamik Video
        self.init_shorts_maker_tab()    # [2] Shorts
        self.init_summary_tab()
        self.init_seo_tab()             # [3] SEO
        self.init_workflow_tab()        # [4] İş Akışı (AI)
        self.init_memory_search_tab()   # [5] Bellek / Arama
        self.init_metrics_tab()         # [6] Metrikler
        self.init_workflow_gen_tab()    # [7] İçerik Şablonu
        self.init_trending_tab()        # [8] Trend
        self.init_settings_tab()        # [9] Ayarlar

        self.connect_signals()
        self._start_system_monitor()

    def connect_signals(self):
        # SEO
        self.search_btn.clicked.connect(self.run_seo_analysis)
        # Metrikler
        self.refresh_metrics_btn.clicked.connect(self.update_metrics)
        # Şablon
        self.gen_template_btn.clicked.connect(self.generate_workflow_template)
        # Trend
        self.get_trends_btn.clicked.connect(self.fetch_trending_videos)
        self.generate_idea_btn.clicked.connect(self.generate_next_video_idea)
        # Dinamik video
        self.dyn_folder_btn.clicked.connect(self.select_dyn_folder)
        self.dyn_analyze_btn.clicked.connect(self.analyze_dynamic_audio)
        self.dyn_clean_btn.clicked.connect(self.create_clean_audio)
        self.dyn_start_btn.clicked.connect(self.run_dynamic_video_maker)
        # Shorts
        self.shorts_start_btn.clicked.connect(self.run_shorts_maker)
        # AI Analiz
        self.analyze_btn.clicked.connect(self.run_ai_pipeline)
        # Bellek araması
        self.memory_search_btn.clicked.connect(self.run_memory_search)
        self.memory_search_input.returnPressed.connect(self.run_memory_search)

    # ═══════════════════════════════════════════════════════════════ #
    #  YARDIMCI FONKSİYONLAR                                          #
    # ═══════════════════════════════════════════════════════════════ #

    def closeEvent(self, event):
        if self._sys_monitor:
            self._sys_monitor.stop()
            self._sys_monitor.wait(1000)
        event.accept()
