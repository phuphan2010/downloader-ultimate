# 🤖 AGENTS REGISTRY & TASK MATRIX — Downloader Ultimate

Tài liệu này tổng hợp toàn bộ các **Agents Chuyên Biệt (Specialized Agents)** và **Skills** được định nghĩa cho dự án **downloader-ultimate**. Mỗi Agent đóng vai trò Expert trong phạm vi nhiệm vụ của mình, chịu trách nhiệm cho các file/module cụ thể và quy trình sửa lỗi khi phát sinh issue.

---

## 📌 DANH SÁCH AGENT & PHÂN CÔNG TASK

### 1. `agent-epic1-infra` — Infrastructure & Setup Expert
- **EPIC phụ trách**: EPIC 1 (Project Setup & Infrastructure)
- **Nhiệm vụ**: Quản lý cấu trúc monorepo, dependencies (`pyproject.toml`), Docker (`docker-compose.yml`, `Dockerfile`), Nginx reverse proxy, CI/CD GitHub Actions, Makefile, Logging JSON (`structlog`), và Health check endpoint.
- **Thư mục/File chịu trách nhiệm**:
  - [pyproject.toml](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/pyproject.toml)
  - [docker-compose.yml](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/docker-compose.yml)
  - [nginx/nginx.conf](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/nginx/nginx.conf)
  - [.github/workflows/](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/.github/workflows/)
  - [Makefile](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/Makefile)
  - [backend/app/core/logging.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/core/logging.py)
  - [backend/app/main.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/main.py)
- **Skill tương ứng**: `.agents/skills/epic1-infra/SKILL.md`

---

### 2. `agent-epic2-download` — Video Downloader Expert
- **EPIC phụ trách**: EPIC 2 (Video Download Module)
- **Nhiệm vụ**: Quản lý tải video từ TikTok & Douyin (loại bỏ watermark), tích hợp `yt-dlp` wrapper, hỗ trợ `impersonate="chrome"` và cookies authentication, retry với backoff, giới hạn đĩa cứng và quản lý vòng đời file (`file_manager.py`).
- **Thư mục/File chịu trách nhiệm**:
  - [backend/app/services/downloader.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/services/downloader.py)
  - [backend/app/models/download.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/models/download.py)
  - [backend/app/storage/file_manager.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/storage/file_manager.py)
  - [backend/app/api/v1/endpoints/download.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/api/v1/endpoints/download.py)
- **Skill tương ứng**: `.agents/skills/epic2-download/SKILL.md`

---

### 3. `agent-epic3-stt` — Audio & Speech-to-Text Expert
- **EPIC phụ trách**: EPIC 3 (Audio Processing & STT)
- **Nhiệm vụ**: Trích xuất audio chuẩn 16kHz mono WAV với FFmpeg `loudnorm` filter, tích hợp `faster-whisper` STT model, tự động nhận dạng ngôn ngữ và định dạng output `.srt` kèm timestamp `HH:MM:SS,mmm`.
- **Thư mục/File chịu trách nhiệm**:
  - [backend/app/services/audio.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/services/audio.py)
  - [backend/app/services/stt.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/services/stt.py)
  - [backend/app/models/stt.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/models/stt.py)
  - [backend/app/api/v1/endpoints/transcribe.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/api/v1/endpoints/transcribe.py)
- **Skill tương ứng**: `.agents/skills/epic3-stt/SKILL.md`

---

### 4. `agent-epic4-translate` — Translation Expert
- **EPIC phụ trách**: EPIC 4 (Translation Module)
- **Nhiệm vụ**: Dịch văn bản và file SRT từng đoạn sang tiếng Việt (Google Translate via `deep-translator` & DeepL API), giữ nguyên timestamp SRT, chuyển đổi sang WebVTT (`.vtt`), và cache kết quả dịch.
- **Thư mục/File chịu trách nhiệm**:
  - [backend/app/services/translator.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/services/translator.py)
  - [backend/app/models/translate.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/models/translate.py)
  - [backend/app/api/v1/endpoints/translate.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/api/v1/endpoints/translate.py)
- **Skill tương ứng**: `.agents/skills/epic4-translate/SKILL.md`

---

### 5. `agent-epic5-subtitle` — Subtitle Burn-In Expert
- **EPIC phụ trách**: EPIC 5 (Subtitle Burn-In)
- **Nhiệm vụ**: Chèn viền chữ hardcode subtitle trực tiếp vào video stream bằng FFmpeg subtitles filter, hỗ trợ tùy chỉnh font size, font color (chuyển đổi Hex sang ASS `&H00BBGGRR`), outline color và vị trí (top, bottom, center).
- **Thư mục/File chịu trách nhiệm**:
  - [backend/app/services/subtitle.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/services/subtitle.py)
  - [backend/app/models/subtitle.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/models/subtitle.py)
  - [backend/app/api/v1/endpoints/subtitle.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/api/v1/endpoints/subtitle.py)
- **Skill tương ứng**: `.agents/skills/epic5-subtitle/SKILL.md`

---

### 6. `agent-epic6-dubbing` — AI Dubbing Expert
- **EPIC phụ trách**: EPIC 6 (Dubbing - Lồng tiếng)
- **Nhiệm vụ**: Tạo giọng đọc AI tiếng Việt qua `gTTS` hoặc `ElevenLabs`, trộn và đồng bộ âm thanh bằng FFmpeg filter complex (chế độ overlay giảm volume nhạc gốc 20% hoặc replace mode thay thế hoàn toàn).
- **Thư mục/File chịu trách nhiệm**:
  - [backend/app/services/tts.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/services/tts.py)
  - [backend/app/services/dubbing.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/services/dubbing.py)
  - [backend/app/models/dub.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/models/dub.py)
  - [backend/app/api/v1/endpoints/dub.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/api/v1/endpoints/dub.py)
