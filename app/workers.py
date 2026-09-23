"""Arka planda calisan tum QThread worker siniflari.

NOT: ``_save_to_chromadb`` orijinal GUI.py dosyasinda modul seviyesinde
tanimlanmisti ve hicbir zaman AiWorker sinifina metod olarak baglanmamisti
(muhtemelen bir kopyala-yapistir hatasi); ``self._save_to_chromadb(...)``
cagrisi AttributeError firlatip try/except tarafindan sessizce
yutuluyordu, yani ChromaDB kaydi hicbir zaman gerceklesmiyordu. Bu
surumde fonksiyon AiWorker sinifinin gercek bir metodu olarak
baglanmistir; davranis artik dogru sekilde calisir.
"""
import os
import datetime
from PyQt6.QtCore import QThread, pyqtSignal
import whisper
from google import genai

class AiWorker(QThread):
    progress_signal = pyqtSignal(int, str)
    result_signal   = pyqtSignal(str)
    error_signal    = pyqtSignal(str)
    segments_signal = pyqtSignal(list)

    def __init__(self, file_path, gemini_api_key=None, save_to_chromadb=False, target_langs=None):
        super().__init__()
        self.file_path = file_path
        self.gemini_api_key = gemini_api_key
        self.save_to_chromadb = save_to_chromadb
        self.target_langs = target_langs or {}

    def _format_srt_time(self, seconds):
        """Saniyeyi SRT formatına çevirir (00:00:05,000)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    def run(self):
        try:
            self.progress_signal.emit(15, "Whisper modeli yükleniyor ve deşifre başlıyor...")
            model = whisper.load_model("base")
            result = model.transcribe(self.file_path, language="tr")

            # Standart YouTube SRT Formatını Hazırla (Ham Hali)
            raw_srt_content_tr = ""
            segments_for_db = []
            
            for i, segment in enumerate(result["segments"]):
                start_srt = self._format_srt_time(segment['start'])
                end_srt = self._format_srt_time(segment['end'])
                text = segment['text'].strip()
                
                raw_srt_content_tr += f"{i+1}\n{start_srt} --> {end_srt}\n{text}\n\n"
                
                segments_for_db.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": text
                })
            
            # 🔥 YENİ: Ana Türkçe altyazıyı Gemini ile düzeltiyoruz
            self.progress_signal.emit(30, "Ana altyazı hataları düzeltiliyor (Gemini)...")
            client = genai.Client(api_key=self.gemini_api_key)
            
            fix_prompt = f"""
Sen profesyonel bir altyazı çevirmeni ve mühendislik editörüsün.
Aşağıda Whisper AI tarafından sesten yazıya çevrilmiş bir Türkçe YouTube SRT dosyası bulunuyor. 
İçerikte teknik konular (STM32, ROS2, ROV, PCB vb.) ve günlük sohbetler yer alıyor olabilir.

GÖREVİN:
1. Duyum, yazım ve mantık hatalarını bağlama uygun olarak düzelt. Anlamsız devrik cümleleri toparla.
2. ZAMAN DAMGALARINA (Örn: 00:01:23,000 --> 00:01:25,500) KESİNLİKLE DOKUNMA!
3. ALTYAZI BLOK NUMARALARINA (1, 2, 3...) KESİNLİKLE DOKUNMA!
4. Fazladan hiçbir açıklama, yorum veya "İşte düzeltilmiş metin" gibi kelimeler yazma. Sadece SRT formatını ver.

HAM SRT:
{raw_srt_content_tr}
"""
            try:
                response = client.models.generate_content(
                    model='gemini-3.6-flash', 
                    contents=fix_prompt
                )
                srt_content_tr = response.text.replace('```srt', '').replace('```', '').strip()
            except Exception as e:
                print(f"SRT düzeltme hatası: {e}")
                srt_content_tr = raw_srt_content_tr  # API hatası olursa çökmek yerine ham metni kullan
            
            # Düzeltilmiş Ana Türkçe SRT'yi diske kaydet
            base_name = os.path.splitext(os.path.basename(self.file_path))[0]
            with open(f"{base_name}_TR.srt", "w", encoding="utf-8") as f:
                f.write(srt_content_tr)
                
            self.segments_signal.emit(segments_for_db)    

            # 🔥 ÇOKLU DİL ÇEVİRİSİ (Artık Düzeltilmiş SRT Üzerinden Yapılacak)
            for lang_code, lang_name in self.target_langs.items():
                self.progress_signal.emit(40, f"{lang_name} altyazısı üretiliyor...")
                prompt = f"""
