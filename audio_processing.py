import os
from pydub import AudioSegment, effects
from pydub.silence import detect_nonsilent

class AudioProcessingError(Exception):
    pass

class AudioProcessor:
    def __init__(self, source_path, output_dir=None):
        self.source_path = source_path
        self.output_dir = output_dir or os.path.dirname(source_path) or '.'
        self._audio = None

    def _load_audio(self):
        if self._audio is None:
            try:
                self._audio = AudioSegment.from_file(self.source_path)
            except Exception as e:
                raise AudioProcessingError(f"Ses dosyası açılamadı: {e}")
        return self._audio

    def analyze_loudness(self, frame_ms=100):
        audio = self._load_audio()
        overall_dbfs = audio.dBFS
        loudness_values = []

        for position in range(0, len(audio), frame_ms):
            chunk = audio[position:position + frame_ms]
            if chunk.rms > 0:
                loudness_values.append(chunk.dBFS)

        if not loudness_values:
            loudness_values = [overall_dbfs]

        loudness_values = [value for value in loudness_values if value != float('-inf')]
        average_dbfs = sum(loudness_values) / len(loudness_values)
        sorted_values = sorted(loudness_values)
        median_dbfs = sorted_values[len(sorted_values) // 2]
        top_dbfs = sum(sorted_values[-max(1, len(sorted_values) // 5):]) / max(1, len(sorted_values) // 5)

        recommended = min(average_dbfs, median_dbfs, top_dbfs) - 18.0
        recommended = max(min(recommended, -20.0), -70.0)

        return {
            'overall_dbfs': round(overall_dbfs, 2),
            'average_dbfs': round(average_dbfs, 2),
            'median_dbfs': round(median_dbfs, 2),
            'top_dbfs': round(top_dbfs, 2),
            'recommended_silence_thresh': round(recommended, 2),
            'recommended_min_silence_ms': 500,
            'frame_ms': frame_ms,
            'duration_seconds': round(len(audio) / 1000.0, 2),
        }

    def recommend_silence_threshold(self):
        analysis = self.analyze_loudness()
        return analysis['recommended_silence_thresh']

    def find_voice_segments(self, min_silence_len=None, silence_thresh=None, keep_silence_ms=200):
        audio = self._load_audio()
        min_silence_len = min_silence_len if min_silence_len is not None else 500
        silence_thresh = silence_thresh if silence_thresh is not None else self.recommend_silence_threshold()

        raw_segments = detect_nonsilent(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh
        )

        if not raw_segments:
            return []

        merged_segments = []
        for start, end in raw_segments:
            padded_start = max(0, start - keep_silence_ms)
            padded_end = min(len(audio), end + keep_silence_ms)

            if merged_segments and padded_start <= merged_segments[-1][1]:
                merged_segments[-1] = (merged_segments[-1][0], max(merged_segments[-1][1], padded_end))
            else:
                merged_segments.append((padded_start, padded_end))

        return merged_segments

    def export_clean_audio(self, output_filename=None, min_silence_len=None, silence_thresh=None, keep_silence_ms=200):
        audio = self._load_audio()
        segments = self.find_voice_segments(min_silence_len=min_silence_len, silence_thresh=silence_thresh, keep_silence_ms=keep_silence_ms)

        if not segments:
            raise AudioProcessingError('Temizlenecek anlamlı konuşma bulunamadı. Lütfen eşik değerini düşürüp tekrar deneyin.')

        cleaned = AudioSegment.empty()
        for start, end in segments:
            cleaned += audio[start:end]

        cleaned = effects.normalize(cleaned)
        
        filename = output_filename or 'temizlenmis_podcast_sesi.wav'
        output_path = os.path.join(self.output_dir, filename)
        cleaned.export(output_path, format='wav')

        return output_path, round(len(cleaned) / 1000.0, 2)
