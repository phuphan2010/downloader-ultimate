# Downloader Ultimate — Video Downloader & Dubbing Tool ⚡

[![CI — Lint & Test](https://github.com/phuphan2010/downloader-ultimate/actions/workflows/ci.yml/badge.svg)](https://github.com/phuphan2010/downloader-ultimate/actions/workflows/ci.yml)
[![Docker Build](https://github.com/phuphan2010/downloader-ultimate/actions/workflows/docker-build.yml/badge.svg)](https://github.com/phuphan2010/downloader-ultimate/actions/workflows/docker-build.yml)

An end-to-end asynchronous REST API service & Web Application for downloading TikTok and Douyin videos without watermarks, extracting audio, performing Speech-to-Text (STT) via Whisper, translating to Vietnamese, AI text-to-speech dubbing, subtitle burning, and custom logo overlaying.

Designed specifically for seamless integration with automation tools (**n8n**, **Zapier**, **Make**).

---

## 🚀 Quick Start (Local Docker)

### 1. Clone & Setup Environment
```bash
git clone git@github.com:phuphan2010/downloader-ultimate.git
cd downloader-ultimate
cp .env.example .env
```

### 2. Start Services
```bash
make dev
```
Access points:
- **Web UI Dashboard**: `http://localhost`
- **FastAPI OpenAPI Swagger Docs**: `http://localhost:8000/docs`
- **Health Check Endpoint**: `http://localhost:8000/health`

---

## 🛠️ Tech Stack

- **Backend Framework**: Python 3.11 FastAPI (Async, Pydantic v2)
- **Task Queue**: Celery + Redis
- **Video Download**: yt-dlp (TikTok/Douyin no-watermark)
- **Video Processing**: FFmpeg
- **Speech-to-Text**: OpenAI Whisper (Local base model)
- **Translation**: Google Translate API / DeepL API
- **Text-to-Speech (TTS)**: gTTS / ElevenLabs API
- **Frontend**: React 18, Vite, TailwindCSS (Glassmorphic dark mode)
- **Authentication**: API Key (`X-API-Key` with bcrypt hash)

---

## 📡 Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health status (Redis & Disk check) |
| `POST` | `/api/v1/download` | Download TikTok/Douyin video |
| `POST` | `/api/v1/transcribe` | Extract audio and generate transcript SRT |
| `POST` | `/api/v1/translate` | Translate SRT to Vietnamese & generate VTT |
| `POST` | `/api/v1/subtitle` | Hardcode/burn SRT subtitles into video |
| `POST` | `/api/v1/dub` | Generate TTS audio and mix with video |
| `POST` | `/api/v1/logo` | Overlay custom PNG watermark logo |
| `POST` | `/api/v1/pipeline` | **One-shot full pipeline execution for n8n** |
| `GET` | `/api/v1/jobs/{job_id}` | Check job progress and retrieve download URLs |
| `POST` | `/api/v1/admin/keys` | Create new API key |

---

## 🤖 n8n Integration Guide

See detailed step-by-step instructions in [docs/n8n_integration_guide.md](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/docs/n8n_integration_guide.md).

### Quick n8n Webhook Workflow Sample:
```json
{
  "url": "https://www.tiktok.com/@user/video/123456789",
  "steps": ["download", "transcribe", "translate", "subtitle", "dub"],
  "webhook_url": "https://your-n8n-instance.com/webhook/video-complete"
}
```

---

## 🧪 Development & Testing

```bash
# Run unit & integration tests
make test

# Format code
make format

# Lint code
make lint
```

---

## 📄 License
MIT License — 2026 phuphan2010
