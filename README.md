# Video Clip Agent

AI-powered tool that extracts engaging short clips from long YouTube videos for social media posting.

## Features

- Download YouTube videos automatically
- Transcribe audio using Whisper (local) or OpenAI Whisper API
- AI-powered key moment detection using GPT-4 or local Ollama
- Export clips in multiple formats for:
  - YouTube / YouTube Shorts
  - Instagram Reels / Stories
  - Facebook
  - TikTok

## Prerequisites

1. **Python 3.9+**
2. **FFmpeg** - Required for video processing
   - Windows: Download from https://ffmpeg.org/download.html
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

3. **Optional**: Ollama for local LLM processing
   - Install from https://ollama.ai
   - Run: `ollama pull llama3`

## Installation

```bash
cd video-clip-agent
pip install -r requirements.txt
```

## Configuration

### Environment Variables (optional)
```bash
export OPENAI_API_KEY=your-api-key-here
```

### Web Interface Settings
- Click "Settings" in the bottom-right corner
- Enter your OpenAI API key for cloud processing

## Usage

```bash
python app.py
```

Then open http://localhost:5000 in your browser.

### Processing Options

1. **Enter YouTube URL** - Paste any YouTube video link
2. **Select Platform** - Choose target social media platform(s)
3. **AI Processing**:
   - **Local (Free)** - Uses local Whisper + Ollama (requires GPU)
   - **OpenAI** - Uses OpenAI Whisper + GPT-4 (requires API key)

## How It Works

1. **Download** - Fetches video and extracts audio
2. **Transcribe** - Converts speech to text with timestamps
3. **Analyze** - AI identifies emotionally impactful moments
4. **Clip** - Creates optimized clips for each platform

## Project Structure

```
video-clip-agent/
├── app.py                    # Flask web application
├── requirements.txt          # Python dependencies
├── services/
│   ├── youtube_downloader.py # Video download
│   ├── transcriber.py        # Audio transcription
│   ├── moment_extractor.py   # AI moment detection
│   └── video_clipper.py      # Clip creation
├── templates/
│   └── index.html            # Web interface
├── static/
│   ├── css/style.css
│   └── js/app.js
├── uploads/                  # Downloaded videos
└── outputs/                 # Generated clips
```

## Platform Specifications

| Platform | Resolution | Max Duration | Aspect Ratio |
|----------|-----------|---------------|--------------|
| YouTube Shorts | 1080x1920 | 60s | 9:16 |
| YouTube | 1920x1080 | 60s | 16:9 |
| Instagram Reels | 1080x1920 | 90s | 9:16 |
| TikTok | 1080x1920 | 180s | 9:16 |
| Facebook | 1080x1080 | 60s | 1:1 |

## Troubleshooting

### "ffmpeg not found"
Ensure FFmpeg is installed and in your PATH. Restart terminal after installation.

### Slow transcription with local Whisper
Use a smaller model: Change `model_size='base'` in `services/transcriber.py` to `'tiny'` or `'small'`.

### Ollama connection errors
Make sure Ollama is running: `ollama serve`

## License

MIT
