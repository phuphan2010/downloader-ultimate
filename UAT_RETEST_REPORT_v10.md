# UAT Retest Report — Downloader Ultimate (Lần 10)
**Ngày test:** 2026-07-05  
**Tester:** BA (End User perspective)  
**Server:** pphu@192.168.1.200  
**Branch tested:** `main` @ commit `eab24af`  
**Kết quả tổng:** ❌ **FAIL — BUG-21 mới (impersonation string sai type), BUG-17 vẫn open (Douyin API không reach được + thiếu key)**

---

## TÓM TẮT EXECUTIVE

> PM lead đã fix BUG-20 (error message) đúng. Tuy nhiên, việc fix BUG-20 đã lộ ra một bug ẩn: **BUG-21** — `"impersonate": "chrome"` là string, nhưng yt-dlp Python API yêu cầu `ImpersonateTarget` object, gây `AssertionError` ngay khi khởi tạo (trước khi request nào được thực hiện). Toàn bộ TikTok và Douyin fail do bug này. Douyin API fallback cũng fail vì `DOUYIN_API_SERVICE_URL=http://localhost:8000` không reach được từ trong Docker container, và thiếu API key trong request.

---

## PHẦN 1 — XÁC NHẬN TIẾN TRIỂN

| Hạng mục | Lần 9 | Lần 10 |
|---------|-------|--------|
| API health | ✅ | ✅ |
| Web UI tại `/` | ✅ 200 OK (BUG-19 fixed) | ✅ vẫn hoạt động |
| BUG-20 error message | ❌ rỗng `""` | ✅ **`AssertionError` — có message** |
| `impersonate` option | 🔴 **`AssertionError` (ẩn)** | 🔴 **AssertionError lộ ra (BUG-21)** |
| TikTok download | ❌ | ❌ FAIL — BUG-21 |
| Douyin download (yt-dlp) | ❌ | ❌ FAIL — BUG-21 |
| Douyin fallback (API service) | ❌ | ❌ FAIL — BUG-17C (localhost + no key) |

---

## PHẦN 2 — ĐÁNH GIÁ BUGS CŨ

---

### ✅ BUG-20 — FIXED | Error message không còn rỗng

| Trường | Lần 9 | Lần 10 |
|--------|-------|--------|
| Error khi job fail | `"Download failed after 3 attempts: "` | ✅ `"Download failed after 3 attempts: AssertionError"` |
| Trạng thái | ❌ | ✅ FIXED |

PM lead đã sửa:
- `"quiet": False` (bỏ `not settings.DEBUG`)  
- Thêm fallback: `err_str = str(e).strip() or getattr(e, 'msg', '') or type(e).__name__`

Fix đúng — BUG-20 confirmed resolved. Error message giờ luôn có giá trị dù yt-dlp suppress message.

---

### 🔴 BUG-17 — STILL OPEN | Douyin API fallback có 3 vấn đề chưa fix

Fallback code đã được thêm vào nhưng không hoạt động vì 3 lý do:

**Vấn đề 1 — `localhost:8000` không reach được từ trong Docker container:**

```
Worker log: douyin_fallback_failed  error=All connection attempts failed
```

Từ bên trong `downloader-worker` container:
- `http://localhost:8000` → **Connection refused** (container không có service nào ở port 8000)
- `http://192.168.1.200:8000` → **200 OK** (host IP hoạt động)

`localhost` trong Docker container trỏ về chính container đó, không phải host machine.

**Vấn đề 2 — Không có `DOUYIN_API_KEY` trong config.py:**

```python
# config.py — THIẾU setting này:
DOUYIN_API_KEY: str = ""  # ← chưa có
```

`api_auth_proxy` tại port 8000 yêu cầu `X-API-Key` header (401 nếu không có). Code hiện tại:
```python
resp = await client.post(api_endpoint, json={"url": url})
# ← không có header X-API-Key
```

User đã thêm API key cho `api_auth_proxy` vào `.env`, nhưng không có setting nào trong `config.py` để đọc nó, và `docker-compose.override.yml` cũng không truyền biến này vào container.

**Vấn đề 3 — Endpoint `/api/download` không tồn tại trên `api_auth_proxy`:**

```bash
# Đã verify — danh sách paths trên api_auth_proxy:
['/health', '/admin/keys', '/admin/keys/{key}', '/admin/keys/{key}/disable', ...]
# → Không có '/api/download'
```

`api_auth_proxy` là auth gateway — nó proxy requests đến `douyin_tiktok_api` sau khi authenticate. PM lead cần xác nhận đúng endpoint và cách proxy hoạt động.

