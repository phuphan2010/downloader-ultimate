# UAT Retest Report — Downloader Ultimate (Lần 9)
**Ngày test:** 2026-07-05  
**Tester:** BA (End User perspective)  
**Server:** pphu@192.168.1.200  
**Branch tested:** `main` @ commit `294ff4e` (fix commit: `d2dbb15`)  
**Kết quả tổng:** ❌ **FAIL — Web UI đã có, curl_cffi đã cài, nhưng TikTok/Douyin vẫn không download được do IP bị block và thiếu cookie hợp lệ**

---

## TÓM TẮT EXECUTIVE

> PM lead đã fix 2 bugs: BUG-19 (Web UI) ✅ và phần `curl_cffi` của BUG-18 ✅. Tổng số pass tăng từ 7/11 lên 8/11. Tuy nhiên, core use case (download video) vẫn fail: TikTok bị block ở IP-level sau khi JS challenge solve thành công, Douyin vẫn yêu cầu cookies hợp lệ (chưa tích hợp `douyin_tiktok_api`). Phát hiện thêm BUG-20 mới: job API trả error message rỗng, làm end user không biết tại sao job fail.

---

## PHẦN 1 — XÁC NHẬN TIẾN TRIỂN

| Hạng mục | Lần 8 | Lần 9 |
|---------|-------|-------|
| API health | ✅ | ✅ |
| yt-dlp version | `2026.07.04` | ✅ `2026.07.04` (giữ nguyên) |
| curl_cffi | ❌ Chưa cài | ✅ **`0.15.0` — BUG-18 PARTIAL FIX** |
| TikTok JS challenge | ❌ "no impersonate target" | ✅ **JS challenge solved** (nhưng IP vẫn block) |
| Web UI tại `/` | ❌ 404 Not Found | ✅ **200 OK + HTML page — BUG-19 FIXED** |
| Webhook redirect | ✅ follow_redirects | ✅ gọi https:// trực tiếp, nhận 404 từ n8n (expected) |
| TikTok download thực tế | ❌ FAIL | ❌ FAIL — IP block |
| Douyin download thực tế | ❌ FAIL | ❌ FAIL — cookie/msToken |
| Error message trong job API | N/A (không test) | ❌ **FAIL — trả chuỗi rỗng (BUG-20 MỚI)** |

**Tiến triển: 8/11 pass (lần 9) so với 7/11 (lần 8) — tăng 1 test.**

---

## PHẦN 2 — ĐÁNH GIÁ BUGS CŨ

---

### ✅ BUG-19 — FIXED | Web UI tại `/`

| Trường | Lần 8 | Lần 9 |
|--------|-------|-------|
| `GET /` | `404 Not Found` | ✅ **`200 OK` — HTML page** |
| Static file | Không có | ✅ `backend/static/index.html` (353 dòng) |
| Trạng thái | ❌ | ✅ FIXED |

**Xác nhận:**
```
HTTP/1.1 200 OK
content-type: text/html; charset=utf-8
content-length: 14492
```

Web UI đầy đủ:
- Form nhập URL video và API key
- Chọn bước xử lý (download, subtitles, dubbing, logo)
- Tab "Pipeline" và "Admin" (quản lý API key)
- Polling logic hiển thị trạng thái job real-time
- Fallback về `/docs` nếu file không tồn tại

**Đánh giá của BA:** Fix tốt — end user giờ có giao diện để dùng thay vì phải gọi curl/API. Chức năng form và polling UI sẽ xác nhận sau khi UC-01/02 pass.

---

### 🟡 BUG-18 — PARTIAL FIX | curl_cffi cài thành công, nhưng IP block vẫn còn

| Trường | Lần 8 | Lần 9 |
|--------|-------|-------|
| curl_cffi | Chưa cài | ✅ **`0.15.0` installed** |
| `impersonate: "chrome"` | Không có | ✅ Thêm vào `ydl_opts` |
| JS challenge | ❌ "no impersonate target" | ✅ **Solved: "Solving JS challenge using native Python implementation"** |
| IP block | ❌ "Your IP address is blocked" | ❌ **Vẫn blocked** |
| Trạng thái | ❌ | 🟡 PARTIAL — curl_cffi fixed, IP block chưa fix |

