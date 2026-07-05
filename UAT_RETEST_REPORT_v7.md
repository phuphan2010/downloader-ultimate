# UAT Retest Report — Downloader Ultimate (Lần 7)
**Ngày test:** 2026-07-05  
**Tester:** BA (End User perspective)  
**Server:** pphu@192.168.1.200  
**Branch tested:** `main` @ commit `7ac89e1`  
**Kết quả tổng:** ❌ **FAIL — yt-dlp 2024.12.23 quá cũ (lỗi thời ~18 tháng), không download được TikTok/Douyin**

---

## TÓM TẮT EXECUTIVE

> BUG-14 (rate limit) và BUG-15 (Celery queue) đã fix đúng. Lần đầu tiên toàn bộ pipeline từ đầu đến cuối chạy được: API nhận request → Celery worker pick up task → xử lý → trả kết quả → gọi webhook. Tuy nhiên, bước download thất bại vì yt-dlp version 2024.12.23 đã lỗi thời 18 tháng, TikTok extractor không còn hoạt động. Douyin yêu cầu cookies xác thực. Core infrastructure đã hoạt động đúng — chỉ còn yt-dlp và Douyin cookies cần fix.

---

## PHẦN 1 — XÁC NHẬN TIẾN TRIỂN

| Hạng mục | Lần 6 | Lần 7 |
|---------|-------|-------|
| API health | ✅ | ✅ |
| Rate limiting (BUG-14) | ❌ FAIL | ✅ **PASS** — 429 sau request 11 |
| Celery queue dispatch (BUG-15) | ❌ FAIL | ✅ **PASS** — worker nhận task ngay |
| Full pipeline flow hoạt động | ❌ N/A | ✅ **PASS** — end-to-end flow chạy được |
| Webhook dispatch | ❌ N/A | ✅ **PASS** — POST gửi đến n8n |
| TikTok download | ❌ N/A | ❌ FAIL — yt-dlp extractor lỗi thời |
| Douyin download | ❌ N/A | ❌ FAIL — cần cookies |

---

## PHẦN 2 — BUGS MỚI

---

### 🔴 BUG-16 | BLOCKER | yt-dlp version 2024.12.23 lỗi thời — TikTok extractor broken

| Trường | Giá trị |
|--------|---------|
| **Severity** | Blocker |
| **File** | `backend/pyproject.toml` |
| **Version hiện tại** | `2024.12.23` (pin cứng từ tháng 12/2024) |
| **Impact** | 100% TikTok downloads fail |

**Error thực tế:**
```
ERROR: [TikTok] 7137444654301729029: Unable to extract webpage video data;
please report this issue on https://github.com/yt-dlp/yt-dlp/issues
Confirm you are on the latest version using yt-dlp -U
```

yt-dlp message chính là "hãy cập nhật lên version mới nhất" — lỗi này do TikTok thay đổi API/webpage structure, yt-dlp 2024.12.23 chưa có extractor fix tương ứng. Cần cập nhật lên yt-dlp 2026.x.x.

**Verify trực tiếp:**
```bash
docker exec downloader-worker yt-dlp --version
# → 2024.12.23  (current July 2026: phải là 2026.x.x)
```

---

**Fix cho PM lead:**

**Option A — Khuyến nghị (5 phút):** Cập nhật constraint trong `pyproject.toml`

```toml
# backend/pyproject.toml — thay:
yt-dlp = "^2024.5.27"

# bằng:
yt-dlp = ">=2026.1.1"
```

Sau đó chạy `poetry update yt-dlp && poetry lock` và rebuild image.

**Option B (thêm vào Dockerfile, không cần rebuild toàn bộ):** Upgrade yt-dlp sau khi poetry install

```dockerfile
# backend/Dockerfile — thêm sau poetry install:
RUN pip install -U yt-dlp
```

---

### 🟠 BUG-17 | High | Douyin yêu cầu cookies — không được cấu hình

| Trường | Giá trị |
|--------|---------|
| **Severity** | High (không phải blocker cho TikTok, nhưng blocker cho Douyin use case) |
| **File** | `backend/app/services/downloader.py` (hoặc yt-dlp options) |
| **Impact** | 100% Douyin downloads fail |

**Error thực tế:**
```
ERROR: [Douyin] 7387629209305226539: Fresh cookies (not necessarily logged in) are needed
```

Douyin yêu cầu cookies hợp lệ (dù không cần login) để tránh bot detection. Hiện tại yt-dlp options không truyền cookies.

**Fix cho PM lead (chọn 1):**

**Option A:** Thêm cookies file mount vào Docker container và truyền vào yt-dlp:
```python
# downloader.py
ydl_opts = {
    ...
    "cookiefile": "/app/cookies/douyin_cookies.txt",
}
```

