# BA Task Breakdown — Video Downloader & Dubbing Tool
**Ngày:** 2026-07-05  
**Version:** 1.0  
**PM/BA:** [Tên]  

---

## 1. TỔNG QUAN DỰ ÁN

### Mô tả
Web application + REST API cho phép:
- Download video từ TikTok / Douyin (không watermark)
- Tách audio, nhận dạng giọng nói → văn bản (STT)
- Dịch nội dung sang tiếng Việt
- Lồng tiếng Việt vào video (TTS + sync)
- Chèn logo vào video (vị trí & kích thước tuỳ chỉnh)
- Expose toàn bộ qua REST API (tích hợp n8n, Zapier, Make...)

### Phạm vi (In Scope)
| # | Tính năng | Độ ưu tiên |
|---|-----------|------------|
| 1 | Download TikTok/Douyin (no watermark) | P0 |
| 2 | Tách audio từ video | P0 |
| 3 | Speech-to-Text (đa ngôn ngữ) | P0 |
| 4 | Dịch sang tiếng Việt | P0 |
| 5 | TTS tiếng Việt + ghép vào video | P1 |
| 6 | Burn subtitle vào video | P1 |
| 7 | Chèn logo (vị trí, kích thước) | P1 |
| 8 | REST API (auth, rate limit) | P0 |
| 9 | Web UI (upload / config / preview) | P2 |
| 10 | Job queue + async processing | P0 |

### Ngoài phạm vi (Out of Scope)
- Upload trực tiếp lên TikTok/YouTube
- Live streaming
- Mobile app native

---

## 2. KIẾN TRÚC ĐỀ XUẤT