- **Skill tương ứng**: `.agents/skills/epic6-dubbing/SKILL.md`

---

### 7. `agent-epic7-logo` — Watermark Logo Overlay Expert
- **EPIC phụ trách**: EPIC 7 (Logo Overlay)
- **Nhiệm vụ**: Xử lý upload logo, validate magic bytes định dạng ảnh (PNG, JPEG, WEBP), chèn logo vào video stream qua FFmpeg overlay filter tại các vị trí 9-grid, tùy chỉnh % kích thước video và độ trong suốt opacity.
- **Thư mục/File chịu trách nhiệm**:
  - [backend/app/services/logo.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/services/logo.py)
  - [backend/app/models/logo.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/models/logo.py)
  - [backend/app/api/v1/endpoints/logo.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/api/v1/endpoints/logo.py)
- **Skill tương ứng**: `.agents/skills/epic7-logo/SKILL.md`

---

### 8. `agent-epic8-pipeline` — Pipeline & Worker Orchestrator
- **EPIC phụ trách**: EPIC 8 (Pipeline Orchestration & Worker Offloading)
- **Nhiệm vụ**: Quản lý batch endpoint One-shot `/api/v1/pipeline` cho n8n/Zapier, điều phối chuỗi xử lý bất đồng bộ (`download -> transcribe -> translate -> subtitle -> dub -> logo`), offload sang Celery Worker, gửi Webhook callback HTTPS kèm retry exponential backoff.
- **Thư mục/File chịu trách nhiệm**:
  - [backend/app/services/pipeline.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/services/pipeline.py)
  - [backend/app/models/pipeline.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/models/pipeline.py)
  - [backend/app/api/v1/endpoints/pipeline.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/api/v1/endpoints/pipeline.py)
  - [backend/app/workers/celery_app.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/workers/celery_app.py)
  - [backend/app/workers/tasks.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/workers/tasks.py)
- **Skill tương ứng**: `.agents/skills/epic8-pipeline/SKILL.md`

---

### 9. `agent-epic9-security` — API Security & Privacy Expert
- **EPIC phụ trách**: EPIC 9 (API Security & Auth Privacy)
- **Nhiệm vụ**: Quản lý xác thực `X-API-Key` mã hóa Bcrypt, lưu trữ persistent trên Redis (`redis_store.py`), Rate Limiting sliding-window per key (`check_rate_limit`), Admin key endpoints (`/admin/keys`), và phân quyền cách ly jobs giữa các users (`GET /jobs`).
- **Thư mục/File chịu trách nhiệm**:
  - [backend/app/core/security.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/core/security.py)
  - [backend/app/api/deps.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/api/deps.py)
  - [backend/app/services/redis_store.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/services/redis_store.py)
  - [backend/app/api/v1/endpoints/admin.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/api/v1/endpoints/admin.py)
  - [backend/app/api/v1/endpoints/jobs.py](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/app/api/v1/endpoints/jobs.py)
- **Skill tương ứng**: `.agents/skills/epic9-security/SKILL.md`

---

### 10. `agent-epic10-ui` — Web UI Dashboard Expert
- **EPIC phụ trách**: EPIC 10 (Web UI Dashboard)
- **Nhiệm vụ**: Phát triển giao diện React + Vite + TailwindCSS, thiết kế Glassmorphism Dark Mode, form chọn step linh hoạt, picker vị trí logo 9-grid, live progress monitor polling, và trang quản trị API key.
- **Thư mục/File chịu trách nhiệm**:
  - [frontend/src/App.jsx](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/frontend/src/App.jsx)
  - [frontend/src/index.css](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/frontend/src/index.css)
  - [frontend/index.html](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/frontend/index.html)
  - [frontend/package.json](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/frontend/package.json)
- **Skill tương ứng**: `.agents/skills/epic10-ui/SKILL.md`

---

### 11. `agent-epic11-docs-test` — QA & Documentation Expert
- **EPIC phụ trách**: EPIC 11 (Documentation & Testing)
- **Nhiệm vụ**: Viết tài liệu [README.md](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/README.md), [n8n Integration Guide](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/docs/n8n_integration_guide.md), [Postman Collection](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/docs/downloader_ultimate.postman_collection.json), và hệ thống kiểm thử tự động `pytest` (unit & integration tests).
- **Thư mục/File chịu trách nhiệm**:
  - [README.md](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/README.md)
  - [docs/](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/docs/)
  - [backend/tests/](file:///c:/Users/15520/Documents/my-work/Antigravity/douyin-download-video/backend/tests/)
- **Skill tương ứng**: `.agents/skills/epic11-docs-test/SKILL.md`

---

## 🔄 QUY TRÌNH KHI CÓ BUG/TASK MỚI

Khi phát sinh bug hoặc có cập nhật tính năng mới ở phiên chat bất kỳ:
1. **PM Lead (Tôi)** sẽ tra cứu bảng trên để xác định exact **Agent** và **Skill** chịu trách nhiệm.
2. **Kích hoạt Agent chuyên biệt** bằng prompt chứa tên agent và nạp hướng dẫn từ skill file tương ứng.
3. **Agent chuyên biệt làm việc trong phạm vi file được giao**, chạy tests verify, sau đó commit lên branch `bugfix/...` hoặc `feature/...`.
4. **PM Lead review & verify AC**, tiến hành merge vào `main` và push lên GitHub remote.
