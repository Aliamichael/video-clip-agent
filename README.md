# Video Clip Agent

AI-powered tool that extracts engaging short clips from long YouTube videos for social media posting.

## Features

- Download YouTube videos automatically
- Transcribe audio using OpenAI Whisper API
- AI-powered key moment detection using GPT-4
- Export clips in multiple formats for:
  - YouTube / YouTube Shorts
  - Instagram Reels / Stories
  - Facebook
  - TikTok

## Hosting Options

### Local (Recommended for full functionality)

```bash
pip install -r requirements-dev.txt
export OPENAI_API_KEY=your-key-here
python app.py
```

### Railway (Best for cloud deployment)

1. Connect your GitHub repo to [Railway](https://railway.app)
2. Add `OPENAI_API_KEY` environment variable
3. Deploy!

Railway supports:
- Long-running processes (no 10s timeout)
- FFmpeg installation via Dockerfile
- Persistent storage

### Vercel (Limited - UI only)

Vercel Lambda has **10-second timeout** - not suitable for video processing.

## Configuration

Set environment variable:
```bash
export OPENAI_API_KEY=sk-your-key-here
```

## Usage

1. Enter a YouTube URL
2. Select target platform(s)
3. Click "Extract Clips"
4. Download the generated clips

## Platform Specifications

| Platform | Resolution | Max Duration | Aspect Ratio |
|----------|-----------|---------------|--------------|
| YouTube Shorts | 1080x1920 | 60s | 9:16 |
| YouTube | 1920x1080 | 60s | 16:9 |
| Instagram Reels | 1080x1920 | 90s | 9:16 |
| TikTok | 1080x1920 | 180s | 9:16 |
| Facebook | 1080x1080 | 60s | 1:1 |

## Project Structure

```
video-clip-agent/
├── app.py                    # Flask web application
├── requirements.txt          # Cloud dependencies (minimal)
├── requirements-dev.txt     # Local development (full)
├── vercel.json              # Vercel config
├── Dockerfile               # Railway/Docker deployment
├── services/
│   ├── youtube_downloader.py # Video download
│   ├── transcriber.py        # Audio transcription
│   ├── moment_extractor.py   # AI moment detection
│   └── video_clipper.py      # Clip creation
├── templates/
│   └── index.html            # Web interface
└── static/
    ├── css/style.css
    └── js/app.js
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/process` | POST | Start video processing |
| `/api/status/<job_id>` | GET | Get job status |
| `/api/clips/<job_id>` | GET | Get generated clips |

## License

MIT