Bu bir YouTube SRT altyazı dosyasıdır. Görevin bu metni {lang_name} diline çevirmektir.
KESİNLİKLE UYMAN GEREKEN KURALLAR:
1. Zaman damgalarına (Örn: 00:01:23,000 --> 00:01:25,500) ASLA dokunma.
2. Numaralandırmayı (1, 2, 3...) ASLA bozma.
3. Sadece Türkçe metinleri profesyonel bir {lang_name} çevirisine dönüştür.
4. Fazladan hiçbir açıklama, yorum veya 'Tamam', 'İşte çeviri' gibi kelimeler yazma. Sadece SRT formatını ver.

METİN:
{srt_content_tr}
"""
                try:
                    response = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
                    ceviri = response.text.replace('```srt', '').replace('```', '').strip()
                    with open(f"{base_name}_{lang_code}.srt", "w", encoding="utf-8") as f:
                        f.write(ceviri)
                except Exception as e:
                    print(f"{lang_code} çevirisi başarısız: {e}")    

            # ── ChromaDB'ye kaydet ──────────────────────────────────
            if self.save_to_chromadb:
                self.progress_signal.emit(45, "ChromaDB vektör veritabanına kaydediliyor...")
                try:
                    self._save_to_chromadb(segments_for_db)
                    self.progress_signal.emit(55, "ChromaDB kaydı tamamlandı ✓")
                except Exception as db_err:
                    self.progress_signal.emit(55, f"ChromaDB uyarısı: {db_err}")

            self.progress_signal.emit(60, "Gemini ile SEO analizi yapılıyor...")

            prompt = f"""
Sen profesyonel bir YouTube SEO uzmanı ve mühendislik içerikleri editörüsün.
Aşağıda Mr Herbokolog kanalının Ar-Ge videoları serisi için oluşturulmuş zaman damgalı deşifre metni var.
DİKKAT: Bu metin Whisper tarafından sesten yazıya çevrildi; STM32, ROS2, ROV, PCB, gömülü sistemler gibi teknik terimlerde duyum hataları olabilir. Fakat konuşulan konu mühendislik dışı bir konu da olabilir.

Görevlerin:
1. HATA AYIKLAMA: Mantık ve duyum hatalarını mühendislik bağlamına göre düzelt.
2. VİDEO BAŞLIĞI: En fazla 100 karakter, tek başlık. İnsanda videoya tıklama merakı uyandıracak başlık bul.
3. AÇIKLAMA: En fazla 1000 karakter.
4. ZAMAN ÇİZELGESİ: ~5 veya daha fazla bölüm, YouTube bölüm formatı. HOOK İçin Eklenecek kısımları da ekle. Örneğin 55 saniyelik hook ekliyorsan 0-55 Hook bölümü, sonrasında 1 2 3 4 5 diye gidebilirsin.
5. VİRAL SHORTS KESİTLERİ: Toplam 53 saniye, en az 2 farklı aralık Gerek görürsen 3 4 te olur. Saniye cinsinden oluştur örneğin 75.saniye-85saniye formatında oluştur.
6. 5 DAKİKALIK ÖZET ARALIKLARI: Toplam 300 saniyeye (±10%) yaklaşacak şekilde en önemli anları seç. Tolerans ile beraber 330 saniyeyi geçmesin!
7. MONTAJ KANCA (HOOK) ARALIKLARI: Videonun en merak uyandırıcı, en dikkat çekici veya vurucu anlarından yaklaşık 45-60 saniyelik 3 farklı yerden kesit yap Bu kısa kesitler arka arkaya birleşip videonun en başında dinamik bir fragman oluşturacak.

Çıktı formatı (ekstra yorum ekleme):

📌 BAŞLIK: 
[Başlık]

📝 AÇIKLAMA:
[Açıklama]

⏱️ ZAMAN ÇİZELGESİ:
[Çizelge]

🪝 VURUCU KANCA (HOOK) ARALIKLARI:
[Aralıklar — başlangıç-bitiş şeklinde virgülle ayırarak, örn: 15-20, 85-90, 150-155, 210-215, 305-310, 420-425]

