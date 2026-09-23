import os
import math
import random
import subprocess
import tempfile
import traceback
from pydub import AudioSegment, effects
from pydub.silence import detect_nonsilent
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, vfx, CompositeVideoClip


class DinamikPodcastUretici:
    def __init__(self, ses_kaynagi, video_klasoru, ai_image_moments=None, green_screen_video=None, green_screen_interval=None):
        self.ses_kaynagi = ses_kaynagi
        self.video_klasoru = video_klasoru
        self.ai_image_moments = ai_image_moments or []
        self.green_screen_video = green_screen_video
        self.green_screen_interval = int(green_screen_interval) if green_screen_interval else 0
        self.min_sessizlik_ms = 500
        self.sessizlik_esigi_db = -55
        self.kesit_suresi_sn = 60

    # ------------------------------------------------------------------ #
    #  SES TEMİZLEME                                                       #
    # ------------------------------------------------------------------ #
    def sesi_temizle(self):
        print("[1/4] Ses dosyası analiz ediliyor ve sessizlikler temizleniyor...")
        ham_ses = AudioSegment.from_file(self.ses_kaynagi)

        anlamli_kisimlar = detect_nonsilent(
            ham_ses,
            min_silence_len=self.min_sessizlik_ms,
            silence_thresh=self.sessizlik_esigi_db,
        )

        temiz_ses = AudioSegment.empty()
        for baslangic, bitis in anlamli_kisimlar:
            temiz_ses += ham_ses[baslangic:bitis]

        print("[BILGI] Sese profesyonel podcast kompresörü ve normalizasyon uygulanıyor...")
        temiz_ses = effects.normalize(temiz_ses)
        temiz_ses = effects.compress_dynamic_range(
            temiz_ses,
            threshold=-15.0,
            ratio=4.0,
            attack=5.0,
            release=50.0,
        )

        kalici_ses_yolu = "temizlenmis_podcast_sesi.wav"
        temiz_ses.export(kalici_ses_yolu, format="wav")
        print(f"[BASARILI] Temiz ses oluşturuldu. Yeni süre: {len(temiz_ses) / 1000.0:.2f} saniye.")
        return kalici_ses_yolu, len(temiz_ses) / 1000.0

    @staticmethod
    def sesi_analiz_et(ses_kaynagi):
        ham_ses = AudioSegment.from_file(ses_kaynagi)
        ortalama_db = ham_ses.dBFS
        return round(ortalama_db - 15, 2)

    @staticmethod
    def sesi_temizle_ve_kaydet(ses_kaynagi, min_sessizlik_ms, esik_db):
        ham_ses = AudioSegment.from_file(ses_kaynagi)
        anlamli_kisimlar = detect_nonsilent(
            ham_ses,
            min_silence_len=min_sessizlik_ms,
            silence_thresh=esik_db,
        )
        temiz_ses = AudioSegment.empty()
        for baslangic, bitis in anlamli_kisimlar:
            temiz_ses += ham_ses[baslangic:bitis]
        kayit_yolu = "manuel_kontrol_icin_ses.wav"
        temiz_ses.export(kayit_yolu, format="wav")
        return kayit_yolu

    # ------------------------------------------------------------------ #
    #  GÖRSEl KATMAN — MoviePy sadece klipleri kesiyor, efekt YOK         #
    # ------------------------------------------------------------------ #
    def dinamik_video_olustur(self, hedef_sure_sn):
        print(f"[2/4] B-Roll klasöründeki ({self.video_klasoru}) videolar taranıyor...")
        
        video_dosyalari = [
            os.path.join(self.video_klasoru, f) 
            for f in os.listdir(self.video_klasoru) 
            if f.lower().endswith(('.mp4', '.mov'))
        ]
        
        if not video_dosyalari:
            raise ValueError(f"HATA: '{self.video_klasoru}' klasöründe hiç video bulunamadı!")
            
        gerekli_klip_sayisi = math.ceil(hedef_sure_sn / self.kesit_suresi_sn)
        klipler = []
        
        for i in range(gerekli_klip_sayisi):
            secilen_video_yolu = random.choice(video_dosyalari)
            video = VideoFileClip(secilen_video_yolu)
            video_suresi = video.duration
            
            if video_suresi <= self.kesit_suresi_sn:
                baslangic = 0
                bitis = video_suresi
            else:
                max_baslangic = video_suresi - self.kesit_suresi_sn
                baslangic = random.uniform(0, max_baslangic)
                bitis = baslangic + self.kesit_suresi_sn
                
            klip = video.subclipped(baslangic, bitis)
            klip = klip.resized(height=1080)
            
            # 1. GİZEMLİ SESLERİ YOK ET: B-Roll'un orijinal ses kanalını siliyoruz
            klip = klip.without_audio()
            
            # 2. GÖRSEL GEÇİŞ: Her 1 dakikalık klibin başına aydınlanma, sonuna kararma
            try:
                klip = klip.with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])
            except AttributeError:
                klip = klip.fx(vfx.fadein, 0.5).fx(vfx.fadeout, 0.5)
            
            # 3. İŞİTSEL GEÇİŞ: Kararırken rastgele whoosh sesi patlat (Eğer dosya varsa)
            if os.path.exists("whoosh.mp3"):
                try:
                    whoosh_tam = AudioFileClip("whoosh.mp3")
                    # Dosyanın süresi ne kadarsa onu aşmayacak şekilde dinamik hesapla
                    max_bas = max(0, whoosh_tam.duration - 1)
                    rastgele_sn = random.uniform(0, max_bas)
                    whoosh_sesi = whoosh_tam.subclipped(rastgele_sn, rastgele_sn + 1)
                    
                    try:
                        whoosh_gecikmeli = whoosh_sesi.with_start(max(0, klip.duration - 1))
                    except AttributeError:
                        whoosh_gecikmeli = whoosh_sesi.set_start(max(0, klip.duration - 1))
                        
                    klip = klip.with_audio(whoosh_gecikmeli)
                    whoosh_tam.close()
                except Exception as e:
                    print(f"[UYARI] Whoosh sesi eklenemedi: {e}")
            
            klipler.append(klip)
            
        print("[3/4] Rastgele seçilen kesitler Full HD (1080p) olarak uç uca ekleniyor...")
        final_gorsel = concatenate_videoclips(klipler) 
        
        # Videonun sonunu sesin tam bittiği saniyeye göre kusursuz kırp
        final_gorsel = final_gorsel.subclipped(0, hedef_sure_sn)
        return final_gorsel

    # ------------------------------------------------------------------ #
    #  FFmpeg ile GEÇİŞ EFEKTİ — MoviePy'ı atla                          #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _ffmpeg_xfade_concat(clip_paths, fade_duration=0.5, output_path="ffmpeg_with_fades.mp4"):
        """
        Birden fazla video dosyasını FFmpeg'in xfade filtresiyle
        siyah-geçişli (fade) olarak birleştirir.
        MoviePy'dan ~10-50x daha hızlıdır çünkü native C kodunda çalışır.
        """
        n = len(clip_paths)
        if n == 1:
            import shutil
            shutil.copy(clip_paths[0], output_path)
            return output_path

        # Her dosyanın süresini ffprobe ile ölç
        def get_duration(path):
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                path,
            ]
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
            return float(out.strip())

        durations = [get_duration(p) for p in clip_paths]

        # -i girişleri
        inputs = []
        for p in clip_paths:
            inputs += ["-i", p]

        # xfade filtre zinciri oluştur
        # Her geçiş için: offset = (süre_toplamı) - fade_duration
        filter_parts = []
        cumulative = 0.0
        prev_label = "[0:v]"

        for i in range(1, n):
            cumulative += durations[i - 1] - fade_duration
            next_label = f"[v{i}]" if i < n - 1 else "[vout]"
            filter_parts.append(
                f"{prev_label}[{i}:v]xfade=transition=fade:duration={fade_duration}"
                f":offset={cumulative:.4f}{next_label}"
            )
            prev_label = next_label

        # Ses için amix (veya sadece ilk kanal)
        audio_filter = "".join(f"[{i}:a]" for i in range(n))
        audio_filter += f"amix=inputs={n}:duration=first[aout]"

        filter_complex = ";".join(filter_parts) + ";" + audio_filter

        cmd = (
            inputs
            + [
                "-filter_complex", filter_complex,
                "-map", "[vout]",
                "-map", "[aout]",
                "-c:v", "libx264",
                "-preset", "veryfast",   # ultrafast'tan bir kademe yukarı = daha iyi kalite, hâlâ hızlı
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "192k",
                "-threads", "0",         # CPU çekirdeklerini otomatik kullan
                "-y", output_path,
            ]
        )
        print("[FFmpeg] xfade geçişleri uygulanıyor...")
        subprocess.run(["ffmpeg"] + cmd, check=True)
        return output_path

    # ------------------------------------------------------------------ #
    #  KANCA (HOOK) + WHOOSH — tamamen FFmpeg ile                         #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _ffmpeg_prepend_hook_with_whoosh(main_video, whoosh_mp3, output_path,
                                         hook_start=15, hook_dur=3,
                                         fade_dur=0.4):
        """
        Ana videodan hook kesiyor, whoosh ekliyor ve başa yapıştırıyor.
        Tüm işlem FFmpeg — MoviePy yok.
        """
        # Whoosh başlangıcını rastgele seç (0-4 sn arası)
        whoosh_offset = random.randint(0, 4)
        tmp_hook = tempfile.mktemp(suffix="_hook.mp4")
        tmp_whoosh = tempfile.mktemp(suffix="_whoosh.wav")

        # 1. Hook klibini kes
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", str(hook_start), "-t", str(hook_dur),
            "-i", main_video,
            "-c:v", "libx264", "-preset", "veryfast",
            "-c:a", "aac",
            tmp_hook,
        ], check=True)

        # 2. Whoosh sesini kes (1 sn)
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", str(whoosh_offset), "-t", "1",
            "-i", whoosh_mp3,
            tmp_whoosh,
        ], check=True)

        # 3. Hook + Whoosh sesini karıştır, fade-out ekle
        # 4. Ana videoya fade-in ekle
        # 5. İkisini xfade ile birleştir
        delay_s = max(0.0, hook_dur - 1.0)  # Whoosh son 1 sn'ye hizalı
        filter_complex = (
            # Hook videosuna fade-out
            f"[0:v]fade=t=out:st={hook_dur - fade_dur:.3f}:d={fade_dur}[hv];"
            # Hook sesine whoosh ekle
            f"[0:a]adelay={int(delay_s * 1000)}|{int(delay_s * 1000)}[hadelayed];"
            f"[2:a][hadelayed]amix=inputs=2:duration=longest[ha];"
            # Ana videoya fade-in
            f"[1:v]fade=t=in:st=0:d={fade_dur}[mv];"
            # Videoları concat
            f"[hv][ha][mv][1:a]concat=n=2:v=1:a=1[vout][aout]"
        )

        subprocess.run([
            "ffmpeg", "-y",
            "-i", tmp_hook,
            "-i", main_video,
            "-i", tmp_whoosh,
            "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-threads", "0",
            output_path,
        ], check=True)

        # Geçici dosyaları temizle
        for f in [tmp_hook, tmp_whoosh]:
            if os.path.exists(f):
                os.remove(f)

        return output_path

    # ------------------------------------------------------------------ #
    #  ANA AKIŞ                                                            #
    # ------------------------------------------------------------------ #
    def uretimi_baslat(self, cikti_yolu="final_dinamik_podcast.mp4", ai_image_count=0, transcript_segments=None, gemini_api_key=None):
        print("[1/4] Temizlenmiş ses okunuyor...")
        from pydub import AudioSegment
        import tempfile
        import subprocess
        import os
        
        # 1. Ses süresini ölç
        islenmis_ses = AudioSegment.from_file(self.ses_kaynagi)
        toplam_ses_suresi = len(islenmis_ses) / 1000.0
        temiz_ses_yolu = self.ses_kaynagi 

        # ─── 🔥 YAPAY ZEKA GÖRSEL VE AKILLI B-ROLL ÜRETİMİ ────────────────────
        ai_uretilen_anlar = None
        
        # Ekranda AI görsel seçilmişse ve elimizde metin varsa Imagen 3'e çizdir
        if ai_image_count > 0 and transcript_segments and gemini_api_key:
            print(f"\n[YAPAY ZEKA] Metinden {ai_image_count} adet kritik an çıkarılıp görsel çizdiriliyor...")
            tam_metin = " ".join([seg.get('text', '') for seg in transcript_segments])
            try:
                from ai_image_broll import AIImageBRoll
                ai_ressam = AIImageBRoll(gemini_api_key=gemini_api_key) 
                ai_uretilen_anlar = ai_ressam.build_ai_image_clips(transcript_text=tam_metin, count=ai_image_count)
            except Exception as e:
                print(f"[UYARI] AI Görsel üretilemedi, normal B-Roll ile devam ediliyor. Hata: {e}")

        print("[BİLGİ] Akıllı B-Roll planı oluşturuluyor...")
        
        # 🔴 FALLBACK RÁPIDO: Sem API key e sem transcript = usar código antigo simples
        if not gemini_api_key and not transcript_segments:
            print("[INFO] Modo rápido: B-Roll aleatório simples (sem análise)...")
            # Usar o código antigo super rápido
            gorsel_katman = self.dinamik_video_olustur(hedef_sure_sn=toplam_ses_suresi)
        else:
            # Modo inteligente com SmartBRollSelector
            from smart_broll_selector import SmartBRollSelector
            
            broll_selector = SmartBRollSelector(
                b_roll_folder=self.video_klasoru, 
                gemini_api_key=gemini_api_key
            )
            
            # 🔴 Eğer transcript_segments boşsa, simple random B-Roll plan yap
            if not transcript_segments:
                print("[BİLGİ] Transcript segmentleri yok. Rastgele B-Roll seçimi kullanılıyor...")
                # Basit bir plan oluştur: ses süresini 60 sanlık parçalara böl
                num_clips = max(1, int(toplam_ses_suresi / 60) + 1)
                plan = []
                for i in range(num_clips):
                    start_time = i * 60
                    end_time = min((i + 1) * 60, toplam_ses_suresi)
                    if end_time > start_time:
                        plan.append({
                            'start': start_time, 
                            'end': end_time, 
                            'video_path': random.choice([
                                os.path.join(self.video_klasoru, f) 
                                for f in os.listdir(self.video_klasoru) 
                                if f.lower().endswith(('.mp4', '.mov'))
                            ]),
                            'is_smart': False
                        })
            else:
                plan = broll_selector.create_smart_broll_plan(
                    segments=transcript_segments,
                    change_interval_secs=45,
                    ai_image_moments=ai_uretilen_anlar 
                )
            
            # Planlanan videoları kes, biç, efektle ve tek bir görsel katman yap
            gorsel_katman = broll_selector.render_broll_from_plan(plan)
        
        # Görüntü sesten uzunsa, sesin bittiği yerde görüntüyü de kes
        if gorsel_katman.duration > toplam_ses_suresi:
            gorsel_katman = gorsel_katman.subclipped(0, toplam_ses_suresi)

        # 🔥 YENİ: DİNAMİK VİDEO İÇİN GREEN SCREEN ANİMASYONU
        if getattr(self, 'green_screen_video', None) and os.path.exists(self.green_screen_video) and getattr(self, 'green_screen_interval', 0) > 0:
            print(f"[BİLGİ] Green Screen animasyonu her {self.green_screen_interval} saniyede bir ekleniyor...")
            try:
                from moviepy import VideoFileClip, vfx, CompositeVideoClip
                gs_clip = VideoFileClip(self.green_screen_video)
                
                # 1. Maskeleme ve Sürüm Uyumluluğu (Eşik 150 yapıldı)
                try:
                    gs_effect = vfx.MaskColor(color=[0, 255, 0], threshold=150, stiffness=5)
                    gs_clip = gs_clip.with_effects([gs_effect])
                except Exception:
                    gs_clip = gs_clip.fx(vfx.mask_color, color=[0, 255, 0], thr=150, s=5)
                
                # 2. Arayüzden Gelen Ölçeklendirme (Sabit 250 silindi)
                scale_factor = getattr(self, 'gs_scale', 25) / 100.0
                gs_clip = gs_clip.resized(width=gorsel_katman.w * scale_factor)
                
                # 3. Arayüzden Gelen Dinamik Konumlandırma
                x_pct = getattr(self, 'gs_x', 95) / 100.0
                y_pct = getattr(self, 'gs_y', 95) / 100.0
                
                pos_x = (gorsel_katman.w - gs_clip.w) * x_pct
                pos_y = (gorsel_katman.h - gs_clip.h) * y_pct
                
                try:
                    gs_clip = gs_clip.with_position((pos_x, pos_y))
                except AttributeError:
                    gs_clip = gs_clip.set_position((pos_x, pos_y))

                # 4. Klipleri Zamana Göre Dizme
                overlays = []
                aralik_sn = self.green_screen_interval 
                t = aralik_sn
                while t < gorsel_katman.duration:
                    try:
                        overlays.append(gs_clip.with_start(t))
                    except AttributeError:
                        overlays.append(gs_clip.set_start(t))
                    t += aralik_sn
                    
                if overlays:
                    gorsel_katman = CompositeVideoClip([gorsel_katman] + overlays)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"[UYARI] Green Screen eklenirken hata oluştu: {e}")
        # ──────────────────────────────────────────────────────────────────

        # 3. Ham birleşik videoyu geçici bir dosyaya yaz (ses YOK, sadece görüntü)
        tmp_no_audio = tempfile.mktemp(suffix="_no_audio.mp4")
        print("[2/4] Ham görsel katman diske yazılıyor (ses henüz yok)...")
        gorsel_katman.write_videofile(
            tmp_no_audio,
            codec="libx264",
            audio=False,          # Ses ekleme — FFmpeg'e bırak
            fps=30,
            preset="ultrafast",   # Geçici dosya için en hızlı preset yeterli
            threads=0,
        )
        gorsel_katman.close()

        # 4. Ses + görüntü birleştirme (Tamamen FFmpeg)
        tmp_with_audio = tempfile.mktemp(suffix="_with_audio.mp4")
        # 4. Ses + görüntü birleştirme (Tamamen FFmpeg)
        print("[3/4] FFmpeg: Temiz ses görüntüyle birleştiriliyor ve geçişler ekleniyor...")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", tmp_no_audio,
            "-i", temiz_ses_yolu,
            "-c:v", "copy",        
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            cikti_yolu, # 🔥 Doğrudan çıktıya yazdırıyoruz
        ], check=True)

        # 🔥 YENİ SİNEMATİK KANCA SİSTEMİ BURAYA GELECEK
        if getattr(self, 'hook_dur', 0) > 0:
            gecis_sesi = getattr(self, 'transition_audio', "whoosh.mp3")
            gecici_final = cikti_yolu.replace(".mp4", "_gecici.mp4")
            import shutil
            shutil.move(cikti_yolu, gecici_final)
            
            self._sinematik_kanca_ekle(
                ana_video=gecici_final, 
                cikti_yolu=cikti_yolu, 
                hook_start=self.hook_start, 
                hook_dur=self.hook_dur, 
                whoosh_sesi=gecis_sesi
            )
            if os.path.exists(gecici_final): os.remove(gecici_final)

        # Geçici dosyaları temizle
        for f in [tmp_no_audio]:
            if os.path.exists(f):
                try: os.remove(f)
                except: pass

        print(f"\n[MÜKEMMEL] İşlem tamamlandı!")
        print(f"  → Çıktı video  : {cikti_yolu}")
        print(f"  → Kullanılan ses: {temiz_ses_yolu}")

    @staticmethod
    def _sinematik_kanca_ekle(ana_video, cikti_yolu, hook_start, hook_dur, whoosh_sesi):
        """
        Videonun içinden hook_start itibariyle hook_dur kadar kesit alır.
        Ses son 1 saniyede hızla azalarak biter (fade-out).
        Araya transition sesi (whoosh) girer.
        Ana video başlarken ses hızla artarak girer (fade-in).
        """
        import os, tempfile, subprocess
        tmp_hook = tempfile.mktemp(suffix="_hook.mp4")
        
        # 1. Kancayı Ana Videodan Kes
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", str(hook_start), "-t", str(hook_dur),
            "-i", ana_video,
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac",
            tmp_hook,
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 2. Whoosh sesini kontrol et
        gecis_sesi = whoosh_sesi if os.path.exists(whoosh_sesi) else None
        
        # 3. Profesyonel FFmpeg Filter Complex (J-Cut / L-Cut mantığı)
        fade_dur = 1.0 # 1 saniyelik agresif azalış/artış
        
        # Kanca Videosu: Sonda kararma ve sesin kısılması
        filter_complex = (
            f"[0:v]fade=t=out:st={hook_dur - fade_dur:.3f}:d={fade_dur}[hv];"
            f"[0:a]afade=t=out:st={hook_dur - fade_dur:.3f}:d={fade_dur}[ha];"
        )
        
        # Ana Video: Başlangıçta aydınlanma ve sesin artması
        filter_complex += f"[1:v]fade=t=in:st=0:d={fade_dur}[mv];"
        filter_complex += f"[1:a]afade=t=in:st=0:d={fade_dur}[ma];"

        inputs = ["-i", tmp_hook, "-i", ana_video]

        if gecis_sesi:
            inputs += ["-i", gecis_sesi]
            # Whoosh sesi, kancanın tam bittiği anın 0.5 saniye öncesine hizalanır
            delay_ms = int(max(0.0, hook_dur - 0.5) * 1000)
            filter_complex += f"[2:a]adelay={delay_ms}|{delay_ms}[whoosh];"
            # Kanca sesi ile Whoosh sesini birleştir
            filter_complex += f"[ha][whoosh]amix=inputs=2:duration=first[ha_mixed];"
            filter_complex += f"[hv][ha_mixed][mv][ma]concat=n=2:v=1:a=1[vout][aout]"
        else:
            filter_complex += f"[hv][ha][mv][ma]concat=n=2:v=1:a=1[vout][aout]"

        # 4. Son Birleştirme ve Render
        print(f"🪝 Kanca birleştiriliyor ({hook_start}. saniyeden {hook_start + hook_dur}. saniyeye kadar)...")
        subprocess.run(
            ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            cikti_yolu
        ], check=True)

        if os.path.exists(tmp_hook):
            os.remove(tmp_hook)