**Option B:** Dùng `--cookies-from-browser` khi crawl thủ công và lưu file cookies vào Docker volume.

**Option C (tạm thời):** Document rõ Douyin yêu cầu cookies — user phải cung cấp cookies file qua API hoặc config.

---

## PHẦN 3 — UAT TEST CASES SUMMARY

| # | Test Case | Kết quả | Ghi chú |
|---|-----------|---------|---------|
| UC-07a | 401 không có key | ✅ **PASS** | HTTP 401 |
| UC-07b | 401 key sai | ✅ **PASS** | HTTP 401 |
| UC-07c | 200 key đúng | ✅ **PASS** | HTTP 200 |
| UC-07d | Path traversal | ✅ **PASS** | HTTP 404 |
| UC-07e | Rate limit 429 | ✅ **PASS** | 429 tại request 11 đúng như config 10/phút |
| UC-01 | Download TikTok | ❌ **FAIL** | BUG-16 — yt-dlp 2024.12.23 extractor broken |
| UC-02 | Download Douyin | ❌ **FAIL** | BUG-17 — cần cookies |
| UC-03 | Subtitle tiếng Việt | ❌ BLOCKED | Phụ thuộc UC-01/02 |
| UC-04 | Lồng tiếng | ❌ BLOCKED | Phụ thuộc UC-01/02 |
| UC-05 | Logo overlay | ❌ BLOCKED | Phụ thuộc UC-01/02 |
| UC-06 | n8n Integration | ✅ **PASS** | webhook_registered=true, POST gửi đến n8n, nhận 301 (http→https redirect — bình thường) |

**6/11 pass (tất cả security + n8n mechanism), 0/6 video processing pass (blocked bởi BUG-16/17).**

---

## PHẦN 4 — PRIORITY FIX LIST cho PM Lead (Lần 7)

| Priority | Bug ID | File | Fix | Thời gian |
|----------|--------|------|-----|-----------|
| **P0** | BUG-16 | `backend/pyproject.toml` | Upgrade yt-dlp `>=2026.1.1` | 5–10 phút |
| **P1** | BUG-17 | `backend/app/services/downloader.py` | Thêm cookies support cho Douyin | 30–60 phút |

---

## PHẦN 5 — CHI TIẾT UC-06 n8n INTEGRATION

```
Kết quả test:
1. POST /api/v1/pipeline với webhook_url → webhook_registered: true ✅
2. Worker xử lý job, gọi webhook sau khi complete/fail ✅
3. HTTP POST đến http://n8n.tinydevops.io.vn/webhook/test-uat
4. n8n trả về 301 Moved Permanently (http → https redirect)
5. Worker retry 3 lần → tất cả đều 301

Nhận xét: Cơ chế webhook đúng. 301 là do dùng http:// thay https://
Để test n8n đầy đủ: cần TikTok/Douyin download thành công trước (BUG-16/17 phải fix).
```

---

## PHẦN 6 — NHẬN XÉT TỔNG

### Điểm tích cực ✅
- **Infrastructure hoàn chỉnh lần đầu tiên** — toàn bộ pipeline từ API → Celery → Worker → Redis → Webhook đều hoạt động đúng
- BUG-14 (rate limit) và BUG-15 (Celery queue) fix hoàn hảo
- Security layer solid: auth, rate limit, path traversal đều pass
- n8n webhook mechanism đúng thiết kế
- Error handling đúng: job trả `status: failed` với error message rõ ràng thay vì crash

### Điểm cần cải thiện ⚠️
- **yt-dlp version quản lý:** Không nên dùng date-versioned constraint cứng (`^2024.5.27`) cho package luôn cần update như yt-dlp. Recommend `>=2026.1.1` hoặc dùng `pip install -U yt-dlp` trong Dockerfile
- **Douyin cookies:** Đây là known limitation cần document rõ trong README — Douyin yêu cầu cookies để tránh bot detection
- **Test URL trong CI:** Cần dùng video URL thực tế đã xác nhận accessible, không phải URL ngẫu nhiên

### Lịch sử tổng hợp bugs:
| Bug | Mô tả | Trạng thái |
|-----|-------|------------|
| BUG-01 đến BUG-13 | Dependencies, auth, Redis, logging, image size | ✅ Fixed |
| BUG-14 | Rate limiting không enforce | ✅ Fixed |
| BUG-15 | Celery queue mismatch | ✅ Fixed |
| BUG-16 | yt-dlp 2024.12.23 lỗi thời | 🔴 Cần fix |
| BUG-17 | Douyin cần cookies | 🟠 Cần fix |

---

*BA sẵn sàng retest ngay khi PM lead fix BUG-16. Sau khi TikTok download hoạt động, sẽ test đầy đủ cả pipeline UC-01 → UC-05 trong một lần.*