```
┌──────────────────────────────────────────────────────┐
│                    CLIENT LAYER                       │
│   Web UI (React)   │   n8n / Zapier   │  API Client  │
└───────────────────────────┬──────────────────────────┘
                            │ HTTPS + API Key / JWT
┌───────────────────────────▼──────────────────────────┐
│                  API GATEWAY (FastAPI)                 │
│  /download  /process  /translate  /dub  /logo  /jobs  │
│  Auth Middleware │ Rate Limiter │ Input Validator       │
└──────┬────────────────────────────────────┬───────────┘
       │                                    │
┌──────▼──────────┐              ┌──────────▼──────────┐
│  Task Queue      │              │  File Storage        │
│  Celery + Redis  │              │  Local / S3          │
└──────┬──────────┘              └─────────────────────┘
       │
┌──────▼──────────────────────────────────────────────┐
│                  WORKER SERVICES                      │
│  ┌─────────┐ ┌──────┐ ┌─────────┐ ┌──────────────┐  │
│  │ Downloader│ │ STT  │ │Translate│ │  TTS + Mux   │  │
│  │ yt-dlp  │ │Whisper│ │ DeepL/  │ │ gTTS+FFmpeg  │  │
│  │         │ │      │ │ Google  │ │              │  │
│  └─────────┘ └──────┘ └─────────┘ └──────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │         Logo Overlay (FFmpeg / Pillow)          │  │
│  └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Tech Stack:**
| Layer | Technology | Lý do chọn |
|-------|-----------|------------|
| Backend API | Python FastAPI | Async, tự động OpenAPI docs |
| Video Download | yt-dlp | Hỗ trợ TikTok/Douyin no-watermark |
| Video Processing | FFmpeg | Industry standard |
| STT | OpenAI Whisper (local) | Miễn phí, chính xác, đa ngôn ngữ |
| Translation | Google Translate API / DeepL | Chất lượng cao tiếng Việt |
| TTS | gTTS hoặc ElevenLabs | gTTS miễn phí, ElevenLabs chất lượng cao |
| Task Queue | Celery + Redis | Xử lý bất đồng bộ |
| Auth | API Key + JWT | Đơn giản, tương thích n8n |
| Storage | Local disk / AWS S3 | Cấu hình qua env |
| Frontend | React + TailwindCSS | Nhanh, đẹp |
| Container | Docker + docker-compose | Dễ deploy |

---

## 3. EPIC & TASK BREAKDOWN

---

### EPIC 1: PROJECT SETUP & INFRA
**Owner:** Backend Lead  
**Estimate:** 3 ngày

#### TASK 1.1 — Khởi tạo project structure
```
Subtasks:
- [ ] Tạo monorepo: /backend, /frontend, /workers, /docs
- [ ] Setup pyproject.toml / poetry cho backend
- [ ] Setup docker-compose.yml (api, worker, redis, nginx)
- [ ] Tạo .env.example với tất cả env vars cần thiết
- [ ] Setup pre-commit hooks (black, isort, flake8)
```
**AC:** `docker-compose up` chạy được, health check endpoint trả 200.

#### TASK 1.2 — CI/CD Pipeline
```
Subtasks:
- [ ] GitHub Actions: lint + test on PR
- [ ] GitHub Actions: build & push Docker image on merge to main
- [ ] Tạo Makefile với các lệnh: make dev, make test, make build
```
**AC:** Mỗi PR tự động chạy lint và test, fail nếu có lỗi.

#### TASK 1.3 — Logging & Monitoring
```
Subtasks:
- [ ] Setup structured logging (JSON format) với Python logging
- [ ] Log mỗi job: job_id, user_id, start_time, end_time, status, error
- [ ] Tích hợp Sentry (optional) cho error tracking
- [ ] Health check endpoint: GET /health (kiểm tra redis, disk space)
```
**AC:** Mọi request đều có log với request_id traceable.

---

### EPIC 2: VIDEO DOWNLOAD MODULE
**Owner:** Backend Dev 1  
**Estimate:** 4 ngày  
**Dependency:** EPIC 1

#### TASK 2.1 — Tích hợp yt-dlp
```
Subtasks:
- [ ] Cài đặt yt-dlp, test download TikTok (có watermark)
- [ ] Implement no-watermark download cho TikTok (API method)
- [ ] Implement download Douyin (cần User-Agent / cookies handling)
- [ ] Xử lý rate limiting từ TikTok/Douyin (retry + backoff)
- [ ] Validate URL: chỉ accept TikTok / Douyin URL
- [ ] Download về /tmp/<job_id>/ để isolate giữa các jobs
```
**AC:** Download được video TikTok và Douyin không watermark, kích thước < 100MB.

#### TASK 2.2 — File management
```
Subtasks:
- [ ] Auto cleanup file sau N giờ (configurable qua env)
- [ ] Giới hạn disk usage: reject job nếu disk > 80% full
- [ ] Sinh signed download URL với expiry (nếu dùng S3)
- [ ] Upload file lên S3 sau khi xử lý xong (optional, toggle qua env)
```
**AC:** Files tự xóa sau 24h, không để lại rác trên server.

#### TASK 2.3 — API Endpoint: Download
```
POST /api/v1/download
Body: { "url": "https://www.tiktok.com/...", "quality": "best|720p|480p" }
Response: { "job_id": "...", "status": "queued" }