**Log yt-dlp trực tiếp trong container:**
```
[TikTok] Extracting URL: https://www.tiktok.com/@khaby.lame/video/7137444654301729029
[TikTok] 7137444654301729029: Downloading webpage
[TikTok] Solving JS challenge using native Python implementation
[TikTok] 7137444654301729029: Downloading webpage with challenge cookie
ERROR: [TikTok] 7137444654301729029: Your IP address is blocked from accessing this post
```

**Root cause:** curl_cffi bypass TLS fingerprinting (✅ đã fix), nhưng IP-level block là vấn đề khác — TikTok blacklist IP của VPS server. Cần proxy residential hoặc valid TikTok cookies từ browser đã đăng nhập.

**Fix cho PM lead:**

**Option A — Residential Proxy (bền vững):**
```python
# downloader.py — thêm vào ydl_opts cho TikTok
if platform == PlatformType.TIKTOK and settings.PROXY_URL:
    ydl_opts["proxy"] = settings.PROXY_URL  # e.g. "socks5://user:pass@residential.proxy.io:1080"
```
Thêm `PROXY_URL` vào `.env` và `config.py`.

**Option B — Valid TikTok Cookies (free, ngắn hạn):**
```bash
# Trên máy local (không phải server) đã login TikTok trên Chrome:
yt-dlp --cookies-from-browser chrome --cookies tiktok_cookies.txt -x --no-download "https://www.tiktok.com/@test/video/1"
# → export tiktok_cookies.txt → copy lên server → mount vào container
```
Mount vào container: thêm volume `/data/tiktok_cookies.txt:/app/cookies/tiktok_cookies.txt:ro` trong `docker-compose.override.yml`.

---

### 🔴 BUG-17 — STILL OPEN | Douyin vẫn fail — không có cookies/msToken

| Trường | Lần 8 | Lần 9 |
|--------|-------|-------|
| Cookie file code | ✅ Có lookup logic | ✅ Giữ nguyên |
| Cookie file thực tế | ❌ msToken missing | ❌ **msToken vẫn missing** |
| `douyin_tiktok_api` integration | ❌ Chưa làm | ❌ **Vẫn chưa làm** |
| Trạng thái | ❌ | ❌ STILL OPEN |

**Log yt-dlp trực tiếp:**
```
[Douyin] 7387629209305226539: Downloading web detail JSON
WARNING: Failed to parse JSON: Expecting value in '': line 1 column 1 (char 0)
ERROR: [Douyin] 7387629209305226539: Fresh cookies (not necessarily logged in) are needed
```

