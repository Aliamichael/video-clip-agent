import os
import subprocess
import json

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class VideoClipper:
    PLATFORM_SPECS = {
        'youtube_shorts': {
            'width': 1080,
            'height': 1920,
            'fps': 30,
            'codec': 'libx264',
            'max_duration': 60,
            'aspect': '9:16'
        },
        'youtube': {
            'width': 1920,
            'height': 1080,
            'fps': 30,
            'codec': 'libx264',
            'max_duration': 60,
            'aspect': '16:9'
        },
        'instagram_reels': {
            'width': 1080,
            'height': 1920,
            'fps': 30,
            'codec': 'libx264',
            'max_duration': 90,
            'aspect': '9:16'
        },
        'instagram_stories': {
            'width': 1080,
            'height': 1920,
            'fps': 30,
            'codec': 'libx264',
            'max_duration': 60,
            'aspect': '9:16'
        },
        'facebook': {
            'width': 1080,
            'height': 1080,
            'fps': 30,
            'codec': 'libx264',
            'max_duration': 60,
            'aspect': '1:1'
        },
        'tiktok': {
            'width': 1080,
            'height': 1920,
            'fps': 30,
            'codec': 'libx264',
            'max_duration': 180,
            'aspect': '9:16'
        }
    }

    def __init__(self, output_dir=None):
        self.output_dir = output_dir or os.path.join(APP_DIR, 'outputs')
        os.makedirs(self.output_dir, exist_ok=True)

    def create_clips(self, video_path, moments, job_id, platform='all'):
        clips = []
        
        platforms = self._get_platforms(platform)
        
        for i, moment in enumerate(moments):
            clip_base = os.path.join(self.output_dir, f'{job_id}_clip_{i+1}')
            
            for plat in platforms:
                specs = self.PLATFORM_SPECS[plat]
                clip_path = f"{clip_base}_{plat}.mp4"
                
                try:
                    self._extract_clip(
                        video_path,
                        clip_path,
                        moment['start'],
                        moment['end'],
                        specs
                    )
                    
                    clips.append({
                        'index': i,
                        'platform': plat,
                        'path': clip_path,
                        'start': moment['start'],
                        'end': moment['end'],
                        'title': moment['title'],
                        'reason': moment['reason'],
                        'platform_score': moment.get('platform_score', {})
                    })
                except Exception as e:
                    print(f"Failed to create {plat} clip: {e}")
        
        return clips

    def _get_platforms(self, platform):
        if platform == 'all':
            return ['youtube_shorts', 'instagram_reels', 'tiktok']
        elif platform == 'youtube':
            return ['youtube', 'youtube_shorts']
        elif platform == 'instagram':
            return ['instagram_reels', 'instagram_stories']
        elif platform == 'facebook':
            return ['facebook']
        elif platform == 'tiktok':
            return ['tiktok']
        else:
            return [platform]

    def _extract_clip(self, input_path, output_path, start, end, specs):
        duration = min(end - start, specs['max_duration'])
        
        cmd = [
            'ffmpeg', '-i', input_path,
            '-ss', str(start),
            '-t', str(duration),
            '-vf', f"scale={specs['width']}:{specs['height']}:force_original_aspect_ratio=decrease,pad={specs['width']}:{specs['height']}:(ow-iw)/2:(oh-ih)/2:black,fps={specs['fps']}",
            '-c:v', specs['codec'],
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y',
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")

    def get_video_duration(self, video_path):
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())

    def get_video_info(self, video_path):
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(result.stdout)
