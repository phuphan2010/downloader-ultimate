# UAT Retest Report — Downloader Ultimate (Lần 8)
**Ngày test:** 2026-07-05  
**Tester:** BA (End User perspective)  
**Server:** pphu@192.168.1.200  
**Branch tested:** `main` @ commit `19bbda7`  
**Kết quả tổng:** ❌ **FAIL — TikTok/Douyin vẫn không download được: server IP bị block, thiếu curl_cffi, và không có cookie file thực tế**

---

## TÓM TẮT EXECUTIVE

> yt-dlp đã upgrade lên `2026.07.04` (BUG-16 FIX ✅) và webhook redirect đã xử lý đúng (follow_redirects ✅). Tuy nhiên, vẫn chưa download được video: TikTok chặn IP server VPS và yêu cầu impersonation library `curl_cffi` chưa được cài (BUG-18 mới). Douyin: code hỗ trợ cookie file đã thêm vào nhưng không có file cookie thực tế nào được mount vào container (BUG-17 PARTIAL FIX — code có, cookie thì không). Cả hai platform đều cần cookies năm 2026.

---

## PHẦN 1 — XÁC NHẬN TIẾN TRIỂN

| Hạng mục | Lần 7 | Lần 8 |
|---------|-------|-------|
| API health | ✅ | ✅ |
| yt-dlp version | `2024.12.23` (lỗi thời) | ✅ **`2026.07.04` (BUG-16 FIXED)** |
| TikTok extractor error | "Unable to extract webpage video data" | ✅ **Error khác — extractor hoạt động** |
| Webhook redirect http→https | ❌ 301 loop | ✅ **follow_redirects=True — nhận 404 (URL test không tồn tại, expected)** |
| Cookie file support (code) | ❌ Không có | ✅ **Thêm code lookup cookie — nhưng không có file thực tế** |
| TikTok download thực tế | ❌ | ❌ FAIL — IP block + thiếu curl_cffi |
| Douyin download thực tế | ❌ | ❌ FAIL — không có cookie file |

---

## PHẦN 2 — ĐÁNH GIÁ BUGS CŨ

### ✅ BUG-16 — FIXED | yt-dlp upgrade thành công

| Trường | Lần 7 | Lần 8 |
|--------|-------|-------|
| Version | `2024.12.23` | **`2026.07.04`** |
| Extractor error | "Unable to extract webpage video data" | Khác loại (IP block / login required) |
| Trạng thái | ❌ | ✅ FIXED |

**Xác nhận:**
```bash
docker exec downloader-worker yt-dlp --version
# → 2026.07.04
```

Extractor TikTok đã hoạt động — error cũ "Unable to extract webpage video data" không còn xuất hiện. Lỗi mới là IP block và login, khác loại hoàn toàn.

---

### 🟡 BUG-17 — PARTIAL FIX | Cookie code thêm vào nhưng không có file thực tế

| Trường | Lần 7 | Lần 8 |
|--------|-------|-------|
| Code cookie support | ❌ Không có | ✅ Code lookup có (`cookie_candidates` list) |
| Cookie file thực tế | ❌ | ❌ **Không có file nào tại các path được check** |
| Douyin download | ❌ | ❌ Vẫn lỗi "Fresh cookies needed" |
| Trạng thái | ❌ | 🟡 PARTIAL — code có, cookie không |

**Log xác nhận không tìm thấy cookie file:**
```
# Không có log "using_cookie_file" trong worker → cookie_file = None → yt-dlp chạy không có cookies
```

**Douyin error vẫn y hệt lần 7:**
```
ERROR: [Douyin] 7387629209305226539: Fresh cookies (not necessarily logged in) are needed
```

Code đã check các path sau nhưng không tìm thấy file nào:
- `/app/cookies/cookies.txt`
- `/app/cookies/douyin_cookies.txt`
- `/data/cookies.txt`
- `/data/douyin_cookies.txt`

---

## PHẦN 3 — BUGS MỚI

---

### 🔴 BUG-18 | BLOCKER | TikTok chặn server IP + thiếu impersonation library

