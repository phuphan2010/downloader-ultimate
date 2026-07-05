# UAT Retest Report — Downloader Ultimate (Lần 5)
**Ngày test:** 2026-07-05  
**Tester:** BA (End User perspective)  
**Server:** pphu@192.168.1.200  
**Branch tested:** `main` @ commit `c197263`  
**Kết quả tổng:** ❌ **FAIL — API 500 Internal Server Error trên mọi endpoint do structlog misconfiguration**

---

## TÓM TẮT EXECUTIVE

> BUG-12 đã được fix đúng — image giảm từ 6.37GB xuống **2.52GB** (giảm 60%), containers start thành công lần đầu tiên. Tuy nhiên, sau khi start, toàn bộ API trả về `500 Internal Server Error` do bug cấu hình structlog: `add_logger_name` processor yêu cầu stdlib logger nhưng code dùng `PrintLoggerFactory`. Middleware gọi logger ở mọi request → 100% requests crash.

---

## PHẦN 1 — XÁC NHẬN TIẾN TRIỂN

| Hạng mục | Lần 4 | Lần 5 |
|---------|-------|-------|
| Docker build | ✅ PASS | ✅ PASS |
| Image size | 6.37GB | ✅ **2.52GB (giảm 60%)** |
| Container start | ❌ FAIL (disk) | ✅ **PASS — lần đầu tiên!** |
| BUG-12 (disk space) | ❌ BLOCKED | ✅ **FIXED** |
| API health endpoint | ❌ N/A | ❌ 500 Error |
| API docs (/docs) | ❌ N/A | ❌ 500 Error |
| Bất kỳ endpoint nào | ❌ N/A | ❌ 500 Error |

**Tích cực: Lần đầu tiên containers start được sau 5 vòng test.**

---

## PHẦN 2 — BUG MỚI

---

### 🔴 BUG-13 | BLOCKER | structlog misconfiguration — mọi request trả 500

| Trường | Giá trị |
|--------|---------|
| **Severity** | Blocker |
| **File** | `backend/app/core/logging.py` |
| **Nguyên nhân gốc** | `add_logger_name` processor không tương thích với `PrintLoggerFactory` |
| **Impact** | 100% requests → `500 Internal Server Error` |

**Root cause:**

```python
# backend/app/core/logging.py — cấu hình hiện tại (SAI)
shared_processors = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,   # ← BUG: cần logger.name
    ...
]

structlog.configure(
    ...
    logger_factory=structlog.PrintLoggerFactory(sys.stdout),  # ← tạo PrintLogger
    ...
)
```

**Chuỗi lỗi:**
```
Mọi request → RequestIDMiddleware.dispatch() → logger.info("request_completed", ...)
    → structlog processor chain chạy
    → add_logger_name processor gọi logger.name
    → PrintLogger KHÔNG có attribute .name
    → AttributeError: 'PrintLogger' object has no attribute 'name'
    → 500 Internal Server Error
```

**Stack trace thực tế:**
```
File "/app/app/core/middleware.py", line 30, in dispatch
    logger.info("request_completed", status_code=..., duration_ms=...)
File "/usr/local/lib/python3.11/site-packages/structlog/stdlib.py", line 805, in add_logger_name
    event_dict["logger"] = logger.name
AttributeError: 'PrintLogger' object has no attribute 'name'
```

---

**Fix cho PM lead — chọn 1 trong 2 options:**

---

**Option A — Quickest fix (2 phút):** Xóa `add_logger_name` khỏi shared_processors

```python
# backend/app/core/logging.py
shared_processors = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    # structlog.stdlib.add_logger_name,  ← XÓA dòng này
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
]
```

**Kết quả:** Logger name sẽ không xuất hiện trong log output, nhưng app hoạt động bình thường.

---

**Option B — Proper fix (10 phút):** Thay `PrintLoggerFactory` bằng stdlib logger factory

