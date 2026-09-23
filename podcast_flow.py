import os
from typing import List, Tuple
import whisper
from audio_processing import AudioProcessor
from transcript_analysis import TranscriptAnalyzer
from shorts_selector import ShortsSelector
from deneme import DinamikPodcastUretici

class PodcastFlow:
    def __init__(self, source_audio_path: str, b_roll_folder: str, output_dir: str = None):
        self.source_audio_path = source_audio_path
        self.b_roll_folder = b_roll_folder
        self.output_dir = output_dir or os.path.dirname(source_audio_path) or '.'

    def analyze_audio(self):
        processor = AudioProcessor(self.source_audio_path, output_dir=self.output_dir)
        return processor.analyze_loudness()

    def export_clean_audio(self, min_silence_ms: int = None, silence_thresh: float = None, keep_silence_ms: int = 200, output_filename: str = None):
        processor = AudioProcessor(self.source_audio_path, output_dir=self.output_dir)
        return processor.export_clean_audio(
            output_filename=output_filename,
            min_silence_len=min_silence_ms,
            silence_thresh=silence_thresh,
            keep_silence_ms=keep_silence_ms
        )

    def transcribe_audio(self, audio_path: str, whisper_model: str = 'base'):
        model = whisper.load_model(whisper_model)
        result = model.transcribe(audio_path, language='tr')
        segments = []
        for segment in result.get('segments', []):
            segments.append({
                'start': float(segment['start']),
                'end': float(segment['end']),
                'text': segment['text'].strip()
            })
        return segments

    def analyze_transcript(self, segments: List[dict]):
        analyzer = TranscriptAnalyzer(segments)
        return analyzer.build_analysis()

    def save_analysis(self, analysis, filename='podcast_analysis.json'):
        output_path = os.path.join(self.output_dir, filename)
        payload = {
            'timeline': [{'timestamp': item[0], 'text': item[1]} for item in analysis.timeline],
            'shorts': [{'start': item[0], 'end': item[1], 'reason': item[2]} for item in analysis.shorts],
            'transcript_text': analysis.transcript_text,
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return output_path

    def render_video(self, clean_audio_path: str, output_video_path: str = 'final_dinamik_podcast.mp4',
                 gemini_api_key: str = None, ai_image_count: int = 2, transcript_segments: list = None):  # <-- yeni parametreler
    
        ai_image_moments = None
        transcript_segments = transcript_segments or []
    
        # YENİ: Gemini API key varsa AI görsel B-Roll üret
        if gemini_api_key:
            try:
                from ai_image_broll import AIImageBRoll
                ai_broll = AIImageBRoll(
                    gemini_api_key=gemini_api_key,
                    output_dir=os.path.join(self.output_dir, 'ai_images')
                )
                # Transkripti al (daha önce analiz edildiyse)
                # Not: transcript_text'i state'de tutmak için analyze_transcript 
                # sonucunu kaydetmeniz gerekiyor
                if hasattr(self, '_last_transcript_text'):
                    ai_image_moments = ai_broll.build_ai_image_clips(
                        self._last_transcript_text, 
                        count=ai_image_count
                    )
            except Exception as e:
                print(f"[UYARI] AI görsel üretimi atlandı: {e}")
    
        producer = DinamikPodcastUretici(
            ses_kaynagi=clean_audio_path, 
            video_klasoru=self.b_roll_folder,
            ai_image_moments=ai_image_moments  
        )
        producer.uretimi_baslat(
            cikti_yolu=output_video_path,
            gemini_api_key=gemini_api_key,
            ai_image_count=ai_image_count,
            transcript_segments=transcript_segments
        )
        return output_video_path

# analyze_transcript metoduna da tek satır ekle:
def analyze_transcript(self, segments):
    analyzer = TranscriptAnalyzer(segments)
    result = analyzer.build_analysis()
    self._last_transcript_text = result.transcript_text  # <-- state'e kaydet
    return result

def create_shorts(self, source_video_path: str, intervals: List[Tuple[int, int]], output_filename: str = 'podcast_shorts.mp4'):
    selector = ShortsSelector(source_video_path)
    return selector.build_short_clips(intervals, output_filename=output_filename)
