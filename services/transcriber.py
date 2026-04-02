import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Transcriber:
    def __init__(self, model_size='tiny'):
        self.model_size = model_size

    def extract_audio(self, video_path, job_id, output_dir=None):
        is_cloud = os.environ.get('VERCEL', '') or os.environ.get('RAILWAY', '')
        if is_cloud:
            output_dir = '/tmp/uploads'
        else:
            output_dir = output_dir or os.path.join(APP_DIR, 'uploads')
        
        os.makedirs(output_dir, exist_ok=True)
        audio_path = os.path.join(output_dir, f'{job_id}_audio.mp3')
        
        logger.info(f"Video path: {video_path}")
        
        if not os.path.exists(video_path):
            raise Exception(f"Video file not found: {video_path}")
        
        file_size = os.path.getsize(video_path)
        logger.info(f"Video file size: {file_size} bytes")
        
        if file_size < 10000:
            raise Exception(f"Video file is too small ({file_size} bytes)")
        
        logger.info(f"Extracting audio to: {audio_path}")
        
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vn', '-acodec', 'libmp3lame', '-ab', '192k',
            '-ar', '16000',
            '-y', audio_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise Exception(f"FFmpeg error: {result.stderr}")
        
        if not os.path.exists(audio_path):
            raise Exception(f"Audio file was not created")
        
        return audio_path

    def transcribe(self, audio_path, job_id, use_local=False):
        logger.info(f"Transcribe called with: {audio_path}")
        
        if not os.path.exists(audio_path):
            raise Exception(f"Audio file not found: {audio_path}")
        
        api_key = os.getenv('OPENAI_API_KEY', '')
        if not api_key:
            raise Exception("OPENAI_API_KEY required for transcription")
        
        return self._transcribe_api(audio_path, api_key)

    def _transcribe_api(self, audio_path, api_key):
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        with open(audio_path, 'rb') as audio_file:
            response = client.audio.transcriptions.create(
                model='whisper-1',
                file=audio_file,
                response_format='verbose_json'
            )
        
        words = response.text.split()
        segments = []
        current_time = 0
        
        for i in range(0, len(words), 8):
            chunk = words[i:i+8]
            duration = len(chunk) / 2.5
            segments.append({
                'start': current_time,
                'end': current_time + duration,
                'text': ' '.join(chunk)
            })
            current_time += duration
        
        return {
            'full_text': response.text,
            'segments': segments,
            'language': 'en'
        }

    def transcribe_with_timestamps(self, audio_path, job_id, use_local=False):
        transcript = self.transcribe(audio_path, job_id, use_local)
        
        timestamped = []
        for seg in transcript['segments']:
            minutes = int(seg['start'] // 60)
            seconds = int(seg['start'] % 60)
            timestamp = f"{minutes:02d}:{seconds:02d}"
            
            timestamped.append({
                'timestamp': timestamp,
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text']
            })
        
        return timestamped
