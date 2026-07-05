# UAT Retest Report — Downloader Ultimate (Lần 3)
**Ngày test:** 2026-07-05  
**Tester:** BA (End User perspective)  
**Server:** pphu@192.168.1.200  
**Branch tested:** `main` @ commit `ab177ff`  
**Kết quả tổng:** ❌ **FAIL — Build vẫn thất bại, BUG-11 chưa được fix đúng cách**

---

## TÓM TẮT EXECUTIVE

> PM lead đã push fix cho BUG-10 (poetry.lock) và cố gắng fix BUG-11 (setuptools). BUG-10 đã fix thành công. Tuy nhiên BUG-11 vẫn còn — cách fix `pip install setuptools>=68.0` không đủ vì Poetry tạo **isolated build environment** riêng biệt khi build `openai-whisper`, và environment đó không có `pkg_resources`. Toàn bộ UAT vẫn bị blocked.

---

## PHẦN 1 — XÁC NHẬN FIX TỪ LẦN 2

| Bug | Mô tả | Kết quả verify lần 3 |
|-----|-------|----------------------|
| BUG-01 | Dependency conflict `googletrans` vs `httpx` | ✅ **FIXED** (confirmed từ lần 2) |
| BUG-02 | `python = "^3.11"` sai section | ✅ **FIXED** (confirmed từ lần 2) |
| BUG-03 | Toàn bộ endpoints thiếu auth | ✅ **FIXED** (confirmed từ lần 2) |
| BUG-04 | API keys lưu in-memory | ✅ **FIXED** (confirmed từ lần 2) |
| BUG-05 | Job state lưu in-memory | ✅ **FIXED** (confirmed từ lần 2) |
| BUG-06 | Celery worker không được dùng | ✅ **FIXED** (confirmed từ lần 2) |
| BUG-07 | `GET /jobs` lộ jobs tất cả users | ✅ **FIXED** (confirmed từ lần 2) |
| BUG-08 | Hardcoded backdoor key | ✅ **FIXED** (confirmed từ lần 2) |
| BUG-10 | `poetry.lock` là file rỗng | ✅ **FIXED** — file thật 4497 dòng đã được commit tại `ab177ff` |

---

## PHẦN 2 — BUG VẪN CÒN TỒN TẠI

---

### 🔴 BUG-11 | BLOCKER | `openai-whisper` không build được — Fix chưa đúng chỗ

| Trường | Giá trị |
|--------|---------|
| **Severity** | Blocker |
| **File** | `backend/Dockerfile` |
| **Commit thử fix** | `ab177ff` |
| **Phát hiện** | `docker compose build` vẫn fail với cùng error |

**Fix đã được apply (nhưng chưa đủ):**
```dockerfile
# PM lead đã sửa thành:
RUN pip install "setuptools>=68.0" poetry==1.8.3
```

**Tại sao fix này KHÔNG hiệu quả:**

`setuptools` được cài vào Python **global environment** của container. Tuy nhiên, khi Poetry install `openai-whisper (20231117)`, nó tạo một **isolated build environment** tại đường dẫn tạm thời `/tmp/tmpXXXXXX/.venv`. Environment này là một Python venv mới, hoàn toàn tách biệt với global environment, và **không kế thừa** `setuptools` từ global.

`openai-whisper`'s `setup.py` gọi `import pkg_resources` (một phần của `setuptools`), nhưng trong isolated build venv đó, `pkg_resources` không tồn tại.

**Error log thực tế:**
```
#11 351.0   File "/tmp/tmpzjlzvozu/.venv/lib/python3.11/site-packages/setuptools/build_meta.py"
#11 351.0     File "<string>", line 5, in <module>
#11 351.0   ModuleNotFoundError: No module named 'pkg_resources'
#11 351.0
#11 351.0 Note: This error originates from the build backend, and is likely not a problem
#11 351.0 with poetry but with openai-whisper (20231117) not supporting PEP 517 builds.
```

**Đường dẫn setuptools trong isolated env:**
```
/tmp/tmpzjlzvozu/.venv/lib/python3.11/site-packages/setuptools/build_meta.py  ← có
ModuleNotFoundError: No module named 'pkg_resources'                            ← KHÔNG có
```