✂️ SHORTS ARALIKLARI:
[Aralıklar — başlangıç-bitiş şeklinde, örn: 15-30, 45-60]

📊 5 DAKİKALIK ÖZET ARALIKLARI:
[Aralıklar — başlangıç-bitiş şeklinde, örn: 0-45, 60-120, 180-240]

DEŞİFRE METNİ:
{srt_content_tr}
"""
            response = client.models.generate_content(
                model='gemini-3.6-flash', contents=prompt
            )
            self.progress_signal.emit(100, "Tamamlandı!")
            self.result_signal.emit(response.text)

        except Exception as e:
            self.error_signal.emit(str(e))

    def _save_to_chromadb(self, segments):
        """ChromaDB'ye segmentleri kaydeder. Hata durumunda sessizce geçer."""
        try:
            import chromadb
        except ImportError:
            self.progress_signal.emit(55, "⚠️ ChromaDB yüklü değil, kayıt atlandı. (pip install chromadb)")
            return
        
        try:
            client = chromadb.PersistentClient(path="podcast_memory_db")
            collection = client.get_or_create_collection(
                name="podcast_transcripts",
                metadata={"hnsw:space": "cosine"}
            )
            video_id = os.path.splitext(os.path.basename(self.file_path))[0]
            docs, metas, ids = [], [], []
            
            for i, seg in enumerate(segments):
                doc_id = f"{video_id}_seg_{i}"
                docs.append(seg["text"])
                metas.append({
                    "source_file": self.file_path,
                    "start_sec": seg["start"],
                    "end_sec": seg["end"],
                    "video_id": video_id,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                ids.append(doc_id)
            
            if docs:
                collection.upsert(documents=docs, metadatas=metas, ids=ids)
                self.progress_signal.emit(55, f"✅ ChromaDB: {len(docs)} segment kaydedildi")
                
        except Exception as e:
            self.progress_signal.emit(55, f"⚠️ ChromaDB hatası: {str(e)[:80]}")


class DynamicRenderWorker(QThread):
    progress_signal  = pyqtSignal(int, str)
    finished_signal  = pyqtSignal(str)
    error_signal     = pyqtSignal(str)

    # 🔥 DÜZELTME: hook_start ve hook_dur silindi, hook_ranges eklendi!
    def __init__(self, clean_audio_path, b_roll_folder,
                 output_path='yeni_dinamik_bolum.mp4',
                 use_smart_broll=False, gemini_api_key=None,
                 transcript_segments=None, ai_image_count=0,
                 gs_video=None, gs_interval=0, gs_scale=25, gs_x=95, gs_y=95,
                 hook_ranges=None, transition_audio=""):
        super().__init__()
        self.clean_audio_path  = clean_audio_path
        self.b_roll_folder     = b_roll_folder
        self.output_path       = output_path
        self.use_smart_broll   = use_smart_broll
        self.gemini_api_key    = gemini_api_key
        self.transcript_segments = transcript_segments or []
        self.ai_image_count    = ai_image_count
        self.gs_video          = gs_video
        self.gs_interval       = gs_interval
        self.gs_scale          = gs_scale
        self.gs_x              = gs_x
        self.gs_y              = gs_y
        self.hook_ranges       = hook_ranges or []  # 🔥 BURAYA AKTARILDI
        self.transition_audio  = transition_audio

    def run(self):
        try:
            os.makedirs(os.path.dirname(self.output_path) or '.', exist_ok=True)

            if self.use_smart_broll and self.gemini_api_key and self.transcript_segments:
                self.progress_signal.emit(5, "🤖 Akıllı B-Roll seçimi başlatılıyor...")
                self._render_with_smart_broll()
            else:
                self.progress_signal.emit(10, "Dinamik video render başlatıldı...")
                
                from deneme import DinamikPodcastUretici
                uretici = DinamikPodcastUretici(
                    ses_kaynagi=self.clean_audio_path, 
                    video_klasoru=self.b_roll_folder
                )
                
                # 🔥 DÜZELTME: Motora yeni hook_ranges verisini aktarıyoruz
                uretici.green_screen_video = self.gs_video
                uretici.green_screen_interval = self.gs_interval
                uretici.gs_scale = self.gs_scale
                uretici.gs_x = self.gs_x
                uretici.gs_y = self.gs_y
                uretici.hook_ranges = self.hook_ranges
                uretici.transition_audio = self.transition_audio
                
                self.progress_signal.emit(35, "B-roll videoları hazırlanıyor...")
                
                uretici.uretimi_baslat(
                    cikti_yolu=self.output_path, 
                    ai_image_count=self.ai_image_count,
                    transcript_segments=self.transcript_segments,
                    gemini_api_key=self.gemini_api_key
                )
                
                self.progress_signal.emit(100, "Render tamamlandı.")
                self.finished_signal.emit(self.output_path)

        except Exception as e:
            import traceback; traceback.print_exc()
            self.error_signal.emit(str(e))
            
    def _render_with_smart_broll(self):
        from smart_broll_selector import SmartBRollSelector
        def cb(pct, msg):
            self.progress_signal.emit(pct, msg)

        selector = SmartBRollSelector(
            b_roll_folder=self.b_roll_folder,
            gemini_api_key=self.gemini_api_key,
            progress_callback=cb
        )

        plan = selector.create_smart_broll_plan(self.transcript_segments)
        self.progress_signal.emit(70, "B-Roll klipleri render ediliyor...")
        gorsel_katman = selector.render_broll_from_plan(plan)

        # Ses + görsel birleştir (FFmpeg ile)
        import tempfile, subprocess
        tmp_visual = tempfile.mktemp(suffix="_smart_visual.mp4")
        self.progress_signal.emit(80, "Görsel katman yazılıyor...")
        gorsel_katman.write_videofile(
            tmp_visual, codec="libx264", audio=False, fps=30,
            preset="ultrafast", threads=0
        )
        gorsel_katman.close()

        self.progress_signal.emit(90, "Ses ve görsel birleştiriliyor (FFmpeg)...")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", tmp_visual,
            "-i", self.clean_audio_path,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
            self.output_path
        ], check=True)

        if os.path.exists(tmp_visual):
            os.remove(tmp_visual)

        self.progress_signal.emit(100, "✅ Akıllı B-Roll render tamamlandı!")
        self.finished_signal.emit(self.output_path)