**Fix cho PM lead (cần làm đủ 3 bước):**

**Bước 1 — Thêm `DOUYIN_API_KEY` vào `config.py`:**
```python
DOUYIN_API_SERVICE_URL: str = "http://192.168.1.200:8000"  # ← Đổi từ localhost
DOUYIN_API_KEY: str = ""  # ← Thêm mới — key lấy từ .env
```

**Bước 2 — Sửa `_download_via_douyin_api` để pass key và dùng đúng endpoint:**
```python
async def _download_via_douyin_api(self, url: str, job_folder: Path) -> Path:
    headers = {}
    if settings.DOUYIN_API_KEY:
        headers["X-API-Key"] = settings.DOUYIN_API_KEY
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        # TODO: PM lead cần verify đúng endpoint với owner của api_auth_proxy
        api_endpoint = f"{settings.DOUYIN_API_SERVICE_URL.rstrip('/')}/???/download"
        resp = await client.post(api_endpoint, json={"url": url})
        ...
```

**Bước 3 — Thêm env vars vào `docker-compose.override.yml`:**
```yaml
services:
  worker:
    environment:
      - DOUYIN_API_SERVICE_URL=http://192.168.1.200:8000
      - DOUYIN_API_KEY=${DOUYIN_API_KEY}  # đọc từ .env
```

---

## PHẦN 3 — BUG MỚI

---

### 🔴 BUG-21 | BLOCKER | `"impersonate": "chrome"` — sai type, gây AssertionError

| Trường | Giá trị |
|--------|---------|
| **Severity** | Blocker |
| **File** | `backend/app/services/downloader.py` |
| **Dòng** | `"impersonate": "chrome"` trong `ydl_opts` |
| **Impact** | 100% TikTok download fail, 100% Douyin yt-dlp fail |

**Root cause:**

yt-dlp Python API yêu cầu `impersonate` option phải là `ImpersonateTarget` object. Truyền string `"chrome"` trực tiếp vào dict gây `AssertionError` tại `YoutubeDL.__init__` trước khi bất kỳ request nào được thực hiện:

```
File "yt_dlp/YoutubeDL.py", line 769, in __init__
    if not self._impersonate_target_available(impersonate_target):
File "yt_dlp/networking/impersonate.py", line 119, in is_supported_target
    assert isinstance(target, ImpersonateTarget)
AssertionError
```

**Lý do bị ẩn ở lần 9:**  
Trước khi BUG-20 được fix, `quiet=True` + `str(e)` trả `""` → error message rỗng → BA nhìn thấy `"Download failed after 3 attempts: "` không biết là `AssertionError`. BUG-20 fix lộ ra bug này.

**Phân biệt quan trọng:**  
CLI (`yt-dlp --impersonate chrome`) tự parse string → `ImpersonateTarget` object. Python API không có auto-parse → phải truyền object thủ công.

**Xác nhận fix đúng:**
```python
# BA đã verify trực tiếp trong container:
from yt_dlp.networking.impersonate import ImpersonateTarget

# Với string → AssertionError
ydl_opts["impersonate"] = "chrome"  # ❌ FAIL

# Với ImpersonateTarget → OK, JS challenge solved
ydl_opts["impersonate"] = ImpersonateTarget("chrome")  # ✅ PASS
```

Log khi dùng `ImpersonateTarget("chrome")`:
```
[TikTok] Extracting URL: ...
[TikTok] Solving JS challenge using native Python implementation
[TikTok] Downloading webpage with challenge cookie
ERROR: Your IP address is blocked from accessing this post  ← đây mới là lỗi thực (BUG-18)
```

**Fix cho PM lead:**

```python
# backend/app/services/downloader.py — đầu file thêm import:
from yt_dlp.networking.impersonate import ImpersonateTarget

# Trong download_video() — thay:
"impersonate": "chrome",                     # ❌ string → AssertionError

# bằng:
"impersonate": ImpersonateTarget("chrome"),  # ✅ object → works
```

---

## PHẦN 4 — UAT TEST CASES SUMMARY (Lần 10)

