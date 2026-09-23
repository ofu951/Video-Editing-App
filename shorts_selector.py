import os

class ShortsSelector:
    def __init__(self, source_video_path):
        self.source_video_path = source_video_path

    def build_short_clips(self, intervals, output_filename='shorts_automatic.mp4'):
        from moviepy import VideoFileClip, concatenate_videoclips
        
        if not intervals:
            raise ValueError('Klip aralığı bulunamadı.')

        clips = []
        source = VideoFileClip(self.source_video_path)

        for start, end in intervals:
            if end <= start:
                continue
            end = min(end, source.duration)
            clips.append(source.subclip(start, end))

        if not clips:
            raise ValueError('Geçerli bir clip aralığı bulunamadı.')

        result = concatenate_videoclips(clips, method='compose')
        result.write_videofile(output_filename, codec='libx264', audio_codec='aac', fps=30)
        result.close()
        source.close()

        return output_filename