| Trường | Giá trị |
|--------|---------|
| **Severity** | Blocker |
| **Platforms** | TikTok (Douyin ít bị ảnh hưởng hơn) |
| **Root cause 1** | IP server VPS bị TikTok blacklist |
| **Root cause 2** | `curl_cffi` chưa được cài — yt-dlp không thể impersonate browser |
| **Impact** | 100% TikTok downloads fail |

**Error từ yt-dlp trực tiếp:**
```bash
docker exec downloader-worker yt-dlp --no-download --get-title \
  "https://www.tiktok.com/@khaby.lame/video/7137444654301729029"

WARNING: [TikTok] The extractor is attempting impersonation, but no impersonate 
target is available. If you encounter errors, then see 
https://github.com/yt-dlp/yt-dlp#impersonation for information on installing 
the required dependencies

ERROR: [TikTok] 7137444654301729029: Your IP address is blocked from accessing this post
```

**Phân tích:**
1. TikTok năm 2026 block hầu hết datacenter/VPS IPs — server `192.168.1.200` (hoặc IP public của nó) nằm trong blacklist
2. yt-dlp khi gặp TikTok cần `curl_cffi` để impersonate Chrome/Firefox TLS fingerprint. Thiếu `curl_cffi` → yt-dlp dùng `urllib` thuần → TikTok nhận biết là bot
3. Dù có `curl_cffi`, VPS IP vẫn cần cookies TikTok hợp lệ để tránh block

**Error phụ — URL ngắn TikTok cũng fail:**
```
ERROR: [TikTok] 7463228783789739269: You do not have permission to view this post. 
Log into an account that has access. Use --cookies-from-browser or --cookies
```

---

**Fix cho PM lead — cần cả 2 steps:**

**Step 1 (bắt buộc) — Thêm curl_cffi vào Dockerfile:**
```dockerfile
# backend/Dockerfile — thêm sau dòng "RUN pip install -U yt-dlp":
RUN pip install -U curl_cffi
# hoặc:
RUN pip install "yt-dlp[default]"   # bundle đầy đủ gồm curl_cffi
```

**Step 2 (bắt buộc) — Cung cấp cookies TikTok:**

Cần export cookies từ browser đã login TikTok:
```bash
# Trên máy local (có browser + TikTok login):
yt-dlp --cookies-from-browser chrome --cookies /tmp/tiktok_cookies.txt \
  --skip-download "https://www.tiktok.com/@khaby.lame/video/7137444654301729029"

# Copy lên server:
scp /tmp/tiktok_cookies.txt pphu@192.168.1.200:/data/cookies.txt
```

Sau đó mount vào container trong `docker-compose.yml`:
```yaml
services:
  worker:
    volumes:
      - /data/cookies.txt:/app/cookies/cookies.txt:ro
  api:
    volumes:
      - /data/cookies.txt:/app/cookies/cookies.txt:ro
```

**Lưu ý:** Cookies TikTok có TTL ~30 ngày — cần quy trình refresh định kỳ.

---

## PHẦN 3B — ĐIỀU TRA THÊM: DOUYIN COOKIES TỪ API-PARSER-DOUYIN

Theo thông tin từ PM lead: cookies Douyin có thể tìm tại `/home/pphu/API-Parser-douyin/config.yaml`.

### Kết quả điều tra:

BA đã thử convert cookies từ `config.yaml` sang Netscape format và mount vào container:
```bash
# Đã tạo /data/cookies.txt (61 cookies từ config.yaml)
# Đã mount vào /app/cookies/cookies.txt trong worker và api containers
```

**Kết quả test:**
```
yt-dlp --cookies /app/cookies/cookies.txt --get-title \
  "https://www.douyin.com/video/7387629209305226539"

→ WARNING: [Douyin] Failed to parse JSON: Expecting value in '': line 1 column 1 (char 0)
→ ERROR: Fresh cookies (not necessarily logged in) are needed
```

**Phân tích root cause:**
```bash
# Direct API call test:
curl -b /tmp/cookies.txt "https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=7387629209305226539"
→ HTTP 200, body size: 0 bytes
```

Douyin API trả HTTP 200 nhưng body rỗng → cookies có nhưng **thiếu `msToken`**.  
`msToken` là security token động do Douyin JS SDK tạo ra, KHÔNG có trong Cookie header của browser. Nó cần được generate qua `https://mssdk.bytedance.com/web/report`.

**Phát hiện quan trọng — Existing Service:**

