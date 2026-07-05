# UAT Retest Report — Downloader Ultimate (Lần 11)
**Ngày test:** 2026-07-05  
**Tester:** BA (End User perspective)  
**Server:** pphu@192.168.1.200  
**Branch tested:** `main` @ commit `ef5d943`  
**Kết quả tổng:** ❌ **FAIL — BUG-21 fixed nhưng phát sinh BUG-22 (cookies read-only), BUG-17C (endpoint sai), BUG-18 (TikTok IP block) vẫn open**

---

## TÓM TẮT EXECUTIVE

> PM lead đã fix BUG-21 (ImpersonateTarget) đúng — TikTok và Douyin giờ vượt qua được init và thực sự attempt download. **BUG-21 CONFIRMED FIXED.** Tuy nhiên, có 2 vấn đề mới lộ ra:
> 1. **BUG-22** — cookies file mount `:ro` (read-only) khiến yt-dlp fail khi cần ghi lại cookies sau khi nhận Set-Cookie từ server. Error: `[Errno 30] Read-only file system`.
> 2. **BUG-17C** vẫn open — Douyin API fallback trigger được (mạng reach được) nhưng endpoint `/api/download` trả HTTP 404 trên `api_auth_proxy`.
>
> Sau khi BA workaround BUG-22 (tháo `:ro` trong test environment), UC-01 TikTok tiến đến đúng error "IP blocked" (BUG-18 confirmed), UC-02 Douyin fallback trigger và reach `api_auth_proxy` nhưng 404.

---

## PHẦN 1 — XÁC NHẬN TIẾN TRIỂN

| Hạng mục | Lần 10 | Lần 11 |
|---------|--------|--------|
| BUG-21 AssertionError | 🔴 **BLOCKER** | ✅ **FIXED — ImpersonateTarget hoạt động** |
| BUG-17 network (localhost) | ❌ connection refused | ✅ **FIXED — reach được 192.168.1.200:8000** |
| BUG-17 API key header | ❌ thiếu | ✅ **FIXED — X-API-Key được truyền** |
| BUG-17C endpoint `/api/download` | ❌ unverified | ❌ **HTTP 404 confirmed** |
| TikTok error message | `AssertionError` | ✅ **"IP blocked" — đúng lỗi thực** |
| Douyin fallback trigger | ❌ không trigger | ✅ **trigger và reach api_auth_proxy** |
| BUG-22 cookies read-only | (không test) | 🔴 **Mới phát sinh** |

---

## PHẦN 2 — ĐÁNH GIÁ BUGS TRƯỚC

---

### ✅ BUG-21 — CONFIRMED FIXED | ImpersonateTarget object đúng type

PM lead fix đúng:

```python
# try/except import với fallback graceful:
try:
    from yt_dlp.networking.impersonate import ImpersonateTarget
    IMPERSONATE_CHROME = ImpersonateTarget("chrome")
except Exception:
    IMPERSONATE_CHROME = "chrome"

# Trong ydl_opts:
"impersonate": IMPERSONATE_CHROME,  # ✅ object, không phải string
```

**Xác nhận trong container:**
```
docker exec downloader-worker python3 -c "from yt_dlp.networking.impersonate import ImpersonateTarget; print(ImpersonateTarget('chrome'))"
# → chrome  ✅ (không còn AssertionError)
```

**Kết quả thực tế:** TikTok job giờ vượt qua init, giải JS challenge, reach đến "IP blocked" error (BUG-18). Douyin job giờ vượt qua init, reach đến "Fresh cookies needed", trigger fallback.

---

### ✅ BUG-17 Sub-issue 1 & 2 — FIXED | Network reach + API key header

**Sub-issue 1 — `localhost:8000` → `192.168.1.200:8000`:**

Worker logs xác nhận fallback reach được `api_auth_proxy`:
```
[info] attempting_douyin_api_service_fallback  job_id=664b9c46...
[warning] douyin_fallback_failed  error=Douyin API service returned HTTP 404
```
Trước đây: `All connection attempts failed` (connection refused). Giờ: HTTP 404 (server trả lời) → network fixed ✅

**Sub-issue 2 — `DOUYIN_API_KEY` env var được inject:**

Xác nhận trong container:
```
docker exec downloader-worker env | grep DOUYIN_API_KEY
# → DOUYIN_API_KEY=***REDACTED*** (có giá trị, không rỗng)
```

Code pass header đúng:
```python
headers = {}
if settings.DOUYIN_API_KEY:
    headers["X-API-Key"] = settings.DOUYIN_API_KEY
```

---

### ❌ BUG-17C — STILL OPEN | Endpoint `/api/download` trả HTTP 404

