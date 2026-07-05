# UAT Test Report — Downloader Ultimate
**Ngày test:** 2026-07-05  
**Tester:** BA (End User perspective)  
**Server:** pphu@192.168.1.200  
**Repo:** git@github.com:phuphan2010/downloader-ultimate.git  
**Kết quả tổng:** ❌ **FAIL — Hệ thống không khởi động được**

---

## TÓM TẮT EXECUTIVE

> Sau khi clone repo và thử deploy lên server, **ứng dụng không build được** do lỗi dependency conflict. Ngoài lỗi build, quá trình review code còn phát hiện **3 lỗ hổng bảo mật nghiêm trọng** ảnh hưởng trực tiếp đến yêu cầu "bảo mật best practices" trong spec. Toàn bộ 7 UAT test cases đều **không thể thực thi** vì app chưa lên được.

---

## PHẦN 1 — FINDINGS

### 🔴 BUG-01 | BLOCKER | Build thất bại: Dependency Conflict

| Trường | Giá trị |
|--------|---------|
| **Severity** | Blocker |
| **File** | `backend/pyproject.toml` |
| **Phát hiện** | Khi chạy `docker compose build` |

**Mô tả:**  
Package `googletrans==4.0.0rc1` (dùng để dịch tiếng Việt) yêu cầu `httpx==0.13.3`, trong khi project lại yêu cầu `httpx>=0.27.0`. Hai version này hoàn toàn không tương thích. Poetry không thể giải quyết dependency, build fail 100%.

**Error thực tế:**
```
Because downloader-ultimate depends on googletrans (4.0.0rc1) which depends
on httpx (0.13.3), httpx is required.
So, because downloader-ultimate depends on httpx (>=0.27.0,<0.28.0),
version solving failed.
```

**Hậu quả:** Toàn bộ hệ thống không thể chạy. Không thể test bất kỳ tính năng nào.

**Đề xuất sửa:** Thay `googletrans==4.0.0rc1` bằng `deep-translator` hoặc dùng `google-cloud-translate` chính thức. Package `googletrans` đã không được maintain từ lâu.

---

### 🔴 BUG-02 | BLOCKER | Invalid `pyproject.toml` — Python key sai vị trí

| Trường | Giá trị |
|--------|---------|
| **Severity** | Blocker |
| **File** | `backend/pyproject.toml`, dòng 6 |

**Mô tả:**  
Key `python = "^3.11"` bị đặt trong section `[tool.poetry]` (metadata của package) thay vì đúng chỗ là `[tool.poetry.dependencies]`. Poetry phiên bản mới từ chối file này.

```toml
# SAI — section [tool.poetry] không chấp nhận key "python"
[tool.poetry]
name = "downloader-ultimate"
authors = ["phuphan2010"]
python = "^3.11"   ← LỖI Ở ĐÂY
```

**Lưu ý:** BA đã tạm thời sửa lỗi này trên server để kiểm tra các lỗi tiếp theo. Cần fix trên repo gốc.

---

### 🔴 BUG-03 | CRITICAL | Toàn bộ API endpoints KHÔNG có Authentication

| Trường | Giá trị |
|--------|---------|
| **Severity** | Critical — Security |
| **File** | Tất cả files trong `backend/app/api/v1/endpoints/` |
| **Yêu cầu gốc** | "Đảm bảo best practices về bảo mật" + "Có API để n8n call" |

**Mô tả:**  
Function `get_current_api_key` được viết đầy đủ trong `app/api/deps.py`, nhưng **không được import hoặc sử dụng ở bất kỳ endpoint nào**. Toàn bộ 8 endpoint groups (download, transcribe, translate, subtitle, dub, logo, pipeline, jobs) đều **hoàn toàn public, không cần API Key**.

**Bằng chứng:**
```bash
$ grep -rn "get_current_api_key" backend/app/
# Chỉ tìm thấy 1 kết quả: chính file định nghĩa nó (deps.py)
# KHÔNG có file nào import hoặc dùng nó
```

**Hậu quả:**
- Bất kỳ ai biết IP server đều có thể download video, lồng tiếng, consume tài nguyên server mà không cần key.
- Rate limiting cũng vô hiệu vì phụ thuộc vào auth.
- Hoàn toàn không đáp ứng yêu cầu bảo mật trong spec.

---