Trên server đã có `douyin_tiktok_api` container chạy liên tục 8 ngày, expose qua `api_auth_proxy` (port 8000). Service này đã giải quyết bài toán msToken. PM lead nên xem xét **tích hợp downloader-ultimate với service này** thay vì gọi Douyin API trực tiếp qua yt-dlp.

---

## PHẦN 3C — BUG MỚI: THIẾU WEB UI

### 🔵 BUG-19 | Medium | Không có Web UI — app chỉ là REST API

| Trường | Giá trị |
|--------|---------|
| **Severity** | Medium |
| **Impact** | End user không thể dùng app qua browser mà không biết dùng API/curl |
| **Test** | `GET http://192.168.1.200:8001/` → `{"detail":"Not Found"}` (404) |

**Xác nhận:**
```bash
curl http://localhost:8001/
→ 404 {"detail":"Not Found"}

# Chỉ có Swagger docs:
curl -o /dev/null -w "%{http_code}" http://localhost:8001/docs
→ 200  (Swagger UI tự động từ FastAPI)
```

App hiện tại chỉ có REST API endpoints (`/api/v1/...`). Không có:
- Trang web để nhập URL video
- Giao diện theo dõi tiến trình job
- Download button cho kết quả

**Yêu cầu từ BA (end user):** Cần có Web UI đơn giản để người dùng có thể:
1. Dán URL TikTok/Douyin vào form
2. Chọn options (chất lượng, subtitle, dubbing, logo)
3. Xem tiến trình realtime
4. Tải file kết quả về

**Fix cho PM lead:**

**Option A (2–4 giờ) — Thêm static HTML frontend:**
```
backend/static/index.html  ← Single-page app với form và polling JS
```
Mount static files trong FastAPI:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

**Option B (nhanh hơn — 30 phút) — Redirect `/` sang `/docs`:**
```python
@app.get("/")
def redirect_to_docs():
    return RedirectResponse(url="/docs")
```
Swagger `/docs` có thể test API nhưng không friendly với end user.

---

## PHẦN 4 — UAT TEST CASES SUMMARY

| # | Test Case | Lần 7 | Lần 8 | Ghi chú |
|---|-----------|-------|-------|---------|
| UC-07a | 401 không có key | ✅ | ✅ **PASS** | HTTP 401 |
| UC-07b | 401 key sai | ✅ | ✅ **PASS** | HTTP 401 |
| UC-07c | 200 key đúng | ✅ | ✅ **PASS** | HTTP 200 |
| UC-07d | Path traversal | ✅ | ✅ **PASS** | HTTP 404 |
| UC-07e | Rate limit 429 | ✅ | ✅ **PASS** | 429 tại request 11 |
| UC-01 | Download TikTok | ❌ BUG-16 | ❌ FAIL | BUG-18 — IP block + thiếu curl_cffi + cần cookies |
| UC-02 | Download Douyin | ❌ BUG-17 | ❌ FAIL | BUG-17 PARTIAL — cần file cookies thực tế |
| UC-03 | Subtitle tiếng Việt | ❌ BLOCKED | ❌ BLOCKED | Phụ thuộc UC-01/02 |
| UC-04 | Lồng tiếng | ❌ BLOCKED | ❌ BLOCKED | Phụ thuộc UC-01/02 |
| UC-05 | Logo overlay | ❌ BLOCKED | ❌ BLOCKED | Phụ thuộc UC-01/02 |
| UC-06 | n8n Integration | ✅ (webhook dispatch) | ✅ **PASS** | follow_redirects=True — nhận 404 đúng (URL test không tồn tại trong n8n) |

**6/12 pass (thêm BUG-19 test), 0/6 video processing pass.**

| UC-08 | Web UI | ❌ **FAIL** | BUG-19 — 404, không có giao diện web |

---

## PHẦN 5 — PRIORITY FIX LIST cho PM Lead (Lần 8)

| Priority | Bug ID | Vấn đề | Fix | Thời gian |
|----------|--------|---------|-----|-----------|
| **P0** | BUG-18 | TikTok IP block + thiếu curl_cffi | Thêm `curl_cffi` vào Dockerfile + cookies mount | 30–60 phút |
| **P0** | BUG-17 | Douyin msToken + cookies | Tích hợp với `douyin_tiktok_api` service đang chạy trên cùng server | 1–2 ngày |
| **P1** | BUG-19 | Không có Web UI | Thêm `static/index.html` + mount StaticFiles trong FastAPI | 2–4 giờ |

