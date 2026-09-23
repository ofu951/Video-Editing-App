import os
import json
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str

@dataclass
class AnalysisResult:
    timeline: List[Tuple[str, str]]
    shorts: List[Tuple[int, int, str]]
    summary_ranges: List[Tuple[int, int]]  # 5 dakikalık özet için zaman aralıkları
    transcript_text: str
    segments: List[TranscriptSegment]

class TranscriptAnalyzer:
    def __init__(self, segments):
        self.segments = [TranscriptSegment(start=s['start'], end=s['end'], text=s['text'].strip()) for s in segments]

    def build_plain_transcript(self):
        lines = []
        for seg in self.segments:
            lines.append(f"[{seg.start:.2f} - {seg.end:.2f}] {seg.text}")
        return '\n'.join(lines)

    def create_timeline(self):
        timeline = []
        for seg in self.segments:
            label = seg.text[:80].strip()
            if not label:
                continue
            label = label.replace('\n', ' ')
            timeline.append((self._format_timestamp(seg.start), label))
        return timeline

    def select_shorts_candidates(self, max_total_seconds=60, clip_seconds=15):
        candidates = []
        for seg in self.segments:
            duration = seg.end - seg.start
            if duration >= 5:
                score = len(seg.text.split()) + duration
                candidates.append((score, seg.start, seg.end, seg.text))

        candidates.sort(reverse=True)
        shorts = []
        total = 0
        for _, start, end, text in candidates:
            if total >= max_total_seconds:
                break
            clip_start = int(start)
            clip_end = min(int(clip_start + clip_seconds), int(end))
            if clip_end - clip_start < 10:
                continue
            shorts.append((clip_start, clip_end, text[:120].replace('\n', ' ')))
            total += clip_end - clip_start
            if total + clip_seconds > max_total_seconds and len(shorts) < 4:
                clip_end = min(int(clip_start + (max_total_seconds - total)), int(end))
        return shorts

    def select_summary_candidates(self, target_seconds=300):  # 5 dakika = 300 saniye
        """Özet için en önemli aralıkları seç (AI kullanmadan)"""
        candidates = []
        for seg in self.segments:
            duration = seg.end - seg.start
            word_count = len(seg.text.split())
            # Puanı: kelime sayısı + en az 5 saniye olmak
            if duration >= 3:
                score = word_count + (duration * 0.5)
                candidates.append((score, seg.start, seg.end, seg.text))

        candidates.sort(reverse=True)
        ranges = []
        total = 0
        
        for _, start, end, _ in candidates:
            if total >= target_seconds:
                break
            seg_start = int(start)
            seg_end = int(end)
            seg_duration = seg_end - seg_start
            
            remaining = target_seconds - total
            if seg_duration > remaining:
                seg_end = seg_start + remaining
            
            ranges.append((seg_start, seg_end))
            total += seg_end - seg_start
        
        ranges.sort(key=lambda x: x[0])  # Zaman sırasına göre sırala
        return ranges

    def _format_timestamp(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m:02}:{s:02}"

    def build_analysis(self):
        transcript_text = self.build_plain_transcript()
        timeline = self.create_timeline()
        shorts = self.select_shorts_candidates()
        summary_ranges = self.select_summary_candidates()  # 5 dakikalık özet aralıkları
        return AnalysisResult(
            timeline=timeline,
            shorts=shorts,
            summary_ranges=summary_ranges,
            transcript_text=transcript_text,
            segments=self.segments
        )

    def save_analysis(self, output_path):
        analysis = self.build_analysis()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timeline': analysis.timeline,
                'shorts': [{'start': s[0], 'end': s[1], 'reason': s[2]} for s in analysis.shorts],
                'transcript_text': analysis.transcript_text
            }, f, ensure_ascii=False, indent=2)
        return output_path
