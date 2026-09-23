import os
import json
import whisper
from google import genai
from moviepy import VideoFileClip, concatenate_videoclips, vfx

class SummaryGenerator:
    def __init__(self, api_key):
        self.api_key = api_key

    def generate_summary_from_ranges(self, video_path, ranges, progress_cb, log_cb):
        """
        Önceden belirlenen zaman aralıklarından özet video oluştur (AI kullanmadan, HIZLI!)
        ranges: [(15, 75), (110, 190), ...] şeklinde tuple listesi
        """
        log_cb(f"[1/3] Zaman aralıkları kontrol ediliyor: {len(ranges)} parça...")
        progress_cb(20, "Video açılıyor...")
        
        video = VideoFileClip(video_path)
        clips = []
        
        for idx, (start, end) in enumerate(ranges):
            start = max(0, int(start))
            end = min(int(video.duration), int(end))
            
            if end > start:
                log_cb(f"  [{idx+1}/{len(ranges)}] {start}s - {end}s arası kesiliyor...")
                clip = video.subclipped(start, end)
                if idx > 0:
                    clip = clip.with_effects([vfx.FadeIn(0.5)])
                clips.append(clip)
        
        if not clips:
            raise ValueError("Kesme yapılacak geçerli aralık bulunamadı!")
        
        log_cb("[2/3] Parçalar birleştiriliyor...")
        progress_cb(60, "Birleştiriliyor...")
        final_video = concatenate_videoclips(clips)
        
        log_cb("[3/3] Video render ediliyor...")
        progress_cb(80, "Render başlıyor...")
        
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        out_path = f"{base_name}_ozet_5dk.mp4"
        
        final_video.write_videofile(
            out_path, 
            codec="libx264", 
            audio_codec="aac", 
            fps=30, 
            preset="fast",
            threads=4
        )
        
        video.close()
        final_video.close()
        
        progress_cb(100, "✅ Özet video tamamlandı!")
        return out_path

    def generate_summary(self, video_path, target_minutes, progress_cb, log_cb):
        # 1. WHISPER İLE DEŞİFRE
        log_cb("[1/4] Whisper ile video deşifre ediliyor (Uzun sürebilir)...")
        progress_cb(15, "Whisper çalışıyor...")
        model = whisper.load_model("base")
        result = model.transcribe(video_path, language="tr")

        transcript = ""
        for seg in result["segments"]:
            transcript += f"[{int(seg['start'])} - {int(seg['end'])}] {seg['text']}\n"

        # 2. GEMINI İLE AKILLI SEÇİM
        log_cb(f"[2/4] Gemini'den {target_minutes} dakikalık özet planı isteniyor...")
        progress_cb(45, "Gemini analiz ediyor...")
        client = genai.Client(api_key=self.api_key)
        
        hedef_saniye = target_minutes * 60

        prompt = f"""
Sen uzman bir video kurgucususun. Aşağıda zaman damgalı video deşifresi var.
Görev: Bu videodan toplam süresi tam olarak {hedef_saniye} saniyeye (±%10) yaklaşacak şekilde EN KRİTİK ve EN ÖNEMLİ anları seç.

KURAL: SADECE aşağıdaki gibi JSON formatında bir liste döndür. Başka hiçbir harf veya açıklama yazma.
[
  {{"start": 15, "end": 75}},
  {{"start": 110, "end": 190}}
]

DEŞİFRE METNİ:
{transcript[:35000]}
"""
        resp = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
        raw_json = resp.text.replace('```json', '').replace('```', '').strip()
        
        try:
            segments = json.loads(raw_json)
        except Exception as e:
            raise ValueError(f"Yapay zeka geçerli bir zaman aralığı döndüremedi. Hata: {e}\nAI Çıktısı: {raw_json}")

        log_cb(f"[BİLGİ] Yapay Zekanın Keseceği Aralıklar: {segments}")

        # 3. VİDEO KESME VE BİRLEŞTİRME
        log_cb("[3/4] Video belirtilen aralıklardan kesiliyor...")
        progress_cb(65, "Video kesiliyor...")
        video = VideoFileClip(video_path)
        clips = []

        for idx, seg in enumerate(segments):
            start = max(0, seg['start'])
            end = min(video.duration, seg['end'])
            if end > start:
                clip = video.subclipped(start, end)
                # Her parçanın başına yumuşak aydınlanma geçişi ekle (ilk parça hariç)
                if idx > 0:
                    clip = clip.with_effects([vfx.FadeIn(0.5)])
                clips.append(clip)

        if not clips:
            raise ValueError("Kesilecek geçerli bir aralık bulunamadı!")

        log_cb("[4/4] Parçalar birleştiriliyor ve render ediliyor...")
        progress_cb(85, "Render başlıyor...")
        final_video = concatenate_videoclips(clips)

        base_name = os.path.splitext(os.path.basename(video_path))[0]
        out_path = f"{base_name}_ozet_{target_minutes}dk.mp4"

        final_video.write_videofile(out_path, codec="libx264", audio_codec="aac", fps=30, preset="fast", threads=4)
        
        video.close()
        final_video.close()

        progress_cb(100, "Özet video tamamlandı!")
        return out_path