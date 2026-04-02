import os
import json
import uuid
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

APP_DIR = os.path.dirname(os.path.abspath(__file__))
IS_CLOUD = os.environ.get('VERCEL', '')

if IS_CLOUD:
    UPLOAD_FOLDER = '/tmp/uploads'
    OUTPUT_FOLDER = '/tmp/outputs'
else:
    UPLOAD_FOLDER = os.path.join(APP_DIR, 'uploads')
    OUTPUT_FOLDER = os.path.join(APP_DIR, 'outputs')

app = Flask(__name__, template_folder=os.path.join(APP_DIR, 'templates'))
CORS(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

jobs = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_video():
    data = request.json
    video_url = data.get('video_url')
    platform = data.get('platform', 'all')
    use_local = data.get('use_local', False)

    if not video_url:
        return jsonify({'error': 'No video URL provided'}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'queued',
        'progress': 0,
        'video_url': video_url,
        'platform': platform,
        'error': 'Cloud hosting (Vercel) does not support video processing. Please run locally or use Railway/Render.'
    }

    return jsonify({
        'job_id': job_id,
        'message': 'Cloud deployment limited. Use Railway or run locally for full functionality.'
    })

@app.route('/api/status/<job_id>')
def get_status(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(jobs[job_id])

@app.route('/api/clips/<job_id>')
def get_clips(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify({'clips': jobs[job_id].get('clips', [])})

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    return jsonify({
        'openai_key': '',
        'cloud_limited': True,
        'message': 'Video processing requires local deployment or Railway/Render hosting'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