### 🔴 BUG-04 | CRITICAL | API Key lưu In-Memory — Mất toàn bộ khi restart

| Trường | Giá trị |
|--------|---------|
| **Severity** | Critical |
| **File** | `backend/app/core/security.py`, dòng 11 |

**Mô tả:**  
Toàn bộ API keys được lưu trong một Python dictionary trong bộ nhớ RAM:

```python
# security.py
api_keys_db: Dict[str, Dict] = {}  # ← mất sạch khi container restart
```

**Hậu quả:**
- Mỗi lần restart container (deploy mới, crash, update), toàn bộ API keys biến mất.
- Không có cách nào tạo key trước rồi dùng — key không tồn tại qua restart.
- Hoàn toàn không dùng được trong production.

**Đề xuất:** Lưu vào SQLite hoặc Redis (đã có sẵn trong docker-compose) với giá trị hash bcrypt.

---

### 🔴 BUG-05 | CRITICAL | Job State lưu In-Memory — Worker và API không chia sẻ được state

| Trường | Giá trị |
|--------|---------|
| **Severity** | Critical |
| **File** | `backend/app/services/job_store.py` |

**Mô tả:**  
Job state lưu bằng dictionary Python trong memory:

```python
jobs_db: Dict[str, Dict] = {}
```

Trong khi đó, docker-compose có 2 container riêng biệt: `api` và `worker`. Hai container này có **bộ nhớ riêng biệt hoàn toàn** — `jobs_db` trong container `api` và `jobs_db` trong container `worker` là 2 object khác nhau, không sync.

**Hậu quả:**
- Celery worker xử lý job xong → cập nhật `jobs_db` của nó → container API vẫn thấy job ở trạng thái cũ.
- `GET /jobs/{job_id}` sẽ không bao giờ trả về status `done` khi dùng Celery worker.
- Jobs mất toàn bộ khi restart.

**Đề xuất:** Dùng Redis để lưu job state (đã có Redis trong stack).

---

### 🟡 BUG-06 | HIGH | Celery Worker không được sử dụng — BackgroundTasks chạy thay

| Trường | Giá trị |
|--------|---------|
| **Severity** | High |
| **File** | `backend/app/api/v1/endpoints/pipeline.py`, `download.py` |

**Mô tả:**  
docker-compose định nghĩa một container `worker` chạy Celery. Tuy nhiên, tất cả background jobs thực tế đều dùng `FastAPI BackgroundTasks` — chạy trong cùng process với API server, không phải Celery worker.

```python
# pipeline.py
background_tasks.add_task(pipeline_service.run_pipeline, ...)  # ← FastAPI BG task, KHÔNG phải Celery
```

**Hậu quả:**
- Container `worker` chạy nhưng không làm gì cả — lãng phí tài nguyên.
- Video xử lý nặng (Whisper STT, FFmpeg) chạy trong API process → API bị block, các request khác timeout.
- Không scale được — không thể thêm worker.

---

### 🟡 BUG-07 | HIGH | `GET /jobs` lộ jobs của tất cả users

| Trường | Giá trị |
|--------|---------|
| **Severity** | High — Privacy / Security |
| **File** | `backend/app/api/v1/endpoints/jobs.py` |

**Mô tả:**  
`GET /api/v1/jobs` trả về danh sách **tất cả jobs** của mọi user, không lọc theo API key:

```python
@router.get("")
async def get_all_jobs():
    return list_jobs()  # ← toàn bộ jobs của tất cả mọi người
```

**Hậu quả:** User A có thể thấy URL download video của User B.

---

### 🟡 BUG-08 | MEDIUM | Hardcoded backdoor key trong Security module

| Trường | Giá trị |
|--------|---------|
| **Severity** | Medium — Security |
| **File** | `backend/app/core/security.py`, dòng 22-23 |

**Mô tả:**  
Có một key tĩnh hardcode trong code:

```python
if settings.APP_ENV == "development" and raw_key == "dev-secret-key-123":
    return True
```

**Rủi ro:** Nếu ai đó deploy với `APP_ENV=development` (nhầm lẫn, hoặc cố ý), key `dev-secret-key-123` sẽ bypass toàn bộ auth. Key này có thể bị leak qua git history, log, hoặc code review.

**Đề xuất:** Dùng env var `DEV_API_KEY` thay vì hardcode, hoặc bỏ hoàn toàn.

---