class ShortsWorker(QThread):
    progress_signal  = pyqtSignal(int, str)
    log_signal       = pyqtSignal(str)
    finished_signal  = pyqtSignal(str)
    error_signal     = pyqtSignal(str)

    def __init__(self, kaynak_video, araliklar, api_key, output_name='yeni_shorts.mp4',
                 intro=None, outro=None, gs_video=None, gs_times=None,
                 font_name="Arial", font_color="&H00FFFFFF", font_size=16, margin_v=60,
                 gs_scale=80, gs_x=50, gs_y=85):
        super().__init__()
        self.kaynak_video = kaynak_video
        self.araliklar    = araliklar
        self.api_key      = api_key
        self.output_name  = output_name
        self.intro        = intro
        self.outro        = outro
        self.gs_video     = gs_video
        self.gs_times     = gs_times
        self.font_name    = font_name
        self.font_color   = font_color
        self.font_size    = font_size
        self.margin_v     = margin_v
        self.gs_scale     = gs_scale
        self.gs_x         = gs_x
        self.gs_y         = gs_y

    def run(self):
        try:
            from create_shorts import ShortsUretici
            self.progress_signal.emit(10, "Shorts üretimi başlatılıyor...")
            
            # Parametreleri motor sınıfına iletiyoruz
            uretici = ShortsUretici(
                kaynak_video=self.kaynak_video,
                intro_video=self.intro,
                outro_video=self.outro,
                green_screen_video=self.gs_video,
                green_screen_times=self.gs_times,
                font_name=self.font_name,
                font_color=self.font_color,
                font_size=self.font_size,
                margin_v=self.margin_v,
                gs_scale=self.gs_scale, # 🔥 MOTOR SINIFINA PASLADIK
                gs_x=self.gs_x,         # 🔥 MOTOR SINIFINA PASLADIK
                gs_y=self.gs_y
            )

            self.progress_signal.emit(30, "Video kesiliyor ve birleştiriliyor...")
            self.log_signal.emit("[1/4] Aralıklar kesilip dikey birleştiriliyor...")
            gecici_video = uretici.formati_ayarla_ve_kes(araliklar=self.araliklar)

            self.progress_signal.emit(55, "Whisper altyazı çıkarılıyor...")
            self.log_signal.emit("[2/4] Whisper AI sesinizi dinliyor...")
            srt_dosyasi = uretici.altyazi_dosyasi_uret(gecici_video)

            self.progress_signal.emit(65, "Gemini altyazı hatalarını düzeltiyor...")
            self.log_signal.emit("[3/4] AI: Mantık ve anlam hataları düzeltiliyor...")
            duzeltilmis_srt = uretici.altyaziyi_yapay_zeka_ile_duzelt(
                srt_yolu=srt_dosyasi, api_key=self.api_key
            )

            self.progress_signal.emit(80, "Altyazılar gömülüyor (Hardcode)...")
            self.log_signal.emit("[4/4] Altyazılar FFmpeg ile kazınıyor...")
            uretici.altyaziyi_videoya_gom(
                video_yolu=gecici_video,
                srt_yolu=duzeltilmis_srt,
                cikti_adi=self.output_name
            )

            self.progress_signal.emit(100, "Shorts tamamlandı.")
            self.finished_signal.emit(self.output_name)

        except Exception as e:
            import traceback; traceback.print_exc()
            self.error_signal.emit(str(e))