| # | Test Case | Lần 9 | Lần 10 | Ghi chú |
|---|-----------|--------|--------|---------|
| UC-07a | 401 không có key | ✅ | ✅ PASS | (không retest — đã stable) |
| UC-07b | 401 key sai | ✅ | ✅ PASS | |
| UC-07c | 200 key đúng | ✅ | ✅ PASS | |
| UC-07d | Path traversal | ✅ | ✅ PASS | |
| UC-07e | Rate limit 429 | ✅ | ✅ PASS | |
| UC-06 | n8n Integration | ✅ | ✅ PASS | |
| UC-08 | Web UI tại `/` | ✅ | ✅ PASS | 200 OK HTML |
| UC-01 | Download TikTok | ❌ | ❌ **FAIL** | **BUG-21** — AssertionError |
| UC-02 | Download Douyin | ❌ | ❌ **FAIL** | **BUG-21** (yt-dlp) + **BUG-17** (fallback) |
| UC-03 | Subtitle tiếng Việt | ❌ | ❌ BLOCKED | Phụ thuộc UC-01/02 |
| UC-04 | Lồng tiếng | ❌ | ❌ BLOCKED | Phụ thuộc UC-01/02 |
| UC-05 | Logo overlay | ❌ | ❌ BLOCKED | Phụ thuộc UC-01/02 |

**8/11 pass (không đổi từ lần 9) — BUG-20 fixed nhưng BUG-21 mới block cả TikTok lẫn Douyin.**

---

## PHẦN 5 — PRIORITY FIX LIST cho PM Lead (Lần 10)

| Priority | Bug ID | File | Fix | Độ khó | Thời gian |
|----------|--------|------|-----|--------|-----------|
| **P0** | **BUG-21** | `downloader.py` | Thay `"chrome"` bằng `ImpersonateTarget("chrome")` | Thấp | **5 phút** |
| **P0** | **BUG-17** | `config.py`, `downloader.py`, `docker-compose.override.yml` | 3 bước: đổi URL localhost→IP, thêm DOUYIN_API_KEY setting + header, wire env vào container | Trung bình | 30 phút |
| P0 | **BUG-18** | `docker-compose.override.yml` | Sau khi BUG-21 fix, TikTok sẽ hiện lại "IP blocked" — cần PROXY_URL hoặc TikTok cookies | Trung bình | tùy proxy |

---

## PHẦN 6 — NHẬN XÉT TỔNG

### Điểm tích cực ✅
- **BUG-20 fix đúng hướng** — error capture logic hoạt động, giờ đây error message `AssertionError` đã lộ ra bug ẩn BUG-21 mà lần 9 không thấy được.
- Không có regression trên các test cases đã pass.

### Điểm cần cải thiện ⚠️
- **BUG-21 là lỗi cơ bản** — yt-dlp documentation rõ ràng: Python API yêu cầu `ImpersonateTarget` object, không phải string. PM lead nên kiểm tra yt-dlp usage docs trước khi submit PR.
- **BUG-17 Douyin API fallback chưa hoàn chỉnh** — có 3 vấn đề độc lập cần fix cùng lúc. Suggest PM lead liên hệ owner `api_auth_proxy` để xác nhận đúng endpoint trước khi implement.
- **BUG-18 TikTok** — chưa test được (blocked by BUG-21). Sau khi BUG-21 fix, cần cung cấp proxy URL hoặc TikTok session cookies.

### Timeline:
- BUG-21 là 1-line fix → sau khi fix, TikTok sẽ đạt được stage "IP blocked" và Douyin yt-dlp sẽ đạt "Fresh cookies needed" 
- Douyin fallback cần thêm vài bước nhưng hoàn toàn làm được trong 30 phút
- TikTok (BUG-18) phụ thuộc vào proxy hoặc cookies — cần chuẩn bị từ bên ngoài

### Lịch sử tổng hợp bugs:
| Bug | Mô tả | Trạng thái |
|-----|-------|------------|
| BUG-01 đến BUG-13 | Dependencies, auth, Redis, logging | ✅ Fixed |
| BUG-14 | Rate limiting | ✅ Fixed |
| BUG-15 | Celery queue mismatch | ✅ Fixed |
| BUG-16 | yt-dlp 2024.12.23 lỗi thời | ✅ Fixed |
| BUG-17 | Douyin API fallback | 🔴 Still Open (3 sub-issues) |
| BUG-18 | TikTok IP block | 🟡 Partially blocked by BUG-21 |
| BUG-19 | Không có Web UI | ✅ Fixed |
| BUG-20 | Error message rỗng | ✅ Fixed |
| **BUG-21** | **`impersonate: "chrome"` sai type** | 🔴 **Mới — Blocker** |

---

*BA sẵn sàng retest ngay khi PM lead fix BUG-21 (5 phút). Đây là fix đơn giản nhất từ trước đến nay nhưng có impact lớn nhất — unlock toàn bộ TikTok và Douyin yt-dlp path.*
