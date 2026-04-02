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

## Deployment

### Local Development

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=your-key-here
python app.py
```

### Cloud Deployment (Vercel)

1. Push to GitHub
2. Connect repo to Vercel
3. Set environment variable: `OPENAI_API_KEY`
4. Deploy!

**Note:** Cloud deployment requires OpenAI API key (pay-per-use, ~$0.006/min for transcription)

## Configuration

Set environment variable:
```bash
export OPENAI_API_KEY=sk-your-key-here
```

Or use the Settings panel in the web UI.

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
├── requirements.txt          # Python dependencies
├── vercel.json              # Vercel config
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
| `/api/download/<job_id>/<index>` | GET | Download clip |

## License

MIT