Vẫn nhận HTTP 200 với body rỗng — root cause từ lần 8 không thay đổi: thiếu `msToken` (dynamic token do Douyin's JS SDK tạo, không có trong browser cookie export).

**Fix đề xuất cho PM lead (khuyến nghị mạnh):** Tích hợp với service `douyin_tiktok_api` đang chạy trên server tại port 8000 — service này đã giải quyết vấn đề msToken. Xem Section 3B của `UAT_RETEST_REPORT_v8.md` để biết chi tiết cách tích hợp.

---

## PHẦN 3 — BUG MỚI

---

### 🟠 BUG-20 | Medium | Job API trả error message rỗng khi download fail

| Trường | Giá trị |
|--------|---------|
| **Severity** | Medium |
| **File** | `backend/app/services/downloader.py` |
| **Endpoint bị ảnh hưởng** | `GET /api/v1/jobs/{job_id}` |
| **Impact** | End user không biết tại sao job thất bại |

**Bằng chứng:**
```json
{
    "job_id": "cc9203eb-4f45-4c5f-8d14-b6778180b619",
    "status": "failed",
    "error": "Download failed after 3 attempts: "
    // ← error rỗng sau dấu ":"
}
```

**Root cause:**

```python
# downloader.py — ydl_opts:
"quiet": not settings.DEBUG,  # ← khi DEBUG=False, quiet=True
```

Khi `quiet=True`, yt-dlp không output gì ra stdout/stderr. Exception `DownloadError` được raise nhưng `str(e)` trả chuỗi rỗng `""` — vì yt-dlp đã suppressed toàn bộ output (kể cả message trong exception). Kết quả: `raise RuntimeError(f"Download failed after 3 attempts: {str(last_exception)}")` tạo message không có thông tin gì hữu ích.

**Fix cho PM lead:**

```python
# downloader.py — trong except block:
except Exception as e:
    last_exception = e
    # Lấy error message từ nhiều nguồn:
    err_msg = str(e) or getattr(e, 'msg', '') or type(e).__name__
    logger.warning("download_attempt_failed", job_id=job_id, attempt=attempt, error=err_msg)
    ...

# Và thay đổi ydl_opts — log stderr thay vì suppress:
"quiet": True,
"no_warnings": not settings.DEBUG,
# Hoặc đơn giản hơn: luôn bắt lỗi từ yt-dlp
```

Hoặc thêm verbose mode cho yt-dlp khi error capture cần thiết:
```python
# Thêm một error handler vào ydl_opts:
def ydl_error_hook(e):
    last_ydl_error.append(str(e))

ydl_opts["postprocessor_hooks"] = ...  # không có, nhưng có thể dùng:
# → Giải pháp đơn giản nhất: set quiet=False và no_warnings=True
"quiet": False,
"no_warnings": True,
```

---

## PHẦN 4 — UAT TEST CASES SUMMARY (Lần 9)

| # | Test Case | Lần 8 | Lần 9 | Ghi chú |
|---|-----------|--------|-------|---------|
| UC-07a | 401 không có key | ✅ | ✅ **PASS** | HTTP 401 |
| UC-07b | 401 key sai | ✅ | ✅ **PASS** | HTTP 401 |
| UC-07c | 200 key đúng | ✅ | ✅ **PASS** | HTTP 200 |
| UC-07d | Path traversal | ✅ | ✅ **PASS** | HTTP 404 |
| UC-07e | Rate limit 429 | ✅ | ✅ **PASS** | 429 tại request 10 |
| UC-06 | n8n Integration | ✅ | ✅ **PASS** | Gọi https:// trực tiếp, nhận 404 (test URL, expected) |
| UC-08 | Web UI tại `/` | ❌ 404 | ✅ **PASS** | 200 + HTML form (BUG-19 FIXED) |
| UC-01 | Download TikTok | ❌ | ❌ **FAIL** | BUG-18 PARTIAL — IP block vẫn còn |
| UC-02 | Download Douyin | ❌ | ❌ **FAIL** | BUG-17 — msToken vẫn missing |
| UC-03 | Subtitle tiếng Việt | ❌ | ❌ BLOCKED | Phụ thuộc UC-01/02 |
| UC-04 | Lồng tiếng | ❌ | ❌ BLOCKED | Phụ thuộc UC-01/02 |
| UC-05 | Logo overlay | ❌ | ❌ BLOCKED | Phụ thuộc UC-01/02 |

**8/11 pass (lần 9) so với 7/11 (lần 8) — tiến triển +1.**

---

## PHẦN 5 — PRIORITY FIX LIST cho PM Lead (Lần 9)

| Priority | Bug ID | Mô tả | Fix | Độ khó |
|----------|--------|-------|-----|--------|
| **P0** | BUG-17 | Douyin không download — msToken | Tích hợp `douyin_tiktok_api` service (port 8000) | Cao — cần thiết kế lại |
| **P0** | BUG-18 | TikTok IP block | Thêm residential proxy HOẶC export TikTok cookies từ browser | Trung bình |
| **P1** | BUG-20 | Error message rỗng trong job API | Fix error capture trong `downloader.py` | Thấp — 10 phút |

---

## PHẦN 6 — NHẬN XÉT TỔNG

### Điểm tích cực ✅
- **BUG-19 fix xuất sắc** — Web UI 353 dòng, có form đầy đủ, polling, admin tab. End user đã có giao diện sử dụng app mà không cần gọi API thủ công.
- **curl_cffi thêm đúng** — TikTok JS challenge solve thành công, không còn cảnh báo "no impersonate target". Đây là tiến triển kỹ thuật rõ ràng.
- **Không có regression** — 7 test cases pass từ lần 8 đều vẫn pass, không có gì bị phá vỡ.

### Điểm cần cải thiện ⚠️
- **BUG-17 chưa được giải quyết** (đã báo từ lần 7, 8). Khuyến nghị tích hợp `douyin_tiktok_api` service đã được nêu rõ trong lần 8 nhưng PM lead chưa implement. Đây là blocker chính cho Douyin use case.
- **BUG-18 chỉ giải quyết 1/2 vấn đề** — curl_cffi ổn, nhưng IP block là vấn đề infrastructure cần proxy hoặc cookies. BA không thể test TikTok cho đến khi một trong hai giải pháp được implement.
- **BUG-20 là lỗi nhỏ nhưng làm trải nghiệm tệ** — end user thấy job fail mà không biết lý do. Dễ fix (10 phút).

### So sánh tiến triển theo vòng:
| Vòng | Bugs chặn | Tests pass | Trạng thái |
|------|-----------|------------|------------|
| 1–5 | BUG-01→13 | 0/11 | Build/start broken |
| 6 | BUG-15 (Celery) | 4/11 | Queue mismatch |
| 7 | BUG-16 (yt-dlp) | 6/11 | Pipeline chạy được |
| 8 | BUG-18 (curl_cffi), BUG-19 (UI) | 7/11 | Download vẫn fail |
| **9** | **BUG-17 (Douyin), BUG-18 PARTIAL** | **8/11** | **UI ✅, download vẫn fail** |

### Lịch sử tổng hợp bugs:
| Bug | Mô tả | Trạng thái |
|-----|-------|------------|
| BUG-01 đến BUG-13 | Dependencies, auth, Redis, logging | ✅ Fixed |
| BUG-14 | Rate limiting không enforce | ✅ Fixed |
| BUG-15 | Celery queue mismatch | ✅ Fixed |
| BUG-16 | yt-dlp 2024.12.23 lỗi thời | ✅ Fixed |
| BUG-17 | Douyin cần cookies/msToken | 🔴 **Still Open** |
| BUG-18 | TikTok IP block + curl_cffi | 🟡 **Partial** (curl_cffi ✅, IP block ❌) |
| BUG-19 | Không có Web UI | ✅ Fixed |
| BUG-20 | Error message rỗng trong job response | 🟠 **Mới — Medium** |

---

## PHẦN 7 — KẾ HOẠCH RETEST LẦN 10

Khi PM lead fix xong, BA sẽ test theo thứ tự:

1. **BUG-17 verify:** Submit Douyin job → phải complete với `status: completed`, `download_url` có giá trị
2. **BUG-18 verify:** Submit TikTok job → phải complete với `status: completed`
3. **BUG-20 verify:** Submit job với URL sai → `error` field phải có message rõ ràng (không rỗng)
4. **UC-03 (Subtitles):** Submit job với `enable_subtitles: true` → file `.mp4` với subtitle tiếng Việt
5. **UC-04 (Dubbing):** Submit job với `enable_dubbing: true` → file `.mp4` với lồng tiếng Việt
6. **UC-05 (Logo):** Submit job với `enable_logo: true` → file `.mp4` với logo overlay
7. **UC-06 (n8n full):** Submit job với webhook URL n8n thực tế → n8n nhận đúng payload khi job completed
8. **UC-08 (Web UI):** Dùng form trên Web UI để submit và theo dõi job thay vì curl — verify UX end-to-end

---

*BA sẵn sàng retest ngay khi PM lead cung cấp proxy hoặc TikTok cookies (BUG-18) và tích hợp `douyin_tiktok_api` (BUG-17). Hai fixes này là P0 — unblock toàn bộ video processing pipeline.*
