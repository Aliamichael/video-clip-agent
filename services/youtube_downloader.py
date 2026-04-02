import os
import yt_dlp

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_ffmpeg_path():
    local_ffmpeg = r"C:\Users\offic\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
    if os.path.exists(local_ffmpeg):
        return os.path.dirname(local_ffmpeg)
    return None

class YouTubeDownloader:
    def __init__(self, output_dir=None):
        is_cloud = os.environ.get('VERCEL', '') or os.environ.get('RAILWAY', '')
        if is_cloud:
            self.output_dir = '/tmp/uploads'
        else:
            self.output_dir = output_dir or os.path.join(APP_DIR, 'uploads')
        os.makedirs(self.output_dir, exist_ok=True)

    def download(self, url, job_id):
        output_template = os.path.join(self.output_dir, f'{job_id}_video.%(ext)s')
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [],
        }
        
        ffmpeg_path = get_ffmpeg_path()
        if ffmpeg_path:
            ydl_opts['ffmpeg-location'] = ffmpeg_path
        
        print(f"Downloading video from: {url}")
        
        video_path = None
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)
                
                if not os.path.exists(video_path):
                    for ext in ['mp4', 'mkv', 'webm', 'avi']:
                        alt_path = video_path.rsplit('.', 1)[0] + f'.{ext}'
                        if os.path.exists(alt_path):
                            video_path = alt_path
                            break
        except Exception as e:
            print(f"Download error: {e}")
            raise
        
        if not video_path or not os.path.exists(video_path):
            raise Exception(f"Failed to download video from {url}")
        
        print(f"Video downloaded: {video_path}")
        print(f"Video size: {os.path.getsize(video_path)} bytes")
        
        return video_path

    def get_video_info(self, url):
        ydl_opts = {'quiet': True, 'no_warnings': True}
        
        ffmpeg_path = get_ffmpeg_path()
        if ffmpeg_path:
            ydl_opts['ffmpeg-location'] = ffmpeg_path
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'description': info.get('description', ''),
            }