Worker log:
```
[warning] douyin_fallback_failed  error=Douyin API service returned HTTP 404
```

`api_auth_proxy` tại `192.168.1.200:8000` không có route `/api/download`. Đã verify ở lần 10: OpenAPI spec của `api_auth_proxy` chỉ có các admin/key management endpoints.

**Fix cần làm:**
PM lead cần xác nhận với owner `api_auth_proxy` đúng endpoint để proxy đến `douyin_tiktok_api`. Sau đó cập nhật:
```python
# backend/app/services/downloader.py
api_endpoint = f"{settings.DOUYIN_API_SERVICE_URL.rstrip('/')}/???/download"
# Thay ??? bằng đúng path prefix
```

---

### 🔴 BUG-18 — STILL OPEN | TikTok IP block

Sau khi BUG-21 fixed, TikTok đạt đến lỗi thực:
```
"error": "Download failed after 3 attempts: ERROR: [TikTok] 7137444654301729029: Your IP address is blocked from accessing this post"
```

BUG-18 là IP-level block, không thể fix bằng code — cần:
- Residential/datacenter proxy qua `PROXY_URL`
- Hoặc valid TikTok session cookies (`--cookies-from-browser chrome`)

---

## PHẦN 3 — BUG MỚI

---

### 🔴 BUG-22 | High | cookies file mounted `:ro` — yt-dlp không thể write cookies

| Trường | Giá trị |
|--------|---------|
| **Severity** | High (blocks download khi cookies file mount `:ro`) |
| **File** | `docker-compose.yml` / `docker-compose.override.yml` documentation |
| **Impact** | 100% download jobs fail với error `Read-only file system` khi cookies được mount `:ro` |

**Lỗi thực tế (lần test đầu lần 11):**
```json
"error": "Download failed after 3 attempts: [Errno 30] Read-only file system: '/app/cookies/cookies.txt'"
```

**Root cause:**

yt-dlp không chỉ ĐỌC cookies — nó còn GHI LẠI cookies mới nhận được từ `Set-Cookie` header của server vào file. Nếu file được mount `:ro`, yt-dlp fail ngay khi cố ghi.

BA workaround: tháo `:ro` trong test environment để tiếp tục test. Nhưng đây là vấn đề PM lead phải xử lý cho production deployment.

**Fix cho PM lead (chọn 1 trong 2):**

**Option A — Khuyến nghị: dùng named volume cho cookies**
```yaml
# docker-compose.yml
services:
  worker:
    volumes:
      - job_data:/data/jobs
      - cookie_data:/app/cookies   # ← named volume, read-write

volumes:
  cookie_data:
    driver: local
```
Sau đó cung cấp cơ chế để user upload/seed cookies vào volume (API endpoint hoặc script).

**Option B: copy cookies file sang temp path trước khi dùng**
```python
# backend/app/services/downloader.py
import tempfile, shutil

if cookie_file:
    # Copy sang writable temp file vì yt-dlp cần write
    tmp_cookie = Path(tempfile.mktemp(suffix=".txt"))
    shutil.copy2(cookie_file, tmp_cookie)
    ydl_opts["cookiefile"] = str(tmp_cookie)
    # cleanup sau khi download xong
```

Option B không cần đổi deploy config, fix ngay trong code.

---

### ⚠️ BUG-23 | Medium | docker-compose.yml port `8000:8000` conflict với `api_auth_proxy`

| Trường | Giá trị |
|--------|---------|
| **Severity** | Medium (deployment blocker trên server này) |
| **File** | `docker-compose.yml` |
| **Impact** | Container `downloader-api` không thể start nếu `api_auth_proxy` đang chạy trên port 8000 |

`api_auth_proxy` đang chiếm `0.0.0.0:8000` trên host. `docker-compose.yml` map `"8000:8000"` → conflict, container không start.

Verify:
```
Error response from daemon: Bind for 0.0.0.0:8000 failed: port is already allocated
```

BA workaround cho test: đổi sang `"8001:8000"` trong `docker-compose.yml`.

**Fix cho PM lead:**

```yaml
# docker-compose.yml
services:
  api:
    ports:
      - "8001:8000"   # ← đổi host port sang 8001 (hoặc configurable qua env var)
```

Hoặc linh hoạt hơn:
```yaml
ports:
  - "${API_HOST_PORT:-8001}:8000"
```

---

## PHẦN 4 — UAT TEST CASES SUMMARY (Lần 11)

