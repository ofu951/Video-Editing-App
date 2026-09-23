import os
import subprocess
import whisper
import random
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips
class ShortsUretici:
    def __init__(self, kaynak_video, intro_video=None, outro_video=None, green_screen_video=None, green_screen_times=None,
                 font_name="Arial", font_color="&H00FFFFFF", font_size=16, margin_v=60,
                 gs_scale=80, gs_x=50, gs_y=85):
        self.kaynak_video = kaynak_video
        self.intro_video = intro_video
        self.outro_video = outro_video
        self.green_screen_video = green_screen_video
        self.green_screen_times = green_screen_times or []
        self.hedef_sure = 53
        # Dinamik Stil Değişkenleri
        self.font_name = font_name
        self.font_color = font_color
        self.font_size = font_size
        self.margin_v = margin_v
        self.gs_scale = gs_scale
        self.gs_x = gs_x
        self.gs_y = gs_y
        
    def formati_ayarla_ve_kes(self, araliklar):
        print(f"[1/3] Video şu aralıklarda kesilip birleştirilecek: {araliklar}")
        from moviepy import VideoFileClip, concatenate_videoclips, vfx, CompositeVideoClip, CompositeAudioClip

        video = VideoFileClip(self.kaynak_video)

        # 1. Önce videoyu 9:16 formatına kırpıyoruz
        w, h = video.size
        hedef_genislik = int(h * 9 / 16)
        if hedef_genislik % 2 != 0:
            hedef_genislik -= 1

        x_merkez = w / 2
        x1 = x_merkez - (hedef_genislik / 2)
        x2 = x_merkez + (hedef_genislik / 2)

        video_dikey = video.cropped(x1=x1, y1=0, x2=x2, y2=h)

        # 2. Parçaları kesiyoruz ve GEÇİŞ EFEKTİ ekliyoruz
        klipler = []
        for i, (baslangic, bitis) in enumerate(araliklar):
            baslangic = min(baslangic, video_dikey.duration)
            bitis = min(bitis, video_dikey.duration)

            if baslangic < bitis:
                kesilen_parca = video_dikey.subclipped(baslangic, bitis)
                if i > 0:
                    kesilen_parca = kesilen_parca.with_effects([vfx.FadeIn(0.4)])
                klipler.append(kesilen_parca)

        if not klipler:
            raise ValueError("Belirtilen aralıklar videodan kesilemedi, saniyeleri kontrol edin.")

        # 3. Kesilen dikey parçaları birleştiriyoruz (bu SADECE ana içerik, intro/outro yok)
        ana_govde = concatenate_videoclips(klipler)
        hedef_boyut = (ana_govde.w, ana_govde.h)

        def _hazirla(video_yolu, boyut):
            """Intro/outro klibini hedef boyuta göre kırpar. Süresine dokunmaz;
            dosyanın kendi gerçek süresi kullanılır (asset ne kadar uzunsa o kadar)."""
            klip = VideoFileClip(video_yolu)
            klip = klip.resized(height=boyut[1])
            klip = klip.cropped(x_center=klip.w / 2, width=boyut[0])
            return klip

        # 🔥 YENİ: Intro / Ana İçerik / Outro sınırlarını ELLE ve KESİN olarak hesaplıyoruz.
        # concatenate_videoclips'in otomatik zamanlamasına GÜVENMİYORUZ — her segmentin
        # başlangıç zamanı (with_start) açıkça belirtiliyor, video ve ses AYRI AYRI aynı
        # zaman çizelgesine yerleştiriliyor. Böylece segmentler arasında çakışma/kayma
        # (bir önceki sesin bir sonraki segmente taşması gibi) mümkün değil.
        segmentler = []      # (video katmanı, with_start uygulanmış)
        ses_parcalari = []   # (ses parçası, with_start uygulanmış) — video ile senkron

        t_imleci = 0.0

        if self.intro_video and os.path.exists(self.intro_video):
            print(f"[DEBUG] ShortsUretici intro video yüklendi: {self.intro_video}")
            intro_dikey = _hazirla(self.intro_video, hedef_boyut)
            segmentler.append(intro_dikey.with_start(t_imleci))
            if intro_dikey.audio is not None:
                ses_parcalari.append(intro_dikey.audio.with_start(t_imleci))
            print(f"[BİLGİ] Intro zaman aralığı: {t_imleci:.2f}s -> {t_imleci + intro_dikey.duration:.2f}s")
            t_imleci += intro_dikey.duration

        ana_govde_baslangic = t_imleci
        segmentler.append(ana_govde.with_start(t_imleci))
        if ana_govde.audio is not None:
            ses_parcalari.append(ana_govde.audio.with_start(t_imleci))
        t_imleci += ana_govde.duration
        print(f"[BİLGİ] Ana içerik zaman aralığı: {ana_govde_baslangic:.2f}s -> {t_imleci:.2f}s")

        if self.outro_video and os.path.exists(self.outro_video):
            print(f"[DEBUG] ShortsUretici outro video yüklendi: {self.outro_video}")
            outro_dikey = _hazirla(self.outro_video, hedef_boyut)
            outro_baslangic = t_imleci
            segmentler.append(outro_dikey.with_start(t_imleci))
            if outro_dikey.audio is not None:
                ses_parcalari.append(outro_dikey.audio.with_start(t_imleci))
            t_imleci += outro_dikey.duration
            print(f"[BİLGİ] Outro zaman aralığı: {outro_baslangic:.2f}s -> {t_imleci:.2f}s")

        toplam_sure = t_imleci

        final_dikey_video = CompositeVideoClip(segmentler, size=hedef_boyut).with_duration(toplam_sure)
        if ses_parcalari:
            final_dikey_video = final_dikey_video.with_audio(CompositeAudioClip(ses_parcalari))

        # 🔥 Green Screen Animasyonu ("beğen abone ol" hatırlatmaları)
        # ÖNEMLİ: self.green_screen_times listesindeki her saniye, YUKARIDA
        # hesaplanan KESİN zaman çizelgesine göredir (0 = introdan başlar).
        # Örn. intro 3sn sürüyorsa ve ana içeriğin 10. saniyesinde bir GS
        # istiyorsanız, listeye 3 + 10 = 13 eklemelisiniz. Ana içeriğin nerede
        # başladığını yukarıdaki "[BİLGİ] Ana içerik zaman aralığı" logundan
        # görebilirsiniz.
       # 🔥 SHORTS İÇİN DİNAMİK GREEN SCREEN KATMANI
        if getattr(self, 'green_screen_video', None) and os.path.exists(self.green_screen_video) and getattr(self, 'green_screen_times', None):
            print(f"[BILGI] Green Screen eklentisi uygulanıyor... (Saniyeler: {self.green_screen_times})")
            try:
                from moviepy import VideoFileClip, vfx, CompositeVideoClip
                gs_clip = VideoFileClip(self.green_screen_video)
                
                # 1. Maskeleme (Eşik 150 - Sürüm Uyumlu Kontrol)
                try:
                    gs_effect = vfx.MaskColor(color=[0, 255, 0], threshold=150, stiffness=5)
                    gs_clip = gs_clip.with_effects([gs_effect])
                except Exception:
                    gs_clip = gs_clip.fx(vfx.mask_color, color=[0, 255, 0], thr=150, s=5)
                
                # 2. Arayüzden Gelen Dinamik Ayarlar
                scale_factor = getattr(self, 'gs_scale', 80) / 100.0
                x_pct = getattr(self, 'gs_x', 50) / 100.0
                y_pct = getattr(self, 'gs_y', 85) / 100.0
                
                # Boyut
                gs_clip = gs_clip.resized(width=final_dikey_video.w * scale_factor)
                
                # Konum
                pos_x = (final_dikey_video.w - gs_clip.w) * x_pct
                pos_y = (final_dikey_video.h - gs_clip.h) * y_pct
                
                try:
                    gs_clip = gs_clip.with_position((pos_x, pos_y))
                except AttributeError:
                    gs_clip = gs_clip.set_position((pos_x, pos_y))
                
                # Zamana göre ekle
                katmanlar = [final_dikey_video]
                for t in self.green_screen_times:
                    if t < final_dikey_video.duration:
                        try:
                            katmanlar.append(gs_clip.with_start(t))
                        except AttributeError:
                            katmanlar.append(gs_clip.set_start(t))
                        
                if len(katmanlar) > 1:
                    final_dikey_video = CompositeVideoClip(katmanlar)
                    
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"[UYARI] Shorts GS eklenirken hata: {e}")

        # 4. Kayıt
        gecici_video_yolu = "gecici_shorts_arkaplan.mp4"
        final_dikey_video.write_videofile(
            gecici_video_yolu, codec="libx264", audio_codec="aac", fps=30, preset="fast"
        )

        video.close()
        final_dikey_video.close()
        return gecici_video_yolu
    def saniye_to_srt(self, saniye):
        """Saniye verisini altyazı formatına (00:00:00,000) çevirir"""
        saat = int(saniye // 3600)
        dakika = int((saniye % 3600) // 60)
        sn = int(saniye % 60)
        ms = int((saniye - int(saniye)) * 1000)
        return f"{saat:02}:{dakika:02}:{sn:02},{ms:03}"

    def altyazi_dosyasi_uret(self, video_yolu):
        print("[2/3] Whisper AI ile ses dinleniyor ve altyazı (.srt) üretiliyor...")
        # 'base' veya 'small' modeli hızlı ve etkilidir. Türkçe dil desteği mevcuttur.
        model = whisper.load_model("base") 
        
        # Whisper doğrudan video dosyasının içindeki sesi okuyabilir
        sonuc = model.transcribe(video_yolu, language="tr")
        
        srt_yolu = "altyazi.srt"
        with open(srt_yolu, "w", encoding="utf-8") as srt_dosyasi:
            for i, segment in enumerate(sonuc["segments"]):
                baslangic = self.saniye_to_srt(segment["start"])
                bitis = self.saniye_to_srt(segment["end"])
                metin = segment["text"].strip()
                
                srt_dosyasi.write(f"{i+1}\n")
                srt_dosyasi.write(f"{baslangic} --> {bitis}\n")
                srt_dosyasi.write(f"{metin}\n\n")
                
        print("[BASARILI] Altyazı dosyası oluşturuldu.")
        return srt_yolu
    
    def altyaziyi_yapay_zeka_ile_duzelt(self, srt_yolu, api_key):
        print("[AI] Altyazılar mantık ve anlam kontrolünden geçiriliyor...")
        from google import genai
        
        with open(srt_yolu, "r", encoding="utf-8") as f:
            ham_srt = f.read()
            
        client = genai.Client(api_key=api_key)
        
        # PROMPT: Teknik bağlamı vererek AI'ın Whisper hatalarını yakalamasını sağlıyoruz
        prompt = f"""
        Sen profesyonel bir video editörüsün ve youtube a içerik üretiyorsun. Aşağıda otomatik oluşturulmuş bir SRT altyazı dosyası bulunuyor.
        Konuşmacı gömülü sistemler, donanım tasarımı, STM32, ROS2, su altı robotikleri (ROV) ve yazılım mühendisliği üzerine deneyimli biridir. Bazen ise konuşmacı gündelik hayatta olan konular teknolojik konular üzerine konuşmaktadır.
        
        Görevlerin:
        1. "Gerçekten bunu demiş olabilir mi?" mantığıyla metni incele. Sesi metne dönüştüren yapay zekanın yanlış duyduğu, anlamsızlaşan kelimeleri (özellikle teknik terimlerdeki duyum hatalarını) cümlenin gidişatına ve mühendislik mantığına göre düzelt.
        2. Zaman damgalarına (Örn: 00:00:05,000 --> 00:00:07,500) ASLA dokunma ve formatı bozma.
        3. Metne ekstra yorum katma, sadece düzeltilmiş SRT dosyasını çıktı olarak ver.
        
        HAM SRT DOSYASI:
        {ham_srt}
        """
        
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        
        duzeltilmis_srt = response.text.strip()
        # Eğer Gemini yanıtı markdown kodu (```) içine alırsa onu temizliyoruz
        if duzeltilmis_srt.startswith("```"):
            duzeltilmis_srt = "\n".join(duzeltilmis_srt.split("\n")[1:-1])
            
        yeni_srt_yolu = "duzeltilmis_" + srt_yolu
        with open(yeni_srt_yolu, "w", encoding="utf-8") as f:
            f.write(duzeltilmis_srt)
            
        return yeni_srt_yolu
    def kanca_ve_gecis_ekle(self, video_yolu, cikti_adi):
        print("\n[4/4] Shorts için Kanca (Hook) ekleniyor...")
        from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips
        import os, random

        ana_video = VideoFileClip(video_yolu)
        
        # 1. KANCAYI KES (15-18 sn arası)
        baslangic = min(15, max(0, ana_video.duration - 3))
        bitis = baslangic + 3
        kanca_klip = ana_video.subclipped(baslangic, bitis)
        
        # 2. WHOOSH KONTROLÜ (Varsa ekle, YOKSA ONSUZ DEVAM ET)
        if os.path.exists("whoosh.mp3"):
            try:
                whoosh_tam = AudioFileClip("whoosh.mp3")
                max_bas = max(0, whoosh_tam.duration - 1)
                rastgele_baslangic = random.uniform(0, max_bas) 
                whoosh_sesi = whoosh_tam.subclipped(rastgele_baslangic, rastgele_baslangic + 1)
                
                # MoviePy Sürüm Uyumluluğu
                try:
                    whoosh_gecikmeli = whoosh_sesi.with_start(max(0, kanca_klip.duration - whoosh_sesi.duration))
                except AttributeError:
                    whoosh_gecikmeli = whoosh_sesi.set_start(max(0, kanca_klip.duration - whoosh_sesi.duration))
                
                if kanca_klip.audio is not None:
                    yeni_kanca_sesi = CompositeAudioClip([kanca_klip.audio, whoosh_gecikmeli])
                else:
                    yeni_kanca_sesi = whoosh_gecikmeli
                    
                try:
                    kanca_klip = kanca_klip.with_audio(yeni_kanca_sesi)
                except AttributeError:
                    kanca_klip = kanca_klip.set_audio(yeni_kanca_sesi)
                    
                whoosh_tam.close()
            except Exception as e:
                print(f"[UYARI] Whoosh efekti eklenirken pürüz çıktı, atlanıyor: {e}")
        else:
            print("[BİLGİ] whoosh.mp3 bulunamadı, kancaya ses efekti eklenmeden temiz devam ediliyor.")
        
        # 3. BİRLEŞTİR VE KAYDET
        final_video = concatenate_videoclips([kanca_klip, ana_video], method="compose")
        final_video.write_videofile(cikti_adi, codec="libx264", audio_codec="aac", fps=30, preset="fast")
        
        # Temizlik
        ana_video.close()
        kanca_klip.close()
        final_video.close()
        
        print(f"\n[MÜKEMMEL] Kancalı Shorts videon hazır: {cikti_adi}")
        return cikti_adi
    def altyaziyi_videoya_gom(self, video_yolu, srt_yolu, cikti_adi):
        print("[3/3] Altyazılar videonun üzerine kazınıyor (Hardcode)...")
        
        # ÇÖZÜM: 'ForceStyle' yerine 'force_style' kullanıyoruz.
        altyazi_stili = f"force_style='FontName={self.font_name} Bold,FontSize={self.font_size},PrimaryColour={self.font_color},BackColour=&H80000000,BorderStyle=3,Outline=0,Shadow=0,Alignment=2,MarginV={self.margin_v}'"
        tam_yol = os.path.abspath(srt_yolu)
        srt_yolu_ffmpeg = tam_yol.replace('\\', '/').replace(':', '\\:')
        
        komut = [
            "ffmpeg", "-y", "-i", video_yolu, 
            "-vf", f"subtitles='{srt_yolu_ffmpeg}':{altyazi_stili}", 
            "-c:a", "copy", cikti_adi
        ]
        
        # FFmpeg loglarını görmek her zaman iyidir, çalışırken ekrana basmasına izin veriyoruz
        subprocess.run(komut)
        
        # Hata çözüldüğü için geçici dosyaları temizleme işlemini tekrar açtık
        if os.path.exists(video_yolu): os.remove(video_yolu)
        if os.path.exists(srt_yolu): os.remove(srt_yolu)
        
        if os.path.exists(cikti_adi):
            print(f"\n[MÜKEMMEL] İşlem tamam! Shorts videon bulunduğun klasöre kaydedildi: {cikti_adi}")
        else:
            print("\n[HATA] Video oluşturulamadı! Lütfen FFmpeg çıktılarını kontrol et.")


# ==== KULLANIM ====
if __name__ == "__main__":
    # Örneğin:
    kaynak_videom = "Kendi editörümü yaptım.mp4" 
    
    uretici = ShortsUretici(kaynak_video=kaynak_videom)
    
    # 1. Aşama: Videoyu kes ve dikey yap
    gecici_video = uretici.formati_ayarla_ve_kes()
    
    # 2. Aşama: Altyazı SRT dosyasını oluştur
    srt_dosyasi = uretici.altyazi_dosyasi_uret(gecici_video)
    
    # 3. Aşama: Altyazıyı göm (Geçici bir ara video olarak kaydediyoruz)
    duz_shorts = "duz_shorts.mp4"
    uretici.altyaziyi_videoya_gom(
        video_yolu=gecici_video, 
        srt_yolu=srt_dosyasi, 
        cikti_adi=duz_shorts
    )
    
    # 4. YENİ AŞAMA: Kanca (Hook) ve rastgele whoosh efektini ekle!
    uretici.kanca_ve_gecis_ekle(
        video_yolu=duz_shorts, 
        cikti_adi="odadan_cikmadan_shorts_1_KANCALI.mp4"
    )