GET /api/v1/jobs/{job_id}
Response: { "status": "processing|done|failed", "download_url": "...", "error": null }
```
**AC:** API trả job_id trong < 500ms, video download async.

---

### EPIC 3: AUDIO PROCESSING & STT
**Owner:** Backend Dev 1  
**Estimate:** 5 ngày  
**Dependency:** EPIC 2

#### TASK 3.1 — Tách audio từ video
```
Subtasks:
- [ ] Dùng FFmpeg: extract audio WAV 16kHz mono (format tốt nhất cho Whisper)
- [ ] Xử lý video không có audio track (return lỗi rõ ràng)
- [ ] Normalize audio level (ffmpeg loudnorm filter)
```
**AC:** Tách được audio từ mọi video download được, file WAV < 50MB.

#### TASK 3.2 — Speech-to-Text với Whisper
```
Subtasks:
- [ ] Cài đặt openai-whisper (local model, không cần API key)
- [ ] Chọn model size: base (nhanh) hoặc medium (cân bằng) — configurable
- [ ] Detect ngôn ngữ tự động từ audio
- [ ] Trả về: transcript text + timestamps từng segment (SRT format)
- [ ] Xử lý video tiếng Trung (zh) — test với Douyin content
- [ ] Fallback: nếu Whisper fail, thử Google Speech-to-Text API
```
**AC:** STT chính xác > 85% với tiếng Anh, tiếng Trung. Trả về SRT với timestamp.

#### TASK 3.3 — API Endpoint: Transcription
```
POST /api/v1/transcribe
Body: { "job_id": "...", "language": "auto|zh|en|..." }
Response: { "job_id": "...", "transcript": "...", "srt_url": "...", "detected_language": "zh" }
```
**AC:** STT hoàn thành trong < 3x độ dài video.

---

### EPIC 4: TRANSLATION MODULE
**Owner:** Backend Dev 2  
**Estimate:** 3 ngày  
**Dependency:** EPIC 3

#### TASK 4.1 — Dịch sang tiếng Việt
```
Subtasks:
- [ ] Tích hợp Google Translate API (googletrans-new hoặc official API)
- [ ] Tích hợp DeepL API như secondary option (chất lượng tốt hơn)
- [ ] Dịch từng segment trong SRT, giữ nguyên timestamp
- [ ] Xử lý văn bản tiếng Trung phồn thể/giản thể
- [ ] Configurable: chọn provider qua env var (TRANSLATE_PROVIDER=google|deepl)
- [ ] Cache kết quả dịch theo hash của text (tránh dịch lại cùng nội dung)
```
**AC:** Dịch được từ zh/en/ko/ja → vi, giữ nguyên SRT timestamps.

#### TASK 4.2 — Xuất file SRT tiếng Việt
```
Subtasks:
- [ ] Generate file .srt tiếng Việt chuẩn format
- [ ] Generate file .vtt (cho web players)
- [ ] Expose endpoint download SRT/VTT
```
**AC:** File SRT mở được trên VLC, Premiere, CapCut.

#### TASK 4.3 — API Endpoint: Translation
```
POST /api/v1/translate
Body: { "job_id": "...", "source_lang": "auto", "target_lang": "vi", "provider": "google" }
Response: { "job_id": "...", "srt_url": "...", "vtt_url": "...", "translated_text": "..." }
```
**AC:** Translation hoàn thành trong < 30s với video 5 phút.

---

### EPIC 5: SUBTITLE BURN-IN
**Owner:** Backend Dev 2  
**Estimate:** 3 ngày  
**Dependency:** EPIC 4

#### TASK 5.1 — Chèn subtitle vào video
```
Subtasks:
- [ ] Dùng FFmpeg subtitles filter: burn SRT vào video
- [ ] Config font: chọn font hỗ trợ tiếng Việt (Roboto, Noto Sans)
- [ ] Config style subtitle: font_size, color, outline, position (top/bottom)
- [ ] Giữ nguyên audio gốc khi burn subtitle
- [ ] Test với video có resolution khác nhau (720p, 1080p, 9:16)
```
**AC:** Subtitle hiển thị rõ trên mọi nền, không bị cắt viền.

#### TASK 5.2 — API Endpoint: Subtitle
```
POST /api/v1/subtitle
Body: {
  "job_id": "...",
  "style": {
    "font_size": 24,
    "font_color": "#FFFFFF",
    "outline_color": "#000000",
    "position": "bottom"  // top | bottom | custom(x,y)
  }
}
Response: { "job_id": "...", "output_url": "..." }
```

---

### EPIC 6: DUBBING (LỒNG TIẾNG)
**Owner:** Backend Dev 2  
**Estimate:** 5 ngày  
**Dependency:** EPIC 4

#### TASK 6.1 — Text-to-Speech tiếng Việt
```
Subtasks:
- [ ] Tích hợp gTTS (Google TTS, miễn phí) làm option cơ bản
- [ ] Tích hợp ElevenLabs API (chất lượng cao, có phí) làm option premium
- [ ] Configurable giọng: nam/nữ, tốc độ (0.75x - 1.5x)
- [ ] Generate audio clip cho từng segment dựa theo SRT timestamps
- [ ] Xử lý trường hợp TTS audio dài hơn segment duration (speed up)
```
**AC:** TTS nghe tự nhiên, không bị cắt giữa câu.

#### TASK 6.2 — Sync & Mix Audio
```
Subtasks:
- [ ] Dùng FFmpeg: mute/giảm volume audio gốc xuống 20%
- [ ] Ghép từng TTS audio clip vào đúng timestamp
- [ ] Mix: audio gốc (20%) + TTS tiếng Việt (80%)
- [ ] Option: tắt hoàn toàn audio gốc (replace mode)
- [ ] Handle audio gap giữa các segments
```
**AC:** Lồng tiếng sync với video, không bị lệch > 0.3s.

#### TASK 6.3 — API Endpoint: Dubbing
```
POST /api/v1/dub
Body: {
  "job_id": "...",
  "voice": "female|male",
  "speed": 1.0,
  "mix_mode": "overlay|replace",
  "original_volume": 0.2,
  "tts_provider": "gtts|elevenlabs"
}
Response: { "job_id": "...", "output_url": "..." }
```

---

### EPIC 7: LOGO OVERLAY
**Owner:** Backend Dev 1  
**Estimate:** 2 ngày  
**Dependency:** EPIC 1

#### TASK 7.1 — Chèn logo vào video
```
Subtasks:
- [ ] Accept logo upload: PNG (có transparency), JPG
- [ ] Validate: kích thước tối đa 5MB, định dạng png/jpg/webp
- [ ] Dùng FFmpeg overlay filter để chèn logo
- [ ] Hỗ trợ position: top-left, top-right, bottom-left, bottom-right, center, custom(x,y)
- [ ] Hỗ trợ custom kích thước logo (% của video width)
- [ ] Hỗ trợ opacity: 0.0 - 1.0
- [ ] Option: logo chỉ hiện trong khoảng thời gian nhất định (start_time - end_time)
```
**AC:** Logo chèn đúng vị trí, không bị méo, PNG transparency giữ nguyên.

#### TASK 7.2 — API Endpoint: Logo
```
POST /api/v1/logo
Content-Type: multipart/form-data
Body: {
  "job_id": "...",
  "logo": <file>,
  "position": "top-right",  // hoặc { "x": 50, "y": 50 } pixel
  "size_percent": 15,        // 15% chiều rộng video
  "opacity": 0.8,
  "start_time": 0,           // giây, null = từ đầu
  "end_time": null           // null = đến cuối
}
Response: { "job_id": "...", "output_url": "..." }
```

---

### EPIC 8: PIPELINE ORCHESTRATION
**Owner:** Backend Lead  
**Estimate:** 3 ngày  
**Dependency:** EPIC 2–7

#### TASK 8.1 — Full Pipeline Endpoint (one-shot)
Endpoint cho phép automation tool (n8n) gọi 1 lần, xử lý toàn bộ:
```
POST /api/v1/pipeline
Body: {
  "url": "https://www.tiktok.com/...",
  "steps": ["download", "transcribe", "translate", "subtitle", "dub", "logo"],
  "options": {
    "quality": "best",
    "subtitle_style": { "font_size": 24, "position": "bottom" },
    "dub": { "voice": "female", "speed": 1.0, "mix_mode": "overlay" },
    "logo": {
      "logo_url": "https://...",  // hoặc base64
      "position": "top-right",
      "size_percent": 15
    }
  },
  "webhook_url": "https://n8n.example.com/webhook/..."  // callback khi xong
}
Response: { "job_id": "...", "status": "queued", "estimated_time": 180 }
```

#### TASK 8.2 — Webhook Callback
```
Subtasks:
- [ ] Khi job hoàn thành: POST đến webhook_url với kết quả
- [ ] Body callback: { "job_id", "status", "output_url", "error", "metadata" }
- [ ] Retry webhook 3 lần nếu thất bại (exponential backoff)
- [ ] Validate webhook_url là HTTPS
```
**AC:** n8n nhận được callback sau khi video xử lý xong.

#### TASK 8.3 — Job Status Polling
```
GET /api/v1/jobs/{job_id}
Response: {
  "job_id": "...",
  "status": "queued|downloading|transcribing|translating|dubbing|done|failed",
  "progress": 65,     // %
  "created_at": "...",
  "updated_at": "...",
  "output_url": "...",
  "error": null,
  "steps_completed": ["download", "transcribe"],
  "steps_remaining": ["translate", "dub"]
}