*(setuptools được tải vào isolated env nhưng phiên bản mới của setuptools đã tách `pkg_resources` thành module riêng không tự động available)*

---

**Cách fix đúng — PM lead chọn 1 trong 2 options:**

**Option A (Khuyến nghị — đơn giản nhất):** Bypass Poetry build isolation cho `openai-whisper` bằng cách cài pip trực tiếp trước khi chạy poetry:

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg curl && rm -rf /var/lib/apt/lists/*

RUN pip install "setuptools>=68.0" poetry==1.8.3

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

# Cài openai-whisper qua pip với --no-build-isolation trước khi poetry chạy
# Điều này bypass isolated env và dùng global setuptools có sẵn
RUN pip install openai-whisper==20231117 --no-build-isolation

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --without dev

COPY . .
RUN mkdir -p /data/jobs
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Option B (Thay thế package):** Thay `openai-whisper` bằng `faster-whisper` — package hiện đại hơn, hỗ trợ PEP 517 đúng cách, tốc độ nhanh hơn 2-4x:

```toml
# pyproject.toml — thay dòng:
openai-whisper = "20231117"
# bằng:
faster-whisper = "^1.0.3"
```

*(Cần update code trong `app/services/transcriber.py` để dùng `faster_whisper.WhisperModel` thay vì `whisper.load_model`)*

---

## PHẦN 3 — UAT TEST CASES SUMMARY

| # | Test Case | Lần 1 | Lần 2 | Lần 3 | Ghi chú |
|---|-----------|-------|-------|-------|---------|
| UC-01 | Download TikTok | ❌ BLOCKED | ❌ BLOCKED | ❌ BLOCKED | Build fail |
| UC-02 | Download Douyin | ❌ BLOCKED | ❌ BLOCKED | ❌ BLOCKED | Build fail |
| UC-03 | Subtitle tiếng Việt | ❌ BLOCKED | ❌ BLOCKED | ❌ BLOCKED | Build fail |
| UC-04 | Lồng tiếng | ❌ BLOCKED | ❌ BLOCKED | ❌ BLOCKED | Build fail |
| UC-05 | Logo overlay | ❌ BLOCKED | ❌ BLOCKED | ❌ BLOCKED | Build fail |
| UC-06 | n8n Integration | ❌ BLOCKED | ❌ BLOCKED | ❌ BLOCKED | Build fail |
| UC-07 | Security check | ❌ FAIL | ❌ BLOCKED | ❌ BLOCKED | Build fail |

**0/7 test cases pass (lần 3).**

---

## PHẦN 4 — PRIORITY FIX LIST cho PM Lead (Lần 3)

Chỉ còn **1 bug** cần fix để unblock toàn bộ UAT:

| Priority | Bug ID | File | Action |
|----------|--------|------|--------|
| **P0** | BUG-11 | `backend/Dockerfile` | Xem Option A hoặc B ở Phần 2 |

**Ước tính thời gian fix: 10-15 phút.**

---

## PHẦN 5 — NHẬN XÉT

### Điểm tích cực ✅
- BUG-10 fix xuất sắc — `poetry.lock` thật với 4497 dòng, build phase đầu tiên thành công
- PM lead còn thêm `.github/workflows/ci.yml` với Docker build step — đúng theo recommendation của BA lần 2
- Tất cả 10 bugs từ 2 lần trước đã fix đúng hướng

### Điểm cần cải thiện ⚠️
- BUG-11 fix chưa test locally trước khi báo cáo — nếu thử `docker build` trên máy dev sau khi fix, lỗi này đã bị catch
- Root cause của BUG-11 là **Poetry build isolation**, không đơn giản là "thiếu setuptools" — cần hiểu đúng cơ chế để fix đúng

---

*BA sẵn sàng thực hiện lần retest 4 ngay khi nhận được confirm từ PM lead về BUG-11 fix.*  
*Đây là bug cuối cùng — sau khi fix, sẽ test đầy đủ 7 UAT cases và report kết quả trong ngày.*
