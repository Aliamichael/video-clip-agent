import os
import json
import uuid
import threading
from flask import Flask, render_template, request, jsonify, send_file, Response
from flask_cors import CORS

APP_DIR = os.path.dirname(os.path.abspath(__file__))

from services.youtube_downloader import YouTubeDownloader
from services.transcriber import Transcriber
from services.moment_extractor import MomentExtractor
from services.video_clipper import VideoClipper

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = os.path.join(APP_DIR, 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(APP_DIR, 'outputs')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

jobs = {}

class VideoClipAgent:
    def __init__(self):
        self.downloader = YouTubeDownloader()
        self.transcriber = Transcriber()
        self.moment_extractor = MomentExtractor()
        self.clipper = VideoClipper()

    def process_video(self, video_source, job_id, platform='all', use_local=True):
        try:
            jobs[job_id]['status'] = 'downloading'
            jobs[job_id]['progress'] = 10

            if video_source.startswith('http'):
                video_path = self.downloader.download(video_source, job_id)
            else:
                video_path = video_source

            jobs[job_id]['status'] = 'extracting_audio'
            jobs[job_id]['progress'] = 20

            audio_path = self.transcriber.extract_audio(video_path, job_id)

            jobs[job_id]['status'] = 'transcribing'
            jobs[job_id]['progress'] = 30

            transcript = self.transcriber.transcribe(audio_path, job_id, use_local=use_local)

            jobs[job_id]['status'] = 'extracting_moments'
            jobs[job_id]['progress'] = 50

            moments = self.moment_extractor.extract_key_moments(
                transcript, 
                job_id, 
                use_local=use_local
            )

            jobs[job_id]['status'] = 'clipping'
            jobs[job_id]['progress'] = 70
            jobs[job_id]['moments'] = moments

            clips = self.clipper.create_clips(
                video_path, 
                moments, 
                job_id, 
                platform=platform
            )

            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['progress'] = 100
            jobs[job_id]['clips'] = clips
            jobs[job_id]['transcript'] = transcript

        except Exception as e:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = str(e)

agent = VideoClipAgent()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_video():
    data = request.json
    video_url = data.get('video_url')
    platform = data.get('platform', 'all')
    use_local = data.get('use_local', True)

    if not video_url:
        return jsonify({'error': 'No video URL provided'}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'queued',
        'progress': 0,
        'video_url': video_url,
        'platform': platform
    }

    thread = threading.Thread(
        target=agent.process_video,
        args=(video_url, job_id, platform, use_local)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'job_id': job_id})

@app.route('/api/status/<job_id>')
def get_status(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(jobs[job_id])

@app.route('/api/moments/<job_id>')
def get_moments(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    if 'moments' not in job:
        return jsonify({'moments': []})
    
    return jsonify({'moments': job['moments']})

@app.route('/api/clips/<job_id>')
def get_clips(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    if 'clips' not in job:
        return jsonify({'clips': []})
    
    return jsonify({'clips': job['clips']})

@app.route('/api/download/<job_id>/<clip_index>')
def download_clip(job_id, clip_index):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    clip_index = int(clip_index)
    if 'clips' not in jobs[job_id] or clip_index >= len(jobs[job_id]['clips']):
        return jsonify({'error': 'Clip not found'}), 404
    
    clip_path = jobs[job_id]['clips'][clip_index]['path']
    filename = os.path.basename(clip_path)
    
    return send_file(
        clip_path,
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/transcript/<job_id>')
def get_transcript(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    if 'transcript' not in job:
        return jsonify({'error': 'Transcript not available yet'}), 404
    
    return jsonify({'transcript': job['transcript']})

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    config_path = 'config.json'
    
    if request.method == 'POST':
        data = request.json
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
        return jsonify({'status': 'saved'})
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return jsonify(json.load(f))
    else:
        return jsonify({
            'openai_key': '',
            'use_local_by_default': True,
            'ollama_url': 'http://localhost:11434'
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