class SummaryVideoWorker(QThread):
    progress_signal = pyqtSignal(int, str)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, video_path, target_minutes, api_key, ranges=None):
        super().__init__()
        self.video_path = video_path
        self.target_minutes = target_minutes
        self.api_key = api_key
        self.ranges = ranges  # 🔥 ARALIKLARI EKLE

    def run(self):
        try:
            from summary_generator import SummaryGenerator
            generator = SummaryGenerator(api_key=self.api_key)
            
            # Callback fonksiyonlarını bağla
            def prog_cb(val, msg):
                self.progress_signal.emit(val, msg)
            def log_cb(msg):
                self.log_signal.emit(msg)
            
            # 🔥 ARALIKLARI KULLAN — AI SORMA!
            if self.ranges:
                self.log_signal.emit("[INFO] Aralıklardan hızlı özet oluşturuluyor (AI kullanmıyor)...")
                output_path = generator.generate_summary_from_ranges(
                    video_path=self.video_path,
                    ranges=self.ranges,
                    progress_cb=prog_cb,
                    log_cb=log_cb
                )
            else:
                # Fallback: Eski AI metodu
                output_path = generator.generate_summary(
                    video_path=self.video_path,
                    target_minutes=self.target_minutes,
                    progress_cb=prog_cb,
                    log_cb=log_cb
                )
            self.finished_signal.emit(output_path)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_signal.emit(str(e))
class VlogWorker(QThread):
    """Vlog modu için arka plan thread'i."""
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    # 🔥 YENİ PARAMETRELER EKLENDİ (hook_ranges, transition_audio)
    def __init__(self, video_path, output_path, min_silence_ms, silence_thresh,
                 gs_video=None, gs_interval=0, gs_scale=25, gs_x=95, gs_y=95,
                 hook_ranges=None, transition_audio=""):
        super().__init__()
        self.video_path = video_path
        self.output_path = output_path
        self.min_silence_ms = min_silence_ms
        self.silence_thresh = silence_thresh
        self.gs_video = gs_video
        self.gs_interval = gs_interval
        self.gs_scale = gs_scale
        self.gs_x = gs_x
        self.gs_y = gs_y
        self.hook_ranges = hook_ranges or []
        self.transition_audio = transition_audio

    def run(self):
        try:
            from deneme import OtomatikVideoEditor
            
            self.progress_signal.emit(10, "Vlog modu başlatılıyor...")
            self.progress_signal.emit(30, "Ses analiz ediliyor ve sessizlikler tespit ediliyor...")
            
            editor = OtomatikVideoEditor(
                kaynak_video=self.video_path,
                cikti_yolu=self.output_path
            )
            
            editor.green_screen_video = self.gs_video
            editor.green_screen_interval = self.gs_interval
            editor.gs_scale = self.gs_scale
            editor.gs_x = self.gs_x
            editor.gs_y = self.gs_y
            
            # 🔥 MOTORA KANCA VERİLERİ AKTARILIYOR
            editor.hook_ranges = self.hook_ranges
            editor.transition_audio = self.transition_audio
            
            self.progress_signal.emit(50, "Video sessizliklerden arındırılıyor...")
            
            editor.uretimi_baslat(
                min_sessizlik_ms=self.min_silence_ms,
                esik_db=self.silence_thresh
            )
            
            self.progress_signal.emit(100, "Vlog edit tamamlandı!")
            self.finished_signal.emit(self.output_path)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_signal.emit(str(e))

