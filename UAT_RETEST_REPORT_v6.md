# UAT Retest Report — Downloader Ultimate (Lần 6)
**Ngày test:** 2026-07-05  
**Tester:** BA (End User perspective)  
**Server:** pphu@192.168.1.200  
**Branch tested:** `main` @ commit `eb7b9e1`  
**Kết quả tổng:** ❌ **FAIL — Celery queue mismatch: tasks gửi vào queue `celery`, worker chỉ listen `default`**

---

## TÓM TẮT EXECUTIVE

> BUG-13 (structlog) đã fix đúng — API lần đầu tiên respond thành công. Health check trả `{"status":"ok"}`, tạo API key thành công, submit job 202 Accepted. Tuy nhiên, tất cả video processing tasks bị stuck ở trạng thái `queued` mãi mãi do Celery queue name mismatch: API dispatch vào queue `celery` (Celery default), worker chỉ listen `-Q default`. Thêm BUG-14 phụ: rate limiting không hoạt động.

---

## PHẦN 1 — XÁC NHẬN TIẾN TRIỂN

| Hạng mục | Lần 5 | Lần 6 |
|---------|-------|-------|
| Docker build | ✅ | ✅ |
| Container start | ✅ | ✅ |
| API health `/health` | ❌ 500 | ✅ **`{"status":"ok"}` — lần đầu tiên!** |
| API docs `/docs` | ❌ 500 | ✅ 200 OK |
| BUG-13 (structlog) | ❌ BLOCKED | ✅ **FIXED** |
| API key creation | ❌ N/A | ✅ **PASS** — key tạo thành công |
| Job submit (POST /pipeline) | ❌ N/A | ✅ 202 Accepted |
| Worker picks up tasks | ❌ N/A | ❌ FAIL — queue mismatch |
| Video processing completes | ❌ N/A | ❌ FAIL |

**Tích cực: API hoạt động lần đầu tiên! Security auth, job creation đều OK.**

---

## PHẦN 2 — BUGS MỚI

---

### 🔴 BUG-15 | BLOCKER | Celery queue name mismatch — tasks không bao giờ được xử lý

| Trường | Giá trị |
|--------|---------|
| **Severity** | Blocker |
| **File** | `backend/app/workers/celery_app.py` |
| **Nguyên nhân gốc** | Task dispatch vào queue `celery`, worker listen `-Q default` |
| **Impact** | 100% video processing jobs stuck `queued` mãi mãi |

**Bằng chứng từ Redis:**

```bash
# Task trong Redis db1 (Celery broker):
routing_key: "celery"    ← API gửi vào đây

# Worker start command (docker-compose.override.yml):
celery ... worker -Q default    ← worker chỉ đọc queue này
```

**Chuỗi lỗi:**
```
POST /api/v1/pipeline
    → run_pipeline_task.delay(...)
    → Celery gửi vào queue "celery" (default Celery queue name)
    → Worker chỉ consume queue "default"
    → Task nằm trong queue "celery" mãi mãi
    → Job status = "queued" không bao giờ thay đổi
```

**Xác nhận qua Redis inspect:**
```json
"delivery_info": {
    "exchange": "",
    "routing_key": "celery"    ← task nằm ở đây
}
```

```bash
redis-cli -n 1 LLEN celery   # → 1 (task đang chờ)
redis-cli -n 1 LLEN default  # → 0 (worker nhìn vào đây, không có gì)
```

---

**Fix cho PM lead — chọn 1 trong 2 options:**

**Option A — Khuyến nghị (2 phút):** Thêm `task_default_queue` vào `celery_app.py`

```python
# backend/app/workers/celery_app.py
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.DOWNLOAD_TIMEOUT_SEC + 60,
    task_default_queue="default",    # ← THÊM dòng này
)
```

Kết quả: API dispatch vào queue `default`, worker `-Q default` sẽ nhận được.

---

**Option B (2 phút):** Thay đổi worker command — bỏ `-Q default`

```yaml
# docker-compose.override.yml hoặc docker-compose.yml
worker:
  command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=1
  # ← bỏ "-Q default", worker sẽ consume tất cả queues bao gồm "celery"
```

---

### 🟡 BUG-14 | Medium | Rate limiting không được enforce

| Trường | Giá trị |
|--------|---------|
| **Severity** | Medium (không phải blocker) |
| **Config** | `.env`: `RATE_LIMIT_PER_MINUTE=10`, `RATE_LIMIT_PER_HOUR=100` |
| **Symptom** | 12 requests liên tiếp đều trả 200, không có 429 |

