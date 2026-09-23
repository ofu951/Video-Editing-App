import os
import random
import base64
from typing import List, Dict, Optional
from moviepy import VideoFileClip, VideoClip, concatenate_videoclips, vfx

def _extract_frame_base64(video_path: str, second: float = 2.0) -> Optional[str]:
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(second * fps))
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return base64.b64encode(buf.tobytes()).decode('utf-8')
    except Exception:
        return None

class SmartBRollSelector:
    def __init__(self, b_roll_folder: str, gemini_api_key: str, progress_callback=None):
        self.b_roll_folder = b_roll_folder
        self.gemini_api_key = gemini_api_key
        self.progress_callback = progress_callback
        self._video_cache: Dict[str, str] = {}
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self.gemini_api_key:
                raise ValueError("[HATA] Gemini API key sağlanmadı. SmartBRoll akıllı seçimi çalışamıyor.")
            from google import genai
            self._client = genai.Client(api_key=self.gemini_api_key)
        return self._client

    def _log(self, pct: int, msg: str):
        if self.progress_callback:
            self.progress_callback(pct, msg)
        print(f"[SmartBRoll {pct}%] {msg}")

    def index_broll_library(self) -> Dict[str, str]:
        video_files = [
            os.path.join(self.b_roll_folder, f)
            for f in os.listdir(self.b_roll_folder)
            if f.lower().endswith(('.mp4', '.mov', '.avi'))
        ]
        if not video_files:
            raise ValueError(f"'{self.b_roll_folder}' klasöründe video bulunamadı.")
        client = self._get_client()
        self._log(0, f"B-Roll kütüphanesi indeksleniyor: {len(video_files)} video...")

        for i, vpath in enumerate(video_files):
            if vpath in self._video_cache:
                continue
            frame_b64 = _extract_frame_base64(vpath, second=2.0)
            if frame_b64 is None:
                fname = os.path.splitext(os.path.basename(vpath))[0]
                self._video_cache[vpath] = fname.replace('_', ' ').replace('-', ' ')
                continue
            try:
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[{
                        "parts": [
                            {"inline_data": {"mime_type": "image/jpeg", "data": frame_b64}},
                            {"text": "Bu video karesini 5-10 anahtar kelime ile tanımla. Sadece Türkçe anahtar kelimeler, virgülle ayrılmış."}
                        ]
                    }]
                )
                desc = response.text.strip()
            except Exception:
                fname = os.path.splitext(os.path.basename(vpath))[0]
                desc = fname.replace('_', ' ').replace('-', ' ')

            self._video_cache[vpath] = desc
            pct = int((i + 1) / len(video_files) * 40)
            self._log(pct, f"  [{i+1}/{len(video_files)}] {os.path.basename(vpath)}: {desc[:60]}")

        return self._video_cache

    def _find_best_match(self, topic_keywords: str, video_library: Dict[str, str]) -> str:
        topic_words = set(topic_keywords.lower().split())
        scored = []
        for vpath, desc in video_library.items():
            desc_words = set(desc.lower().replace(',', ' ').split())
            overlap = len(topic_words & desc_words)
            scored.append((overlap, vpath, desc))
        scored.sort(key=lambda x: x[0], reverse=True)
        best_candidates = [x for x in scored[:3] if x[0] > 0]
        if best_candidates:
            return best_candidates[0][1]
        return random.choice(list(video_library.keys()))

    def create_smart_broll_plan(self, segments: List[Dict], change_interval_secs: int = 45, ai_image_moments=None) -> List[Dict]:
        self._log(0, "Akıllı B-Roll planı oluşturuluyor...")
        video_library = self.index_broll_library()
        if not video_library:
            raise ValueError("B-Roll kütüphanesi boş!")
        if not segments:
            return []

        total_duration = segments[-1]['end'] if segments else 0
        plan = []
        client = self._get_client()
        bucket_start = 0
        current_bucket_text = []

        self._log(45, "Konuşma içerikleri analiz ediliyor...")

        def process_bucket(b_start, b_end, text_chunk):
            if not text_chunk:
                video_path = random.choice(list(video_library.keys()))
                return {'start': b_start, 'end': b_end, 'video_path': video_path, 'topic': 'genel', 'matched_desc': video_library.get(video_path, ''), 'is_smart': False}
            try:
                resp = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=(f"Aşağıdaki podcast metninde konuşulan ana konuyu 5 anahtar kelimeyle özetle. SADECE anahtar kelimeleri virgülle yaz.\n\nMetin: {' '.join(text_chunk)[:500]}")
                )
                topic = resp.text.strip()
            except Exception:
                topic = ' '.join(text_chunk[:3])

            best_video = self._find_best_match(topic, video_library)
            return {'start': b_start, 'end': b_end, 'video_path': best_video, 'topic': topic, 'matched_desc': video_library.get(best_video, ''), 'is_smart': True}

        for seg in segments:
            if seg['start'] >= bucket_start + change_interval_secs:
                b_end = seg['start']
                plan.append(process_bucket(bucket_start, b_end, current_bucket_text))
                bucket_start = b_end
                current_bucket_text = []
            current_bucket_text.append(seg.get('text', ''))

        if current_bucket_text or bucket_start < total_duration:
            plan.append(process_bucket(bucket_start, total_duration, current_bucket_text))

        # 🔥 AI GÖRSELLERİ BURADA (Plan tamamen oluştuktan SONRA) EKLENMELİ 🔥
        if ai_image_moments:
            new_plan = []
            for item in plan:
                item_start = item['start']
                item_end = item['end']
                
                inserted_moment = None
                for moment in ai_image_moments:
                    m_start = moment['start_sec']
                    m_end = moment['end_sec']
                    
                    # Eğer AI görseli bu B-Roll aralığının içine düşüyorsa yakala
                    if item_start <= m_start < item_end:
                        inserted_moment = moment
                        break
                
                if inserted_moment:
                    m_start = inserted_moment['start_sec']
                    m_end = inserted_moment['end_sec']
                    
                    # 1. AI görselden ÖNCEKİ B-Roll kısmı (Eğer varsa)
                    if m_start > item_start:
                        new_plan.append({
                            'start': item_start, 'end': m_start, 
                            'video_path': item['video_path'], 'is_smart': item.get('is_smart', False)
                        })
                    
                    # 2. AI Görselin TAM KENDİSİ (Araya sıkıştırıyoruz)
                    new_plan.append({
                        'start': m_start, 'end': m_end, 
                        'ai_clip': inserted_moment['clip'], 'ai_topic': inserted_moment['topic']
                    })
                    
                    # 3. AI görselden SONRAKİ B-Roll kısmı (Eğer varsa)
                    if m_end < item_end:
                        new_plan.append({
                            'start': m_end, 'end': item_end, 
                            'video_path': item['video_path'], 'is_smart': item.get('is_smart', False)
                        })
                        
                    self._log(90, f"  [AI Görsel Eklendi] {inserted_moment['topic']} ({m_start}s - {m_end}s)")
                else:
                    # Bu aralıkta AI görseli yoksa planı olduğu gibi ekle
                    new_plan.append(item)
                    
            plan = new_plan
            self._log(90, f"Plan AI görselleriyle güncellendi: Toplam {len(plan)} segment.")

        self._log(90, f"Nihai plan hazır: {len(plan)} B-Roll/AI segmenti.")
        return plan

    def render_broll_from_plan(self, plan: List[Dict]) -> 'VideoClip':
        from moviepy import VideoFileClip, concatenate_videoclips, vfx
        self._log(92, "B-Roll video klipleri render ediliyor...")
        clips = []

        for item in plan:
            # 🔥 EĞER AI GÖRSELİ VARSA VİDEO YERİNE ONU KULLAN 🔥
            if item.get('ai_clip'):
                clips.append(item['ai_clip'])
                continue

            vpath = item['video_path']
            duration_needed = item['end'] - item['start']
            if duration_needed <= 0:
                continue
            try:
                vid = VideoFileClip(vpath)
                if vid.duration <= duration_needed:
                    import math
                    loops = math.ceil(duration_needed / vid.duration)
                    clip = concatenate_videoclips([vid] * loops)
                    clip = clip.subclipped(0, duration_needed)
                else:
                    max_start = vid.duration - duration_needed
                    start = random.uniform(0, max_start)
                    clip = vid.subclipped(start, start + duration_needed)

                clip = clip.resized(height=1080)
                clip = clip.without_audio()
                clip = clip.with_effects([vfx.FadeIn(0.4), vfx.FadeOut(0.4)])
                clips.append(clip)
            except Exception as e:
                self._log(92, f"  [UYARI] Yüklenemedi: {e}")
                continue

        if not clips:
            raise ValueError("Hiçbir B-Roll klibi render edilemedi!")
        self._log(98, "B-Roll klipleri birleştiriliyor...")
        return concatenate_videoclips(clips)