| # | Test Case | Lần 10 | Lần 11 | Ghi chú |
|---|-----------|--------|--------|---------|
| UC-07a | 401 không có key | ✅ | ✅ PASS | |
| UC-07b | 401 key sai | ✅ | ✅ PASS | |
| UC-07c | 200 key đúng | ✅ | ✅ PASS | |
| UC-07d | Path traversal | ✅ | ✅ PASS | |
| UC-07e | Rate limit 429 | ✅ | ✅ PASS | 429 tại request 11 đúng (key limit=10) |
| UC-06 | n8n Integration | ✅ | ✅ PASS | webhook fires; 404 từ n8n là webhook không active |
| UC-08 | Web UI tại `/` | ✅ | ✅ PASS | 200 OK HTML |
| UC-01 | Download TikTok | ❌ BUG-21 | ❌ **FAIL** | **BUG-18** — IP blocked (progress: không còn AssertionError) |
| UC-02 | Download Douyin | ❌ BUG-21 | ❌ **FAIL** | Cookies stale + **BUG-17C** endpoint 404 |
| UC-03 | Subtitle tiếng Việt | ❌ BLOCKED | ❌ BLOCKED | Phụ thuộc UC-01/02 |
| UC-04 | Lồng tiếng | ❌ BLOCKED | ❌ BLOCKED | Phụ thuộc UC-01/02 |
| UC-05 | Logo overlay | ❌ BLOCKED | ❌ BLOCKED | Phụ thuộc UC-01/02 |

**8/11 pass (không đổi về count, nhưng quality cải thiện: BUG-21 fixed, Douyin fallback giờ trigger được)**

---

## PHẦN 5 — PRIORITY FIX LIST cho PM Lead (Lần 11)

| Priority | Bug ID | File | Fix | Độ khó | Thời gian |
|----------|--------|------|-----|--------|-----------|
| **P0** | **BUG-17C** | `downloader.py` | Xác nhận đúng endpoint `/???/download` với owner `api_auth_proxy`; update code | Trung bình | 15 phút + confirm |
| **P0** | **BUG-22** | `downloader.py` | Thêm logic copy cookies sang temp file trước khi truyền cho yt-dlp (Option B) | Thấp | 10 phút |
| **P0** | **BUG-18** | `docker-compose.override.yml` | Thêm `PROXY_URL` hoặc TikTok session cookies | Trung bình | tùy proxy |
| **P1** | **BUG-23** | `docker-compose.yml` | Đổi host port `8000→8001` tránh conflict | Thấp | 2 phút |

---

## PHẦN 6 — NHẬN XÉT TỔNG

### Điểm tích cực ✅
- **BUG-21 fix chất lượng cao** — try/except với graceful fallback, không crash nếu import fail
- **BUG-17 Sub-issue 1 & 2 fixed** — Douyin fallback giờ reach được `api_auth_proxy` và gửi API key đúng
- **DOUYIN_API_KEY inject vào container** thành công qua `docker-compose.override.yml` + `.env`
- Không có regression trên 8 test cases đang pass

### Điểm cần cải thiện ⚠️
- **BUG-22 (cookies read-only)** — yt-dlp cần write cookies là behavior đã biết từ yt-dlp docs. PM lead nên handle trước khi deploy, không để user tự phát hiện.
- **BUG-17C endpoint** — PM lead nên liên hệ owner `api_auth_proxy` để xác nhận đúng endpoint TRƯỚC khi code, không code rồi để test fail mới phát hiện.
- **BUG-23 port conflict** — cần test deploy trên cùng môi trường với user trước khi submit.

### Lịch sử tổng hợp bugs:
| Bug | Mô tả | Trạng thái |
|-----|-------|------------|
| BUG-01 đến BUG-16 | Dependencies, auth, Redis, Celery, yt-dlp version | ✅ Fixed |
| BUG-17 sub-1 & 2 | Douyin fallback: network + API key | ✅ Fixed |
| BUG-17C | Douyin API endpoint `/api/download` → HTTP 404 | 🔴 Still Open |
| BUG-18 | TikTok IP block | 🟡 Open (cần proxy/cookies) |
| BUG-19 | Web UI | ✅ Fixed |
| BUG-20 | Error message rỗng | ✅ Fixed |
| BUG-21 | `impersonate: "chrome"` sai type | ✅ **Fixed lần 11** |
| **BUG-22** | **cookies file `:ro` → yt-dlp write fail** | 🔴 **Mới — cần fix** |
| **BUG-23** | **docker-compose port 8000 conflict** | 🟠 **Mới — deployment issue** |

---

*BA sẵn sàng retest ngay khi PM lead fix BUG-22 (10 phút) và BUG-17C (verify endpoint). Sau khi 2 bug này fix, UC-02 Douyin có khả năng pass qua API fallback. UC-01 TikTok vẫn cần proxy hoặc cookies.*