```python
# backend/app/core/logging.py
structlog.configure(
    processors=processors,
    wrapper_class=structlog.stdlib.BoundLogger,         # ← thay thế
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),    # ← thay thế
    cache_logger_on_first_use=True,
)
```

Và thêm stdlib logger handler:
```python
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
)
```

**Kết quả:** Logger name hiển thị đúng trong logs, app hoạt động đầy đủ.

---

## PHẦN 3 — UAT TEST CASES SUMMARY

| # | Test Case | Lần 1 | Lần 2 | Lần 3 | Lần 4 | Lần 5 | Ghi chú |
|---|-----------|-------|-------|-------|-------|-------|---------|
| UC-01 | Download TikTok | ❌ | ❌ | ❌ | ❌ | ❌ BLOCKED | API 500 |
| UC-02 | Download Douyin | ❌ | ❌ | ❌ | ❌ | ❌ BLOCKED | API 500 |
| UC-03 | Subtitle tiếng Việt | ❌ | ❌ | ❌ | ❌ | ❌ BLOCKED | API 500 |
| UC-04 | Lồng tiếng | ❌ | ❌ | ❌ | ❌ | ❌ BLOCKED | API 500 |
| UC-05 | Logo overlay | ❌ | ❌ | ❌ | ❌ | ❌ BLOCKED | API 500 |
| UC-06 | n8n Integration | ❌ | ❌ | ❌ | ❌ | ❌ BLOCKED | API 500 |
| UC-07 | Security check | ❌ | ❌ | ❌ | ❌ | ❌ BLOCKED | API 500 |

**0/7 test cases pass (lần 5).**

---

## PHẦN 4 — PRIORITY FIX LIST cho PM Lead (Lần 5)

| Priority | Bug ID | File | Fix | Thời gian |
|----------|--------|------|-----|-----------|
| **P0** | BUG-13 | `backend/app/core/logging.py` | Option A hoặc B ở trên | 2–10 phút |

---

## PHẦN 5 — NHẬN XÉT

### Điểm tích cực ✅
- **BUG-12 fix xuất sắc** — `faster-whisper` thay `openai-whisper` đúng hướng, image 6.37GB → 2.52GB (giảm 60%), container start thành công lần đầu tiên sau 5 vòng
- PM lead phản hồi nhanh và chọn Option A (khuyến nghị của BA) cho BUG-12
- Từ đây chỉ còn 1 bug nhỏ (2-10 phút fix) để unblock toàn bộ UAT

### Điểm cần cải thiện ⚠️
- **Test `curl http://localhost:PORT/health` trước khi báo cáo BA** — lần này containers start nhưng API hoàn toàn broken. PM lead nên test cả end-to-end trên staging trước khi giao BA
- BUG-13 là lỗi cơ bản — structlog docs rõ ràng: `add_logger_name` chỉ dùng với stdlib-backed loggers. Cần review kỹ hơn khi configure logging stack
- Recommend: thêm smoke test đơn giản vào CI: `curl /health` sau khi `docker compose up` trong pipeline

### Lịch sử bugs theo vòng:
| Vòng | Bug chặn | Đã fix |
|------|---------|--------|
| 1 | BUG-01 đến BUG-09 | ✅ |
| 2 | Security (BUG-03, BUG-07, BUG-08) | ✅ |
| 3 | BUG-10 (empty poetry.lock) | ✅ |
| 4 | BUG-11 (PEP 517), BUG-12 (disk) | BUG-11 ✅, BUG-12 ❌→ |
| 5 | BUG-12 (disk) | ✅ — BUG-13 mới |
| **6** | **BUG-13 (structlog)** | **Cần fix** |

---

*BA sẵn sàng retest ngay khi PM lead fix BUG-13 (chỉ cần 1 dòng xóa hoặc sửa trong logging.py). Lần 6 nếu qua được health check, sẽ test đầy đủ 7 UAT cases.*
