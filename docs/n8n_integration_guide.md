# n8n Integration Guide — Downloader Ultimate

This guide explains how to connect your **n8n** workflows with the **Downloader Ultimate** API to automate downloading TikTok/Douyin videos, generating Vietnamese subtitles, and AI dubbing.

---

## 🏗️ Architecture Flow

```
┌─────────┐             ┌─────────────────────┐             ┌─────────┐
│   n8n   │ ──POST───►  │ Downloader Ultimate │ ──POST───►  │   n8n   │
│ Workflow│ /pipeline   │      API Engine     │ Webhook     │ Webhook │
└─────────┘             └─────────────────────┘             └─────────┘
```

---

## Step 1: Create API Key

1. Log in to your Downloader Ultimate Admin UI or use the API:
   ```bash
   curl -X POST http://localhost:8000/api/v1/admin/keys \
     -H "Content-Type: application/json" \
     -d '{"name": "n8n Automation Engine"}'
   ```
2. Copy the returned `api_key` (e.g., `dt_x89aF...`).

---

## Step 2: Configure HTTP Request Node in n8n

1. Add an **HTTP Request** node to your n8n canvas.
2. Set Parameters:
   - **Method**: `POST`
   - **URL**: `https://your-api-domain.com/api/v1/pipeline`
   - **Authentication**: `Header Auth`
     - **Header Name**: `X-API-Key`
     - **Header Value**: `dt_x89aF...`
   - **Body Content Type**: `JSON`
   - **JSON Body**:
     ```json
     {
       "url": "https://www.tiktok.com/@user/video/7091234567890",
       "steps": ["download", "transcribe", "translate", "subtitle", "dub"],
       "options": {
         "quality": "best",
         "dub": {
           "voice": "female",
           "mix_mode": "overlay"
         }
       },
       "webhook_url": "https://n8n.yourdomain.com/webhook/downloader-result"
     }
     ```

---

## Step 3: Configure Webhook Node in n8n

1. Add a **Webhook** node in n8n.
2. Set Method to `POST` and Path to `downloader-result`.
3. When the video processing completes, Downloader Ultimate sends a payload:
   ```json
   {
     "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
     "status": "done",
     "output_url": "http://your-api-domain.com/static/9b1deb4d/video_dubbed.mp4",
     "error": null
   }
   ```
4. Use an **HTTP Request** node to download the binary file from `output_url` for publishing to Google Drive, Telegram, or S3.