GET /api/v1/jobs           // list jobs của user (paginated)
DELETE /api/v1/jobs/{job_id}  // cancel + cleanup
```

---

### EPIC 9: API SECURITY
**Owner:** Backend Lead  
**Estimate:** 4 ngày  
**Dependency:** EPIC 1

#### TASK 9.1 — Authentication
```
Subtasks:
- [ ] API Key authentication: header X-API-Key
- [ ] API Key hashing: lưu bcrypt hash trong DB, không lưu plain text
- [ ] Admin endpoint: POST /api/v1/admin/keys (tạo key mới)
- [ ] Admin endpoint: DELETE /api/v1/admin/keys/{key_id} (revoke)
- [ ] JWT token (optional): POST /api/v1/auth/token cho web UI login
```
**AC:** Mọi /api/v1/* đều yêu cầu X-API-Key hợp lệ, trừ /health và /docs.

#### TASK 9.2 — Authorization & Rate Limiting
```
Subtasks:
- [ ] Rate limiting per API key: 10 req/min, 100 req/hour (configurable)
- [ ] Rate limiting response: 429 Too Many Requests + Retry-After header
- [ ] Per-key quota: giới hạn số job/ngày (configurable khi tạo key)
- [ ] IP-based rate limiting như tầng bảo vệ thứ 2
- [ ] Dùng Redis để track rate limit counter
```
**AC:** Key bị rate limit sau khi vượt ngưỡng, trả 429 với thông báo rõ ràng.

#### TASK 9.3 — Input Validation & Sanitization
```
Subtasks:
- [ ] Validate URL: chỉ chấp nhận TikTok / Douyin URL (regex whitelist)
- [ ] Validate file upload: kiểm tra magic bytes (không chỉ extension)
- [ ] Giới hạn request body size (max 10MB cho logo upload)
- [ ] Dùng Pydantic models cho tất cả request/response
- [ ] Không expose internal paths trong error messages
- [ ] Sanitize filename trước khi lưu xuống disk
```
**AC:** Gửi URL độc hại / file giả mạo → bị reject trước khi xử lý.

#### TASK 9.4 — Security Headers & HTTPS
```
Subtasks:
- [ ] Thêm security headers: HSTS, X-Frame-Options, CSP, X-Content-Type-Options
- [ ] CORS: chỉ allow domain cụ thể (configurable CORS_ORIGINS env)
- [ ] Nginx config: force HTTPS redirect, TLS 1.2+
- [ ] Không log API keys trong application logs
- [ ] Secrets chỉ đọc từ env var, không hardcode
```
**AC:** SecurityHeaders.com scan đạt grade A.

#### TASK 9.5 — Job Isolation
```
Subtasks:
- [ ] Mỗi job chạy trong thư mục riêng: /data/jobs/{job_id}/
- [ ] Path traversal protection: validate tất cả file paths
- [ ] User chỉ xem/xóa được job của mình (theo API key)
- [ ] Temp files không expose qua web server trực tiếp
- [ ] Signed URLs cho download (expire sau 1 giờ)
```
**AC:** User A không thể truy cập job của User B.

---

### EPIC 10: WEB UI
**Owner:** Frontend Dev  
**Estimate:** 5 ngày  
**Dependency:** EPIC 2–8

#### TASK 10.1 — Layout & Navigation
```
Subtasks:
- [ ] Setup React + Vite + TailwindCSS
- [ ] Header: logo app, nav (Dashboard, History, API Docs)
- [ ] Responsive: mobile + desktop
- [ ] Dark mode toggle
```

#### TASK 10.2 — Main Form (Pipeline Config)
```
Subtasks:
- [ ] Input URL với validation realtime
- [ ] Checkbox chọn steps: Subtitle / Dub / Logo
- [ ] Collapsible config panels cho từng step
- [ ] Logo upload dropzone (drag & drop)
- [ ] Logo position picker: visual 9-grid selector
- [ ] Preview thumbnail URL sau khi paste link
```

#### TASK 10.3 — Job Progress UI
```
Subtasks:
- [ ] Progress bar per step (polling GET /jobs/{id} mỗi 3s)
- [ ] Live status text: "Đang tách audio...", "Đang dịch..."
- [ ] Estimated time remaining
- [ ] Error state với message rõ ràng
- [ ] Download button khi done
```

#### TASK 10.4 — Job History
```
Subtasks:
- [ ] Danh sách jobs với filter status
- [ ] Re-download video đã xử lý
- [ ] Xóa job + cleanup
```

#### TASK 10.5 — API Key Management (Admin)
```
Subtasks:
- [ ] Trang admin: tạo / revoke API key
- [ ] Hiển thị usage stats per key
- [ ] Copy-to-clipboard cho API key
```

---

### EPIC 11: DOCUMENTATION & TESTING
**Owner:** Cả team  
**Estimate:** 3 ngày

#### TASK 11.1 — API Documentation
```
Subtasks:
- [ ] FastAPI tự sinh OpenAPI spec tại /docs (Swagger UI)
- [ ] Viết description đầy đủ cho mỗi endpoint
- [ ] Thêm example request/response cho mỗi endpoint
- [ ] Tạo Postman Collection export
- [ ] README.md với Quick Start guide
```

#### TASK 11.2 — n8n Integration Guide
```
Subtasks:
- [ ] Viết workflow mẫu n8n: download + dịch + download kết quả
- [ ] Screenshot step-by-step
- [ ] Mẫu cấu hình webhook callback trong n8n
```

#### TASK 11.3 — Testing
```
Subtasks:
- [ ] Unit tests: validate URL, logo upload, SRT parser
- [ ] Integration tests: mock yt-dlp, test full pipeline với video mẫu
- [ ] Load test: 10 concurrent jobs (Locust)
- [ ] Security test: OWASP ZAP scan trên staging
- [ ] Manual UAT checklist (xem Section 5)
```

---

## 4. DEPENDENCY MAP

```
EPIC 1 (Setup)
    └── EPIC 2 (Download)
            └── EPIC 3 (STT)
                    └── EPIC 4 (Translation)
                            ├── EPIC 5 (Subtitle Burn)
                            └── EPIC 6 (Dubbing)
    └── EPIC 7 (Logo)     ← độc lập, chỉ cần EPIC 1
    └── EPIC 9 (Security) ← chạy song song với EPIC 2-8
    