### 🟡 BUG-09 | MEDIUM | Thiếu `poetry.lock` file

| Trường | Giá trị |
|--------|---------|
| **Severity** | Medium |
| **File** | Repo root / `backend/` |

**Mô tả:**  
Không có file `poetry.lock` trong repo. Mỗi lần build Docker image, Poetry sẽ resolve lại toàn bộ dependencies từ đầu, dẫn đến:
- Build không deterministic (hôm nay build khác ngày mai).
- Dễ bị breaking changes từ dependency mới.
- CI/CD có thể break bất ngờ.

---

## PHẦN 2 — UAT TEST CASES SUMMARY

| # | Test Case | Kết quả | Ghi chú |
|---|-----------|---------|---------|
| UC-01 | Download TikTok | ❌ BLOCKED | App không build |
| UC-02 | Download Douyin | ❌ BLOCKED | App không build |
| UC-03 | Subtitle tiếng Việt | ❌ BLOCKED | App không build |
| UC-04 | Lồng tiếng | ❌ BLOCKED | App không build |
| UC-05 | Logo overlay | ❌ BLOCKED | App không build |
| UC-06 | n8n Integration | ❌ BLOCKED | App không build + auth bị thiếu |
| UC-07 | Security check | ❌ FAIL | Confirmed: no auth on any endpoint |

**0/7 test cases passed.**

---

## PHẦN 3 — PRIORITY FIX LIST cho PM Lead

Sắp xếp theo thứ tự cần fix để unblock team QA:

| Priority | Bug ID | Action cần làm |
|----------|--------|----------------|
| P0 — Fix ngay | BUG-01 | Thay `googletrans==4.0.0rc1` → `deep-translator` hoặc `google-cloud-translate` |
| P0 — Fix ngay | BUG-02 | Xóa `python = "^3.11"` khỏi `[tool.poetry]` trong pyproject.toml |
| P0 — Fix ngay | BUG-03 | Thêm `Depends(get_current_api_key)` vào tất cả endpoints trong router |
| P1 — Sprint này | BUG-04 | Chuyển API key store từ in-memory → Redis hoặc SQLite |
| P1 — Sprint này | BUG-05 | Chuyển job store từ in-memory → Redis |
| P1 — Sprint này | BUG-06 | Wire lại pipeline tasks để dùng Celery thay vì BackgroundTasks |
| P2 — Sprint sau | BUG-07 | Filter `GET /jobs` theo API key của caller |
| P2 — Sprint sau | BUG-08 | Bỏ hardcoded `dev-secret-key-123` |
| P2 — Sprint sau | BUG-09 | Commit `poetry.lock` vào repo |

---

## PHẦN 4 — ĐÁNH GIÁ TỔNG THỂ

### Những gì làm tốt ✅
- Cấu trúc project đúng theo thiết kế BA (backend/frontend/workers/docs)
- Docker-compose có đủ các services: api, worker, redis, nginx
- Nginx config có security headers chuẩn (X-Frame-Options, CSP, HSTS)
- Downloader service có URL validation, retry logic, disk check
- Code có logging rõ ràng với structured log
- Có Postman collection và n8n integration guide trong `/docs`

### Khoảng cách với yêu cầu ❌
| Yêu cầu | Trạng thái |
|---------|-----------|
| Download TikTok/Douyin | ❓ Code có, chưa test được |
| STT + Translation + Dub | ❓ Code có, chưa test được |
| **API Security (auth)** | ❌ **Auth được code nhưng chưa được wire vào — hoàn toàn không hoạt động** |
| **API cho n8n** | ❌ **Blocked bởi build failure + thiếu auth** |
| Logo overlay | ❓ Code có, chưa test được |
| Async job processing | ⚠️ Dùng BackgroundTasks thay vì Celery như thiết kế |

### Kết luận
Dự án có nền tảng code khá tốt về cấu trúc và logic nghiệp vụ, nhưng **chưa production-ready** ở hai khía cạnh quan trọng nhất: **bảo mật (auth chưa wire) và stability (in-memory state)**. Cần fix P0 bugs trước khi BA có thể thực hiện UAT lần 2.

---

*Báo cáo này dựa trên code review và build log. Cần retest toàn bộ 7 UAT cases sau khi P0 fixes được merge.*  
*BA sẵn sàng retest ngay khi PM lead confirm fix xong.*