**Test evidence:**
```bash
# Gửi 12 requests liên tiếp vào GET /api/v1/jobs:
Request 1-12: HTTP 200   ← tất cả đều pass, không có 429
```

Config đặt limit=10/phút nhưng không được áp dụng. Rate limiting middleware hoặc decorator có thể chưa được implement hoặc không được wired vào router.

**Fix:** PM lead kiểm tra lại rate limiting implementation — đảm bảo middleware/decorator đang active trên các endpoint. Không phải blocker cho UAT hiện tại.

---

## PHẦN 3 — UAT TEST CASES SUMMARY

| # | Test Case | Lần 1–5 | Lần 6 | Ghi chú |
|---|-----------|---------|-------|---------|
| UC-07a | 401 không có key | ❌ | ✅ **PASS** | HTTP 401 đúng |
| UC-07b | 401 key sai | ❌ | ✅ **PASS** | HTTP 401 đúng |
| UC-07c | 200 key đúng | ❌ | ✅ **PASS** | HTTP 200 đúng |
| UC-07d | Path traversal | ❌ | ✅ **PASS** | HTTP 404, không leak |
| UC-07e | Rate limiting | ❌ | ❌ **FAIL** | BUG-14 — 12 req đều 200 |
| UC-01 | Download TikTok | ❌ | ❌ BLOCKED | BUG-15 — stuck queued |
| UC-02 | Download Douyin | ❌ | ❌ BLOCKED | BUG-15 |
| UC-03 | Subtitle tiếng Việt | ❌ | ❌ BLOCKED | BUG-15 |
| UC-04 | Lồng tiếng | ❌ | ❌ BLOCKED | BUG-15 |
| UC-05 | Logo overlay | ❌ | ❌ BLOCKED | BUG-15 |
| UC-06 | n8n Integration | ❌ | ❌ BLOCKED | BUG-15 |

**4/11 security sub-tests pass. 0/6 video processing tests pass.**

---

## PHẦN 4 — PRIORITY FIX LIST cho PM Lead (Lần 6)

| Priority | Bug ID | File | Fix | Thời gian |
|----------|--------|------|-----|-----------|
| **P0** | BUG-15 | `backend/app/workers/celery_app.py` | Option A: thêm `task_default_queue="default"` | 2 phút |
| P1 | BUG-14 | Rate limiting middleware | Kiểm tra và wire lại rate limiting | 15–30 phút |

---

## PHẦN 5 — NHẬN XÉT

### Điểm tích cực ✅
- **API lần đầu respond đúng** — health, auth, job creation đều hoạt động
- BUG-13 fix chính xác theo đúng Option A (xóa `add_logger_name` + dùng `structlog.processors` thay `structlog.stdlib`)
- Security foundation vững: 401/200/path traversal đều đúng
- Worker đã kết nối Redis, registered tasks đúng, chỉ cần fix queue name

### Điểm cần cải thiện ⚠️
- **BUG-15 là lỗi config đơn giản** (1 dòng) nhưng block toàn bộ core functionality. Recommend PM lead tự smoke test `curl /api/v1/jobs/{id}` sau khi submit pipeline — nếu status mãi là `queued` sau 30s là đã biết lỗi
- BUG-14 (rate limiting): cần implement đầy đủ trước khi production — rate limiting là security feature quan trọng
- **Suggestion cho CI**: thêm một integration test nhỏ: submit job → poll 30s → assert status != "queued"

### Lịch sử tổng hợp bugs:
| Bug | Mô tả | Trạng thái |
|-----|-------|------------|
| BUG-01 đến BUG-09 | Dependencies, auth, Redis, Celery wiring | ✅ Fixed |
| BUG-10 | Empty poetry.lock | ✅ Fixed |
| BUG-11 | openai-whisper PEP 517 | ✅ Fixed |
| BUG-12 | Image 6.37GB (CUDA) | ✅ Fixed → 2.52GB |
| BUG-13 | structlog PrintLogger `.name` | ✅ Fixed |
| BUG-14 | Rate limiting không enforce | 🟡 Cần fix |
| BUG-15 | Celery queue mismatch | 🔴 **Cần fix ngay** |

---

*BA sẵn sàng retest ngay khi PM lead fix BUG-15. Sau khi fix, sẽ test đầy đủ các video processing use cases (UC-01 đến UC-06) và verify end-to-end pipeline.*