EPIC 8 (Pipeline) ← cần EPIC 2-7 hoàn thành
EPIC 10 (UI)      ← cần EPIC 8 hoàn thành
EPIC 11 (Docs)    ← chạy song song, hoàn thiện cuối cùng
```

---

## 5. UAT CHECKLIST

### UC-01: Download TikTok
- [ ] Paste URL TikTok → nhận job_id
- [ ] GET /jobs/{id} polling → status = done
- [ ] Download video: không có watermark TikTok
- [ ] URL không hợp lệ → lỗi rõ ràng (400, không phải 500)

### UC-02: Download Douyin
- [ ] Paste URL Douyin → nhận job_id
- [ ] Video download thành công

### UC-03: Subtitle tiếng Việt
- [ ] Gọi pipeline với steps=["download","transcribe","translate","subtitle"]
- [ ] Video output có subtitle tiếng Việt
- [ ] Subtitle sync đúng với nội dung nói
- [ ] Font đọc rõ trên nền sáng và tối

### UC-04: Lồng tiếng
- [ ] Gọi pipeline với steps bao gồm "dub"
- [ ] Giọng TTS tiếng Việt nghe rõ
- [ ] Âm thanh không bị lệch > 0.5s so với video
- [ ] Audio gốc nghe nhỏ hơn TTS

### UC-05: Logo overlay
- [ ] Upload PNG có nền trong suốt
- [ ] Chọn vị trí top-right
- [ ] Logo xuất hiện đúng vị trí trong video output
- [ ] PNG transparency giữ nguyên

### UC-06: n8n Integration
- [ ] Tạo HTTP Request node trong n8n
- [ ] POST /api/v1/pipeline với X-API-Key header
- [ ] n8n nhận webhook callback khi job xong
- [ ] Parse output_url từ callback và download file

### UC-07: Security
- [ ] Gọi API không có key → 401
- [ ] Gọi quá rate limit → 429 + Retry-After
- [ ] Upload file PHP giả extension PNG → bị reject
- [ ] Thử path traversal trong job_id → bị reject (400/404)

---

## 6. PHÂN CÔNG & TIMELINE

### Team
| Vai trò | Số người | Trách nhiệm |
|---------|----------|-------------|
| Backend Lead | 1 | EPIC 1, 8, 9, Review |
| Backend Dev 1 | 1 | EPIC 2, 3, 7 |
| Backend Dev 2 | 1 | EPIC 4, 5, 6 |
| Frontend Dev | 1 | EPIC 10 |
| QA | 1 | EPIC 11, UAT |

### Sprint Plan (2-week sprints)

#### Sprint 1 (Tuần 1-2)
| Task | Owner | Story Points |
|------|-------|-------------|
| EPIC 1: Setup | Backend Lead | 8 |
| EPIC 2: Download | Backend Dev 1 | 10 |
| EPIC 9: Security (Auth + Rate Limit) | Backend Lead | 8 |

**Sprint Goal:** Có thể download TikTok/Douyin qua API với auth.

#### Sprint 2 (Tuần 3-4)
| Task | Owner | Story Points |
|------|-------|-------------|
| EPIC 3: STT | Backend Dev 1 | 12 |
| EPIC 4: Translation | Backend Dev 2 | 8 |
| EPIC 9: Input Validation | Backend Lead | 5 |

**Sprint Goal:** Nhận URL TikTok → trả file SRT tiếng Việt.

#### Sprint 3 (Tuần 5-6)
| Task | Owner | Story Points |
|------|-------|-------------|
| EPIC 5: Subtitle Burn | Backend Dev 2 | 8 |
| EPIC 6: Dubbing | Backend Dev 2 | 12 |
| EPIC 7: Logo Overlay | Backend Dev 1 | 5 |
| EPIC 10: UI (bắt đầu) | Frontend Dev | 8 |

**Sprint Goal:** Có video output với subtitle + lồng tiếng + logo.

#### Sprint 4 (Tuần 7-8)
| Task | Owner | Story Points |
|------|-------|-------------|
| EPIC 8: Pipeline + Webhook | Backend Lead | 8 |
| EPIC 10: UI (hoàn thiện) | Frontend Dev | 10 |
| EPIC 11: Docs + Testing | QA + All | 10 |
| UAT & Bug Fix | All | - |

**Sprint Goal:** Production-ready, n8n integration tested.

**Tổng thời gian ước tính: 8 tuần (2 tháng)**

---

## 7. RỦI RO & GIẢI PHÁP

| Rủi ro | Xác suất | Ảnh hưởng | Giải pháp |
|--------|----------|-----------|-----------|
| TikTok/Douyin thay đổi API → yt-dlp fail | Cao | Cao | Monitor yt-dlp updates, có script auto-update |
| Whisper quá chậm trên CPU | Cao | Trung bình | Dùng GPU instance hoặc fallback Google STT API |
| TTS tiếng Việt nghe không tự nhiên | Trung bình | Trung bình | Tích hợp ElevenLabs như option premium |
| Disk đầy vì nhiều job concurrent | Trung bình | Cao | Auto cleanup, giới hạn concurrent jobs, alert monitoring |
| IP bị TikTok block | Trung bình | Cao | Rotate User-Agent, xem xét residential proxy |
| Dịch sai nghĩa | Thấp | Thấp | Cho user chọn provider (Google/DeepL), hiển thị bản gốc |

---

## 8. DEFINITION OF DONE

Một task được coi là **Done** khi:
- [ ] Code đã được review và approve bởi ít nhất 1 người
- [ ] Unit/integration tests viết xong và pass
- [ ] API endpoint có documentation trong Swagger
- [ ] Không có lỗi lint
- [ ] Đã test thủ công trên staging environment
- [ ] Không có secret/credential hardcoded

---

*Tài liệu này là living document — cập nhật khi requirements thay đổi.*
