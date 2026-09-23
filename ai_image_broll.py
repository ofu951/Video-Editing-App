# ai_image_broll.py
import os
import json
from typing import List, Dict
from google import genai
from google.genai import types

class AIImageBRoll:
    """
    Podcast transkriptinden kritik anları tespit edip
    Imagen 3 ile görsel üretir, Ken Burns efektli klibe çevirir.
    """
    def __init__(self, gemini_api_key: str, output_dir: str = "ai_images"):
        self.client = genai.Client(api_key=gemini_api_key)
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def find_critical_moments(self, transcript_text: str, count: int = 2) -> List[Dict]:
        """
        Transkriptten en kritik 2-3 anı + saniyelerini + görsel prompt'unu döndürür.
        """
        prompt = f"""
Sen bir video prodüksiyon uzmanısın. Aşağıdaki podcast transkriptini analiz et.

Görev: Anlatımın en kritik, teknik açıdan en güçlü {count} anını bul.
Bunlar izleyicinin "dur, bu önemli" diyeceği anlardır.

Her an için şunu üret:
- start_sec: Konuşmanın başladığı saniye (integer)
- end_sec: Konuşmanın bittiği saniye (integer)  
- topic_tr: Türkçe kısa konu özeti (max 10 kelime)
- image_prompt: İngilizce, detaylı Imagen 3 prompt'u (sinematik, photorealistic, 3D render tarzı)

SADECE JSON döndür, başka hiçbir şey yazma:
[
  {{
    "start_sec": 45,
    "end_sec": 60,
    "topic_tr": "...",
    "image_prompt": "A highly detailed 3D render of ..."
  }}
]

TRANSKRİPT:
{transcript_text[:4000]}
"""
        response = self.client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:-1])
        
        return json.loads(raw)

    def generate_image(self, prompt: str, filename: str) -> str:
        """Imagen 3 ile görsel üretir, dosyaya kaydeder."""
        response = self.client.models.generate_images(
            model='imagen-3.0-generate-002',  # veya imagen-4.0-generate-preview-05-20
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                safety_filter_level="block_only_high"
            )
        )
        
        output_path = os.path.join(self.output_dir, filename)
        image_bytes = response.generated_images[0].image.image_bytes
        with open(output_path, 'wb') as f:
            f.write(image_bytes)
        
        return output_path

    def image_to_clip(self, image_path: str, duration: float = 5.0):
        """
        Fotoğrafa Ken Burns (yavaş zoom-in) efekti verip MoviePy klibi döndürür.
        """
        from moviepy import ImageClip, vfx
        import numpy as np
        
        clip = ImageClip(image_path, duration=duration)
        
        # Ken Burns: başlangıçta %100, sonda %115 zoom
        def zoom_effect(get_frame, t):
            frame = get_frame(t)
            h, w = frame.shape[:2]
            scale = 1.0 + 0.15 * (t / duration)  # 1.0 → 1.15
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            from PIL import Image
            img = Image.fromarray(frame)
            img_resized = img.resize((new_w, new_h), Image.LANCZOS)
            
            x1 = (new_w - w) // 2
            y1 = (new_h - h) // 2
            cropped = img_resized.crop((x1, y1, x1 + w, y1 + h))
            return np.array(cropped)
        
        return clip.transform(zoom_effect).with_effects([
            vfx.FadeIn(0.5),
            vfx.FadeOut(0.5)
        ])

    def build_ai_image_clips(self, transcript_text: str, count: int = 2) -> List[Dict]:
        """
        Ana fonksiyon. Kritik anları bulur, görselleri üretir, klipleri döndürür.
        
        Returns: [{'start_sec': int, 'end_sec': int, 'clip': VideoClip, 'topic': str}]
        """
        print(f"[AIImageBRoll] Transkriptten {count} kritik an aranıyor...")
        moments = self.find_critical_moments(transcript_text, count=count)
        
        result = []
        for i, moment in enumerate(moments):
            print(f"  [{i+1}] {moment['topic_tr']} ({moment['start_sec']}s-{moment['end_sec']}s)")
            print(f"       Prompt: {moment['image_prompt'][:80]}...")
            
            filename = f"ai_broll_{i+1}_{moment['start_sec']}s.jpg"
            image_path = self.generate_image(moment['image_prompt'], filename)
            print(f"       ✓ Görsel kaydedildi: {image_path}")
            
            duration = float(moment['end_sec'] - moment['start_sec'])
            clip = self.image_to_clip(image_path, duration=max(duration, 3.0))
            
            result.append({
                'start_sec': moment['start_sec'],
                'end_sec': moment['end_sec'],
                'clip': clip,
                'topic': moment['topic_tr'],
                'image_path': image_path
            })
        
        return result