**BUG-17 revised:** Không còn đơn giản là "mount cookie file" nữa. Cookies từ config.yaml thiếu `msToken` động. Recommend PM lead **tích hợp với `douyin_tiktok_api` service** (đang hoạt động trên cùng server, port 8000) thay vì cố dùng yt-dlp trực tiếp cho Douyin.

---

## PHẦN 6 — HƯỚNG DẪN CHI TIẾT CHO PM LEAD

### Quy trình lấy cookies (một lần thiết lập):

1. **Trên máy có browser (Windows/Mac):**
   ```bash
   # Bước 1: Login vào cả TikTok và Douyin trên Chrome/Firefox
   
   # Bước 2: Export cookies
   yt-dlp --cookies-from-browser chrome --cookies cookies_tiktok.txt \
     --skip-download "https://www.tiktok.com/@khaby.lame/video/7137444654301729029"
   
   yt-dlp --cookies-from-browser chrome --cookies cookies_douyin.txt \
     --skip-download "https://www.douyin.com/video/7387629209305226539"
   ```

2. **Copy lên server:**
   ```bash
   scp cookies_tiktok.txt pphu@192.168.1.200:/data/cookies.txt
   # (1 file cookies.txt có thể chứa cả TikTok và Douyin nếu đã login cả 2 trên browser)
   ```

3. **Thêm volume mount vào `docker-compose.yml`:**
   ```yaml
   services:
     api:
       volumes:
         - /data/cookies.txt:/app/cookies/cookies.txt:ro
     worker:
       volumes:
         - /data/cookies.txt:/app/cookies/cookies.txt:ro
   ```

4. **Thêm curl_cffi vào `backend/Dockerfile`:**
   ```dockerfile
   RUN pip install -U yt-dlp curl_cffi
   ```

5. **Rebuild và restart:**
   ```bash
   docker compose build --no-cache && docker compose up -d
   ```

---

## PHẦN 7 — NHẬN XÉT TỔNG

### Điểm tích cực ✅
- yt-dlp `2026.07.04` hoạt động đúng — extractor TikTok không còn "Unable to extract"
- Webhook `follow_redirects=True` fix đúng — không còn 301 loop, nhận response thực
- Cookie support code trong `downloader.py` đúng hướng — check nhiều path, log khi tìm thấy
- Infrastructure hoàn chỉnh — API, Celery, Redis, Webhook tất cả OK

### Điểm cần cải thiện ⚠️
- **BUG-17 fix chưa hoàn chỉnh**: Thêm code mà không cung cấp cookies — giống như code mở cửa nhưng không có chìa khóa. PM lead cần cung cấp cookie file thực tế và document quy trình lấy/refresh
- **BUG-18 không được anticipate**: TikTok block VPS IPs là behavior đã biết từ 2023, nên đã nằm trong thiết kế từ đầu. Cần thêm `curl_cffi` vào dependencies từ sớm
- **Không có smoke test**: PM lead nên test `docker exec worker yt-dlp --get-title <real-url>` trước khi báo cáo BA

### Lịch sử tổng hợp bugs:
| Bug | Mô tả | Trạng thái |
|-----|-------|------------|
| BUG-01 đến BUG-15 | Toàn bộ build, auth, Redis, logging, Celery | ✅ Fixed |
| BUG-16 | yt-dlp 2024.12.23 lỗi thời | ✅ **Fixed** — 2026.07.04 |
| BUG-17 | Douyin cookies → msToken động | 🔴 **Cần redesign** — tích hợp douyin_tiktok_api |
| BUG-18 | TikTok IP block + thiếu curl_cffi | 🔴 **Cần fix** |
| BUG-19 | Không có Web UI | 🔵 **Gap mới** — end user không thể dùng qua browser |

---

*BA sẵn sàng retest ngay khi PM lead fix BUG-18 (curl_cffi + TikTok cookies) và BUG-19 (Web UI tối thiểu). BUG-17 cần thảo luận thêm về hướng tích hợp với douyin_tiktok_api service.*