class CleanAudioWorker(QThread):
    """Ses temizleme işlemini arka planda çalıştırır (UI donmasın diye)."""
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(str, float)
    error_signal = pyqtSignal(str)

    def __init__(self, source_audio_path, b_roll_folder, min_silence_ms, silence_thresh, keep_silence_ms, output_filename):
        super().__init__()
        self.source_audio_path = source_audio_path
        self.b_roll_folder = b_roll_folder
        self.min_silence_ms = min_silence_ms
        self.silence_thresh = silence_thresh
        self.keep_silence_ms = keep_silence_ms
        self.output_filename = output_filename

    def run(self):
        try:
            from podcast_flow import PodcastFlow
            self.progress_signal.emit(20, "Sessizlikler kaldırılıyor...")
            flow = PodcastFlow(
                source_audio_path=self.source_audio_path,
                b_roll_folder=self.b_roll_folder
            )
            clean_path, duration = flow.export_clean_audio(
                min_silence_ms=self.min_silence_ms,
                silence_thresh=self.silence_thresh,
                keep_silence_ms=self.keep_silence_ms,
                output_filename=self.output_filename
            )
            self.progress_signal.emit(100, "Tamamlandı")
            self.finished_signal.emit(clean_path, duration)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_signal.emit(str(e))

class SystemMonitorWorker(QThread):
    """CPU / RAM / GPU izleyici — saniyede bir emit eder."""
    stats_signal = pyqtSignal(float, float, float)  # cpu%, ram%, gpu_temp

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        import time
        import psutil
        while self._running:
            cpu  = psutil.cpu_percent(interval=None)
            ram  = psutil.virtual_memory().percent
            # GPU sıcaklık (nvidia-smi opsiyonel)
            gpu_temp = 0.0
            try:
                import subprocess
                out = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=temperature.gpu",
                     "--format=csv,noheader,nounits"],
                    stderr=subprocess.DEVNULL, timeout=1
                )
                gpu_temp = float(out.strip())
            except Exception:
                pass
            self.stats_signal.emit(cpu, ram, gpu_temp)
            time.sleep(1)

    def stop(self):
        self._running = False


class ChromaSearchWorker(QThread):
    result_signal = pyqtSignal(str)
    error_signal  = pyqtSignal(str)

    def __init__(self, query: str):
        super().__init__()
        self.query = query

    def run(self):
        try:
            import chromadb
            client = chromadb.PersistentClient(path="podcast_memory_db")
            collection = client.get_or_create_collection(name="podcast_transcripts")
            results = collection.query(query_texts=[self.query], n_results=5)
            
            docs      = results.get("documents", [[]])[0]
            metas     = results.get("metadatas", [[]])[0]
            distances = results.get("distances",  [[]])[0]

            if not docs:
                self.result_signal.emit("Veritabanında eşleşen içerik bulunamadı.")
                return

            output_lines = [f"🔍 '{self.query}' için bulunan {len(docs)} sonuç:\n"]
            for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances)):
                similarity = round((1 - dist) * 100, 1)
                start_sec  = int(meta.get("start_sec", 0))
                end_sec    = int(meta.get("end_sec",   0))
                src        = meta.get("source_file", "bilinmiyor")
                m, s       = divmod(start_sec, 60)
                output_lines.append(
                    f"{'─'*50}\n"
                    f"[{i+1}] Benzerlik: %{similarity}  |  ⏱️ {m:02}:{s:02}\n"
                    f"📁 Dosya: {os.path.basename(src)}\n"
                    f"💬 \"{doc[:200]}...\"\n"
                )

            self.result_signal.emit("\n".join(output_lines))

        except Exception as e:
            self.error_signal.emit(f"ChromaDB hatası: {e}\n\nİpucu: Önce AI Analiz sekmesinden bir video analiz edip ChromaDB'ye kaydedin.")