class OtomatikVideoEditor:
    def __init__(self, kaynak_video, cikti_yolu="otomatik_editlenmis_video.mp4", 
                 green_screen_video=None, green_screen_interval=0,
                 gs_scale=25, gs_x=95, gs_y=95):
        self.kaynak_video = kaynak_video
        self.cikti_yolu = cikti_yolu
        self.green_screen_video = green_screen_video
        self.green_screen_interval = int(green_screen_interval)
        self.gs_scale = gs_scale
        self.gs_x = gs_x
        self.gs_y = gs_y
        self.hook_ranges = []
        self.transition_audio = ""
        
    def uretimi_baslat(self, min_sessizlik_ms=500, esik_db=-45):
        print("[1/3] Video içindeki ses analiz ediliyor...")
        
        # 🔥 Scope hatasını engellemek için içe aktarmalar sadece dosyanın en tepesinde.
        video = VideoFileClip(self.kaynak_video)
        
        temp_audio = tempfile.mktemp(suffix=".wav")
        video.audio.write_audiofile(temp_audio, logger=None)
        
        ham_ses = AudioSegment.from_file(temp_audio)
        anlamli_kisimlar = detect_nonsilent(ham_ses, min_silence_len=min_sessizlik_ms, silence_thresh=esik_db)
        
        klipler = []
        for bas_ms, bit_ms in anlamli_kisimlar:
            klipler.append(video.subclipped(bas_ms/1000.0, bit_ms/1000.0))
            
        final_video = concatenate_videoclips(klipler)
        
        # 🔥 VLOG İÇİN GREEN SCREEN
        if getattr(self, 'green_screen_video', None) and os.path.exists(self.green_screen_video) and getattr(self, 'green_screen_interval', 0) > 0:
            print(f"[VLOG] Green screen ekleniyor (Interval: {self.green_screen_interval}s)...")
            
            gs_clip = VideoFileClip(self.green_screen_video)
            
            try:
                gs_effect = vfx.MaskColor(color=[0, 255, 0], threshold=150, stiffness=5)
                gs_clip = gs_clip.with_effects([gs_effect])
            except Exception:
                gs_clip = gs_clip.fx(vfx.mask_color, color=[0, 255, 0], thr=150, s=5)
            
            scale_factor = getattr(self, 'gs_scale', 25) / 100.0
            gs_clip = gs_clip.resized(width=final_video.w * scale_factor)
            
            x_pct = getattr(self, 'gs_x', 95) / 100.0
            y_pct = getattr(self, 'gs_y', 95) / 100.0
            pos_x = (final_video.w - gs_clip.w) * x_pct
            pos_y = (final_video.h - gs_clip.h) * y_pct
            
            try:
                gs_clip = gs_clip.with_position((pos_x, pos_y))
            except AttributeError:
                gs_clip = gs_clip.set_position((pos_x, pos_y))
            
            overlays = []
            aralik_sn = self.green_screen_interval
            t = aralik_sn
            while t < final_video.duration:
                try:
                    overlays.append(gs_clip.with_start(t))
                except AttributeError:
                    overlays.append(gs_clip.set_start(t))
                t += aralik_sn
                
            if overlays:
                final_video = CompositeVideoClip([final_video] + overlays)

        try:
            final_video = final_video.with_effects([vfx.FadeIn(1.0), vfx.FadeOut(1.0)])
        except AttributeError:
            final_video = final_video.fx(vfx.fadein, 1.0).fx(vfx.fadeout, 1.0)
        
        print("Render başlatılıyor...")
        final_video.write_videofile(
            self.cikti_yolu, 
            codec="libx264", 
            audio_codec="aac", 
            fps=30, 
            preset="fast", 
            threads=8
        )
        
        video.close()
        final_video.close()
        
        # 🔥 YENİ SİNEMATİK KANCA SİSTEMİ 
        if getattr(self, 'hook_ranges', []):
            gecis_sesi = getattr(self, 'transition_audio', "whoosh.mp3")
            gecici_final = self.cikti_yolu.replace(".mp4", "_gecici.mp4")
            import shutil
            shutil.move(self.cikti_yolu, gecici_final)
            
            self._sinematik_kanca_ekle(
                ana_video=gecici_final, 
                cikti_yolu=self.cikti_yolu, 
                hook_ranges=self.hook_ranges, 
                whoosh_sesi=gecis_sesi
            )
            if os.path.exists(gecici_final): os.remove(gecici_final)

        if os.path.exists(temp_audio):
            try: os.remove(temp_audio)
            except: pass
                
        print(f"\n[MÜKEMMEL] Video başarıyla editlendi: {self.cikti_yolu}")

    @staticmethod
    def _sinematik_kanca_ekle(ana_video, cikti_yolu, hook_ranges, whoosh_sesi):
        import os, tempfile, subprocess
        # İç aktarmalar (import) çökme yaratmaması için buradan da kaldırıldı. Dosyanın en üstünden okunacak.
        
        tmp_hook = tempfile.mktemp(suffix="_hook.mp4")
        
        print(f"🪝 {len(hook_ranges)} farklı kesitten oluşan dinamik montaj hazırlanıyor...")
        ana_klip = VideoFileClip(ana_video)
        parcalar = []
        for bas, bit in hook_ranges:
            parcalar.append(ana_klip.subclipped(bas, bit))
            
        hook_klip = concatenate_videoclips(parcalar)
        hook_dur = hook_klip.duration
        
        hook_klip.write_videofile(tmp_hook, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
        
        for p in parcalar: p.close()
        hook_klip.close()
        ana_klip.close()

        gecis_sesi = whoosh_sesi if os.path.exists(whoosh_sesi) else None
        fade_dur = 1.0 
        
        filter_complex = (
            f"[0:v]fade=t=out:st={hook_dur - fade_dur:.3f}:d={fade_dur}[hv];"
            f"[0:a]afade=t=out:st={hook_dur - fade_dur:.3f}:d={fade_dur}[ha];"
            f"[1:v]fade=t=in:st=0:d={fade_dur}[mv];"
            f"[1:a]afade=t=in:st=0:d={fade_dur}[ma];"
        )

        inputs = ["-i", tmp_hook, "-i", ana_video]

        if gecis_sesi:
            inputs += ["-i", gecis_sesi]
            delay_ms = int(max(0.0, hook_dur - 0.5) * 1000)
            filter_complex += f"[2:a]adelay={delay_ms}|{delay_ms}[whoosh];"
            filter_complex += f"[ha][whoosh]amix=inputs=2:duration=first[ha_mixed];"
            filter_complex += f"[hv][ha_mixed][mv][ma]concat=n=2:v=1:a=1[vout][aout]"
        else:
            filter_complex += f"[hv][ha][mv][ma]concat=n=2:v=1:a=1[vout][aout]"

        print("🪝 Montaj kancası, whoosh ve ana video birleştiriliyor...")
        subprocess.run(
            ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            cikti_yolu
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if os.path.exists(tmp_hook): os.remove(tmp_hook)
# ==== KULLANIM ====
if __name__ == "__main__":
    ses_dosyasi = "podcast4.wav"
    video_havuzu_klasoru = "arkaplan_videolari"

    uretici = DinamikPodcastUretici(ses_kaynagi=ses_dosyasi, video_klasoru=video_havuzu_klasoru)
    uretici.uretimi_baslat("yeni_rastgele_bolum.mp4")